# Running the Toolkit

```bash
pip install -r requirements.txt
make data      # regenerate sample_data/ (seeded)
make demo      # every report
make test      # unit tests, SQL/Python parity, prompt evals
make webhook   # enrichment API on :8000
```

No API keys needed. Run any SQL file with `python -m shared_core.metrics.run_sql <file.sql>`.

| Command | Track | Output |
|---|---|---|
| `python -m shared_core.data_quality.dq_monitor` | 🟪 | Rule pass rates; `outputs/dq_failures.csv` |
| `python -m gtm_engineer.lead_scoring.score_leads` | 🟦 | Grade grid, top leads |
| `python -m gtm_engineer.lead_scoring.calibrate_scoring` | 🟦 | Conversion by grade; segment weight suggestions |
| `python -m gtm_engineer.lead_routing.route_leads` | 🟦 | R1–R7 decisions with reasons |
| `python -m gtm_engineer.lead_lifecycle.lifecycle_sla` | 🟦 | SLA by SDR and source |
| `python -m gtm_engineer.funnel_analytics.funnel_report` | 🟦 | Cohort funnel, velocity, outlook |
| `python -m gtm_engineer.sdr_capacity.capacity_model` | 🟦 | Headcount math |
| `python -m gtm_engineer.ai_research.account_research` | 🟦 | AI briefs → review queue |
| `python -m gtm_strategy_ops.pipeline_analytics.pipeline_report` | 🟩 | Coverage, segmentation, aging |
| `python -m gtm_strategy_ops.forecasting.forecast_accuracy` | 🟩 | Accuracy and bias by region |
| `python -m gtm_strategy_ops.ai_deal_risk.deal_risk` | 🟩 | Risk queue + AI commentary |
| `python -m gtm_strategy_ops.consumption.commit_burndown` | 🟩 | Overage and shelfware |
| `python -m gtm_strategy_ops.renewals.renewal_signals` | 🟩 | Renewal health, GRR, cross-sell |
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

**Change an assumption:** edit `config/company.yaml` and re-run. Weights, stages, SLAs, consumption thresholds and quota flow through every script.
