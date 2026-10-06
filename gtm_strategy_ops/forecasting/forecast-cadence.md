# Forecast Cadence & Operating Rhythm

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** manage forecasting cadence, categories and accuracy measurement; deliver decision-focused pipeline and forecast narratives to senior cross-functional leaders.

## Weekly rhythm (example; adjust days to the company's calendar. Fiscal quarters follow `fiscal.year_start_month` in config)

| Day | Meeting / artifact | Who | Inputs from this repo |
|---|---|---|---|
| **Mon AM** | Pipeline hygiene sweep | RevOps | [DQ monitor](../../shared_core/data_quality/dq_monitor.py) failures routed to owners; [stage aging](../pipeline_analytics/pipeline_report.py) |
| **Mon PM** | AE forecast submissions in Salesforce Forecasts (assumed) due | AEs | Deal-risk flags in Salesforce Forecasts (assumed) notes (accepted ones only) |
| **Tue** | Manager forecast calls (by region) | Front-line managers + RevOps | [Deal-risk review queue](../ai_deal_risk/deal_risk.py); high-risk Commit deals first |
| **Wed** | Leadership forecast call | CRO, VPs, RevOps, Finance | [AI forecast commentary](../ai_deal_risk/prompts/forecast_commentary.md) (edited), coverage, [bias-adjusted roll-up](forecast_accuracy.py) |
| **Thu** | Finance sync | RevOps + FP&A | Commit / best case / renewal forecast, separately |
| **Fri** | Forecast snapshot frozen | System | Salesforce Forecasts (assumed) snapshot → warehouse (feeds accuracy measurement) |

## Quarterly

- **Week 1:** coverage check for this quarter and the next ([`pipeline_report.py`](../pipeline_analytics/pipeline_report.py)). Any region under 2x triggers a pipeline-generation plan with the 🟦 GTM Engineer.
- **Weeks 4, 8, 12:** accuracy checkpoints logged ([`forecast_accuracy.py`](forecast_accuracy.py)).
- **Quarter close + 2 weeks:** forecast retrospective covering accuracy and bias by region, commit conversion, slipped deals and why. The bias pattern is discussed with each regional leader.

## Measuring the AI workflows' effect on the forecast

Measure workflow impact on forecast accuracy and seller capacity. The design:

| Measure | Before | After | Method |
|---|---|---|---|
| Week-8 commit accuracy | Prior 2 quarters (baseline) | 2 quarters after deal-risk flags go live | Same metric, same checkpoint |
| Slipped-deal rate | % of week-8 Commit deals not closed in quarter | same | Snapshot comparison |
| Manager prep time | Self-reported hours per forecast call | same | Monthly pulse |
| Flag precision | — | % of HIGH flags the manager agreed with | HITL review queue |
