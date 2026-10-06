# Closed-Lost & Churn Taxonomy

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** capture closed-lost and churn insights for actionable analysis.

One picklist for new-business losses and one for churn. Each value has an owner who acts on it. Values are mirrored in the company config (`opportunity.closed_lost_reasons`) so the code and the CRM can't drift.

## New business: `Closed_Lost_Reason__c` (required on Closed Lost)

| Value | Use when | Required detail | Fix owner |
|---|---|---|---|
| Price | Chose a cheaper option or no budget at our price | Competitor or alternative price, if known | Sales leadership |
| Lost to Competitor | Signed with a named vendor | `Competitor__c` required | Product Marketing |
| No Decision / Status Quo | Project stopped; stayed with the current process | Last stage reached | Sales |
| Build In-House | Building internally | — | Product |
| Security / Compliance Blocker | Failed the security review, data residency or regulator concern | Specific blocker | Security / Legal |
| Integration Effort | Couldn't resource the integration (core system, app, onboarding flow) | System involved | Solutions Engineering |
| Timing / Budget | Real need, wrong quarter or fiscal year | Re-engage date (auto-creates a task) | Marketing nurture |
| Champion Left | Champion or sponsor departed mid-cycle | — | Sales ops (multi-threading standard) |

## Churn and downgrade: `Churn_Reason__c` (required on lost renewal or downsell)

| Value | Notes | Signal that predicted it (validate quarterly) |
|---|---|---|
| Volume decline | Fewer transactions or seats. Check whether it is structural or temporary. | `volume_trend` component |
| Consolidated vendor | Moved to a platform bundle from a larger vendor | `competitive` component |
| M&A | Acquired; acquirer's vendor won | News signal |
| Product gap | Needed a capability we lack | Gong (assumed) mentions |
| Service / support | Sev-1 history, implementation issues | `support` component |
| Price at renewal | Pushback on uplift or commit | — |
| Business closure | — | — |

## Review loop

- **Monthly:** [`closed_lost_analysis.py`](closed_lost_analysis.py) output reviewed with Sales and Product Marketing leaders. Each top reason gets an owner and a dated action.
- **Quarterly:** check the [renewal health model](renewal_signals.py) against what actually churned. Did the drivers we weighted predict the churn reasons we got? Re-weight if not.
- **Data quality:** blank reasons are tracked in the [DQ monitor](../../shared_core/data_quality/dq_monitor.py) (rule O03). An "Other" value is deliberately not allowed.
