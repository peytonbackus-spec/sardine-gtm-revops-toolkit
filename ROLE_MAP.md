# Role Map: Sardine Revenue Operations Manager

Every responsibility and requirement in the [Revenue Operations Manager posting](https://jobs.ashbyhq.com/sardine/b6ca1fd5-a374-4c99-a6fd-a0c4d0859a61), linked to the artifact in this repo that answers it. The posting describes the role as sitting "at the intersection of Revenue Operations and GTM Engineering", acting as the internal GTM Engineer. Sardine has also posted a separate GTM Engineer role, described as its "first GTM Engineer", and its scope is mapped at the bottom. In this repo, one person covers both 🟦 tracks and 🟩 tracks.

Legend: ▶ runs on sample data · 📐 spec / design · 🧪 tested in CI

## Responsibilities

| Posting asks for | Where it's answered | |
|---|---|---|
| **Next-gen tech evaluation:** own the evaluation of GTM technology so the stack scales in an AI-first world | [Stack evaluation framework](shared_core/context/gtm-stack-evaluation.md) · [stack map](shared_core/context/gtm-stack-map.md) | 📐 |
| **Analytics:** design, build and maintain analytics infrastructure tracking GTM performance | [Semantic layer SQL](shared_core/metrics/sql/semantic_layer.sql) · [metric definitions](shared_core/metrics/metric-definitions.md) · [funnel report](gtm_engineer/funnel_analytics/funnel_report.py) · [pipeline report](gtm_strategy_ops/pipeline_analytics/pipeline_report.py) | ▶ 🧪 |
| **Strategic insights** on key decisions | Narrative sections in every report; [scoring calibration](gtm_engineer/lead_scoring/calibrate_scoring.py) (which segments are mis-weighted); [forecast bias by region](gtm_strategy_ops/forecasting/forecast_accuracy.py); [closed-lost → owner actions](gtm_strategy_ops/renewals/closed_lost_analysis.py) | ▶ |
| **Vibe coding & automation:** use AI dev tools to build custom tools, integrations and automation | This repo, built AI-assisted: 14 runnable modules, a FastAPI enrichment webhook, a rules-engine waterfall, a lead-to-account matcher, and AI workflows with evals | ▶ 🧪 |
| **Cross-functional collaboration** with Sales, Marketing and Post-Sales leaders | [First 90 days](FIRST_90_DAYS.md) (stakeholder map and cadence); every action list is routed to a named owner | 📐 |
| **Project execution** against strategic initiatives | [First 90 days](FIRST_90_DAYS.md) · [roadmap](docs/overview/roadmap.md) · [decision log](docs/overview/decision-log.md) | 📐 |
| **Workflow automation across the lead-to-cash lifecycle** | [Lead-to-cash map](gtm_strategy_ops/consumption/lead-to-cash.md) · [commit burn-down](gtm_strategy_ops/consumption/commit_burndown.py) · [routing engine](gtm_engineer/lead_routing/route_leads.py) · [lifecycle SLAs](gtm_engineer/lead_lifecycle/lifecycle_sla.py) | ▶ 📐 |

## Requirements

| Posting asks for | Evidence here | |
|---|---|---|
| 5+ years in technical RevOps, GTM Engineering or Sales Systems | The breadth of this repo: lead scoring through renewal, plus the data model and governance underneath | n/a |
| AI coding assistants (Cursor, Claude, v0) | The repo itself, plus [AI governance](shared_core/ai_governance/README.md) for how AI output is controlled | 🧪 |
| Data analytics, clean data architecture, funnel metrics | [Data-quality monitor](shared_core/data_quality/dq_monitor.py) (16 rules, owner per rule) · [funnel SQL](gtm_engineer/funnel_analytics/sql/lead_funnel.sql) · Python/SQL parity tests | ▶ 🧪 |
| Prototypes over lengthy documentation | Every spec here has runnable code beside it; `make demo` runs all of it offline | ▶ |
| APIs, webhooks, middleware (Zapier, Clay, Workato, Tray.io) | [FastAPI enrichment webhook](gtm_engineer/integrations/webhook.py) · [waterfall rules engine](gtm_engineer/enrichment/rules_engine.py) · [enrichment waterfall spec](gtm_engineer/platform_admin/enrichment-waterfall.md) | ▶ 🧪 |
| Salesforce and GTM tools (HubSpot, Unify, Clay, n8n) | [Salesforce object model](shared_core/data_model/salesforce-object-model.md) · [routing flow spec](gtm_engineer/lead_routing/salesforce-routing-flow-spec.md) · [stack map](shared_core/context/gtm-stack-map.md) (HubSpot↔Salesforce field ownership, Unify/Clay boundary, n8n as orchestrator) | 📐 |
| Relational data models and process automation mapping | [Object model](shared_core/data_model/salesforce-object-model.md) · [lead-to-cash data model additions](gtm_strategy_ops/consumption/lead-to-cash.md#data-model-additions-salesforce) · [lead lifecycle spec](gtm_engineer/lead_lifecycle/lead-lifecycle-spec.md) | 📐 |
| Translate business needs into technical requirements | Every spec opens with the business question, then the design | 📐 |
| *Nice to have:* SQL, Python, JavaScript | Python throughout; SQL semantic layer, funnel and coverage models | ▶ 🧪 |
| *Nice to have:* high-growth fintech / complex B2B | Sardine-shaped model: two budgets (fraud vs compliance), bank TPRM gates, consumption revenue | ▶ |

## GTM Engineer posting: scope covered

| GTM Engineer posting asks for | Where it's answered | |
|---|---|---|
| Systems architecture: own the technical roadmap for the GTM stack | [Stack evaluation](shared_core/context/gtm-stack-evaluation.md) · [architecture](docs/overview/architecture.md) | 📐 |
| Workflow automation across lead-to-cash | [Lead-to-cash](gtm_strategy_ops/consumption/lead-to-cash.md) | 📐 |
| Data engineering & orchestration: pipelines between tools | [Enrichment waterfall](gtm_engineer/platform_admin/enrichment-waterfall.md) · [webhook](gtm_engineer/integrations/webhook.py) · [L2A matcher](gtm_engineer/enrichment/l2a_matcher.py) | ▶ 🧪 |
| Lifecycle engineering: the full customer journey | [Lead lifecycle](gtm_engineer/lead_lifecycle/lead-lifecycle-spec.md) → [stages](gtm_strategy_ops/opportunity_lifecycle/stage-definitions.md) → [consumption](gtm_strategy_ops/consumption/commit_burndown.py) → [renewals](gtm_strategy_ops/renewals/renewal_signals.py) | ▶ |
| CRM administration as configuration-as-code | All rules live in [`config/company.yaml`](config/company.yaml) and Git; CI tests every change | 🧪 |
| Performance dashboards and technical insights | [Funnel dashboard spec](gtm_engineer/funnel_analytics/dashboard-spec.md) · [pipeline dashboard spec](gtm_strategy_ops/pipeline_analytics/dashboard-spec.md) | 📐 |
