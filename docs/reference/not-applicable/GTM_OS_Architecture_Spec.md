# Enterprise GTM Operating System Architecture Spec

> **Not applicable to Sardine.** Template reference only; Sardine is assumed to be sales-led. See [README](README.md).

## 1. System Topology & Data Flow
The GTM Operating System acts as a unified revenue orchestration framework linking Product-Qualified Leads (PQLs), CRM record enrichment, MEDDPICC deal qualification, and churn risk intelligence.

```
  [ Product Telemetry / PQL ]
              │
              ▼
    ┌──────────────────┐
    │ L2A Match Engine │ ── (Domain & Fuzzy Matching)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ MEDDPICC Health  │ ── (Deal Progression Gatekeeping)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Churn & Renewal  │ ── (Retention Health & Risk Scoring)
    └──────────────────┘
```

## 2. Core Field Mapping Schema

| Object | Field Name | API Name | Data Type | Usage |
| :--- | :--- | :--- | :--- | :--- |
| Opportunity | Quantified ROI | `Quantified_ROI__c` | Checkbox | MEDDPICC Metrics verification |
| Opportunity | Economic Buyer Contacted | `Economic_Buyer_Contacted__c` | Checkbox | MEDDPICC Economic Buyer verification |
| Opportunity | Health Score | `MEDDPICC_Health_Score__c` | Number (0-100) | Calculated deal health score |
| Account | WAU Change | `WAU_Change_30D__c` | Percent | Churn risk evaluation input |
| Account | Risk Level | `Churn_Risk_Level__c` | Picklist | Values: LOW, ELEVATED, CRITICAL |

## 3. Automation Modules

Paths are relative to the repository root.

- **PQL Ingestion**: [`docs/reference/not-applicable/sfdc_pql_ingestor.py`](sfdc_pql_ingestor.py) (not applicable)
- **Lead-to-Account Matching**: [`gtm_engineer/enrichment/l2a_matcher.py`](../../../gtm_engineer/enrichment/l2a_matcher.py)
- **MEDDPICC Risk Scoring**: [`prototypes/meddpicc_health_engine.py`](../../../prototypes/meddpicc_health_engine.py)
- **Churn Prediction**: [`prototypes/churn_prediction_pipeline.py`](../../../prototypes/churn_prediction_pipeline.py)
- **Tech Debt Audit**: [`prototypes/revops_tech_debt_tracker.py`](../../../prototypes/revops_tech_debt_tracker.py)
- **Attribution Engine**: [`shared_core/metrics/sql/attribution/w_shaped_attribution.sql`](../../../shared_core/metrics/sql/attribution/w_shaped_attribution.sql)
