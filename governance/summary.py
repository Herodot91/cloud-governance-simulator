"""Headline numbers shown on the dashboard."""


def compliance_percent(estate, findings):
    """Share of resources with no open finding."""
    if not estate:
        return 100.0
    bad = {f["resource"] for f in findings}
    return round(100 * (len(estate) - len(bad)) / len(estate), 1)


def blocked_at_deploy(findings):
    """Findings from 'deny' policies: these would have been stopped at deployment time."""
    return [f for f in findings if f["effect"] == "deny"]


def total_risk(findings):
    return round(sum(f["risk"] for f in findings), 1)
