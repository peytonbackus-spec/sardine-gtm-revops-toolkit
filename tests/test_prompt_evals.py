"""Prompt eval suites for every AI workflow. CI fails if any case regresses."""
import pytest

from gtm_engineer.ai_research.account_research import research
from gtm_strategy_ops.ai_deal_risk.deal_risk import evaluate_deal
from shared_core.ai_governance.eval_harness import run_evals

SUITES = [
    ("🟦 account research", "gtm_engineer/ai_research/evals/account_research_cases.json", research),
    ("🟩 deal risk", "gtm_strategy_ops/ai_deal_risk/evals/deal_risk_cases.json", evaluate_deal),
]


@pytest.mark.parametrize("name,path,fn", SUITES, ids=[s[0] for s in SUITES])
def test_eval_suite_passes(name, path, fn):
    result = run_evals(path, fn)
    failures = [c for c in result["cases"] if not c["passed"]]
    assert not failures, f"{name}: {failures}"
