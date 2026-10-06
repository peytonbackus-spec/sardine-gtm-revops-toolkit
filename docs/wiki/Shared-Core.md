# 🟪 Shared Core

Built once, used by both tracks: [shared_core/](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/tree/main/shared_core/).

| Piece | What it gives |
|---|---|
| [Salesforce object model](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/data_model/salesforce-object-model.md) | One owner per field, and the lead → opportunity handoff boundary |
| [Data-quality monitor](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/data_quality/dq_monitor.py) | 16 rules with pass rates; each failing record routed to an owner |
| [Metric definitions](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/metrics/metric-definitions.md) + [semantic layer](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/metrics/sql/semantic_layer.sql) | One definition per metric. Tests check that Python and SQL return identical numbers. |
| [AI governance](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/ai_governance/README.md) | PII guard, LLM client, eval harness, human-review policy. See [[AI Governance]]. |
| [config/company.yaml](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/config/company.yaml) | Every Sardine-specific value in one file; nothing is hardcoded in code |
