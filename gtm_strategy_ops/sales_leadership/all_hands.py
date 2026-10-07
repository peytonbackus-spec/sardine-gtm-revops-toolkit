"""Inputs for a sales all-hands: wins, recognition, what happened (good and bad), lessons, focus.

Output is a slide-by-slide outline with the numbers filled in and speaker prompts, so the VP (or
whoever presents) spends their prep time on the story, not on pulling data.

Periods:
  --period quarter   the last full fiscal quarter (quarterly all-hands / QBR opener)   [default]
  --days 7           the last 7 days (weekly team meeting)
  --days 1           yesterday and today (daily stand-up pulse: "what happened today")

Rules built in, because an all-hands is a culture moment, not a performance review:
  - Recognize the top `recognize_top_n` by name. Never rank the bottom publicly; under-performance
    goes to the manager 1:1 (rep_scorecard.py).
  - Bad news is shown as team patterns (loss reasons, slipped dollars), never as a name on a slide.
  - Recognition is specific: the deal, the competitor displaced, the behaviour that won it. Gallup's
    recognition research finds generic praise lands as inauthentic; the story prompts ask for specifics.
  - Every number reconciles to the VP brief: same deal board, same quotas, same definitions.

    python -m gtm_strategy_ops.sales_leadership.all_hands
    python -m gtm_strategy_ops.sales_leadership.all_hands --days 7
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import timedelta

from gtm_strategy_ops.sales_leadership import deal_board, segment_performance, stage_velocity
from gtm_strategy_ops.sales_leadership.history import close_pushes, load_history, stage_timelines
from gtm_strategy_ops.sales_leadership.vp_brief import money
from gtm_strategy_ops.sales_planning.team import ramp_factor, rep_quotas, roster, shift_quarter
from shared_core.config import AS_OF, OUTPUT_DIR, fiscal_quarter, load_config, parse_date, pct, read_csv, to_float


def in_window(d, period: str, days: int, prev_q: str) -> bool:
    if d is None:
        return False
    if period == "quarter":
        return fiscal_quarter(d) == prev_q
    return AS_OF - timedelta(days=days) <= d <= AS_OF


def build(period: str = "quarter", days: int = 7, cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    opps, history = read_csv("opportunities.csv"), load_history()
    sl = cfg["sales_leadership"]
    q, prev_q = cfg["current_fiscal_quarter"], shift_quarter(cfg["current_fiscal_quarter"], -1)
    labels = {k: v["label"] for k, v in cfg["segments"].items()}
    none_vals = sl["all_hands"]["competitor_none_values"]

    def win(d):
        return in_window(d, period, days, prev_q)

    closed = [o for o in opps if o["is_closed"] == "True" and win(parse_date(o["close_date"]))]
    wins = sorted([o for o in closed if o["is_won"] == "True"], key=lambda o: -to_float(o["amount"]))
    losses = [o for o in closed if o["is_won"] != "True"]
    created = [o for o in opps if win(parse_date(o["created_date"]))]
    tl = stage_timelines(opps, history, cfg)
    advances = [t for t in tl if t["outcome"] == "advanced" and t["next_stage"] != "Closed Won" and win(t["exited"])]
    pushes = close_pushes(history)
    pushed = {oid for oid, ps in pushes.items() if any(win(p["changed_date"]) for p in ps)}
    amount = {o["opportunity_id"]: to_float(o["amount"]) for o in opps}
    first_win = {}
    for o in opps:
        if o["is_won"] == "True":
            first_win[o["segment"]] = min(first_win.get(o["segment"], parse_date(o["close_date"])), parse_date(o["close_date"]))

    win_rows = []
    for o in wins:
        cycle = (parse_date(o["close_date"]) - parse_date(o["created_date"])).days
        tags = []
        if o["competitor"] not in none_vals:
            tags.append("chose us over building in-house" if "in-house" in o["competitor"].lower()
                        else f"displaced {o['competitor']}")
        if o["type"] == "Expansion":
            tags.append("expansion")
        if parse_date(o["close_date"]) == first_win[o["segment"]] and o["type"] == "New Logo":
            tags.append("first win in segment")
        win_rows.append({"account_name": o["account_name"], "segment": labels.get(o["segment"], o["segment"]), "owner": o["owner"],
                         "amount": int(to_float(o["amount"])), "type": o["type"], "product_line": o["product_line"],
                         "cycle_days": cycle, "contacts": o["contacts_engaged"], "tags": ", ".join(tags)})

    # Recognition: top N only, ramped reps judged on attainment, everyone on pipeline created.
    n = sl["all_hands"]["recognize_top_n"]
    recog = {}
    if period == "quarter":
        quotas = rep_quotas(cfg, prev_q)
        att = []
        for ae, info in roster(cfg).items():
            if quotas[ae] and ramp_factor(info["start_date"], prev_q, cfg) >= 1:
                w = sum(to_float(o["amount"]) for o in wins if o["owner"] == ae)
                att.append((ae, pct(w, quotas[ae]), w))
        att = sorted([a for a in att if a[1] >= 100], key=lambda a: -a[1])[:n]
        recog["Quota attainment"] = [f"{ae} {round(a)}% ({money(w)})" for ae, a, w in att]
    by_created = defaultdict(float)
    for o in created:
        by_created[o["owner"]] += to_float(o["amount"])
    recog["Pipeline created"] = [f"{k} ({money(v)})" for k, v in sorted(by_created.items(), key=lambda x: -x[1])[:n]]
    by_adv = Counter(t["owner"] for t in advances)
    recog["Deals moved forward"] = [f"{k} ({plural(v, 'stage advance', 'stage advances')})" for k, v in by_adv.most_common(n)]

    board = deal_board.build(cfg, opps, history)
    base = segment_performance.company_baseline(opps, cfg)
    segs = segment_performance.performance_by(opps, "segment", cfg, label=lambda k: labels.get(k, k))
    vel = stage_velocity.analyze(cfg, opps, history)
    quota_prev = sum(cfg["quota"].get(prev_q, {}).values())
    return {
        "cfg": cfg, "period": period, "days": days, "q": q, "prev_q": prev_q,
        "label": prev_q if period == "quarter" else ("today" if days <= 1 else f"last {days} days"),
        "won_$": sum(to_float(o["amount"]) for o in wins), "won_n": len(wins), "quota_prev": quota_prev,
        "lost_$": sum(to_float(o["amount"]) for o in losses), "lost_n": len(losses),
        "loss_reasons": Counter(o["closed_lost_reason"] or "No reason given" for o in losses).most_common(3),
        "lost_to": Counter(o["competitor"] for o in losses if o["competitor"] not in none_vals).most_common(2),
        "created_$": sum(to_float(o["amount"]) for o in created), "created_n": len(created),
        "advances_n": len(advances), "advanced_deals": len({t["opportunity_id"] for t in advances}),
        "advances_$": sum(amount[oid] for oid in {t["opportunity_id"] for t in advances}),
        "pushed_n": len(pushed), "pushed_$": sum(amount.get(oid, 0) for oid in pushed),
        "wins": win_rows, "recognition": recog, "board": board, "base": base, "segments": segs, "velocity": vel,
        "win_rate_%": pct(len(wins), len(closed)),
    }


def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def render(d: dict) -> str:
    cfg, q = d["cfg"], d["q"]
    hot = sorted([r for r in d["board"] if r["bucket"] == "Hot"], key=lambda r: -r["amount"])
    in_q = [r for r in d["board"] if r["in_quarter"]]
    pipe_q = sum(r["amount"] for r in in_q)
    quota_q = sum(cfg["quota"][q].values())
    strong = [s for s in d["segments"] if s["verdict"] == "Double down"]
    b = d["velocity"]["bottleneck"]
    process = [x for x in d["velocity"]["drivers"] if x["dimension"] != "owner"]
    L = [f"# Sales all-hands inputs · {d['label']}", "",
         "_Slide outline with numbers filled in. Confirm names with managers before presenting._", "",
         "## Slide 1 · The number"]
    if d["period"] == "quarter":
        L.append(f"- {d['prev_q']}: {money(d['won_$'])} closed won vs {money(d['quota_prev'])} quota "
                 f"(**{pct(d['won_$'], d['quota_prev'])}%**), {d['won_n']} deals, {d['win_rate_%']}% win rate.")
    else:
        L.append(f"- {d['label'].capitalize()}: {d['won_n']} wins ({money(d['won_$'])}), {plural(d['advanced_deals'], 'deal', 'deals')} moved forward a stage "
                 f"({money(d['advances_$'])}), {plural(d['created_n'], 'new opportunity', 'new opportunities')} ({money(d['created_$'])}).")
    L.append(f"- {q} starts with {money(pipe_q)} open pipeline against {money(quota_q)} quota "
             f"({round(pipe_q / max(1, quota_q), 2)}x; target {cfg['opportunity']['coverage_target']}x).")
    L += ["", "## Slide 2 · Wins"]
    if d["wins"]:
        top = d["wins"][0]
        fastest = min(d["wins"], key=lambda w: w["cycle_days"])
        comp = [w for w in d["wins"] if "displaced" in w["tags"] or "in-house" in w["tags"]]
        L.append(f"- **Biggest:** {top['account_name']} ({top['segment']}), {money(top['amount'])}, {top['owner'].replace('AE - ', '')}.")
        L.append(f"- **Fastest:** {fastest['account_name']} in {fastest['cycle_days']} days, {fastest['owner'].replace('AE - ', '')}.")
        if comp:
            L.append("- **Competitive displacements:** " + "; ".join(f"{w['account_name']} ({w['tags'].split(',')[0].replace('displaced ', 'over ').replace('chose us over building in-house', 'over an in-house build')})" for w in comp[:4]) + ".")
        new_seg = [w for w in d["wins"] if "first win in segment" in w["tags"]]
        if new_seg:
            L.append("- **First wins in a new segment:** " + ", ".join(f"{w['account_name']} ({w['segment']})" for w in new_seg) + ".")
        L += ["", "| Account | Segment | AE | Amount | Cycle (d) | Notes |", "|---|---|---|---|---|---|"]
        L += [f"| {w['account_name']} | {w['segment']} | {w['owner'].replace('AE - ', '')} | {money(w['amount'])} | {w['cycle_days']} | {w['tags']} |"
              for w in d["wins"][:10]]
    else:
        L.append("- No closed-won deals in this window. Lead with deals that moved forward (slide 4).")
    L += ["", "## Slide 3 · Recognition (top performers only)"]
    for title, rows in d["recognition"].items():
        if rows:
            L.append(f"- **{title}:** " + "; ".join(r.replace("AE - ", "") for r in rows))
    L += ["", "## Slide 4 · What happened: the good and the bad",
          f"- **Good:** {plural(d['won_n'], 'win', 'wins')} ({money(d['won_$'])}); {plural(d['advanced_deals'], 'deal', 'deals')} moved forward "
          f"({plural(d['advances_n'], 'stage advance', 'stage advances')}, {money(d['advances_$'])}); {plural(d['created_n'], 'new opportunity', 'new opportunities')} ({money(d['created_$'])}).",
          f"- **Bad:** {plural(d['lost_n'], 'loss', 'losses')} ({money(d['lost_$'])}); {plural(d['pushed_n'], 'deal', 'deals')} had a close date pushed ({money(d['pushed_$'])}).",
          "- Top loss reasons: " + (", ".join(f"{r} ({c})" for r, c in d["loss_reasons"]) or "none") + "."
          + (" Lost most often to: " + ", ".join(f"{c} ({n})" for c, n in d["lost_to"]) + "." if d["lost_to"] else ""),
          "", "## Slide 5 · What we learned",
          f"- Win rate is {d['base']['win_rate_%']}% over the trailing year."
          + (" We win most in " + ", ".join(f"{s['segment']} ({s['win_rate_%']}%)" for s in strong) + ": bring those stories to similar accounts." if strong else ""),
          f"- {d['loss_reasons'][0][0] if d['loss_reasons'] else 'Loss reasons'} is the top reason we lose. One specific counter-move from a win this period.",
          "", "## Slide 6 · Focus for next period",
          f"- **One behaviour:** deals slow most in {b['stage']} (median {b['median_days']}d)."
          + (f" {process[0]['fix_to_test']}" if process else ""),
          "- **Deals to rally around:** " + ("; ".join(f"{r['account_name']} {money(r['amount'])} ({r['owner'].replace('AE - ', '')})" for r in hot[:3]) or "none flagged hot yet") + ".",
          "", "## Speaker prompts (ask the AE behind each top win)",
          "- What was the trigger that opened the deal, and how did we find it?",
          "- Who was the champion, and what did we give them to sell internally?",
          "- What nearly killed it, and what did we do about it?",
          "- What would you tell a teammate working a similar account next week?",
          "", "## Prep checklist",
          "- [ ] Names and wins confirmed with each manager (no surprises on stage).",
          "- [ ] Numbers match this week's VP brief (same deal board and quota file).",
          "- [ ] Under-performance stays in 1:1s; nothing on a slide ranks the bottom of the team.",
          "- [ ] One customer quote or call clip per top win, if the customer allows it."]
    return "\n".join(L) + "\n"


def write(period: str = "quarter", days: int = 7) -> tuple[str, str]:
    d = build(period, days)
    text = render(d)
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / (f"all_hands_{d['prev_q']}.md" if period == "quarter" else f"all_hands_last_{days}d.md")
    path.write_text(text, encoding="utf-8")
    return text, str(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", choices=["quarter", "days"], default=None)
    ap.add_argument("--days", type=int, default=None)
    a = ap.parse_args()
    period = "days" if a.days is not None or a.period == "days" else "quarter"
    text, path = write(period, a.days or 7)
    print(text)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
