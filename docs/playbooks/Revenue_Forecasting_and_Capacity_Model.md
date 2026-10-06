---
type: area
category: revops
tags:
  - area
  - forecasting
  - salesops
  - capacity
status: active
last_updated: 2026-08-21
---

# Revenue Forecasting & Sales Capacity Model

## Executive Summary
This operational playbook details the revenue forecasting methodology, weighted pipeline coverage rules, and rep capacity planning models used to predict quarterly ARR growth.

## 1. Weighted Forecasting Methodology

Pipeline is categorized into forecast categories with strict probability weightings:

* **Omitted (0%):** Unqualified leads or disqualified opportunities.
* **Pipeline (10% - 20%):** Stage 1 Discovery & Qualification.
* **Best Case (50%):** Stage 3 Technical Validation / Business Case complete.
* **Commit (85%):** Stage 4 Procurement / Legal Review; verbal approval secured.
* **Closed Won (100%):** Fully executed contract.

Weighted Pipeline = Sum(Opportunity Amount * Stage Probability)

## 2. Pipeline Coverage Target Ratios

Target pipeline coverage ratios must be maintained at the start of each quarter:

| Deal Motion | Sales Cycle Length | Required Pipeline Coverage Ratio |
| :--- | :--- | :--- |
| SMB | < 30 days | 3.0x of remaining quota |
| Mid-Market | 30 - 90 days | 3.5x of remaining quota |
| Enterprise | > 90 days | 4.5x of remaining quota |

## 3. Quota & AE Capacity Model

Effective capacity calculates total ramped Account Executive (AE) quota output:

* **Ramped AE:** Counts as 1.0 FTE (100% quota target).
* **Ramping AE (Months 1-3):** Counts as 0.25 FTE.
* **Ramping AE (Months 4-6):** Counts as 0.65 FTE.

Effective AE Capacity = (Ramped AEs * 1.0) + Sum(Ramping AEs * Ramp Factor)

### Operational Safeguards
* **SDR Ratio:** Maintain 1 SDR per 2 Mid-Market AEs to ensure top-of-funnel pipeline volume.
* **Slippage Buffer:** Always apply an empirical 15% slippage factor to Enterprise deals forecasting close within the final 10 days of the quarter.
