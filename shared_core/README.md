# 🟪 Shared Core: supports BOTH roles

![Shared](https://img.shields.io/badge/supports-BOTH%20roles-7B61FF) ![GTM Engineer](https://img.shields.io/badge/GTM%20Engineer-✓-1F6FEB) ![Strategy & Ops](https://img.shields.io/badge/GTM%20Strategy%20%26%20Ops-✓-2DA44E)

The two role tracks overlap heavily: CRM data modeling, data-quality monitoring, dashboard architecture, AI workflow design and governance, and cross-functional leadership. That overlap lives here, built once. Each role track builds on it.

| Folder | What it is | Why it is shared |
|---|---|---|
| [`context/`](context/) | [ICP & personas](context/icp-and-personas.md), [stack map](context/gtm-stack-map.md) | One segment model for lead scoring, routing and every dashboard cut |
| [`data_model/`](data_model/) | [Salesforce object & field model](data_model/salesforce-object-model.md), including the Lead→Opportunity handoff boundary | Both tracks write to the same objects; one owner per field |
| [`data_quality/`](data_quality/) | [`dq_monitor.py`](data_quality/dq_monitor.py): rules across Lead and Opportunity, with an owner and pass rate per rule | Same rules, same pass rate, whichever role runs them |
| [`ai_governance/`](ai_governance/) | [AI workflow standard](ai_governance/README.md), [PII guard](ai_governance/pii_guard.py), [LLM client](ai_governance/llm_client.py), [eval harness](ai_governance/eval_harness.py), [HITL policy](ai_governance/hitl.py) | Every AI workflow follows one standard |
| [`metrics/`](metrics/) | [Metric definitions](metrics/metric-definitions.md), [semantic-layer SQL](metrics/sql/semantic_layer.sql), [SQL runner](metrics/run_sql.py) | One definition per metric, so lead-side and opportunity-side numbers reconcile |

```bash
python -m shared_core.data_quality.dq_monitor            # rule pass rates + failing records
python -m shared_core.metrics.run_sql                    # build the semantic layer on sample data
```
