---
type: resource
category: tech-stack
tags:
  - resource
  - hubspot
  - sfdc
  - custom-objects
status: active
last_updated: 2026-08-21
---

# Salesforce & HubSpot Custom Object Architecture

## Executive Summary
Data dictionary and relationship architecture for custom objects representing subscriptions, partner engagements, and usage-based billing data across HubSpot and Salesforce.

## Custom Object: `Partner_Referral__c` / `partner_referrals`

Tracks co-selling dynamics, partner sourcing credit, and revenue-share payouts.

### Field Definitions & Data Types

| Field Name | API Name | Type | Sync Direction | Master System |
| :--- | :--- | :--- | :--- | :--- |
| **Partner Name** | `Partner_Account__c` | Lookup (Account) | SFDC -> HS | Salesforce |
| **Commission Rate** | `Commission_Rate__c` | Percent | SFDC -> HS | Salesforce |
| **Referral Status** | `Referral_Status__c` | Picklist | Bi-directional | State Machine |
| **Sourced ARR** | `Sourced_ARR__c` | Currency | SFDC -> HS | Salesforce |

## Custom Object: `Subscription_Product__c` / `subscriptions`

Stores product-level usage metrics, active entitlement licenses, and renewal health scores.

* **Relationships:** Account (1) to Many `Subscription_Product__c`; Opportunity (1) to Many `Subscription_Product__c`.

### Key Logic & Automations
* **Health Score Breach:** If `Usage_Health_Score__c` drops below 50, trigger a high-priority CSM task in HubSpot and flag the Account in Salesforce as "At-Risk Renewal".
