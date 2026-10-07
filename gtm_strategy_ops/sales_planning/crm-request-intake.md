# CRM Request Intake (Salesforce and HubSpot)

![Strategy & Ops](https://img.shields.io/badge/role-GTM%20Strategy%20%26%20Ops-2DA44E)

**Problem it solves:** requests arrive by Slack DM, in hallway asks and in forecast calls; the loudest ones get built, nobody knows what is in flight, and changes reach production untested. One front door, one priority rule, one release path.

## Front door

One intake form (a Salesforce case record type, or a Jira/Linear form; Slack shortcut that creates the record). Required fields:

| Field | Why |
|---|---|
| Requester team | Sales, Sales Leadership, Marketing, Marketing Ops, CS, Finance, Partners |
| System | Salesforce, HubSpot, both, an integration |
| Category | Picks the change class (below) |
| What and why | The decision or task this enables, not the solution ("I need to see X to decide Y") |
| Revenue impact | Blocks deal · Blocks team · Improves efficiency · Nice to have |
| Users affected | Reach |
| Due date and reason | Only if there is a real date (board meeting, event, launch) |

DMs get a friendly link to the form. Nothing is built from a DM.

## Priority (first match wins)

| Priority | Rule | First response |
|---|---|---|
| **P0** | A live deal or a rep's ability to sell is broken today | 8 business hours (same day) |
| **P1** | Blocks a team; a new hire can't access the system; or a real due date within 3 business days | 24 business hours |
| **P2** | Efficiency gain for 10+ users | 5 business days |
| **P3** | Everything else; batched into the release train | 10 business days |

First response = priority, owner and an ETA, back to the requester. Inside a priority, order by impact × reach ÷ effort (S/M/L/XL).

## Change class decides the path

| Class | Categories (config `sales_planning.request_intake.change_classes`) | Path |
|---|---|---|
| **Standard** | Reports and dashboards, list views, access, data fixes | Same week, straight in production, logged |
| **Normal** | Fields and picklists, validation rules, page layouts, email templates | Built in sandbox, tested by the requester, shipped in the fortnightly release with notes |
| **Major** | Flows and automation, objects and data model, routing and assignment, integrations | Design review with the requesting leader first, then sandbox, UAT, release; rollback plan written before deploy |

Release notes go to the requesting teams in one message per release. Every field change updates the [Salesforce object model](../../shared_core/data_model/salesforce-object-model.md); every metric change updates the [metric definitions](../../shared_core/metrics/metric-definitions.md).

## Weekly review (15 minutes, RevOps + Marketing Ops + a sales manager)

1. SLA by priority last week; anything P0/P1 that missed.
2. Duplicates to merge (same ask from two teams is one build).
3. Priority inversions: P2/P3 work in progress while P0/P1 waits.
4. Themes: reports and list views above ~25% of the queue means a self-serve reporting session is cheaper than building more reports; repeated data fixes mean a missing validation rule or automation, so fix the cause.

## Measures

SLA met % by priority · median cycle time by change class · open backlog and oldest item · share of break-fix vs enhancement work (tech debt signal) · requests per team.

Runs on the sample queue: `python -m gtm_strategy_ops.sales_planning.request_triage`.

## Marketing Ops in the same queue

HubSpot requests (forms, lists, workflows, sync fields) come through the same door so one team can see a Salesforce field change that breaks a HubSpot sync before it ships. Ownership split is in the [Marketing Ops README](../../gtm_engineer/marketing_ops/README.md#who-owns-what).
