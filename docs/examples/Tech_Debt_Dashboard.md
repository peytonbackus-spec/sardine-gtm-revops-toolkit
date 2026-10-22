---
type: area
category: revops
tags:
  - revops
  - tech-debt
  - dashboard
date: 2026-08-21
status: active
---

# RevOps Technical Debt Dashboard

*Last Scanned: 2026-08-21 13:38* | **Active Debt Items: 2**

---

## Active Technical Debt Backlog

| Source Note | Location | Description / Remedy | Status |
| :--- | :--- | :--- | :--- |
| [Sync_Inclusion_Rules.md](../specs/architecture/Sync_Inclusion_Rules.md) | Line 14 | Disqualification workflow currently lacks field validation for missing reasons. | Open |
| [Lead_Scoring_PQL_Spec.md](../reference/not-applicable/Lead_Scoring_PQL_Spec.md) | Line 25 | Review scoring decay rules quarterly to prevent stale MQL volume. | Open |

---

## Usage Guide
To register a new piece of RevOps technical debt, add a row to the backlog above with the source doc, the line and the remedy.

For the Salesforce field audit (fill rate and days since last change, with a deprecate / review / retain call per field), run from the repository root:

```bash
python3 prototypes/revops_tech_debt_tracker.py
```

It runs on sample schema telemetry; point it at a real field-usage export before acting on the report.
