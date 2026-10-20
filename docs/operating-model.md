# Operating model (sample)

This is the operating model the simulator assumes for a small Azure estate. It is a working draft for discussion, not a description of a real company.

## Roles

| Role | Decides | Does not decide |
|---|---|---|
| Cloud platform lead | Landing-zone design, allowed regions, exceptions for platform guardrails | Security exceptions |
| Security & compliance | Data-protection and compliance guardrails, security exceptions | Cost budgets |
| FinOps lead | Tagging standard, budgets, cost reporting | Security exceptions |
| Platform engineering | Network and resilience guardrails, pipeline templates | Regions, budgets |
| Application teams | Their own resources inside the guardrails | The guardrails themselves |

## Decision rights for a guardrail

1. The **owner** proposes and maintains the policy (see the Operating model tab).
2. A policy starts as **audit** so teams can see the impact. It moves to **deny** once existing findings are cleaned up.
3. An application team that must break a guardrail asks the **exception approver**. The exception has a reason and an end date.
4. Exceptions are reviewed monthly. An exception with no end date is itself a finding.

## Service management

- Findings from `audit` policies go into the owning team's backlog, ordered by risk points.
- Findings from `deny` policies are blocked at deployment, so they should only appear on resources that existed before the policy.

## Metrics the simulator reports

- Share of compliant resources
- Open findings and risk points (severity x exposure x age)
- Share of spend without a costCenter tag
- Cost centers over budget
