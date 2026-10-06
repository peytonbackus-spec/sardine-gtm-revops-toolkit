"""Two-axis lead scoring (Fit x Intent).

Role scope (GTM Engineer): own lead capture, enrichment, scoring, routing and
disqualification, and keep improving scoring using conversion outcomes and fit signals.

Why two axes instead of one blended number: an enterprise buyer with no
activity (A4) and a student who downloaded three ebooks (D1) can blend to the
same score. They need opposite treatment: ABM plays for the first, nurture or
disqualify for the second. The grade keeps that visible.

  Fit (0-100)    = segment + persona + size + product/segment alignment + region
  Intent (0-100) = sum of signal points, each decayed by its half-life
  Grade          = Fit letter (A-D) + Intent number (1-4), e.g. "A2"

All weights come from the company config (lead_scoring, segments, personas); calibrate_scoring.py tunes them.

    python -m gtm_engineer.lead_scoring.score_leads
"""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from shared_core.config import AS_OF, load_config, parse_date, read_csv, table, to_bool, to_float, write_csv


def hand_raiser_signals(cfg: dict) -> set[str]:
    """Signals flagged hand_raiser: true in config (explicit buying actions)."""
    return {k for k, v in cfg["lead_scoring"]["intent_signals"].items() if v.get("hand_raiser")}


def size_points(lead: dict, cfg: dict) -> int:
    """Employee-count bands from config (lead_scoring.size_bands); first match wins."""
    emp = to_float(lead.get("employees"))
    ls = cfg["lead_scoring"]
    for band in ls["size_bands"]:
        if emp >= band["min_employees"]:
            return band["points"]
    return ls["size_default_points"]


def alignment_points(lead: dict, cfg: dict) -> int:
    """Reward the product/segment combos the company actually wins (config: lead_scoring.alignment)."""
    seg, interest = lead.get("segment", ""), lead.get("product_interest", "")
    segs = cfg["segments"]
    for rule in cfg["lead_scoring"]["alignment"]:
        if rule["product_interest"] != interest:
            continue
        allowed = rule["segments"]
        if allowed == "core_segments":
            ok = bool(segs.get(seg, {}).get("core_segment"))
        elif allowed == "all_icp":
            ok = seg in segs and seg != "other"
        else:
            ok = seg in allowed
        if ok:
            return rule["points"]
    return 0


def fit_score(lead: dict, cfg: dict) -> int:
    seg_pts = cfg["segments"].get(lead.get("segment"), {"icp_points": 0})["icp_points"]
    per_pts = cfg["personas"].get(lead.get("persona"), {"points": 0})["points"]
    region_pts = cfg["lead_scoring"]["region_points"].get(lead.get("region", ""), 0)
    score = seg_pts + per_pts + size_points(lead, cfg) + alignment_points(lead, cfg) + region_pts
    return min(100, score)


def parse_signals(raw: str) -> list[tuple[str, date]]:
    out = []
    for item in filter(None, (raw or "").split("|")):
        name, _, when = item.partition("@")
        out.append((name, parse_date(when) or AS_OF))
    return out


def intent_score(lead: dict, cfg: dict, as_of: date = AS_OF) -> int:
    weights = cfg["lead_scoring"]["intent_signals"]
    total = 0.0
    for name, when in parse_signals(lead.get("intent_signals", "")):
        w = weights.get(name)
        if not w:
            continue
        age = max(0, (as_of - when).days)
        total += w["points"] * 0.5 ** (age / w["half_life_days"])
    return min(100, round(total))


def grade(fit: int, intent: int, cfg: dict) -> str:
    fb, ib = cfg["lead_scoring"]["fit_bands"], cfg["lead_scoring"]["intent_bands"]
    letter = "A" if fit >= fb["A"] else "B" if fit >= fb["B"] else "C" if fit >= fb["C"] else "D"
    number = 1 if intent >= ib[1] else 2 if intent >= ib[2] else 3 if intent >= ib[3] else 4
    return f"{letter}{number}"


def recommend(lead: dict, g: str, cfg: dict, as_of: date = AS_OF) -> str:
    hand_raisers = hand_raiser_signals(cfg)
    recent_hand_raise = any(n in hand_raisers and (as_of - d).days <= 14
                            for n, d in parse_signals(lead.get("intent_signals", "")))
    if to_bool(lead.get("is_existing_customer")):
        return "Route to account owner (expansion)"
    if g[0] == "D":
        return "Nurture / disqualify review"
    if g in cfg["lead_scoring"]["mql_grades"] or (recent_hand_raise and g[0] in "ABC"):
        return "MQL -> route to SDR now"
    if g[0] == "A":
        return "Target account: add to ABM play"
    return "Nurture"


def score_all(leads: list[dict], cfg: dict | None = None, as_of: date = AS_OF, point_in_time_days: int | None = None) -> list[dict]:
    """Score every lead. With point_in_time_days set, intent is scored as it looked N days after the
    lead was created. Calibration needs that, because scoring an old lead's intent "as of today"
    would decay every signal to zero and hide whether intent predicted conversion."""
    cfg = cfg or load_config()
    out = []
    for lead in leads:
        when = as_of
        if point_in_time_days is not None:
            when = min(as_of, (parse_date(lead["created_date"]) or as_of) + timedelta(days=point_in_time_days))
        f, i = fit_score(lead, cfg), intent_score(lead, cfg, when)
        g = grade(f, i, cfg)
        out.append({**lead, "fit_score": f, "intent_score": i, "grade": g, "recommendation": recommend(lead, g, cfg, when)})
    return out


def main() -> None:
    scored = score_all(read_csv("leads.csv"))
    grid = Counter(r["grade"] for r in scored)
    print(f"=== {load_config()['company']['name']} lead grade distribution (Fit letter x Intent number) ===\n")
    rows = [{"fit": L, **{str(n): grid.get(f"{L}{n}", 0) for n in range(1, 5)}} for L in "ABCD"]
    print(table(rows, ["fit", "1", "2", "3", "4"]))
    print("\nRecommendations:")
    for rec, n in Counter(r["recommendation"] for r in scored).most_common():
        print(f"  {n:>4}  {rec}")
    top = sorted(scored, key=lambda r: (r["fit_score"] + r["intent_score"]), reverse=True)[:8]
    print("\nTop leads right now:")
    print(table(top, ["lead_id", "company", "title", "segment", "fit_score", "intent_score", "grade", "recommendation"]))
    path = write_csv("scored_leads.csv", scored)
    print(f"\nFull output -> outputs/{path.name}")


if __name__ == "__main__":
    main()
