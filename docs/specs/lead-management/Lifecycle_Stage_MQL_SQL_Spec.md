---
type: area
category: revops
tags:
  - hubspot
  - sfdc
  - lifecycle
  - mql
  - sql
  - revops
date: 2026-08-21
status: active
---

# HubSpot to SFDC Lifecycle Stage & Lead Status Mapping Spec

## 1. Universal Stage Definitions

| Stage | Owner | System Master | Definition | Primary Trigger |
| :--- | :--- | :--- | :--- | :--- |
| **Subscriber** | Marketing | HubSpot | Top-of-Funnel contact. | Form submit without demo request. |
| **Lead** | Marketing | HubSpot | Fit target profile (ICP match). | Company domain match or score threshold. |
| **MQL** | Marketing -> SDR | HubSpot | Explicit hand-raiser / high score. | Demo request or PQL threshold. |
| **SQL** | SDR / Sales | Salesforce | Accepted by SDR, meeting set. | Lead Status = Working / Meeting Booked. |
| **Opportunity** | AE | Salesforce | Qualified deal with pipeline value. | AE creates SFDC Opportunity. |
| **Unqualified** | SDR / Sales | Salesforce | Bad fit, false contact, or timing. | Lead Status = Unqualified. |

---

## 2. Field Mapping & Sync Rules

### A. Directional Field Flow
* **HubSpot (MQL Trigger):** Sets Lifecycle Stage = MQL -> Syncs to SFDC -> Creates Lead (Status = New).
* **Salesforce (SQL Acceptance):** SDR sets Lead Status = Working -> Syncs to HubSpot -> Lifecycle Stage = SQL.
* **Salesforce (Disqualification):** SDR sets Lead Status = Unqualified -> Syncs to HubSpot -> Workflow removes from Sync Inclusion List.

### B. Sync Field Matrix

| Field Name | HubSpot Property | SFDC Field | Direction | Ownership Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Lifecycle Stage** | `lifecyclestage` | `Lifecycle_Stage__c` | Bi-directional | HS owns up to MQL; SFDC overrides on Opp creation. |
| **Lead Status** | `hs_lead_status` | `Status` | SFDC -> HS | SFDC is Master. SDR changes mirror back to HS. |
| **Disqualification Reason** | `unqualified_reason` | `Unqualified_Reason__c` | SFDC -> HS | Required field in SFDC on Disqualification. |
| **MQL Timestamp** | `became_mql_date` | `MQL_Date__c` | HS -> SFDC | Set once by HS workflow; read-only in SFDC. |

---

## 3. SLA & Disqualification Rules
* **4-Hour SLA Rule:** When `Lifecycle Stage` hits `MQL`, trigger an alert to assigned SDR. If not updated within 4 hours, escalate to SDR Manager.
* **Recycling Nurture Loop:** When Lead Status = Unqualified (Bad Timing), remove from Sync Inclusion List and push into 90-day HubSpot Nurture Workflow.
