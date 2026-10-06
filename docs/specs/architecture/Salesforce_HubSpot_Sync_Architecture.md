---
type: resource
category: tech-stack
tags:
  - resource
  - sfdc
  - hubspot
  - integration
status: active
last_updated: 2026-08-21
---

# Salesforce & HubSpot Bi-Directional Sync Architecture

## Executive Summary
This document defines field mapping, state machine sync logic, and Lead-to-Account (L2A) matching rules between HubSpot and Salesforce.

## Core System Boundaries
* **HubSpot:** Owns top-of-funnel activity, lead capture, marketing automation, email engagement, and initial enrichment.
* **Salesforce:** Owns accounts, opportunities, sales pipeline, CPQ, legal/contracting, and primary revenue metrics.

## Bi-Directional Field Mapping & Master Ownership

| HubSpot Property | SFDC Field | Direction | Master System | Sync Logic / Edge Cases |
| :--- | :--- | :--- | :--- | :--- |
| email | Email | HS -> SFDC | HubSpot | Immutable key. Prevents duplicates on sync. |
| lifecyclestage | Lifecycle_Stage__c | Bi-directional | State Machine | Moves forward automatically; regression requires Ops override. |
| hubspot_owner_id | OwnerId | Bi-directional | SFDC | SFDC owner assignment overrides HS owner immediately. |
| hs_lead_score | Lead_Score__c | HS -> SFDC | HubSpot | Updated on engagement threshold breaches (>75). |
| annualrevenue | AnnualRevenue | SFDC -> HS | SFDC | Enriched firmographics in SFDC update HS for segmentation. |

## Lead-to-Account (L2A) Matching Rules
1. **Domain-Based Matching:** Match email domain (@company.com) against existing SFDC Account.Website or Account.Domain__c.
2. **Exclusion Filters:** Ignore generic email domains (gmail.com, yahoo.com, hotmail.com).
3. **Contact vs. Lead Creation:** If matching SFDC Account exists -> create SFDC Contact tied to Account. If no match exists -> create SFDC Lead.

## Sync State Machine & Conflict Resolution
* **Conflict Rule:** SFDC always wins field collisions on core financial or owner assignment data.
* **Sync Delay Guard:** Field updates must pass a 2-second debounce filter to avoid infinite loops between systems.
