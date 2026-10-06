# AI Workflow Standard

![Shared](https://img.shields.io/badge/supports-BOTH%20roles-7B61FF)

Production AI work needs four things: **production-ready** workflows; defined **prompts, outputs, evaluation criteria and human-in-the-loop controls**; **governance** for data security; and **measured realized gains**. Every AI workflow in this repo follows this one standard, whichever role uses it.

| Workflow | Role | Code |
|---|---|---|
| Account research & qualification brief | 🟦 GTM Engineer | [`gtm_engineer/ai_research/`](../../gtm_engineer/ai_research/) |
| Deal-risk detection + forecast commentary | 🟩 Strategy & Ops | [`gtm_strategy_ops/ai_deal_risk/`](../../gtm_strategy_ops/ai_deal_risk/) |
| Renewal signal brief | 🟩 Strategy & Ops | [`gtm_strategy_ops/renewals/`](../../gtm_strategy_ops/renewals/) |

## The six parts every AI workflow must have

| # | Part | What "done" means | Where it lives |
|---|---|---|---|
| 1 | **Prompt spec** | Versioned file with id, version, owner, inputs, output schema and refusal rules | `*/prompts/*.md` |
| 2 | **Output contract** | JSON with declared keys. Anything else is rejected, never "best-effort parsed". | [`llm_client.py`](llm_client.py) `OutputContractError` |
| 3 | **Data boundary** | Field allow-list plus PII redaction before the model sees anything | [`pii_guard.py`](pii_guard.py) |
| 4 | **Eval set** | 5+ fixed cases with checks, run in CI on every prompt change | [`eval_harness.py`](eval_harness.py), `*/evals/*.json` |
| 5 | **HITL policy** | Which actions auto-apply and which wait for a person | [`hitl.py`](hitl.py) |
| 6 | **Impact metric** | The business number the workflow should move, with a baseline captured *before* launch | Table below |

## Data security

Adjust the strictness to the company's data. If its product handles identity documents, financial records or health data, a GTM workflow that leaks prospect or customer data into a model is a compliance problem as well as a credibility one.

- **Deny by default.** Only fields on the allow-list in `pii_guard.PROMPT_SAFE_FIELDS` reach a prompt. Email addresses, phone numbers, account and routing numbers, card numbers and DOBs are redacted from free text.
- **No customer production data in prompts.** Renewal health uses aggregated usage trends (volume % change, utilization %), never record-level data.
- **Audit log.** Every call writes prompt id@version, mode, input field names (not values) and PII actions to `outputs/ai_audit_log.jsonl`.
- **Vendor posture.** In live mode, use a provider and tier with zero-retention terms approved by the company's security team. The client reads the model from `ANTHROPIC_MODEL` and never uses a silent default.

## Measuring realized gains

Measure realized gains in conversion, speed and team capacity, and workflow impact on forecast accuracy and seller capacity.

| Workflow | Leading metric | Business metric | Baseline window |
|---|---|---|---|
| Account research brief | Brief acceptance rate (HITL Accept %) | SDR research minutes per account; MQL→SQL conversion | 4 weeks pre-launch |
| Lead qualification assist | Override rate on AI-suggested disqualifications | Speed-to-lead; SAL→SQL conversion | 4 weeks |
| Deal-risk flags | % of flags the AE/manager agrees with | Slipped-deal rate; forecast accuracy at week 8 of quarter | Prior 2 quarters |
| Forecast commentary | Manager edit distance on generated commentary | Hours spent on forecast-call prep | 2 forecast cycles |
| Renewal signals | Lead time between flag and renewal date | Gross retention on flagged vs unflagged accounts | Prior 4 quarters |

Rollout: shadow mode (generate but don't show) → assisted (shown to the rep, rep decides) → auto-apply for low-impact actions only.
