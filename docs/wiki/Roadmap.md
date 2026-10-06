# Roadmap

What I'd build next with real Sardine data and access.

## First 30 days
- Point the data-quality monitor at a read-only Salesforce export, and baseline it
- Back-test the lead score on 12 months of closed-won, by segment
- Pull usage vs commit for every customer from billing, and run the burn-down on real data
- Replace every `[ASSUME]` in the config with actuals

## Days 31–90
| 🟦 GTM Engineering | 🟩 RevOps |
|---|---|
| Routing v2 in Salesforce Flow, replay-tested on recent MQLs | Consumption fields on the Account, synced nightly |
| Unify/Clay boundary agreed and documented | Overage → expansion opp automation in n8n |
| Regulatory-action signal sourced and wired into scoring | Renewal opps pre-filled with trailing usage |
| AI research brief: shadow → assisted | Forecast accuracy and bias by region, weekly |

## Later
- dbt models in the warehouse built from the semantic layer
- Live LLM mode once security approves vendor terms
- Commit-sizing model: predict right-sized commits from backtest volume
