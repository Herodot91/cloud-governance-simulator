from pathlib import Path

from governance.engine import evaluate, load_estate, load_policies, matches

ROOT = Path(__file__).parent.parent
POLICIES = load_policies(ROOT / "policies")
ESTATE = load_estate(ROOT / "data" / "sample_estate.json")


def test_exists_false_flags_missing_tag():
    rule = {"field": "tags['costCenter']", "exists": "false"}
    assert matches({"tags": {}}, rule)
    assert not matches({"tags": {"costCenter": "CC-1"}}, rule)


def test_not_in_flags_other_regions():
    rule = {"field": "location", "notIn": ["westeurope"]}
    assert matches({"location": "eastus"}, rule)
    assert not matches({"location": "westeurope"}, rule)


def test_alias_and_boolean_comparison():
    rule = {"allOf": [{"field": "type", "equals": "Microsoft.Storage/storageAccounts"},
                      {"field": "Microsoft.Storage/storageAccounts/allowBlobPublicAccess", "equals": "true"}]}
    bad = {"type": "Microsoft.Storage/storageAccounts", "properties": {"allowBlobPublicAccess": True}}
    good = {"type": "Microsoft.Storage/storageAccounts", "properties": {"allowBlobPublicAccess": False}}
    assert matches(bad, rule) and not matches(good, rule)


def test_missing_property_is_not_equal():
    rule = {"field": "Microsoft.Sql/servers/minimalTlsVersion", "notEquals": "1.2"}
    assert matches({"properties": {}}, rule)


def test_exception_removes_finding():
    all_rows = evaluate(ESTATE, POLICIES)
    target = all_rows[0]
    rows = evaluate(ESTATE, POLICIES, {(target["resource"], target["policy"])})
    assert len(rows) == len(all_rows) - 1


def test_sample_estate_has_known_violations():
    rows = evaluate(ESTATE, POLICIES)
    flagged = {(r["resource"], r["policy"]) for r in rows}
    assert ("stlegacyexport", "storage-no-public-blob") in flagged
    assert ("vm-test-old", "vm-no-public-ip") in flagged
    assert ("sql-legacy", "sql-min-tls12") in flagged
    assert ("kv-prod", "keyvault-purge-protection") not in flagged
