# AI Governance

Standard: [shared_core/ai_governance/README.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/ai_governance/README.md). Sardine sells model governance to banks, so its internal GTM AI should meet the same bar.

| # | Every AI workflow has | Where |
|---|---|---|
| 1 | A versioned prompt spec | `*/prompts/*.md` |
| 2 | A strict JSON output contract (anything else is rejected) | `llm_client.py` |
| 3 | A data boundary: field allow-list plus PII redaction | `pii_guard.py` |
| 4 | An eval set run in CI | `*/evals/*.json` |
| 5 | A human-in-the-loop policy | `hitl.py` |
| 6 | An impact metric with a pre-launch baseline | standard README |

**Workflows:** account research brief (🟦), deal-risk and forecast commentary (🟩), renewal brief (🟩). All run on a deterministic mock model by default; live mode is opt-in. The account-research prompt forbids stating regulatory actions or losses unless a field in the record says so.
