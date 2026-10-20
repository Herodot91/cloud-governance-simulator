"""Risk scoring.

Adapted from the moderation-risk model I wrote for the Caucasus Watch TikTok analysis:
    risk = tone_weight x visibility_factor x age_factor
Here the same three-part idea is used for cloud misconfigurations:
    risk = severity x exposure_factor x age_factor
One difference: in the TikTok model an older post is less risky (the factor decays).
For a cloud misconfiguration the opposite is true: the longer it stays open, the riskier it is.
"""

EXPOSURE_FACTOR = {"internet": 1.5, "partner": 1.0, "internal": 0.4, "isolated": 0.1}
POINTS = 10  # scale so one severe, internet-exposed, year-old finding is up to about 30 points


def age_factor(age_days):
    return min(1 + 0.01 * max(age_days, 0), 2.0)


def finding_risk(severity, exposure, age_days):
    return round(severity * EXPOSURE_FACTOR.get(exposure, 0.4) * age_factor(age_days) * POINTS, 1)


def score_findings(findings, estate, policies):
    """Add a risk value to each finding row (resource, policy, effect)."""
    by_resource = {r["name"]: r for r in estate}
    by_policy = {p["name"]: p for p in policies}
    scored = []
    for f in findings:
        r, p = by_resource[f["resource"]], by_policy[f["policy"]]
        scored.append({**f,
                       "category": p["category"],
                       "severity": p["severity"],
                       "exposure": r["exposure"],
                       "ageDays": r["ageDays"],
                       "risk": finding_risk(p["severity"], r["exposure"], r["ageDays"])})
    return scored
