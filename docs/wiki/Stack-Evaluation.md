# Stack Evaluation

The posting's first responsibility is owning the evaluation of GTM technology so it "scales in an AI-first world". Full framework: [gtm-stack-evaluation.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/context/gtm-stack-evaluation.md). Current stack and data flows: [gtm-stack-map.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/shared_core/context/gtm-stack-map.md).

**Every tool is scored on six criteria:** data ownership, API and webhook surface, AI-agent readiness, overlap, adoption, and cost per outcome.

**Where I expect overlap (to verify):** Unify ↔ Clay ↔ HubSpot sequences for signals and outbound; n8n ↔ Zapier/Workato/Tray for middleware; ZoomInfo ↔ the Clay waterfall for contact data; HubSpot ↔ Salesforce for lifecycle stage.

**Gaps I'd look for:** consumption data missing from the CRM, configuration not in Git, no single semantic layer, and no written standard for what AI agents may write.

**Output:** a keep / consolidate / replace memo in week 8, with cost, effort and a two-quarter migration order.
