# Roadmap

What to build next in a derived repo, once there's real company data and access. Ordered by when it happens.

## First 30 days (baseline before building)

- Point the [DQ monitor](../../shared_core/data_quality/dq_monitor.py) at a read-only CRM export; first pass-rate baseline
- Back-test the current lead score with the [calibration method](../../gtm_engineer/lead_scoring/calibrate_scoring.py) on 12 months of outcomes
- Compute week 4/8/12 forecast accuracy and bias from 4 quarters of forecasting-tool snapshots
- Replace every `[ASSUME]` in the company config with actuals

## Days 31–90

| 🟦 GTM Engineer | 🟩 Strategy & Ops |
|---|---|
| Routing v2 in CRM flows, replay-tested against the last 200 MQLs | Stage exit criteria as validation rules |
| Re-weighted two-axis scoring | Separate forecast tabs: new business / renewals |
| Paid contact-data spend limited to B+ fit economic buyers | Deal-risk flags in shadow mode, then shown before manager calls |
| AI research brief: shadow → assisted | Renewal health v1 for the T-180 window |

## Later

- Swap the SQLite runner for the real warehouse with dbt models built from the semantic layer
- Live LLM mode once vendor and retention terms are approved by security
- Calibrate renewal health weights and expected churn rates on actual outcomes
- Partner portal / deal registration integration once the partner data path is known
- Promote scripts from `prototypes/` into the tracks, with tests
