# GTM Stack Evaluation: Built for an AI-First World

![Shared](https://img.shields.io/badge/supports-BOTH%20tracks-7B61FF)

The RevOps Manager posting's first responsibility is to "own the evaluation of our GTM technology" so the stack scales in an AI-first world. This is the framework I'd run in the first 60 days. The verdicts at the bottom are **hypotheses from public information**, written to be overturned by what I find inside.

## How each tool is scored

Each tool gets 1–5 on six criteria. Anything averaging under 3 goes on the consolidate-or-replace list.

| Criterion | The question | Why it matters now |
|---|---|---|
| **Data ownership** | Is it the system of record for something, or a copy of data that lives elsewhere? | Copies drift. Every copy is a reconciliation job. |
| **API & webhook surface** | Can n8n, Clay or a script read and write everything a user can? | Tools you can't automate become manual work. |
| **AI-agent readiness** | Can an agent act through it safely: scoped tokens, audit log, a sandbox, an MCP server or clean API? | Agents will do more of the work; the stack has to let them in with guardrails. |
| **Overlap** | How much of its job does another tool in the stack already do? | Overlap means double cost and two sources of truth. |
| **Adoption** | Weekly active users ÷ seats; share of reps' activity that flows through it | Shelfware costs money and hides real process. |
| **Cost per outcome** | Annual cost ÷ the outcome it drives (meetings, enriched records, hours saved) | Makes cut decisions defensible to Finance. |

## Where I expect overlap (to verify)

| Overlap | Tools | The decision to make |
|---|---|---|
| Signals and outbound | Unify ↔ Clay ↔ HubSpot sequences | One home for signal detection and one for sequencing. Clay for enrichment and research, Unify for intent and plays, HubSpot for marketing nurture only. Agree the boundary and write it down. |
| Middleware | n8n ↔ Zapier / Workato / Tray.io | Standardise on one orchestrator (n8n is named in both postings), version-control the workflows, and retire scattered zaps. |
| Contact data | ZoomInfo ↔ Clay waterfall providers | Pay for ZoomInfo seats only where the waterfall can't match its coverage. Measure fill rate and cost per verified contact by segment. |
| Marketing ↔ CRM | HubSpot ↔ Salesforce | One owner per field and one lifecycle definition. Lifecycle stage is the most common source of funnel-report disagreement. |
| Forecasting and call data | Salesforce Forecasts ↔ a forecasting tool ↔ Gong | Decide whether native forecasting plus a warehouse snapshot covers it before buying a forecasting tool. |

## Gaps I'd look for

- **Lead-to-cash in the CRM.** Is commit vs usage visible on the Account? If usage lives only in billing, expansion and churn signals arrive at renewal instead of monthly. See [lead-to-cash](../../gtm_strategy_ops/consumption/lead-to-cash.md).
- **Configuration as code.** Are Salesforce metadata, n8n workflows and Clay tables in Git with review? If not, that comes before new automation.
- **A warehouse model of the funnel.** One semantic layer (see [`semantic_layer.sql`](../metrics/sql/semantic_layer.sql)) that every dashboard reads, instead of report-by-report logic.
- **Agent guardrails.** A written standard for what AI agents may write to Salesforce, reviewed by Sardine's own security team. Sardine sells model governance to banks, so its internal GTM AI should meet the same bar.

## Output

A one-page stack decision memo in week 8: keep / consolidate / replace / buy, with cost and effort for each, and a 2-quarter migration sequence. Changes ship behind a pilot with one team first, and adoption is measured before rollout.
