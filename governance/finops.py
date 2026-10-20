"""Cost views for the FinOps part of the simulator."""
UNTAGGED = "UNTAGGED"


def cost_by_cost_center(estate):
    totals = {}
    for r in estate:
        key = r.get("tags", {}).get("costCenter", UNTAGGED)
        totals[key] = round(totals.get(key, 0) + r["monthlyCostEur"], 2)
    return totals


def untagged_share(estate):
    total = sum(r["monthlyCostEur"] for r in estate)
    if total == 0:
        return 0.0
    untagged = sum(r["monthlyCostEur"] for r in estate if "costCenter" not in r.get("tags", {}))
    return round(100 * untagged / total, 1)


def over_budget(estate, budgets):
    """Cost centers whose monthly cost is above their budget (EUR)."""
    totals = cost_by_cost_center(estate)
    return {cc: (cost, budgets[cc]) for cc, cost in totals.items() if cc in budgets and cost > budgets[cc]}
