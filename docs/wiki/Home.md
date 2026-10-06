# Sardine GTM RevOps Toolkit Wiki

**One revenue engine, one owner, lead to cash.** This wiki is the narrative layer on top of the [repository](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit). The repo holds the working code and specs; the wiki explains how the pieces fit and why they're built this way for Sardine.

Sardine's Revenue Operations Manager role sits "at the intersection of Revenue Operations and GTM Engineering". So one person owns all three areas below.

| | Track | Covers | Start with |
|---|---|---|---|
| 🟦 | **GTM Engineering** | Signal (Unify, HubSpot) → enrich (Clay) → score → route → AI research → SQL | [[GTM Engineering Track]] |
| 🟩 | **RevOps** | Opportunity → stage gates → deal risk → forecast → close → consumption → renewal | [[RevOps Track]] |
| 🟪 | **Shared Core** | Salesforce data model, data quality, AI governance, metric definitions | [[Shared Core]] |

## Pages

- [[The Role]]: what the posting asks for and where each item is answered
- [[Sardine Context]]: what Sardine sells, who buys it, and the four facts that shape RevOps there
- [[Consumption and Lead to Cash]]: usage vs minimum commit, overage and shelfware, and automating the cash half of the lifecycle
- [[Stack Evaluation]]: how I'd evaluate the GTM stack for an AI-first world
- [[Architecture]]: how data moves from signal to renewal
- [[AI Governance]]: the six parts every AI workflow has
- [[Running the Toolkit]]: setup, every command, what each report shows
- [[First 90 Days]] · [[Decision Log]] · [[Glossary]] · [[Roadmap]]

## Ground rules

- **Synthetic data only.** Everything in `sample_data/` is fictional. Sardine facts are sourced in the [company brief](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/context/sardine-company-brief.md).
- **Fact vs assumption is always labelled.** Config values carry `[PUBLIC]`, `[POSTING]`, `[ASSUME]` or `[VERIFY]`.
