# Variables: how the toolkit was filled in for Sardine

This repo was generated from a generic GTM & RevOps toolkit template. `[TOKEN]` placeholders in the docs and prompts were resolved from the `variables:` block of [`config/company.yaml`](config/company.yaml). This table records each value and where it came from, so a reader can tell sourced fact from assumption.

**Provenance:** `PUBLIC` = Sardine's site, press releases, analyst coverage · `POSTING` = a Sardine job posting · `ASSUME` = a working assumption to confirm in week one · `VERIFY` = third-party estimate

| Variable | Value | Provenance | Source |
|---|---|---|---|
| `[COMPANY_NAME]` | Sardine | PUBLIC | [sardine.ai](https://www.sardine.ai/) |
| `[CRM]` | Salesforce | POSTING | RevOps Manager and GTM Engineer postings |
| `[MARKETING_AUTOMATION]` | HubSpot | POSTING | RevOps Manager posting; Marketing Ops posting |
| `[SIGNALS_PLATFORM]` | Unify | POSTING | RevOps Manager posting |
| `[ENRICHMENT_ORCHESTRATION]` | Clay | POSTING | RevOps Manager, GTM Engineer and Marketing Ops postings |
| `[WORKFLOW_AUTOMATION]` | n8n | POSTING | RevOps Manager posting (Zapier, Workato and Tray.io also named as middleware) |
| `[DATA_PROVIDER]` | ZoomInfo | POSTING | Marketing Ops posting |
| `[FORECAST_TOOL]` | Salesforce Forecasts | ASSUME | No forecasting tool named in any posting |
| `[CONVERSATION_INTELLIGENCE]` | Gong | ASSUME | Not named |
| `[SEQUENCER]` | Unify / HubSpot Sequences | ASSUME | Unify includes sequencing; no standalone sequencer named |
| `[DIALER]` | none confirmed | ASSUME | Not named |
| `[WEBSITE_CHAT]` | HubSpot Chat | ASSUME | Not named |
| `[SOCIAL_SELLING]` | LinkedIn Sales Navigator | ASSUME | Not named |

Other Sardine facts in the config (segments, product lines, regions, partners, pricing model) are tagged inline in [`config/company.yaml`](config/company.yaml) and sourced in the [company brief](shared_core/context/sardine-company-brief.md).

Postings: [Revenue Operations Manager](https://jobs.ashbyhq.com/sardine/b6ca1fd5-a374-4c99-a6fd-a0c4d0859a61) · [GTM Engineer](https://remotive.com/remote/jobs/all-others/gtm-engineer-4525868) · Marketing Operations Lead (listing removed Aug 2026).
