---
type: area
category: revops
tags:
  - area
  - cs
  - health-score
  - retention
status: active
last_updated: 2026-08-21
---

# Customer Health Scoring & Retention Framework

## Executive Summary
Composite scoring system designed to identify expansion candidates, track retention risk, and trigger proactive CS playbooks based on telemetry and engagement signals.

## Weighted Health Score Components

Health Score = (Product Usage * 0.40) + (CSM Engagement * 0.25) + (Support Health * 0.20) + (Executive Sponsor * 0.15)

* **Product Usage (40%):** DAU/MAU ratio, license utilization (>80%), key feature adoption depth.
* **CSM Engagement (25%):** QBR cadence completed, response latency to CSM outreach.
* **Support Ticket Health (20%):** Zero critical (P1) open tickets, low CSAT trend (<4 is flagged).
* **Executive Relationship (15%):** Active executive sponsor touchpoint within 90 days.

## Health Tiers & Action Matrix

| Health Score Range | Health Status | Primary Operational Playbook |
| :--- | :--- | :--- |
| **80 - 100** | Green (Healthy) | Expansion / Upsell inspection; request advocacy & case study. |
| **50 - 79** | Yellow (At Risk) | CSM check-in; product adoption audit; executive sync. |
| **0 - 49** | Red (Critical) | High-priority Red Account workflow; exec sponsor intervention. |
