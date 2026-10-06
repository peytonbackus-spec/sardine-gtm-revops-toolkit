# Lead-to-Opportunity Dashboard Spec

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

**Scope:** dashboards covering volume, conversion velocity, pipeline value and account penetration, plus early-pipeline outlooks and performance narratives.

Data: [`lead_funnel.sql`](sql/lead_funnel.sql) on top of the shared [semantic layer](../../shared_core/metrics/sql/semantic_layer.sql). The Python equivalent ([`funnel_report.py`](funnel_report.py)) produces the same numbers from the same definitions. Build it in CRM reports for reps and in the BI tool for leadership.

## Layout (one page, top to bottom = question order)

| Row | Tile | Metric (see [definitions](../../shared_core/metrics/metric-definitions.md)) | Viz |
|---|---|---|---|
| 1 | **Narrative** | Auto-generated 3-sentence summary from `funnel_report.narrative()` | Text |
| 1 | Early-pipeline outlook | Expected opps and $ range, next 30 days | Stat with range |
| 2 | **Volume** | Leads and MQLs by week, by source | Stacked bar |
| 2 | **Conversion** | Cohort funnel MQL→SAL→SQL→Opp, last 6 matured cohorts | Funnel / heat table |
| 3 | **Velocity** | Median days created→SQL, SQL→Opp, by source | Bar |
| 3 | **SLA** | MQL→SAL within SLA, by SDR | Bar with target line |
| 4 | **Pipeline value** | Lead-sourced pipeline $ and $ per lead, by source and product line | Bar |
| 4 | **Account penetration** | % ICP accounts engaged, % multi-persona, by segment | Bar |
| 5 | **Scoring health** | Conversion by fit letter and intent number; monotonic flag | Small multiples |

**Filters:** segment, region, product line, source, owner (the same dimensions as the 🟩 pipeline dashboard).

**Cadence:** reps see the Salesforce version live. Leadership gets the BI version every Monday with the narrative tile pasted into chat.
