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
| `make run-webhook` | 🟦 | Enrichment waterfall API on port 8000 |
| `python -m gtm_strategy_ops.pipeline_analytics.pipeline_report` | 🟩 | Coverage, segmentation, win rates, aging, narrative |
| `python -m gtm_strategy_ops.forecasting.forecast_accuracy` | 🟩 | Accuracy and bias by region |
| `python -m gtm_strategy_ops.ai_deal_risk.deal_risk` | 🟩 | Risk queue + AI region commentary |
| `python -m gtm_strategy_ops.renewals.renewal_signals` | 🟩 | Renewal health, forecast GRR, expansion signals |
| `python -m gtm_strategy_ops.renewals.closed_lost_analysis` | 🟩 | Loss reasons → owner actions |

## Changing assumptions

Edit the company config (`config/company.yaml`) and re-run. Segment weights, persona points, stage limits, SLAs, health weights, fiscal calendar and quota all flow through every script. Point at another config with `GTM_CONFIG=path/to/file.yaml`.
