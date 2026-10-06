# Renewal Process

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** design the renewal process, capture closed-lost and churn insights for actionable analysis, and act as operational partner to sales, finance and customer success.

## Timeline (anchored to renewal date, T)

| When | Step | Owner | System |
|---|---|---|---|
| **T-180** | Renewal opportunity auto-created (`Type = Renewal`, amount = current ARR, stage 1) | System (flow on contract) | CRM |
| **T-180** | Health score computed ([`renewal_signals.py`](renewal_signals.py)); band written to the opportunity | RevOps | Warehouse → CRM |
| **T-150** | **At Risk:** AI renewal brief → CS + AE review → escalation plan. **Healthy with expansion signal:** create a linked Expansion opportunity. | CSM + AE | CRM, chat |
| **T-120** | Usage review with the customer: review the usage trend against what they bought. | CSM | — |
| **T-90** | Commercial proposal. Renewal forecast category set (Commit only with a verbal yes). | AE | Salesforce Forecasts (assumed) |
| **T-60** | Security and legal paperwork started. Regulated and enterprise buyers need this lead time. | AE + Legal | — |
| **T-30** | Signature target. Escalate to the VP if unsigned. | AE | — |
| **T+0** | Closed Won / Closed Lost; **churn reason required** ([taxonomy](closed-lost-and-churn-taxonomy.md)) | AE | CRM |

## Forecasting renewals

- Renewals are forecast **separately** from new business in Salesforce Forecasts (assumed) (a separate forecast type), so a large renewal can't mask a new-logo miss, or the reverse.
- Forecast GRR = 1 − Σ(ARR × expected churn by health band). Expected churn rates per band are calibrated quarterly against actual outcomes.
- Track gross and net retention by **product line**. Product lines can carry very different risk profiles.

## Health model inputs (aggregated only, no transaction data)

| Component | Weight | Source |
|---|---|---|
| Volume trend (90d) | 30% | Usage telemetry |
| Utilization of committed volume | 20% | Billing |
| Sev-1 tickets (90d) | 15% | Support system |
| Exec sponsor active | 20% | CSM-maintained field |
| Competitive signal | 15% | Gong (assumed) mentions, AE flag |
