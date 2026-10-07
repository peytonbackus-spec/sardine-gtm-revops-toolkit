"""VP of Sales brief, in two depths from the same numbers.

  snapshot  one phone screen: the number, three things to know, deals to act on, asks.
            For the leader who wants it fast. Every line names a decision or an action.
  full      the snapshot plus the evidence: rep scorecard, segment table, stage velocity with
            drivers, the full deal board and the definitions. For the leader who wants to dig in,
            and for the RevOps owner to defend any number in the snapshot.

Which one is the default is a question for the VP, not a RevOps guess (see vp-intake.md). Both are
written as Markdown to outputs/, ready to paste into Slack or email or to drop into a doc.

    python -m gtm_strategy_ops.sales_leadership.vp_brief                  # snapshot
    python -m gtm_strategy_ops.sales_leadership.vp_brief --mode full
"""
from __future__ import annotations

import argparse

from gtm_strategy_ops.pipeline_analytics.pipeline_report import coverage
from gtm_strategy_ops.sales_leadership import deal_board, rep_scorecard, segment_performance, stage_velocity
from gtm_strategy_ops.sales_planning.team import rep_quotas, shift_quarter
from shared_core.config import AS_OF, OUTPUT_DIR, fiscal_quarter, load_config, parse_date, pct, read_csv, to_float


def md_table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "_none_"
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
    body = "\n".join("| " + " | ".join(_fmt(r.get(c, "")) for c in cols) + " |" for r in rows)
    return f"{head}\n{body}"


def _fmt(v) -> str:
    if isinstance(v, bool):
        return "yes" if v else ""
    if isinstance(v, int) and abs(v) >= 1000:
        return f"{v:,}"
    return str(v)


def money(v: float) -> str:
    v = float(v)
    return f"${v / 1e6:.2f}M" if abs(v) >= 1e6 else f"${v / 1e3:.0f}K"


