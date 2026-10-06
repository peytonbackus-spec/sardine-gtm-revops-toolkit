"""Human-in-the-loop review queue.

AI output in this repo never writes straight to the CRM, the sequencer or the forecasting tool.
It lands in a review queue with a recommended action. A policy decides what can
auto-apply and what needs a person:

  * auto_apply: confidence >= threshold AND the action is low-impact (e.g. a field
    suggestion on a lead)
  * human_review: everything else, and always for revenue-impacting actions
    (forecast category changes, deal-risk flags on large deals, renewal escalations)

The reviewer marks Accept / Modify / Reject. Acceptance rate per prompt is the
first eval signal in production: a prompt with a falling accept rate gets reworked.
"""
from __future__ import annotations

from dataclasses import dataclass

from shared_core.config import write_csv


@dataclass
class HITLPolicy:
    auto_apply_confidence: float = 0.85
    always_review_actions: tuple[str, ...] = ("change_forecast_category", "flag_deal_risk", "escalate_renewal",
                                              "disqualify_lead", "route_to_ae")
    large_deal_threshold: float = 150_000

    def decide(self, action: str, confidence: float, amount: float = 0.0) -> str:
        if action in self.always_review_actions or amount >= self.large_deal_threshold:
            return "human_review"
        return "auto_apply" if confidence >= self.auto_apply_confidence else "human_review"


def write_queue(name: str, items: list[dict]) -> str:
    rows = [{**i, "review_status": "Pending" if i.get("decision") == "human_review" else "Auto-applied",
             "reviewer": "", "reviewer_action": ""} for i in items]
    return str(write_csv(f"review_queue_{name}.csv", rows))
