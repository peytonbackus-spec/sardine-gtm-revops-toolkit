# Enterprise GTM Operating System Architecture Spec

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

- **PQL Ingestion**: `30_Resources/Code/sfdc_pql_ingestor.py`
- **Lead-to-Account Matching**: `30_Resources/Code/orchestrators/l2a_matching_engine.py`
- **MEDDPICC Risk Scoring**: `30_Resources/Code/scoring/meddpicc_health_engine.py`
- **Churn Prediction**: `30_Resources/Code/scoring/churn_prediction_pipeline.py`
- **Tech Debt Audit**: `30_Resources/Code/revops_tech_debt_tracker.py`
- **Attribution Engine**: `30_Resources/Code/attribution/w_shaped_attribution.sql`
