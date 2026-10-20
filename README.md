# Cloud governance simulator

A small Streamlit app that checks a **sample Azure estate** against **real Azure Policy definitions** and shows how compliance, risk and cost change when guardrails are switched on or off.

It is a simulation. It does not connect to Azure and does not deploy anything. The policy files are written in the Azure Policy format, so the same JSON can be deployed to Azure later.

## What it shows

| Area | In this repo |
|---|---|
| Policy-as-code | 7 policy definitions in `policies/` (required tag, allowed regions, no public blobs, HTTPS only, SQL TLS 1.2, no public IP on VMs, Key Vault purge protection) |
| Cloud operating model | Owner and exception approver for each guardrail; decision rights in `docs/operating-model.md` |
| DevSecOps | GitHub Actions workflow that validates the policy files and runs the tests on every push |
| FinOps | Cost by costCenter, share of spend without a tag, budget warnings |
| Risk | Risk = severity x exposure x age, per finding |

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
pytest
```

## How it works

- `governance/engine.py` evaluates a subset of the Azure Policy rule language: `field` with `equals`, `notEquals`, `in`, `notIn`, `exists`, and `allOf`, `anyOf`, `not`.
- `governance/risk.py` scores each finding.
- `governance/finops.py` and `governance/summary.py` produce the cost and headline numbers.
- `data/sample_estate.json` is an invented estate of 20 resources.

## Origin of the risk model

The scoring idea comes from the moderation-risk model I wrote for the Caucasus Watch TikTok analysis (tone weight x visibility x age). Here the same three parts become severity x exposure x age. One part is reversed: in the TikTok model an older post is less risky, while a cloud misconfiguration that stays open is more risky, so the age factor grows (capped at 2).

## Limits

- The estate is invented and small. The numbers show how the model behaves, not a real organisation.
- Only the policy conditions listed above are supported.
- Severity weights and exposure factors are my own choices and are easy to change.

## Next

- Deploy the same policies to a free Azure subscription with Bicep and a GitHub Actions pipeline that signs in with OIDC.
- Read the estate from `az resource list` output instead of the sample file.
