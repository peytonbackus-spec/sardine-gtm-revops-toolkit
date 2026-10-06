"""AI account research + qualification brief (production pattern, offline by default).

Role scope (GTM Engineer): production-ready AI workflows for account research,
enrichment, qualification and routing, connected to GTM systems via low-code tools
and APIs, with defined prompts, outputs, evaluation criteria and human-in-the-loop controls.

Flow (one record):
  CRM lead/account -> pii_guard (allow-list + redaction) -> versioned prompt
  -> LLM (mock or live) -> JSON contract check -> HITL policy -> review queue
  -> (on Accept) write brief to the CRM + Unify / HubSpot Sequences (assumed) cadence variable

In production the trigger is a CRM flow / enrichment-tool HTTP column calling this as
a small API (or an n8n workflow). The Python is the same either way.

    python -m gtm_engineer.ai_research.account_research            # mock mode, no API key
    GTM_LLM_MODE=anthropic ANTHROPIC_MODEL=<model> python -m ...   # live mode
"""
from __future__ import annotations

from pathlib import Path

from gtm_engineer.lead_scoring.score_leads import score_all
from shared_core.ai_governance.hitl import HITLPolicy, write_queue
from shared_core.ai_governance.llm_client import LLMClient, load_prompt
from shared_core.config import load_config, read_csv, table, to_bool

PROMPT_PATH = Path(__file__).parent / "prompts" / "account_research.md"
REQUIRED_KEYS = ["summary", "likely_use_case", "recommended_products", "persona_angle", "qualification",
                 "evidence", "unknowns", "next_action", "confidence"]

def product_set(cfg: dict, line: str) -> list[str]:
    """First two products of a product line, used as the default recommendation."""
    return cfg["product_lines"][line]["products"][:2]


def render_prompt(text: str, cfg: dict) -> str:
    """Fill {{COMPANY_NAME}} and {{PRODUCT_LINES}} from config so the prompt never names a real company."""
    lines = "\n".join(f"- {v['label']}: {', '.join(v['products'])}"
                      for k, v in cfg["product_lines"].items() if k != "cross_sell")
    return text.replace("{{COMPANY_NAME}}", cfg["company"]["name"]).replace("{{PRODUCT_LINES}}", lines)


def mock_responder(rec: dict) -> dict:
    """Deterministic stand-in for the model: same contract, same rules, no network."""
    seg, persona = rec.get("segment", ""), rec.get("persona", "")
    owned = set(filter(None, str(rec.get("products_owned", "")).split(";")))
    cfg = load_config()
    non_icp = seg in ("other", "") or cfg["personas"].get(persona, {}).get("role") == "none"
    lines = [k for k in cfg["product_lines"] if k != "cross_sell"]
    primary, secondary = lines[0], lines[1]
    if primary in owned and secondary not in owned:
        products = product_set(cfg, secondary)
    elif secondary in owned and primary not in owned and cfg["segments"].get(seg, {}).get("core_segment"):
        products = product_set(cfg, primary)[:1]
    elif rec.get("product_interest") in lines:
        products = product_set(cfg, rec["product_interest"])
    else:
        products = product_set(cfg, secondary)
    evidence = [{"claim": f"Segment is {seg}", "source_field": "segment"},
                {"claim": f"Title '{rec.get('title', '')}' maps to persona {persona}", "source_field": "title"}]
    if rec.get("intent_signals"):
        evidence.append({"claim": f"Recent signals: {rec['intent_signals'].split('|')[0].split('@')[0]}",
                         "source_field": "intent_signals"})
    unknowns = [f for f in ("employees", "region", "intent_signals") if not rec.get(f)]
    unknowns.append("current vendor and contract end date")
    confidence = round(max(0.4, 0.95 - 0.12 * (len(unknowns) - 1)), 2)
    customer = to_bool(rec.get("is_existing_customer"))
    return {
        "summary": f"{rec.get('company')} ({cfg['segments'].get(seg, {}).get('label', seg)}, {rec.get('region') or 'region unknown'}). "
                   f"{'Existing customer' if customer else 'Prospect'}; contact is {rec.get('title')}.",
        "likely_use_case": (f"Cross-sell to existing customer: {', '.join(products)} alongside current {', '.join(sorted(owned))} deployment"
                            if customer and owned and not non_icp
                            else cfg["segments"].get(seg, {}).get("use_case") or "Unclear: no use case identified"),
        "recommended_products": [] if non_icp else products,
        "persona_angle": cfg["personas"].get(persona, {}).get("angle") or "Confirm role and whether they own the outcome",
        "qualification": {"fit_assessment": "Non-ICP" if non_icp else ("Strong" if cfg["segments"].get(seg, {}).get("icp_points", 0) >= 26 else "Moderate"),
                          "disqualify_flag": non_icp,
                          "disqualify_reason": "Non-ICP segment or non-buyer persona" if non_icp else ""},
        "evidence": evidence,
        "unknowns": unknowns,
        "next_action": "disqualify_lead" if non_icp else ("route_to_ae" if customer else "enroll_cadence"),
        "confidence": confidence,
    }


def research(record: dict, client: LLMClient | None = None) -> dict:
    client = client or LLMClient()
    prompt_id, system = load_prompt(PROMPT_PATH)
    system = render_prompt(system, load_config())
    return client.complete_json(prompt_id=prompt_id, system=system, record=record, required_keys=REQUIRED_KEYS,
                                mock_responder=mock_responder, task="Produce the pre-call brief.")


def main() -> None:
    cfg = load_config()
    accounts = {a["account_id"]: a for a in read_csv("accounts.csv")}
    leads = [l for l in score_all(read_csv("leads.csv"), cfg) if l["status"] in ("New", "MQL", "Enriching")][:12]
    policy, queue = HITLPolicy(), []
    for lead in leads:
        rec = {**lead, "products_owned": accounts.get(lead["account_id"], {}).get("products_owned", "")}
        brief = research(rec)
        decision = policy.decide(brief["next_action"], brief["confidence"])
        queue.append({"lead_id": lead["lead_id"], "company": lead["company"], "grade": lead["grade"],
                      "use_case": brief["likely_use_case"], "products": ", ".join(brief["recommended_products"]),
                      "next_action": brief["next_action"], "confidence": brief["confidence"], "decision": decision,
                      "unknowns": "; ".join(brief["unknowns"])})
    print("=== AI account research: review queue ===\n")
    print(table(queue, ["lead_id", "company", "grade", "products", "next_action", "confidence", "decision"]))
    print(f"\nQueue -> {write_queue('account_research', queue)}")
    print("Audit log -> outputs/ai_audit_log.jsonl")


if __name__ == "__main__":
    main()
