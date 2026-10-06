---
type: resource
category: tech-stack
tags:
  - resource
  - plg
  - pql
  - hubspot
status: active
last_updated: 2026-08-21
---

# Product-Qualified Lead (PQL) Routing Architecture

## Executive Summary
Automated routing framework to identify product-led conversion signals from self-serve product usage and assign handoffs to Sales AEs.

## PQL Qualification Thresholds

An account flags as a Product-Qualified Lead (PQL) when hitting any of the following triggers:

* **Velocity Trigger:** Workspace reaches 10 active seats within first 14 days of signup.
* **Feature Trigger:** Free-tier workspace hits or exceeds usage limit on a core premium feature 3 times in 7 days.
* **Domain Trigger:** Domain match identifies 5+ independent free signups under the same corporate domain (@company.com).

## Lead Assignment & Routing Workflow
1. Free User Sign-up occurs.
2. Segment/PostHog sends Telemetry Event.
3. If PQL Criteria met -> Create SFDC Opportunity + Set Stage to "PQL Qualified".
4. Route via L2A Engine to Territory AE.

### SLA Requirements
* **Response SLA:** Account Executive must initiate outreach within 2 hours of PQL flag creation.
