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
| [Lead_Scoring_PQL_Spec.md](../specs/lead-management/Lead_Scoring_PQL_Spec.md) | Line 25 | Review scoring decay rules quarterly to prevent stale MQL volume. | Open |

---

## Usage Guide
To register a new piece of RevOps technical debt, add `#tech-debt` followed by an explanation anywhere in your Obsidian notes, then run:

```bash
python3 "$HOME/GTM 2nd Brain/30_Resources/Code/revops_tech_debt_tracker.py"
```
