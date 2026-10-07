"""Stage timelines and close-date pushes from opportunity field history.

Source: Salesforce OpportunityFieldHistory (field history tracking on StageName and CloseDate),
exported here as sample_data/opportunity_field_history.csv. Every opportunity starts in the first
open stage on its created date; each StageName change ends one stage and starts the next.

Why field history and not `stage_entered_date`: the opportunity row only knows the current stage.
Stage velocity ("how long does Qualify -> Discovery take, and for whom?") needs every stage a
deal passed through, including the ones it has left.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from shared_core.config import AS_OF, parse_date, read_csv

CLOSED = ("Closed Won", "Closed Lost")


def load_history(name: str = "opportunity_field_history.csv") -> list[dict]:
    return read_csv(name)


def stage_order(cfg: dict) -> list[str]:
    return [s["name"] for s in cfg["opportunity"]["stages"] if s["name"] not in CLOSED]


def stage_timelines(opps: list[dict], history: list[dict], cfg: dict, as_of: date = AS_OF) -> list[dict]:
    """One row per (opportunity, open stage it entered).

    outcome: 'advanced' (moved to a later open stage or won), 'lost' (closed lost from this stage),
    'open' (still sitting here). days: time in the stage; for 'open', days so far.
    """
    order = stage_order(cfg)
    rank = {s: i for i, s in enumerate(order)}
    changes = defaultdict(list)
    for h in history:
        if h["field"] == "StageName":
            changes[h["opportunity_id"]].append(h)
    rows = []
    for o in opps:
        oid = o["opportunity_id"]
        seq = sorted(changes.get(oid, []), key=lambda h: (h["changed_date"], rank.get(h["new_value"], 99)))
        entered, stage = parse_date(o["created_date"]), order[0]
        for h in seq:
            when, nxt = parse_date(h["changed_date"]), h["new_value"]
            outcome = "lost" if nxt == "Closed Lost" else "advanced"
            rows.append(_row(o, stage, entered, when, nxt, outcome))
            if nxt in CLOSED:
                stage = None
                break
            entered, stage = when, nxt
        if stage is not None:
            rows.append(_row(o, stage, entered, None, "", "open", as_of))
    return rows


def _row(o: dict, stage: str, entered: date, exited: date | None, nxt: str, outcome: str, as_of: date = AS_OF) -> dict:
    days = ((exited or as_of) - entered).days
    return {"opportunity_id": o["opportunity_id"], "owner": o["owner"], "segment": o["segment"], "region": o["region"],
            "source": o["source"], "product_line": o["product_line"], "type": o["type"],
            "economic_buyer_engaged": o.get("economic_buyer_engaged", ""), "contacts_engaged": o.get("contacts_engaged", ""),
            "amount": o["amount"], "is_won": o.get("is_won", ""), "stage": stage, "entered": entered, "exited": exited,
            "next_stage": nxt, "outcome": outcome, "days": max(days, 0)}


def close_pushes(history: list[dict]) -> dict[str, list[dict]]:
    """Close-date changes per opportunity that moved the date later (a 'push'), with days pushed."""
    out = defaultdict(list)
    for h in history:
        if h["field"] != "CloseDate" or not h["old_value"] or not h["new_value"]:
            continue
        delta = (parse_date(h["new_value"]) - parse_date(h["old_value"])).days
        if delta > 0:
            out[h["opportunity_id"]].append({"changed_date": parse_date(h["changed_date"]), "days_pushed": delta})
    return out


def last_advance(timelines: list[dict]) -> dict[str, date]:
    """Most recent date each opportunity moved forward a stage."""
    out = {}
    for t in timelines:
        if t["outcome"] == "advanced" and t["exited"]:
            out[t["opportunity_id"]] = max(out.get(t["opportunity_id"], t["exited"]), t["exited"])
    return out
