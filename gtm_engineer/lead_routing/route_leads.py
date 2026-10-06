"""Lead routing engine: ordered rules, first match wins, every decision explained.

Role scope (GTM Engineer): own lead capture, enrichment, scoring, routing and
disqualification, and translate GTM policy into CRM configuration.

The rule order *is* the GTM policy, written so Sales, Marketing and SDR
leadership can read it and argue about it:

  R1  Bad data / non-ICP          -> Disqualify queue (with reason)
  R2  Existing open opportunity   -> Opportunity owner (no new lead work)
  R3  Existing customer           -> Account owner (expansion play)
  R4  Partner referral            -> Partner manager (channel partners in config)
  R5  Not yet MQL                 -> Nurture
  R6  Pod match (segment+region)  -> SDR in that pod, capacity-aware round robin
  R7  Fallback                    -> Ops review queue (a routing gap to fix)

Every lead gets `routing_rule` and `routing_reason` stamped, so "why did this
lead go to X?" is answerable from the record. In Salesforce this maps to a
record-triggered Flow calling an invocable Apex/Flow subflow per rule (see
salesforce-routing-flow-spec.md); here it is plain Python against sample data.

    python -m gtm_engineer.lead_routing.route_leads
"""
from __future__ import annotations

from collections import Counter, defaultdict

from gtm_engineer.lead_scoring.score_leads import score_all
from shared_core.config import load_config, read_csv, table, to_bool, write_csv


def pod_for(lead: dict, cfg: dict) -> str | None:
    for pod, rule in cfg["lead_routing"]["pods"].items():
        seg_ok = "*" in rule["segments"] or lead.get("segment") in rule["segments"]
        if seg_ok and lead.get("region") in rule["regions"]:
            return pod
    return None


class Router:
    def __init__(self, cfg: dict, open_opp_accounts: dict[str, str], account_owners: dict[str, str]):
        self.cfg = cfg
        self.open_opp_accounts = open_opp_accounts      # account_id -> opp owner
        self.account_owners = account_owners            # account_id -> AE owner (customers)
        self.load = defaultdict(int)                    # sdr -> leads assigned in this run
        self.cap = cfg["lead_routing"]["max_open_leads_per_sdr"]

    def _round_robin(self, pod: str) -> str | None:
        candidates = [s for s in self.cfg["lead_routing"]["pod_sdrs"].get(pod, []) if self.load[s] < self.cap]
        if not candidates:
            return None
        sdr = min(candidates, key=lambda s: self.load[s])  # least-loaded first
        self.load[sdr] += 1
        return sdr

    def route(self, lead: dict) -> dict:
        def done(rule, owner, reason):
            return {**lead, "routed_to": owner, "routing_rule": rule, "routing_reason": reason}

        if lead.get("segment") == "other" or not lead.get("email"):
            return done("R1", "Disqualify Queue", "Non-ICP segment" if lead.get("segment") == "other" else "No valid email")
        acct = lead.get("account_id", "")
        if acct in self.open_opp_accounts:
            return done("R2", self.open_opp_accounts[acct], "Open opportunity on account: attach as contact role")
        if to_bool(lead.get("is_existing_customer")):
            return done("R3", self.account_owners.get(acct, "AE - Unassigned"), "Existing customer: expansion/cross-sell")
        if lead.get("partner"):
            return done("R4", self.cfg["lead_routing"]["partner_manager"], f"Partner referral via {lead['partner']}")
        if not lead.get("recommendation", "").startswith("MQL"):
            return done("R5", "Nurture", f"Grade {lead.get('grade')} below MQL threshold")
        pod = pod_for(lead, self.cfg)
        if pod:
            sdr = self._round_robin(pod)
            if sdr:
                return done("R6", sdr, f"Pod {pod}; least-loaded SDR")
            return done("R7", "Ops Review Queue", f"Pod {pod} at capacity")
        return done("R7", "Ops Review Queue", "No pod matches segment/region (often a blank region)")


def build_router(cfg: dict) -> Router:
    opps = read_csv("opportunities.csv")
    open_opp = {o["account_id"]: o["owner"] for o in opps if o["is_closed"] != "True"}
    owners = {o["account_id"]: o["owner"] for o in opps}
    return Router(cfg, open_opp, owners)


def main() -> None:
    cfg = load_config()
    # route only the active top-of-funnel: new/enriching/MQL leads from the scored set
    leads = [l for l in score_all(read_csv("leads.csv"), cfg) if l["status"] in ("New", "Enriching", "MQL")]
    router = build_router(cfg)
    routed = [router.route(l) for l in leads]
    print(f"=== Routed {len(routed)} active leads ===\n")
    print(table([{"rule": r, "leads": n} for r, n in sorted(Counter(x["routing_rule"] for x in routed).items())]))
    print("\nSDR load this run:", dict(router.load))
    print("\nSample decisions:")
    print(table(routed[:10], ["lead_id", "company", "segment", "region", "grade", "routing_rule", "routed_to", "routing_reason"]))
    write_csv("routed_leads.csv", routed)
    print("\nFull output -> outputs/routed_leads.csv")


if __name__ == "__main__":
    main()
