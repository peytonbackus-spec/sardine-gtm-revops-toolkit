# Salesforce Forecasts (assumed) Configuration & CRM Integration Spec

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** administer the forecasting platform and optimize its CRM integration; establish data-quality monitoring across the CRM and the forecasting tool; optionally run conversation intelligence (Gong (assumed)).

A design spec for setting Salesforce Forecasts (assumed) up so it reads clean CRM data and gives the forecast one source of truth. Written for Salesforce as the CRM. Vendor behaviors below are general patterns for roll-up forecasting tools; mark anything `[VERIFY]` against the vendor's current documentation before relying on it.

## Modules and what each is for

| Module | What it does | Use at Sardine |
|---|---|---|
| **Forecast** | Roll-up forecasting: reps submit calls, managers roll up, with categories, waterfall (movement and slippage) views and historical trending | Weekly forecast calls; week 4/8/12 accuracy |
| **Inspect** | Pipeline inspection and deal risk: changes, score, engagement, next steps | Manager deal reviews; complements [`deal_risk.py`](../ai_deal_risk/deal_risk.py) |
| **Conversation intelligence** | Call recording, transcription, trackers, summaries | Deal-risk themes; economic-buyer evidence |
| **Activity capture** | Email and calendar sync into the deal timeline | Feeds engagement signals; this is what makes "No activity in 30d" trustworthy |

## Hierarchy: the constraint to design around

Roll-up forecasting tools typically roll up along the **CRM role hierarchy**, the only roll-up path. It works well for the people view (AE → manager → VP → CRO), but it has consequences:

| Need | Solved natively? | How to handle it |
|---|---|---|
| AE → regional manager → VP → CRO | ✅ Yes | Keep the CRM role hierarchy clean and current. A rep in the wrong role puts their pipeline in the wrong roll-up. |
| New business vs renewals | ✅ Separate forecast tabs filtered by `Type` | Two tabs: New Business (New Logo + Expansion) and Renewals |
| Product lines | ⚠️ Filtered tabs work, but managers still get one roll-up per tab | Tabs for visibility; the official product-line forecast for Finance comes from the warehouse, built from forecast snapshots + `Product_Line__c` |
| Partner-sourced pipeline across all managers | ⚠️ Cuts across the hierarchy | Partner view in the warehouse / BI layer ([pipeline report](../pipeline_analytics/pipeline_report.py) `source` dimension), not as a roll-up |

When channel and renewals report into the same CRO as direct sales, design the hierarchy on purpose.

## Categories

- Pipeline / Best Case / Commit / Closed / Omitted, mapped 1:1 to the CRM's forecast category. No tool-only category: if a category exists in only one system, the two systems will disagree.
- Commit rules follow the [stage definitions](../opportunity_lifecycle/stage-definitions.md). A Commit in stage 1–2 is flagged (DQ rule O05).
- Keep both rep calls and manager overrides. The gap between them, over time, is one of the inputs to the [bias analysis](../forecasting/forecast_accuracy.py).

## CRM field rules for the forecasting tool

| Rule | Why |
|---|---|
| **No formula fields as tool inputs.** Mirror anything the tool needs (days in stage, risk level) into a real field stamped by a flow. `[VERIFY]` | Many tools can't consume CRM formula fields directly. This is a commonly cited admin pain point. The 🟪 [object model](../../shared_core/data_model/salesforce-object-model.md) already uses flow-stamped fields. |
| Validation rules live in the CRM only, never duplicated as tool logic | Rules in two places drift |
| Keep the synced field count lean, and give every field an owner | API limits and sync lag grow with field count |
| Picklist values mirrored in the company config | Code, CRM and forecasting tool share one definition |

## Sync & data quality

| Check | Frequency | Action |
|---|---|---|
| Tool ↔ CRM totals by forecast category (count and $) | Weekly, before the forecast call | Investigate any gap > 0.5%; usually sync lag or a field-mapping change |
| Opportunities with tool activity but no CRM activity | Weekly | Activity-capture gaps (email/calendar sync, unlicensed users) |
| Role-hierarchy changes vs forecast roll-up | On every org change | Reps moved in HR but not in CRM roles roll up to the wrong manager |
| Snapshot export to warehouse | Weekly | Feeds [`forecast_accuracy.py`](../forecasting/forecast_accuracy.py) and the product-line / partner views above |
| Users owning opportunities without tool access | Monthly | Licence / provisioning hygiene |

## Deal inspection: how the repo's deal-risk model fits

Vendor deal-inspection features usually combine: what changed (7/14/30-day views), a win-likelihood score, engagement and relationship signals, and suggested next steps / CRM updates from call transcripts.

[`deal_risk.py`](../ai_deal_risk/deal_risk.py) doesn't replace these. It adds what a native score doesn't make explicit:

| Native | Repo deal-risk model | Combined use |
|---|---|---|
| Win-likelihood score (derivation often opaque) | Named, explainable rules ("security review not started at stage 4+") | Use the score as one input; the rules explain *why* in language a manager can act on |
| Generic engagement signals | Company-specific gates: technical validation (POC) and security review | The long poles get first-class signals |
| CRM-field suggestions from transcripts | HITL policy: AI may *suggest* `Economic_Buyer_Engaged__c`, never set it | Same idea; the repo makes the review step explicit |

## Conversation intelligence

- Trackers for the company's deal-risk themes: security review, POC / pilot, competitor names, budget. Tracker hits write to the deal timeline.
- **Economic-buyer detection:** a meeting with a contact whose persona is an economic buyer (from the 🟪 [persona model](../../shared_core/context/icp-and-personas.md)) can *suggest* `Economic_Buyer_Engaged__c = true` for AE confirmation. Never set automatically.
- Competitor tracker hits feed the competitive component of the [renewal health model](../renewals/renewal_signals.py).

## AI outputs into the forecasting tool

Deal-risk commentary from [`deal_risk.py`](../ai_deal_risk/deal_risk.py) posts to the deal note **only after human review**. The note is labelled `[AI-assisted · reviewed by <manager>]`, so nobody mistakes it for the AE's own words.

## Week-one questions

1. Which conversation-intelligence tool records calls today? Is more than one in use?
2. Are renewals already a separate forecast tab?
3. Does the CRM role hierarchy match the current GTM org under the CRO?
4. Who administers the forecasting tool today, and how many CRM formula fields are being worked around?