def gather(cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    opps = read_csv("opportunities.csv")
    board = deal_board.build(cfg, opps)
    q, prev_q = cfg["current_fiscal_quarter"], shift_quarter(cfg["current_fiscal_quarter"], -1)
    labels = {k: v["label"] for k, v in cfg["segments"].items()}
    won_prev = sum(to_float(o["amount"]) for o in opps
                   if o["is_won"] == "True" and fiscal_quarter(parse_date(o["close_date"])) == prev_q)
    quota_prev = sum(cfg["quota"].get(prev_q, {}).values())
    cov = coverage(opps, cfg)
    return {
        "cfg": cfg, "q": q, "prev_q": prev_q, "board": board,
        "won_prev": won_prev, "quota_prev": quota_prev, "attain_prev": pct(won_prev, quota_prev),
        "coverage": cov, "pipe_q": sum(c["open_pipeline"] for c in cov), "quota_q": sum(c["quota"] for c in cov),
        "commit_q": sum(c["commit"] for c in cov),
        "reps": rep_scorecard.scorecard(cfg, opps, board),
        "segments": segment_performance.performance_by(opps, "segment", cfg, label=lambda k: labels.get(k, k)),
        "base": segment_performance.company_baseline(opps, cfg),
        "velocity": stage_velocity.analyze(cfg, opps),
        "unassigned_quota": {r: v for r, v in cfg["quota"].get(q, {}).items()
                             if not any(rep_quotas(cfg, q)[ae] for ae, i in cfg["sales_team"]["ae_roster"].items() if i["region"] == r)},
    }


def asks(d: dict) -> list[str]:
    """Decisions only the VP can make, generated from the findings. Each names the evidence."""
    out = []
    v = d["velocity"]
    process = [x for x in v["drivers"] if x["dimension"] != "owner"]    # rep-specific drivers go to coaching, not process
    top = process[0] if process else None
    if top:
        out.append(f"**Approve a process fix for {v['bottleneck']['stage']}:** {top['fix_to_test']} "
                   f"(evidence: {top['dimension']} = {top['value']} runs +{top['excess_days']}d on {top['deals']} deals).")
    past_due = [r for r in d["board"] if r["bucket"] == "Past due"]
    if past_due:
        out.append(f"**Set a clean-up deadline:** {len(past_due)} open deals ({money(sum(r['amount'] for r in past_due))}) have a "
                   "close date in the past. Owners fix or close them before the forecast call.")
    cfgq = d["cfg"]["quota"][d["q"]]
    for r in d["coverage"]:
        if r["status"] == "GAP":
            out.append(f"**Decide on {r['region']} coverage:** {r['coverage_x']}x against {money(cfgq[r['region']])} quota. "
                       "Pull pipeline forward, move marketing spend, or re-forecast.")
    ramping = [x for x in d["reps"] if not x["ramped"] and isinstance(x["coverage_x"], float) and x["quota_$"]]
    for x in ramping:
        solo = sum(1 for y in d["reps"] if y["region"] == x["region"]) == 1
        if solo:
            out.append(f"**Quota check, {x['region']}:** the whole region quota sits on {x['owner']}, who is {x['ramp'].lower()}. "
                       "Confirm the number or cover it elsewhere (see the quota plan).")
    return out[:4]


def snapshot(d: dict) -> str:
    v, base = d["velocity"], d["base"]
    in_q = [r for r in d["board"] if r["in_quarter"]]
    risky = sorted([r for r in in_q if r["bucket"] in ("At risk", "Slipping", "Past due")], key=lambda r: -r["amount"])[:3]
    hot = sorted([r for r in d["board"] if r["bucket"] == "Hot"], key=lambda r: -r["amount"])[:2]
    strong = [s for s in d["segments"] if s["verdict"] == "Double down"]
    weak = [s for s in d["segments"] if s["verdict"] == "Fix"]
    coach = [r for r in d["reps"] if r["status"] == "Coach"]
    b = v["bottleneck"]
    top = v["drivers"][0] if v["drivers"] else None
    target = d["cfg"]["opportunity"]["coverage_target"]
    lines = [f"# Sales snapshot · {AS_OF.isoformat()}", "",
             f"**The number.** {d['prev_q']} closed {money(d['won_prev'])} vs {money(d['quota_prev'])} quota "
             f"({d['attain_prev']}%). {d['q']}: {money(d['pipe_q'])} pipeline = "
             f"{round(d['pipe_q'] / max(1, d['quota_q']), 2)}x coverage (target {target}x), commit {money(d['commit_q'])}.", "",
             "**Three things to know**",
             f"1. **Pipeline slows in {b['stage']}:** median {b['median_days']}d vs {b['limit_days']}d limit"
             + (f"; {top['dimension']} = {top['value']} deals take +{top['excess_days']}d." if top else "."),
             "2. **Industries:** " + ("winning in " + ", ".join(f"{s['segment']} ({s['win_rate_%']}%)" for s in strong) if strong else "no segment clearly ahead")
             + ("; losing in " + ", ".join(f"{s['segment']} ({s['win_rate_%']}%, mostly {s['top_loss_reason'].lower()})" for s in weak) if weak else "")
             + f" vs {base['win_rate_%']}% overall.",
             f"3. **Reps:** {sum(1 for r in d['reps'] if r['status'] in ('Ahead', 'On track'))} of {len(d['reps'])} on track for {d['q']}; "
             + (", ".join(f"{r['owner'].replace('AE - ', '')} ({rep_reason(r, target)})" for r in coach) + " need help now." if coach else "none need intervention."),
             "", f"**Deals to act on ({d['q']})**"]
    for r in risky:
        lines.append(f"- {r['bucket']}: {r['account_name']} {money(r['amount'])} ({r['owner'].replace('AE - ', '')}, {r['forecast_category']}): {r['why']}")
    for r in hot:
        lines.append(f"- Hot: {r['account_name']} {money(r['amount'])} ({r['owner'].replace('AE - ', '')}): {r['why']}")
    lines += ["", "**Asks for you**"] + [f"- {a}" for a in asks(d)]
    return "\n".join(lines) + "\n"


def rep_reason(r: dict, target: float) -> str:
    """One short reason a rep is flagged: the weak lever if there is one, else coverage."""
    lever = r.get("weakest_lever", "")
    if lever and not lever.startswith("none"):
        name, gap = lever.split(" (", 1)
        return f"{name.replace('_', ' ').replace(' $', '')} {gap.split(' vs')[0]} vs team"
    return f"coverage {r['coverage_x']}x vs {target}x" + ("; ramping" if not r.get("ramped", True) else "")


def full(d: dict) -> str:
    v = d["velocity"]
    parts = [snapshot(d).replace("# Sales snapshot", "# Sales brief (full)"), "---",
             "## 1. Coverage by region", md_table(d["coverage"], ["region", "quota", "closed_won", "open_pipeline", "weighted", "commit", "coverage_x", "status"]),
             f"## 2. Reps ({d['prev_q']} result, {d['q']} setup)",
             md_table(d["reps"], ["owner", "ramp", "status", "last_q_attainment_%", "quota_$", "pipeline_in_q_$", "coverage_x",
                                  "commit_$", "needs_attention", "win_rate_%", "avg_won_$", "cycle_days", "weakest_lever"]),
             "Coaching focus (manager 1:1s only):", "\n".join(f"- {r['owner']}: {r['coaching_focus']}" for r in d["reps"] if r["status"] in ("Watch", "Coach")),
             "## 3. Industries (trailing year)", segment_performance.headline(d["segments"], "segment", d["base"]),
             md_table(d["segments"], ["segment", "closed", "win_rate_%", "range_80%", "vs_company_pts", "avg_won_$", "median_cycle_days",
                                      "open_pipeline_$", "top_loss_reason", "top_competitor_lost_to", "verdict"]),
             "## 4. Where pipeline slows", stage_velocity.headline(v),
             md_table(v["stages"], ["stage", "entered", "conversion_%", "median_days", "p75_days", "limit_days", "pressure", "open_past_limit",
                                    "won_median_days", "lost_deal_median_days"]),
             f"Drivers inside {v['bottleneck']['stage']}:",
             md_table(v["drivers"][:5], ["dimension", "value", "deals", "median_days", "excess_days", "likely_cause", "fix_to_test"]),
             "## 5. Deal board", md_table(deal_board.summary(d["board"], in_quarter_only=True), ["bucket", "deals", "amount_$", "of_which_commit_$"]),
             md_table([r for r in d["board"] if r["in_quarter"] and r["bucket"] != "On track"],
                      ["bucket", "account_name", "owner", "stage", "amount", "forecast_category", "close_date", "why"]),
             "## 6. Definitions and data notes",
             "- Win rate = won / (won + lost), by close date, trailing year. Ranges are 80% Wilson intervals.\n"
             "- Coverage = open pipeline closing this quarter / (quota - closed won). Rep quota = region quota split by ramped rep equivalents.\n"
             "- Stage days come from field history on StageName; medians, so one stuck deal does not set the number.\n"
             "- Deal buckets: see deal_board.py. Risk levels come from the same model the forecast call uses.\n"
             "- All data in this repo is synthetic; patterns were planted so the reports have something to find."]
    return "\n\n".join(parts) + "\n"


def write(mode: str = "snapshot", cfg: dict | None = None) -> tuple[str, str]:
    d = gather(cfg)
    text = snapshot(d) if mode == "snapshot" else full(d)
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"vp_brief_{mode}.md"
    path.write_text(text, encoding="utf-8")
    return text, str(path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["snapshot", "full"], default="snapshot")
    text, path = write(ap.parse_args().mode)
    print(text)
    print(f"-> {path}")


if __name__ == "__main__":
    main()
