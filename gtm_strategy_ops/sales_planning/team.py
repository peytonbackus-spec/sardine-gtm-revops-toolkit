"""The AE roster, ramp and per-rep quota: one definition shared by planning and leadership reporting.

Rep quota for a quarter = the region's quota (config `quota`) split across that region's AEs in
proportion to their ramped rep equivalents (RREs). A rep in their first quarter carries no quota;
a fully ramped rep carries a full share. The same split feeds the capacity model, the quota plan,
the rep scorecard and the all-hands leaderboard, so a rep's number never differs between reports.
"""
from __future__ import annotations

from datetime import date

from shared_core.config import fiscal_quarter


def quarter_index(label: str) -> int:
    """'FY26-Q3' -> a sortable integer, so tenure can be counted in quarters."""
    fy, q = label.split("-Q")
    return int(fy[2:]) * 4 + int(q) - 1


def quarter_label(index: int) -> str:
    return f"FY{index // 4:02d}-Q{index % 4 + 1}"


def shift_quarter(label: str, n: int) -> str:
    return quarter_label(quarter_index(label) + n)


def roster(cfg: dict) -> dict[str, dict]:
    return cfg["sales_team"]["ae_roster"]


def tenure_quarter(start: date, quarter: str) -> int:
    """1 = the quarter the AE started in; 0 or less = not yet hired."""
    return quarter_index(quarter) - quarter_index(fiscal_quarter(start)) + 1


def ramp_factor(start: date, quarter: str, cfg: dict) -> float:
    t = tenure_quarter(start, quarter)
    if t < 1:
        return 0.0
    vec = cfg["sales_team"]["ramp_vector"]
    return float(vec[min(t, len(vec)) - 1])


def ramp_status(start: date, quarter: str, cfg: dict) -> str:
    f = ramp_factor(start, quarter, cfg)
    return "Ramped" if f >= 1 else f"Ramping ({int(f * 100)}%)"


def rep_quotas(cfg: dict, quarter: str) -> dict[str, float]:
    """Quota per AE for a quarter, from the region quota split by ramped rep equivalents."""
    region_quota = cfg["quota"].get(quarter, {})
    team = roster(cfg)
    rre = {ae: ramp_factor(r["start_date"], quarter, cfg) for ae, r in team.items()}
    out = {}
    for ae, r in team.items():
        pool = sum(rre[a] for a, rr in team.items() if rr["region"] == r["region"])
        share = rre[ae] / pool if pool else 0.0
        out[ae] = int(round(region_quota.get(r["region"], 0) * share, -3))   # whole thousands, as quotas are set
    return out
