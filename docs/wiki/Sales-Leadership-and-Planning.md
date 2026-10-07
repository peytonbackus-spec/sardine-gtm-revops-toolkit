# Sales Leadership and Planning

What a VP of Sales asks RevOps for, answered before the meeting, in the depth they want. Plus the planning work behind the number: capacity, quota, territory, pipeline distribution and the CRM request queue.

## Two depths, one set of numbers

| | Snapshot | Full |
|---|---|---|
| Contents | The number · three things to know · deals to act on · asks | Snapshot + rep scorecard, industries, stage velocity with drivers, full deal board, definitions |
| Length | One phone screen | Five minutes |
| For | A leader who wants it fast | A leader who wants to dig in, and RevOps defending any snapshot number |

Which one is the default is the VP's call, settled in the first 1:1 with the [intake questions](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/vp-intake.md).

## The questions and where they're answered

| The VP asks | Module |
|---|---|
| Are we going to hit the number? | [vp_brief.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/vp_brief.py) |
| How is each rep doing, and why? | [rep_scorecard.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/rep_scorecard.py): result, setup, weakest velocity lever, coaching focus |
| Which industries are we winning and losing? | [segment_performance.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/segment_performance.py): win rate with an 80% range so small samples aren't over-read |
| Where is pipeline slowing, and why? | [stage_velocity.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/stage_velocity.py): where deals slow, where they die, and the drivers (owner, source, segment, economic-buyer access) with the fix to test |
| Which deals are hot or at risk? | [deal_board.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/deal_board.py): Past due · Slipping · At risk · Stalled · Hot · On track |
| What do we tell the team at the all-hands? | [all_hands.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/all_hands.py): the number, wins, recognition for the top, the good and the bad as patterns, focus, speaker prompts |

Full spec: [sales_leadership/README.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_leadership/README.md).

## Planning

| Question | Module |
|---|---|
| Can the team deliver the plan? How many AEs, starting when? | [capacity_plan.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/capacity_plan.py) |
| Are quotas fair and achievable? | [quota_plan.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/quota_plan.py) |
| Are territories balanced? | [territory_plan.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/territory_plan.py) |
| Is pipeline spread so each rep can hit? | [pipeline_distribution.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/pipeline_distribution.py) |
| What is in the Salesforce / HubSpot queue? | [crm-request-intake.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/crm-request-intake.md) · [request_triage.py](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_strategy_ops/sales_planning/request_triage.py) |

One roster, one ramp curve, one productivity number feed all of it, so a rep's quota is the same in the planning deck and the Monday brief.

## Marketing Ops

The RevOps role works closely with Marketing Ops. The [Marketing Ops page](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/marketing_ops/README.md) sets who owns what (HubSpot, sync, campaigns, MQL, consent, attribution), the [campaign operations spec](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/marketing_ops/campaign-operations-spec.md) and the [demand plan](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/gtm_engineer/marketing_ops/demand_plan.py) that turns the bookings plan into leads and MQLs by channel.

> All data is synthetic. Patterns were planted (slow inbound hand-off, one slow AE in Qualify, banks slow in technical validation, deals without an economic buyer slow in business case, lost deals pushed more) so the reports have something to find.
