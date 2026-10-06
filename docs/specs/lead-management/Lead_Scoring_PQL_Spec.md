---
type: area
category: revops
tags:
  - hubspot
  - lead-scoring
  - pql
  - revops
date: 2026-08-21
status: active
---

# Lead Scoring & Product-Qualified Lead (PQL) Spec

## 1. Fit & Intent Scoring Matrix

| Criteria Category | Property / Metric | Score Delta | System Source |
| :--- | :--- | :--- | :--- |
| **ICP Fit** | Employee Count (100-500) | +20 | HubSpot / Clearbit |
| **ICP Fit** | Role = Operations / Revenue | +15 | HubSpot |
| **Intent** | Demo Request Form Submit | +50 (Immediate MQL) | HubSpot |
| **Product Engagement** | 3+ Active Users Onboarded | +25 (PQL Trigger) | Product DB / Segment |
| **Negative Fit** | Student / Personal Email Domain | -50 | HubSpot |

#tech-debt Review scoring decay rules quarterly to prevent stale MQL volume.
