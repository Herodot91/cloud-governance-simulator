"""Cloud governance simulator: switch policies on and off, grant exceptions,
and see compliance, risk and cost change for a sample Azure estate."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from governance.engine import evaluate, load_estate, load_policies
from governance.finops import UNTAGGED, cost_by_cost_center, over_budget, untagged_share
from governance.risk import score_findings
from governance.summary import blocked_at_deploy, compliance_percent, total_risk

ROOT = Path(__file__).parent
st.set_page_config(page_title="Cloud governance simulator", layout="wide")

estate = load_estate(ROOT / "data" / "sample_estate.json")
policies = load_policies(ROOT / "policies")
names = {p["name"]: p["displayName"] for p in policies}

st.title("Cloud governance simulator")
st.caption("A sample Azure estate checked against real Azure Policy definitions. "
           "Turn policies on or off, grant exceptions, and watch compliance, risk and cost change.")

# ---------- sidebar: policies, exceptions, budgets ----------
st.sidebar.header("Guardrails")
active = [p for p in policies if st.sidebar.checkbox(
    f"{p['displayName']} ({p['effect']})", value=True, key=p["name"])]

st.sidebar.header("Exceptions")
baseline = evaluate(estate, active)
options = [f"{f['resource']} | {f['policy']}" for f in baseline]
chosen = st.sidebar.multiselect("Approved exceptions", options,
                                help="An exception removes one finding. In real life the exception approver decides.")
exceptions = {tuple(c.split(" | ")) for c in chosen}

st.sidebar.header("Monthly budgets (EUR)")
centers = sorted({r["tags"].get("costCenter") for r in estate if r["tags"].get("costCenter")})
budgets = {cc: st.sidebar.number_input(cc, min_value=0, value=600, step=50) for cc in centers}

# ---------- evaluation ----------
all_policies_findings = score_findings(evaluate(estate, policies), estate, policies)
findings = score_findings(evaluate(estate, active, exceptions), estate, policies)
df = pd.DataFrame(findings)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Findings", "FinOps", "Operating model", "What-if"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliant resources", f"{compliance_percent(estate, findings)}%")
    c2.metric("Open findings", len(findings))
    c3.metric("Risk points", total_risk(findings))
    c4.metric("Spend without costCenter", f"{untagged_share(estate)}%")
    if df.empty:
        st.success("No open findings with the current guardrails and exceptions.")
    else:
        left, right = st.columns(2)
        by_policy = df.groupby("policy").size().rename("findings").reset_index()
        by_policy["policy"] = by_policy["policy"].map(names)
        left.plotly_chart(px.bar(by_policy, x="findings", y="policy", orientation="h",
                                 title="Findings by policy"), width="stretch")
        top = df.groupby("resource")["risk"].sum().sort_values(ascending=False).head(8).reset_index()
        right.plotly_chart(px.bar(top, x="risk", y="resource", orientation="h",
                                  title="Highest-risk resources"), width="stretch")
    st.caption("Risk = severity x exposure x age. The model is adapted from my moderation-risk model "
               "for the Caucasus Watch TikTok analysis. Here, older findings are riskier, not less risky.")

with tab2:
    if df.empty:
        st.info("Nothing to show.")
    else:
        view = df.copy()
        view["policy"] = view["policy"].map(names)
        st.dataframe(view.sort_values("risk", ascending=False), width="stretch", hide_index=True)

with tab3:
    totals = cost_by_cost_center(estate)
    cost_df = pd.DataFrame({"costCenter": list(totals), "monthlyCostEur": list(totals.values())})
    st.plotly_chart(px.bar(cost_df, x="costCenter", y="monthlyCostEur",
                           title="Monthly cost by costCenter (EUR)"), width="stretch")
    st.write(f"**{untagged_share(estate)}%** of spend has no costCenter tag (shown as {UNTAGGED}).")
    for cc, (cost, budget) in over_budget(estate, budgets).items():
        st.warning(f"{cc} is over budget: {cost:.0f} EUR against {budget} EUR.")

with tab4:
    st.subheader("Who owns what")
    st.dataframe(pd.DataFrame([{
        "Guardrail": p["displayName"], "Effect": p["effect"], "Category": p["category"],
        "Owner": p["owner"], "Exception approver": p["exceptionApprover"]} for p in policies]),
        width="stretch", hide_index=True)
    st.markdown(
        "**Decision rights.** The owner maintains the guardrail. The exception approver decides "
        "whether a resource may break it, for a limited time. Every exception is listed in the sidebar "
        "so it can be reviewed. See `docs/operating-model.md`.")

with tab5:
    base = score_findings(evaluate(estate, policies), estate, policies)
    now = findings
    b1, b2 = st.columns(2)
    b1.metric("Compliance with all guardrails", f"{compliance_percent(estate, base)}%")
    b2.metric("Compliance with your selection", f"{compliance_percent(estate, now)}%",
              delta=f"{compliance_percent(estate, now) - compliance_percent(estate, base):.1f} pts")
    blocked = blocked_at_deploy(now)
    st.write(f"With your selection, **{len(blocked)}** existing findings come from `deny` policies. "
             "These would have been blocked at deployment. The rest are `audit` findings: "
             "reported, not blocked.")
    st.write(f"Switching guardrails off hides {len(all_policies_findings) - len(findings)} findings. "
             "That is a lower number on the dashboard, not a safer estate.")
