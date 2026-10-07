# Changelog

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
