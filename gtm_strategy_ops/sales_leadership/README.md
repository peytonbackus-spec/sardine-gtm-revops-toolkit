# Sales Leadership Reporting: what the VP of Sales asks, answered fast

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Principle:** give the VP of Sales the answer to the question they are about to ask, before the meeting, in the depth they want. Every number names the decision or action it supports; anything that does not change a decision stays out of the snapshot.

Two depths from one set of numbers ([`vp_brief.py`](vp_brief.py)):

| Mode | What's in it | Who it's for | Length |
|---|---|---|---|
| **Snapshot** | The number · three things to know · deals to act on · asks | A leader who wants it fast | One phone screen |
| **Full** | Snapshot + rep scorecard, industry table, stage velocity with drivers, full deal board, definitions | A leader who wants to dig in, and RevOps defending any snapshot number | 5 minutes |

Which is the default, and when it lands, is the VP's call: the [intake questions](vp-intake.md) settle it in the first 1:1. Until then, send the snapshot with the full brief one click away.

## Question catalog

| The VP asks | Module | Answer shape | Snapshot? |
|---|---|---|---|
| Are we going to hit the number? | [`pipeline_report.coverage`](../pipeline_analytics/pipeline_report.py), [`deal_board`](deal_board.py) | Last quarter vs quota; this quarter coverage vs 3x; commit | ✅ |
| How is each rep doing, and why? | [`rep_scorecard`](rep_scorecard.py) | Result (attainment) · setup (coverage) · weakest velocity lever vs team · coaching focus | Names only if they need help |
| Which industries are we winning and losing? | [`segment_performance`](segment_performance.py) | Win rate with an 80% range, deal size, cycle, top loss reason, verdict: Double down / Fix / Watch / Hold / Too early | ✅ |
| Where is pipeline slowing, and why? (e.g. intro call → discovery is slow) | [`stage_velocity`](stage_velocity.py) | Where deals slow (time vs stage limit) · where they die (conversion) · drivers by owner, source, segment, product, EB access, threading · likely cause and fix to test | ✅ |
| Which deals are hot, which are at risk? | [`deal_board`](deal_board.py) | Every open deal in Past due / Slipping / At risk / Stalled / Hot / On track, with the reason and the action | Top 3 risk + top 2 hot |
| What do we tell the team at the all-hands? | [`all_hands`](all_hands.py) | Slide outline: number, wins, recognition, good and bad, lessons, focus, speaker prompts | n/a |
| Is pipeline spread so we can hit it? | [`../sales_planning/pipeline_distribution`](../sales_planning/pipeline_distribution.py) | Per-rep load, coverage, concentration, stage mix; team Gini | Full only |
| Do we have the capacity / right quotas / fair territories? | [`../sales_planning/`](../sales_planning/README.md) | Capacity vs plan, hiring plan, quota vs capacity, territory balance | Planning cycle |

## Definitions (also in the [metric definitions](../../shared_core/metrics/metric-definitions.md))

| Metric | Definition | Why this way |
|---|---|---|
| Win rate | Won ÷ (won + lost), by close date, trailing 365 days | Period-based, so it moves when behaviour changes |
| 80% range | Wilson score interval on the win rate | With 7 closed deals, 43% could be 20% or 68%. Leaders move territories on these numbers |
| Sales velocity | (opportunities × win rate × average won deal) ÷ cycle days | The four levers a rep or segment can move; the weakest one is the coaching focus |
| Stage days | Days between stage entries, from field history on StageName; **median** | One deal stuck for 200 days should not set the team's number |
| Stage pressure | Median days in stage ÷ the stage's time limit (config) | Separates "slow" from "slow against what we expect" |
| Rep quota | Region quota split by ramped rep equivalents | A rep in quarter 2 of ramp is not judged on a full number |
| Push | A CloseDate change that moves the date later | Lost deals get pushed more often and further than won deals (research below) |

## The four bottleneck questions, and how the report answers each

The stage velocity module turns "intro-to-discovery takes forever" into a short list of checkable causes:

1. **Is it really slow, or just long?** Pressure (median ÷ stage limit) and won-deal medians vs lost-deal medians.
2. **Is it slow, or is it where deals die?** Two different answers: *where deals slow* (highest pressure) and *where deals die* (lowest forward conversion). Different fixes.
3. **Is it pipeline inflation?** When lost deals sit in a stage more than twice as long as winners did, the stage holds dead deals nobody closed out. That is a hygiene fix, not a selling fix.
4. **Which deals drive it?** Slices by owner, source, segment, product line, deal type, economic-buyer access and contact count, ranked by excess deal-days. Each driver carries the usual cause and the first fix to test. Owner-level drivers go to coaching; process-level drivers become an ask for the VP.

