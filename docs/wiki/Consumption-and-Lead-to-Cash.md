# Consumption and Lead to Cash

![RevOps](https://img.shields.io/badge/track-🟩%20RevOps-2DA44E)

At a usage-priced company, bookings (the minimum commit) and billed revenue (commit plus overage) drift apart every month. Both expansion and churn show up in the usage data months before renewal, but only if someone puts that data in front of the account owner.

| Flag | Rule (config: `consumption`) | Action |
|---|---|---|
| **Overage** | Trailing 3-month usage ≥ 100% of commit | Expansion opp: re-commit at a better rate now, not at renewal |
| **Shelfware** | Trailing 3-month usage < 60% of commit, after the ramp window | CSM adoption plan before renewal |
| **Ramping** | First 3 months live | Excused from shelfware alerts |

**Run it:** `python -m gtm_strategy_ops.consumption.commit_burndown` ([code](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/consumption/commit_burndown.py)). It prints commit vs usage by product line and region, the top overage and shelfware accounts with owners, and writes the action list to `outputs/consumption_actions.csv`.

**The full lifecycle:** [lead-to-cash.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/consumption/lead-to-cash.md) maps nine steps from lead to renewal: the system for each, what breaks without automation, the n8n/Salesforce automation that fixes it, and the Salesforce fields needed (`Monthly_Commit__c`, `Utilization_3mo__c`, `Consumption_Flag__c`…).

**Metrics it unlocks:** NRR on billed revenue, time to first production transaction, commit accuracy (actual utilization ÷ quoted commit), and overage-sourced expansion pipeline.
