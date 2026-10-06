# Pipeline-to-Renewal Dashboard Spec

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** commercial data models and dashboard architecture for pipeline-to-renewal metrics: pipeline coverage, conversion rates, forecast accuracy and retention, segmented by region, product, source and owner.

Data: [`pipeline_coverage.sql`](sql/pipeline_coverage.sql) on top of the shared [semantic layer](../../shared_core/metrics/sql/semantic_layer.sql), plus Salesforce Forecasts (assumed) snapshots for forecast accuracy. The Python equivalents are [`pipeline_report.py`](pipeline_report.py), [`forecast_accuracy.py`](../forecasting/forecast_accuracy.py) and [`renewal_signals.py`](../renewals/renewal_signals.py).

## Three pages, one per decision

### Page 1: "Will we hit the quarter?" (CRO, weekly)

| Tile | Metric | Viz |
|---|---|---|
| Narrative | Auto-generated summary (`pipeline_report.narrative()`) + edited AI forecast commentary | Text |
| Coverage by region | Open pipeline ÷ remaining quota vs 3.0x target | Bullet chart |
| Commit vs quota | Commit, best case, closed, by region | Stacked bar with quota line |
| High-risk Commit | $ in Commit flagged HIGH by the deal-risk model | Stat + list |
| Forecast accuracy trend | Week-8 accuracy and bias by region, last 4 quarters | Line |

### Page 2: "Where is pipeline healthy or broken?" (VPs, managers)

| Tile | Metric | Viz |
|---|---|---|
| Pipeline by product line × region | Open $ and count | Heat table |
| Win rate and cycle | By source, segment, product line | Bar pair |
| Stage aging | Deals over the stage limit, by owner | Table, sorted by overage |
| Hygiene by owner | Past close date, late-stage without EB, single-threaded | Table |
| Closed-lost reasons | $ by reason, by product line | Bar |

### Page 3: "Are we keeping and growing customers?" (CRO, CS, Finance, monthly)

| Tile | Metric | Viz |
|---|---|---|
| Renewing ARR by health band | Next 180 days, by product line | Stacked bar |
| Forecast GRR | 1 − expected churn ÷ renewing ARR | Stat by product line |
| Actual GRR / NRR | Trailing 4 quarters | Line |
| Expansion signals | Overage and cross-sell accounts with ARR | Table |
| Churn reasons | $ by reason | Bar |

**Filters on every page:** region, product line, source, owner, segment, type. These are the same dimensions as the 🟦 funnel dashboard, so a lead-side number and an opportunity-side number for the same segment always reconcile.