Common causes for a slow first hop (Qualify → Discovery), in the order to check: the deal was created before a discovery meeting was booked (hand-off), one rep's calendar or load, a segment that needs more people in the first call, no access to power yet.

## Deal board rules

First match wins. Thresholds live in config (`sales_leadership`).

| Bucket | Rule | Action |
|---|---|---|
| Past due | Close date passed, deal still open | Fix the date or close it, before the forecast call |
| Slipping | Pushed 2+ times, or one push of 3+ weeks in the last 30 days | Re-confirm the close plan with the buyer in writing |
| At risk | HIGH on the deal-risk model (same model the forecast call uses) | Manager deal review on the top risk reason |
| Stalled | Past the stage time limit, or no activity in 21 days | Dated next step, or close it out |
| Hot | Advanced a stage in 30 days, active this week, EB engaged, 3+ contacts, low risk, no recent push | Pull in exec and SE time; clear the paper process |
| On track | Everything else | Normal cadence |

## Cadence

| When | What | Channel |
|---|---|---|
| Monday before 9 | Snapshot (full brief linked) | Slack DM or email, per intake |
| Before the forecast call | Deal board for the quarter + past-due clean-up list to managers | Forecast tool / Slack |
| Monthly | Full brief + industry table + pipeline distribution | Doc |
| Quarterly | All-hands inputs, quota and capacity check | Doc + slides |

## Run it

```bash
python -m gtm_strategy_ops.sales_leadership.vp_brief                 # snapshot -> outputs/vp_brief_snapshot.md
python -m gtm_strategy_ops.sales_leadership.vp_brief --mode full     # full brief
python -m gtm_strategy_ops.sales_leadership.all_hands                # last quarter's all-hands inputs
python -m gtm_strategy_ops.sales_leadership.all_hands --days 1       # "what happened today"
python -m gtm_strategy_ops.sales_leadership.stage_velocity
python -m shared_core.metrics.run_sql gtm_strategy_ops/sales_leadership/sql/stage_velocity.sql
```

**Data needed in Salesforce:** field history tracking on `StageName` and `CloseDate` (OpportunityFieldHistory), `LastActivityDate`, `Economic_Buyer_Engaged__c`, `Contacts_Engaged__c` (or a roll-up of Opportunity Contact Roles), `Next_Step__c`, and a user roster with start dates. Without stage history, stage velocity falls back to current-stage age only.

## Research behind the choices

- What leaders actually use: a handful of metrics with trends and a decision attached, not 25-KPI dashboards; individual rep detail belongs below the leadership view ([SyncGTM](https://syncgtm.com/blog/revops-dashboard-leadership-uses)). Hence snapshot vs full.
- Close-date pushes predict losses: Gong found win rates fall as close dates are pushed further, across 13,439 opportunities ([Gong](https://www.gong.io/blog/your-crm-close-date-isnt-giving-you-the-full-picture-heres-what-youre-missing)); Aviso reports higher win rates on deals with no push-outs ([Aviso](https://www.aviso.com/blog/relationship-between-close-date-and-win-rate)). Hence pushes as a Slipping signal.
- Sales velocity's four levers as the diagnostic frame ([Salesforce](https://www.salesforce.com/blog/sales-velocity/)).
- Bottleneck method: stage concentration, duration vs target and conversion drop, then root-cause categories (process, resource, skill, buyer-side, organizational) ([Rework](https://resources.rework.com/fr/libraries/pipeline-management/pipeline-bottleneck-analysis)).
- Recognition that lands is frequent, specific and authentic ([Gallup via Workhuman](https://www.workhuman.com/blog/new-gallup-research-on-how-to-design-recognition-programs-that-drive-business-impact/)); team meetings work when wins, including small ones, are shared by the people who won them ([Close](https://close.com/blog/effective-sales-meetings)). Hence named recognition for the top, patterns (not names) for the bad news, and speaker prompts.

> All data in this repo is synthetic. Patterns were planted (slow inbound hand-off, one slow AE in Qualify, banks slow in technical validation, deals without an economic buyer slow in business case, lost deals pushed more) so the reports have something real to find.
