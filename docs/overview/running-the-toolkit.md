# Running the Toolkit

## Setup

```bash
pip install -r requirements.txt     # PyYAML, pytest, plus FastAPI/pydantic for the enrichment API tests
make test                           # unit tests, SQL/Python parity, prompt evals
make demo                           # every report, both tracks
```

No API keys needed. The AI workflows use a deterministic mock model by default. To run the same prompts live: `GTM_LLM_MODE=anthropic ANTHROPIC_MODEL=<model> ANTHROPIC_API_KEY=... python -m ...`

## Commands

| Command | Role | Output |
|---|---|---|
| `make data` | — | Regenerates `sample_data/` (seeded, identical every time) |
| `python -m shared_core.data_quality.dq_monitor` | 🟪 | Rule pass rates; `outputs/dq_failures.csv` |
| `python -m shared_core.metrics.run_sql <file.sql>` | 🟪 | Runs any SQL file against sample data |
| `python -m gtm_engineer.lead_scoring.score_leads` | 🟦 | Grade grid, top leads |
| `python -m gtm_engineer.lead_scoring.calibrate_scoring` | 🟦 | Conversion by grade; weight suggestions |
| `python -m gtm_engineer.lead_routing.route_leads` | 🟦 | R1–R7 decisions with reasons |
| `python -m gtm_engineer.lead_lifecycle.lifecycle_sla` | 🟦 | SLA by SDR and source; stuck leads |
| `python -m gtm_engineer.ai_research.account_research` | 🟦 | AI briefs → review queue + audit log |
| `python -m gtm_engineer.funnel_analytics.funnel_report` | 🟦 | Cohort funnel, velocity, penetration, outlook, narrative |
| `python -m gtm_engineer.sdr_capacity.capacity_model` | 🟦 | Headcount math with sensitivity |
| `make webhook` | 🟦 | Enrichment waterfall API on port 8000 |
| `python -m gtm_strategy_ops.pipeline_analytics.pipeline_report` | 🟩 | Coverage, segmentation, win rates, aging, narrative |
| `python -m gtm_strategy_ops.forecasting.forecast_accuracy` | 🟩 | Accuracy and bias by region |
| `python -m gtm_strategy_ops.ai_deal_risk.deal_risk` | 🟩 | Risk queue + AI region commentary |
| `python -m gtm_strategy_ops.renewals.renewal_signals` | 🟩 | Renewal health, forecast GRR, expansion signals |
| `python -m gtm_strategy_ops.renewals.closed_lost_analysis` | 🟩 | Loss reasons → owner actions |
| `python -m gtm_strategy_ops.sales_leadership.vp_brief [--mode full]` | 🟩 | VP of Sales snapshot or full brief → `outputs/vp_brief_*.md` |
| `python -m gtm_strategy_ops.sales_leadership.all_hands [--days 1]` | 🟩 | All-hands inputs for last quarter, or "what happened today" |
| `python -m gtm_strategy_ops.sales_leadership.stage_velocity` | 🟩 | Stage bottlenecks, drivers, deals stuck now |
| `python -m gtm_strategy_ops.sales_planning.capacity_plan` | 🟩 | Capacity vs plan, hiring plan |
| `python -m gtm_strategy_ops.sales_planning.quota_plan` | 🟩 | Quota vs capacity, next year's proposal |
| `python -m gtm_strategy_ops.sales_planning.territory_plan` | 🟩 | Account tiers, named books, balance |
| `python -m gtm_strategy_ops.sales_planning.pipeline_distribution` | 🟩 | Per-rep load, coverage, concentration; routing priority |
| `python -m gtm_strategy_ops.sales_planning.request_triage` | 🟩 | CRM request SLA, queue order, duplicates |
| `python -m gtm_engineer.marketing_ops.campaign_report` | 🟦 | Channel ROI, attribution, campaign and consent hygiene |
| `python -m gtm_engineer.marketing_ops.demand_plan` | 🟦 | Leads and MQLs needed by channel |

## Changing assumptions

Edit the company config (`config/company.yaml`) and re-run. Segment weights, persona points, stage limits, SLAs, health weights, fiscal calendar and quota all flow through every script. Point at another config with `GTM_CONFIG=path/to/file.yaml`.
