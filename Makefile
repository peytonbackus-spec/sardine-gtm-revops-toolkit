.PHONY: help data demo brief test lint webhook new

PY ?= python3

help:
	@echo "make data                  regenerate synthetic sample_data/ from config"
	@echo "make demo                  run every module on the sample data"
	@echo "make brief                 VP of Sales snapshot (outputs/vp_brief_snapshot.md)"
	@echo "make test                  run the pytest suite"
	@echo "make lint                  ruff check"
	@echo "make webhook               run the FastAPI enrichment webhook on :8000"
	@echo 'make new COMPANY="Acme"    scaffold a new company repo from this template'
	@echo '    optional: DEST=path FY_START=1-12'

data:
	$(PY) scripts/generate_sample_data.py

demo:
	$(PY) -m gtm_engineer.lead_scoring.score_leads
	$(PY) -m gtm_engineer.lead_scoring.calibrate_scoring
	$(PY) -m gtm_engineer.lead_routing.route_leads
	$(PY) -m gtm_engineer.lead_lifecycle.lifecycle_sla
	$(PY) -m gtm_engineer.funnel_analytics.funnel_report
	$(PY) -m gtm_engineer.sdr_capacity.capacity_model
	$(PY) -m gtm_engineer.ai_research.account_research
	$(PY) -m gtm_strategy_ops.pipeline_analytics.pipeline_report
	$(PY) -m gtm_strategy_ops.forecasting.forecast_accuracy
	$(PY) -m gtm_strategy_ops.renewals.renewal_signals
	$(PY) -m gtm_strategy_ops.renewals.closed_lost_analysis
	$(PY) -m gtm_strategy_ops.consumption.commit_burndown
	$(PY) -m gtm_strategy_ops.ai_deal_risk.deal_risk
	$(PY) -m shared_core.data_quality.dq_monitor
	$(PY) -m gtm_engineer.marketing_ops.campaign_report
	$(PY) -m gtm_engineer.marketing_ops.demand_plan
	$(PY) -m gtm_strategy_ops.sales_leadership.rep_scorecard
	$(PY) -m gtm_strategy_ops.sales_leadership.segment_performance
	$(PY) -m gtm_strategy_ops.sales_leadership.stage_velocity
	$(PY) -m gtm_strategy_ops.sales_leadership.deal_board
	$(PY) -m gtm_strategy_ops.sales_leadership.vp_brief
	$(PY) -m gtm_strategy_ops.sales_leadership.vp_brief --mode full
	$(PY) -m gtm_strategy_ops.sales_leadership.all_hands
	$(PY) -m gtm_strategy_ops.sales_planning.capacity_plan
	$(PY) -m gtm_strategy_ops.sales_planning.quota_plan
	$(PY) -m gtm_strategy_ops.sales_planning.territory_plan
	$(PY) -m gtm_strategy_ops.sales_planning.pipeline_distribution
	$(PY) -m gtm_strategy_ops.sales_planning.request_triage

brief:
	$(PY) -m gtm_strategy_ops.sales_leadership.vp_brief

test:
	$(PY) -m pytest

lint:
	$(PY) -m pip install ruff -q
	ruff check shared_core gtm_engineer gtm_strategy_ops prototypes scripts tests

webhook:
	uvicorn gtm_engineer.integrations.webhook:app --reload --port 8000

new:
	@test -n "$(COMPANY)" || (echo 'Usage: make new COMPANY="Acme Corp" [DEST=path] [FY_START=1-12]'; exit 1)
	$(PY) scripts/new_company.py "$(COMPANY)" $(if $(DEST),--dest "$(DEST)") $(if $(FY_START),--fy-start-month $(FY_START)) --git
