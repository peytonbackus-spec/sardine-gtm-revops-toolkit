# Opportunity Stage Definitions & Exit Criteria

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Scope:** own the opportunity lifecycle configuration and data-quality standards, and partner with sales leadership to improve execution discipline.

Stages are defined by **verifiable buyer outcomes**, not by seller activity. Every exit criterion is a field, so stage integrity can be reported on and enforced with validation rules. The example design reflects long-cycle enterprise deals: technical validation (POC, sandbox or data test) and security/vendor-risk review are slow and often run in parallel, so each has its own stage gate. If your deals don't stall there, change the stages in config and the rules follow.

| Stage | Prob. | Max days | Exit criteria (all required) | Enforced by |
|---|---|---|---|---|
| **1 – Qualify** | 10% | 21 | SQL standard met (from 🟦 [lifecycle spec](../../gtm_engineer/lead_lifecycle/lead-lifecycle-spec.md)); `Product_Line__c` set; discovery meeting booked | Validation rule on save to stage 2 |
| **2 – Discovery** | 20% | 30 | Pain quantified (cost of the current problem in dollars or hours); current vendor and contract end captured; ≥2 contacts engaged | Required fields: `Current_Vendor__c`, `Contract_End__c` |
| **3 – Technical Validation** | 40% | 45 | Success criteria agreed **in writing** with the buyer; `POC_Status__c` = Passed **or** N/A with reason | Validation rule; SE sign-off field |
| **4 – Business Case & Security Review** | 60% | 45 | `Economic_Buyer_Engaged__c` = true; business case shared; `Security_Review__c` = In Progress or Complete | Validation rule (EB required) |
| **5 – Negotiate & Contract** | 80% | 30 | Verbal selection; paper process mapped (legal, procurement, signer); `Security_Review__c` = Complete | Validation rule; Commit allowed only here or with VP override |
| **Closed Won** | 100% | — | Signed order form attached | Approval process |
| **Closed Lost** | 0% | — | `Closed_Lost_Reason__c` (+ competitor if applicable) | Validation rule |

## Forecast category rules (Salesforce Forecasts (assumed))

| Category | Allowed stages | Rule |
|---|---|---|
| Pipeline | 1–3 | Default for early stages |
| Best Case | 3–5 | AE judgement |
| Commit | 5 (4 with manager approval) | Requires `Economic_Buyer_Engaged__c` and a dated next step |
| Omitted | any | Pushed out of the quarter or no longer viable |

The [DQ monitor](../../shared_core/data_quality/dq_monitor.py) (rules O01–O06) and the [deal-risk model](../ai_deal_risk/deal_risk.py) both read these definitions from the company config (`opportunity.stages`), so changing a stage limit updates the rules, the risk model and the aging report together.

## Stage velocity

"Intro call" is stage 1 (Qualify) and "discovery" is stage 2. Time between them is measured from field history on StageName, and the [stage velocity report](../sales_leadership/stage_velocity.py) splits it by owner, source, segment and economic-buyer access, so "intro to discovery is slow" comes with the reason. Close-date changes are tracked the same way (field history on CloseDate) and feed the Slipping bucket on the [deal board](../sales_leadership/deal_board.py).

## Opportunity types

| Type | Created by | Notes |
|---|---|---|
| New Logo | Lead conversion or AE | `Originating_Lead__c` for attribution back to the 🟦 funnel |
| Expansion | AE / CSM, or the [renewal expansion signal](../renewals/renewal_signals.py) | Cross-sell between product lines (`product_lines.cross_sell`), or a volume overage |
| Renewal | Auto-created at T-180 | Forecast separately; see [renewal process](../renewals/renewal-process.md) |
