# Metric Definitions (single source of truth)

![Shared](https://img.shields.io/badge/supports-BOTH%20roles-7B61FF)

Both roles build dashboards. If the GTM Engineer's "conversion rate" and the Strategy & Ops "conversion rate" are computed differently, the first leadership meeting turns into a debate about whose number is right. Every metric used in the repo is defined here once. The SQL in [`sql/semantic_layer.sql`](sql/semantic_layer.sql) and the Python reports implement these definitions exactly.

## Lead-side metrics (🟦 GTM Engineer)

| Metric | Definition | Grain |
|---|---|---|
| **MQL rate** | Leads that reached MQL ÷ leads created, by created-month cohort | Cohort |
| **MQL→SAL acceptance** | Leads with `SAL_Date` ÷ leads with `MQL_Date` | Cohort |
| **SLA compliance** | MQLs accepted within `sla_hours.mql_to_sal` ÷ MQLs accepted | Period |
| **SAL→SQL conversion** | Leads with `SQL_Date` ÷ leads with `SAL_Date` | Cohort |
| **Lead→Opp conversion** | Converted leads ÷ leads created | Cohort |
| **Conversion velocity** | Median days created → SQL, and SQL → opportunity created | Cohort |
| **Pipeline sourced** | Sum of `Amount` on opps whose `Source__c` ∈ {Marketing, SDR}, by created date | Period |
| **Account penetration** | ICP accounts with ≥1 engaged contact ÷ ICP accounts in territory | Snapshot |

## Opportunity-side metrics (🟩 Strategy & Ops)

| Metric | Definition | Grain |
|---|---|---|
| **Pipeline coverage** | Open pipeline closing in period ÷ (quota − closed won to date) | Snapshot |
| **Win rate (count)** | Closed Won ÷ (Closed Won + Closed Lost), by close date | Period |
| **Win rate ($)** | Closed Won $ ÷ (Closed Won $ + Closed Lost $) | Period |
| **Sales cycle** | Median days created → closed, won deals only | Period |
| **Stage conversion** | Opps that exited stage N forward ÷ opps that entered stage N | Cohort |
| **Forecast accuracy** | 1 − \|commit − actual\| ÷ actual, at a fixed week of quarter (week 4, 8, 12) | Quarter × region |
| **Forecast bias** | (commit − actual) ÷ actual. Positive = over-call, negative = sandbag | Quarter × region |
| **Commit conversion** | Commit $ at week N that closed won ÷ commit $ at week N | Quarter |
| **Gross revenue retention** | (Renewing ARR − churn − downgrade) ÷ renewing ARR | Period |
| **Net revenue retention** | GRR + expansion ARR ÷ renewing ARR | Period |
| **Stage days** | Days from entering a stage to entering the next, from field history on StageName; reported as the **median** | Cohort by stage |
| **Stage pressure** | Median stage days ÷ the stage's time limit (`opportunity.stages.max_days`) | Snapshot |
| **Close-date push** | A CloseDate change that moves the date later; count and total days per deal | Event |
| **Sales velocity** | (opportunities × win rate × average won deal) ÷ cycle days, per rep or segment | Trailing 365 days |
| **Win-rate range** | 80% Wilson interval on win rate; below `min_sample` closed deals, "too early" | Trailing 365 days |
| **Rep quota** | Region quota split across that region's AEs by ramped rep equivalents | Quarter |
| **Capacity** | Ramped rep equivalents (net of attrition) × steady-state productivity | Quarter |
| **Implied over-assignment** | Quota ÷ capacity − 1 | Quarter × region |
| **Coverage Gini** | Gini coefficient of pipeline coverage across reps (0 = even) | Snapshot |

## Marketing metrics (🟦 with Marketing Ops)

| Metric | Definition | Grain |
|---|---|---|
| **Sourced pipeline** | Opp amount by the originating lead's first campaign type | Cohort |
| **Influenced pipeline (W-shaped)** | 30% first touch, 30% MQL touch, 30% opp-creation touch, 10% the rest; 180-day lookback | Cohort |
| **Cost per MQL / per opp** | Campaign spend ÷ MQLs or opps from leads first touched by that channel | Period |
| **Pipeline per $** | W-shaped attributed pipeline ÷ spend | Period |
| **Demand-plan gap** | (leads last 90 days − leads needed) ÷ leads needed, by channel | Quarter |

## Shared dimensions

Every metric can be cut by: `segment`, `region`, `product_line`, `source`, `owner`, `partner`, `type`. These are the standard cuts for pipeline reporting. The GTM Engineer funnel reports use the same values.

## Rules

1. **Cohort vs period:** conversion rates are cohort-based, so this month's leads are measured on what *they* eventually did. Activity counts are period-based. Never mix the two in one chart.
2. **Dates are stamped, not inferred.** Funnel dates come from Flow-stamped fields, not `LastModifiedDate`.
3. **Fiscal calendar:** quarters in every report are fiscal, from `fiscal.year_start_month` in the config. Sardine doesn't publish its fiscal year, so the config assumes calendar year `[ASSUME]`.
