# Changelog

## Unreleased
- Docs: README "Open first" now points to the workbook loader and a new [take-home method note](docs/takehome-method.md) (pipeline, definitions, sensitivities, how to reproduce). Three template-only specs (`GTM_OS_Architecture_Spec`, `HubSpot_SFDC_Architecture_Framework`, `Lifecycle_Stage_MQL_SQL_Spec`) and `prototypes/sfdc_pql_ingestor.py` moved to `docs/reference/not-applicable/` and tagged; private vault paths removed from the tech-debt dashboard doc, the architecture spec and `prototypes/gtm_researcher.py` (now writes to `GTM_RESEARCH_DIR` or `outputs/research`).
- Wiki: Decision Log S6 no longer claims every pod has more than one rep (EMEA and APAC each run on one AE).
- Tests: the loader's duplicate-ID fixture uses invented companies and attributes.
- Loader: computes both pricing classifications on every line (`pricing_model_product`, `pricing_model_usage`); `pricing_model` follows `method`, now `"product"` by default. Flat-rate products are configurable. Docstring made generic. Tests cover both methods.
- Docs: README gains an "Operating assumptions" table (sales-led, 12 AEs, one RevOps owner, flat + consumption, Hightouch / n8n / Hex). PLG/PQL specs moved to `docs/reference/not-applicable/`.
- Config and brief: LATAM wording aligned (no dedicated reps; sits with NA); unverified third-party pricing figures removed; Hightouch and Hex added to the stack and stack map.
- Config: sales org now matches a sales-led company of 12 AEs (10 NA, 1 EMEA, 1 APAC, ~80% US) with one RevOps employee. Regions are NA, EMEA and APAC (MENA folds into EMEA, LATAM into NA); pods, quotas, productivity, region points and the campaign-name pattern updated. New `go_to_market` block.
- Config: new `pricing` block. Contracts are a mix of flat-rate and consumption; `commit_burndown` excludes flat-rate contracts from overage and shelfware alerts and reports the flat vs consumption revenue split.
- Sample data regenerated: `consumption.csv` gains a `pricing_model` column; the AE roster is read from the config so data and config cannot drift.
- Docs: PLG/PQL specs and prototype marked not applicable (sales-led); README, wiki, first-90-days and company brief updated.
- Tests: roster-shape, flat-rate and pricing-mix tests added; region-specific tests updated.

## 0.2.0 (2026-10-07)
- New `gtm_strategy_ops/sales_leadership/`: VP of Sales brief (snapshot or full), rep scorecard (result, setup, weakest velocity lever, coaching focus), industry win/loss with 80% confidence ranges, stage velocity with drivers and fixes, deal board (Past due / Slipping / At risk / Stalled / Hot / On track), sales all-hands inputs (`--days 1` for "today"), VP intake questions, SQL.
- New `gtm_strategy_ops/sales_planning/`: AE capacity and hiring plan, quota vs capacity and next year's proposal, territory carve and balance, pipeline distribution with region-aware routing priority, CRM request intake process and triage (SLA, duplicates, priority inversions).
- New `gtm_engineer/marketing_ops/`: Marketing Ops RACI and joint cadence, campaign operations spec, channel funnel and ROI, W-shaped attribution, campaign and consent hygiene (M01–M09), demand plan by channel.
- Sample data: `opportunity_field_history.csv` (StageName and CloseDate changes, modelled on OpportunityFieldHistory), campaigns, campaign members, lead consent, CRM requests. Each uses its own seeded RNG, so existing files are unchanged.
- Semantic layer: `v_stage_history`, `v_close_date_pushes`.
- Config: `sales_team`, `sales_planning`, `sales_leadership`, `marketing_ops`; FY26-Q3 quota.
- Fix: open opportunities could show a stage entry date before the opportunity existed (15 rows); now clamped to the created date.
- Fix: metric definitions said the fiscal year ends Sep 30; the config assumes calendar year.

## 0.1.1 (2026-10-06)
- Wiki: 15 pages in `docs/wiki/`, published with `scripts/publish_wiki.sh`.
- `scripts/set_repo_about.sh` sets the GitHub About panel (description, topics, wiki link).
- Docs: running guide names the right webhook target (`make webhook`).

## 0.1.0 (2026-10-06)
- Generated from the GTM & RevOps toolkit template (v0.4.2) and filled in for Sardine.
- Config: 11 segments from Sardine's named customers and sales roles; two product lines (Onboarding & AML Compliance; Fraud, Device & Cyber); Sardine's posted stack (Salesforce, HubSpot, Unify, Clay, n8n, ZoomInfo); five regions.
- New: consumption vs minimum commit module (`gtm_strategy_ops/consumption/`) with lead-to-cash map, sample data and tests.
- New docs: sourced company brief, stack map and AI-first stack evaluation, role map, first 90 days.
