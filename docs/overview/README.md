# Sardine GTM RevOps Toolkit: Overview

**One revenue engine, lead to cash.** At Sardine both tracks below belong to one role, the Revenue Operations Manager. This folder is the narrative layer on top of the repo. The repo holds the working code and specs; these pages explain how the pieces fit and why they're built this way.

| | Role | Owns | Start with |
|---|---|---|---|
| 🟦 | **GTM Engineer** | First signal → enrichment → score → route → AI research → SQL | [`gtm_engineer/README.md`](../../gtm_engineer/README.md) |
| 🟩 | **GTM Strategy & Operations** | Opportunity → stage gates → deal risk → forecast → close → renewal | [`gtm_strategy_ops/README.md`](../../gtm_strategy_ops/README.md) |
| 🟪 | **Shared Core** | CRM data model, data quality, AI governance, metric definitions | [`shared_core/README.md`](../../shared_core/README.md) |

## Pages

- [Architecture](architecture.md): how data moves from signal to renewal, and where the handoff between roles sits
- [Running the toolkit](running-the-toolkit.md): setup, every command, what each report shows
- [Decision log](decision-log.md): design choices and the reasoning behind each
- [Glossary](glossary.md): terms used across the repo
- [Roadmap](roadmap.md): what to build next with real company data
- [Company brief](../../shared_core/context/sardine-company-brief.md) · [Stack evaluation](../../shared_core/context/gtm-stack-evaluation.md) · [Lead-to-cash](../../gtm_strategy_ops/consumption/lead-to-cash.md): the Sardine-specific pages

## Ground rules

- **Synthetic data only.** Everything in `sample_data/` is fictional.
- **Source facts.** Company facts in a derived repo carry a provenance tag (`[PUBLIC]`, `[POSTING]`, `[ASSUME]`, `[VERIFY]`) so a reader can tell fact from guess.
- **No private material.** Strategy, financials, client notes and prospect data live in a separate private repo, never here.
