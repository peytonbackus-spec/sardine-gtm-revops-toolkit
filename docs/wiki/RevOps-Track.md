# 🟩 RevOps Track

Track README: [gtm_strategy_ops/README.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/README.md)

| Piece | What it does | Code |
|---|---|---|
| Stage gates | 5 stages with exit criteria; stage 3 = sandbox + backtest, stage 4 = security + model-risk review | [stage-definitions.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/opportunity_lifecycle/stage-definitions.md) |
| Pipeline | Coverage vs quota by region; pipeline by product line, source, owner; aging past stage limits | [pipeline_report.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/pipeline_analytics/pipeline_report.py) |
| Forecast | Week 4/8/12 commit accuracy and bias by region, with an adjustment factor | [forecast_accuracy.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/forecasting/forecast_accuracy.py) |
| Deal risk | Rules score risk; AI writes the deal and region commentary; human review | [ai_deal_risk/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_strategy_ops/ai_deal_risk/) |
| **Consumption** | Usage vs minimum commit: overage and shelfware | [[Consumption and Lead to Cash]] |
| Renewals | Health score, forecast GRR, fraud ↔ compliance cross-sell signals | [renewal_signals.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/renewals/renewal_signals.py) |
| Closed-lost | Loss reasons and competitors → owner actions | [closed_lost_analysis.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/renewals/closed_lost_analysis.py) |
| **VP of Sales reporting** | Snapshot or full brief; reps, industries, stage bottlenecks, hot and at-risk deals; all-hands inputs | [[Sales Leadership and Planning]] |
| Planning | Capacity and hiring, quota vs capacity, territory balance, pipeline distribution, CRM request intake | [sales_planning/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_strategy_ops/sales_planning/) |
