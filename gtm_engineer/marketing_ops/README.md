# Marketing Ops: working with RevOps

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

The RevOps Manager role works closely with Marketing Ops (Sardine has a separate Marketing Ops posting naming HubSpot, ZoomInfo, Influ2 and Google Analytics). The line between them is where most data breaks: the HubSpot ↔ Salesforce sync, the MQL hand-off, campaign attribution and consent. This folder covers that line.

## What's here

| Piece | What it answers | Runs? |
|---|---|---|
| [`campaign_report.py`](campaign_report.py) | Channel funnel and ROI, W-shaped attribution, campaign and consent hygiene (M01–M09) | ▶ |
| [`demand_plan.py`](demand_plan.py) | The reverse funnel: from the bookings plan to pipeline, opps by source, and leads and MQLs by channel, vs the last 90 days | ▶ |
| [Campaign operations spec](campaign-operations-spec.md) | Naming, member statuses, UTMs, list imports, consent, attribution | 📐 |

And elsewhere in the repo, the pieces Marketing Ops depends on:

| Piece | Where |
|---|---|
| MQL definition, MQL → SAL SLA, recycle rules | [Lead lifecycle spec](../lead_lifecycle/lead-lifecycle-spec.md) · [`lifecycle_sla.py`](../lead_lifecycle/lifecycle_sla.py) |
| Lead scoring (fit × intent) and whether it predicts conversion | [`score_leads.py`](../lead_scoring/score_leads.py) · [`calibrate_scoring.py`](../lead_scoring/calibrate_scoring.py) |
| Routing into segment × region pods | [`route_leads.py`](../lead_routing/route_leads.py) |
| Funnel by cohort and source | [`funnel_report.py`](../funnel_analytics/funnel_report.py) |
| HubSpot ↔ Salesforce sync: field ownership, inclusion rules | [Stack map](../../shared_core/context/gtm-stack-map.md) · [sync architecture](../../docs/specs/architecture/Salesforce_HubSpot_Sync_Architecture.md) · [sync inclusion rules](../../docs/specs/architecture/Sync_Inclusion_Rules.md) |
| Enrichment (Clay, ZoomInfo) | [Enrichment waterfall](../platform_admin/enrichment-waterfall.md) |
| Database health (duplicates, missing fields) | [`dq_monitor.py`](../../shared_core/data_quality/dq_monitor.py) |
| One request queue for Salesforce and HubSpot changes | [CRM request intake](../../gtm_strategy_ops/sales_planning/crm-request-intake.md) |
| Pipeline needed and source mix, agreed with Sales | [Demand plan](demand_plan.py) · [capacity plan](../../gtm_strategy_ops/sales_planning/capacity_plan.py) |

## Who owns what

R = does it, A = accountable, C = consulted. A working proposal to agree in the first 30 days.

| Area | Marketing Ops | RevOps | Sales leadership |
|---|---|---|---|
| HubSpot (forms, lists, workflows, email, subscription status) | A/R | C | |
| Salesforce objects, fields, validation, automation | C | A/R | C |
| HubSpot ↔ Salesforce sync rules and field ownership | R | A | |
| Campaign taxonomy, member statuses, UTMs | A/R | C | |
| MQL definition and lead scoring model | A | R (build, calibrate) | C |
| MQL → SAL SLA and routing | C | A/R | C |
| Event and webinar list imports | A/R | C | |
| Consent and opt-out handling | A/R (with Legal) | C | |
| Attribution model and channel ROI reporting | R | A (one metric definition) | C |
| Demand plan (leads and MQLs needed by channel) | R | A | C |
| Pipeline target and source mix | C | R | A |

## The joint cadence

| When | What |
|---|---|
| Weekly | Funnel and SLA check (MQL → SAL, list-import lag, hygiene report); CRM request review |
| Monthly | Channel ROI and attributed pipeline; demand plan vs run rate; scoring calibration |
| Quarterly | Source-mix target and demand plan for the next two quarters, agreed with Sales; campaign taxonomy review |

## Questions for Marketing Ops in week one

1. Where does the MQL definition live today, and who changes it?
2. Which fields does HubSpot own and which does Salesforce own? Any sync errors we live with?
3. How are event and webinar lists loaded today, and how long does it take?
4. How is consent captured for Canadian and EU/UK contacts?
5. What attribution view does leadership see today, and do Sales and Marketing agree with it?
6. What is Marketing's pipeline target, and how was it set?
7. What request to Sales Ops / RevOps has waited the longest?

> Campaigns, members, spend and consent records in `sample_data/` are synthetic. Campaign names follow the convention; a few break it on purpose so the hygiene report has something to find.
