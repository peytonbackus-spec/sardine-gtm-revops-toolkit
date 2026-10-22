# Not applicable to Sardine

These specs and one prototype come from the toolkit template. Most describe product-led (PLG) motions: product-qualified leads, self-serve routing and PQL scoring. The rest are generic template architecture notes built around product telemetry and PQLs rather than Sardine's stack. Sardine is assumed to be entirely sales-led, with every deal run by an AE, so none of them are part of the Sardine build. They are kept here for reference only: nothing in the toolkit links to them, imports them or tests them.

| Spec | What it covers |
|---|---|
| [Lead_Scoring_PQL_Spec.md](Lead_Scoring_PQL_Spec.md) | Lead and PQL scoring with decay |
| [PLG_PQL_Routing.md](PLG_PQL_Routing.md) | PQL triggers and routing framework |
| [PLG_PQL_Routing_Rules.md](PLG_PQL_Routing_Rules.md) | PQL routing rule detail |
| [SFDC_PQL_Routing.md](SFDC_PQL_Routing.md) | Salesforce architecture for PQL routing |
| [GTM_OS_Architecture_Spec.md](GTM_OS_Architecture_Spec.md) | Template GTM operating-system topology, starting from product telemetry and PQLs |
| [HubSpot_SFDC_Architecture_Framework.md](HubSpot_SFDC_Architecture_Framework.md) | Generic HubSpot vs Salesforce paradigm notes, with PQL sync triggers |
| [Lifecycle_Stage_MQL_SQL_Spec.md](Lifecycle_Stage_MQL_SQL_Spec.md) | Template lifecycle-stage mapping with a PQL path; the Sardine lifecycle lives in [`gtm_engineer/lead_lifecycle/`](../../../gtm_engineer/lead_lifecycle/) |
| [sfdc_pql_ingestor.py](sfdc_pql_ingestor.py) | Prototype PQL payload ingestion (Python; not run or tested) |
