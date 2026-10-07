# 🟦 GTM Engineering Track

Track README: [gtm_engineer/README.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/README.md)

| Piece | What it does | Code |
|---|---|---|
| Lead lifecycle | Statuses, SLAs, disqualify reasons; SLA monitor by SDR and source | [lead_lifecycle/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/lead_lifecycle/) |
| Scoring | Fit × intent grade (A1–D4); intent decays by half-life; `regulatory_action` is a top signal | [score_leads.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/lead_scoring/score_leads.py) |
| Calibration | Tests the score against conversion and flags mis-weighted segments | [calibrate_scoring.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/lead_scoring/calibrate_scoring.py) |
| Routing | R1–R7 ordered rules into segment × region pods, with a reason on every lead | [route_leads.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/lead_routing/route_leads.py) |
| Enrichment | Waterfall rules engine, lead-to-account matcher, FastAPI webhook | [enrichment/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/enrichment/), [integrations/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/integrations/) |
| AI research | Pre-call brief that recommends the other product line to existing customers; human review; evals | [ai_research/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/ai_research/) |
| Funnel + capacity | Cohort funnel, velocity, pipeline per lead by source; SDR capacity model | [funnel_analytics/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/funnel_analytics/) |
| Marketing Ops | Who owns what with Marketing Ops; campaign taxonomy, UTMs, consent, W-shaped attribution, channel ROI; demand plan by channel | [marketing_ops/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/gtm_engineer/marketing_ops/) |

**Sardine stack on this side:** HubSpot (marketing automation), Unify (signals and plays), Clay (enrichment), ZoomInfo (data), n8n (orchestration), Salesforce (system of record).
