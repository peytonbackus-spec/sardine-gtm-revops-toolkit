---
type: area
category: revops
tags:
  - area
  - territory-planning
  - revops
  - salesops
status: active
last_updated: 2026-08-21
---

# Enterprise Territory Planning & Equalization Model

## Executive Summary
Methodology for carving, equalizing, and balancing sales territories using Total Addressable Market (TAM), historical win rates, and account tiering to ensure quota equity across AEs.

## Account Scoring & Tiering Formula
Account Potential Index (API) balances firmographic fit and propensity to buy:

API = (Employee Count Score * 0.4) + (Tech Stack Match * 0.3) + (Funding/Growth Signal * 0.3)

* **Tier 1 (API > 85):** Top 10% of TAM. Assigned max 25 named accounts per AE.
* **Tier 2 (60 <= API <= 85):** Mid-market fit. Assigned max 75 named accounts per AE.
* **Tier 3 (API < 60):** Unassigned pooled territory for inbound/SDR routing.

## Territory Balancing Metrics

| Metric | Balance Target | Variance Threshold |
| :--- | :--- | :--- |
| **Pipeline Target Per Territory** | 4.0x AE Quota | +/- 10% across reps |
| **Tier 1 Account Count** | 20-25 Accounts | Max 2-account delta |
| **Historical Bookings Potential** | $1.2M ARR potential | Rebalance if delta > 15% |
