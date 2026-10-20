from pathlib import Path

from governance.engine import evaluate, load_estate, load_policies
from governance.finops import cost_by_cost_center, over_budget, untagged_share
from governance.risk import age_factor, finding_risk, score_findings
from governance.summary import compliance_percent, total_risk

ROOT = Path(__file__).parent.parent
POLICIES = load_policies(ROOT / "policies")
ESTATE = load_estate(ROOT / "data" / "sample_estate.json")


def test_older_findings_are_riskier_up_to_a_cap():
    assert age_factor(0) == 1
    assert age_factor(100) == 2.0
    assert age_factor(900) == 2.0


def test_internet_exposure_scores_higher_than_isolated():
    assert finding_risk(0.9, "internet", 300) > finding_risk(0.9, "isolated", 300)


def test_scored_findings_have_risk():
    scored = score_findings(evaluate(ESTATE, POLICIES), ESTATE, POLICIES)
    assert scored and all(f["risk"] > 0 for f in scored)
    assert total_risk(scored) > 0


def test_compliance_drops_when_findings_exist():
    assert compliance_percent(ESTATE, []) == 100.0
    scored = score_findings(evaluate(ESTATE, POLICIES), ESTATE, POLICIES)
    assert compliance_percent(ESTATE, scored) < 100.0


def test_cost_views():
    totals = cost_by_cost_center(ESTATE)
    assert round(sum(totals.values()), 2) == round(sum(r["monthlyCostEur"] for r in ESTATE), 2)
    assert 0 < untagged_share(ESTATE) < 100
    assert "CC-100" in over_budget(ESTATE, {"CC-100": 1})
