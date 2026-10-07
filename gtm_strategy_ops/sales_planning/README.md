# Sales Planning: capacity, quota, territory, pipeline distribution, CRM requests

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Principle:** one roster, one ramp curve, one productivity number. Capacity, quota, territory books, the rep scorecard and the all-hands leaderboard all read the same [`team.py`](team.py), so a rep's number never differs between the planning deck and the Monday snapshot.

| Question | Asked by | Module | Cadence |
|---|---|---|---|
| Can the team we have deliver the plan? How many AEs, starting when? | CRO, Finance | [`capacity_plan`](capacity_plan.py) | Annual plan, re-check quarterly |
| Are this quarter's quotas fair and achievable? What should next year's be? | VP Sales, Finance | [`quota_plan`](quota_plan.py) | Quarterly; annual set |
| Are territories balanced? Who owns which accounts? | VP Sales, managers | [`territory_plan`](territory_plan.py) | Annual carve; review on every hire or exit |
| Is pipeline spread so each rep can hit their number? | VP Sales, managers | [`pipeline_distribution`](pipeline_distribution.py) | Monthly; weekly in the last month of a quarter |
| What is in the Salesforce / HubSpot queue and what gets built next? | Everyone who asks RevOps for something | [`request_triage`](request_triage.py) · [process](crm-request-intake.md) | Daily triage, weekly review |

All inputs are in `config/company.yaml` (`sales_team`, `sales_planning`, `quota`) and are tagged `[ASSUME]` until replaced with the company's own history.

## 1. Capacity

| Term | Definition |
|---|---|
| Ramp factor | Share of full productivity in a fiscal quarter of tenure. Default `[0, 0.33, 0.66, 1.0]`: a new AE closes little in quarters 1 and 2 of a long-cycle enterprise sale |
| Ramped rep equivalents (RRE) | Sum of ramp factors, reduced by expected attrition (`annual_attrition_pct`) |
| Productivity | What a ramped AE actually sells per quarter in that region. **Not quota.** Taken from history |
| Capacity | RRE × productivity |
| Hiring plan | Gap to plan ÷ productivity at the ramp a hire will have reached; reqs opened `hire_lead_time_quarters` before the start quarter |
| Minimum quota to assign | Plan × (1 + over-assignment) |

The method follows Dave Kellogg's productivity-based capacity model: start from what reps really sell, uplift by over-assignment to get the quota to hand out, and model ramp and attrition explicitly ([Kellblog](https://www.kellblog.com/how-to-make-and-use-a-proper-sales-bookings-productivity-and-quota-capacity-model/)).

## 2. Quota

**Top-down meets bottom-up.** The plan Finance commits to is top-down; capacity is bottom-up. The quota plan shows both and the gap between them.

| Check | Rule | Why |
|---|---|---|
| Implied over-assignment | Region quota ÷ region capacity − 1 | Practitioners run about 10–25% (most enterprise software near 20%); far higher means reps miss while the company "hits plan", which damages the team ([Kellblog](https://www.kellblog.com/quota-over-assignment-and-culture/)). Default here: 15% |
| Quota on ramping reps | Region quota split by RRE, not headcount | A rep in ramp quarter 2 carries a third of a number, not a full one |
| Region with no ramped AE | Flag | Nobody can carry that number this quarter |
| Attainment spread | Share of ramped reps at ≥100%, 70–99%, <70% last quarter | If almost nobody hits, the quotas are the problem, not the people |

Next year's proposal: plan × (1 + over-assignment), split by region on capacity, then by AE on ramp. Territory potential can weight the split further once the carve is agreed.

## 3. Territory

1. **Potential per account** = segment fit (`segments.*.icp_points`) + company size (`lead_scoring.size_bands`) + whitespace (+10 when a customer owns one product line and not the other: the fraud ↔ compliance cross-sell).
2. **Tiers** by percentile: T1 top 15%, T2 to 50%, the rest pooled for inbound and SDR coverage.
3. **Carve** within each region. Live customers stay with their owner (`keep_customer_owner`). T1 and T2 then go, highest potential first, to the AE with the least potential per seat, within the caps (`max_named_accounts_per_ae`). A ramping AE is a fraction of a seat.
4. **Balance check**: potential per seat vs the region mean; outside ±15% the carve is not fair, and quotas built on it won't be.

Replaces "who had it last year". Run it on every hire or exit, not only once a year. Region-level potential vs region quota is also worth a look: a thin book (here, APAC) can't carry a full number however well it is split.

## 4. Pipeline distribution

| Flag | Rule (config `sales_planning.pipeline_distribution`) | Action |
|---|---|---|
| Overloaded | More open opps than one AE can work (18) | Close out or re-route stale stage 1–2 deals; pause routing |
| Starved | Fewer than 6 open opps | Next inbound SQLs and SDR focus on their T1 accounts |
| Under-covered | In-quarter pipeline below 3x of their (ramp-adjusted) quota | Pull in real next-quarter deals; prospect the T1 book for size |
| Concentrated | One deal is >50% of the quarter | Second-path plan for the quarter |
| Early-heavy | >70% of in-quarter $ still in stages 1–2 | Re-check close dates |

Team view: Gini of coverage across reps and the top-two reps' share of pipeline. Routing gets one rep per region (biggest dollar gap), because inbound can't be weighted to everyone and it routes by region. Before weighting inbound to a rep, check their win rate on the [rep scorecard](../sales_leadership/rep_scorecard.py): more deals won't help a rep whose weak lever is converting them.

## 5. CRM requests

Intake, priority, change class, SLA and release path are in [crm-request-intake.md](crm-request-intake.md). The module reports SLA by priority, cycle time by change class, the open queue in work order, duplicates to merge, and priority inversions (P2/P3 work in progress while P0/P1 waits).

## Run it

```bash
python -m gtm_strategy_ops.sales_planning.capacity_plan
python -m gtm_strategy_ops.sales_planning.quota_plan
python -m gtm_strategy_ops.sales_planning.territory_plan
python -m gtm_strategy_ops.sales_planning.pipeline_distribution
python -m gtm_strategy_ops.sales_planning.request_triage
```

> Roster, quotas, productivity and requests are synthetic and fictional. Replace `sales_team.ae_roster` from Salesforce Users and productivity from the last four quarters of bookings by ramped AE.
