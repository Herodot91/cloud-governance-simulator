"""Small evaluator for a subset of the Azure Policy rule language.

Supported conditions: field + equals / notEquals / in / notIn / exists,
and the logical operators allOf / anyOf / not. Policies are plain Azure
Policy definition JSON files, so the same files can later be deployed to Azure.
"""
import json
from pathlib import Path


def _norm(value):
    """Azure Policy compares booleans as strings; normalise everything to lowercase text."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).lower()


def resolve_field(resource, field):
    """Return (found, value) for a policy field name."""
    if field in ("type", "location", "name"):
        return field in resource, resource.get(field)
    if field.startswith("tags['") and field.endswith("']"):
        tag = field[6:-2]
        tags = resource.get("tags", {})
        return tag in tags, tags.get(tag)
    if "/" in field:  # alias such as Microsoft.Storage/storageAccounts/allowBlobPublicAccess
        prop = field.split("/")[-1]
        props = resource.get("properties", {})
        return prop in props, props.get(prop)
    return False, None


def matches(resource, condition):
    """True when the resource matches the policy 'if' condition."""
    if "allOf" in condition:
        return all(matches(resource, c) for c in condition["allOf"])
    if "anyOf" in condition:
        return any(matches(resource, c) for c in condition["anyOf"])
    if "not" in condition:
        return not matches(resource, condition["not"])

    found, value = resolve_field(resource, condition["field"])
    if "exists" in condition:
        return found == (_norm(condition["exists"]) == "true")
    if "equals" in condition:
        return found and _norm(value) == _norm(condition["equals"])
    if "notEquals" in condition:
        return (not found) or _norm(value) != _norm(condition["notEquals"])
    if "in" in condition:
        return found and _norm(value) in [_norm(v) for v in condition["in"]]
    if "notIn" in condition:
        return (not found) or _norm(value) not in [_norm(v) for v in condition["notIn"]]
    raise ValueError(f"Unsupported condition: {condition}")


def load_policies(folder):
    policies = []
    for path in sorted(Path(folder).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        props = data["properties"]
        meta = props.get("metadata", {})
        policies.append({
            "name": data["name"],
            "displayName": props["displayName"],
            "rule": props["policyRule"]["if"],
            "effect": props["policyRule"]["then"]["effect"],
            "severity": float(meta.get("severity", 0.5)),
            "owner": meta.get("owner", ""),
            "exceptionApprover": meta.get("exceptionApprover", ""),
            "category": meta.get("category", ""),
        })
    return policies


def load_estate(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(estate, policies, exceptions=None):
    """Return one row per (resource, violated policy). `exceptions` is a set of (resource, policy)."""
    exceptions = exceptions or set()
    rows = []
    for resource in estate:
        for policy in policies:
            if (resource["name"], policy["name"]) in exceptions:
                continue
            if matches(resource, policy["rule"]):
                rows.append({"resource": resource["name"], "policy": policy["name"], "effect": policy["effect"]})
    return rows
