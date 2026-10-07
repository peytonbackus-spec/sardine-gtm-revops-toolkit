# Campaign Operations Spec

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

**Why:** attribution, channel ROI and the demand plan are only as good as campaign data. Every rule below is checked by [`campaign_report.py`](campaign_report.py) (rules M01–M09), so drift shows up in a weekly report instead of in a board deck.

## 1. Campaign naming

`FY{yy}-Q{n}_{TYPE}_{REGION}_{Short-Name}`, e.g. `FY26-Q3_WBN_NA_AML-Agents-Live`. Pattern in config (`marketing_ops.campaign_name_pattern`). One Salesforce Campaign per activity per quarter; a parent campaign per program when a program spans quarters.

| Code | Type | Member statuses (in order) | Counts as a response |
|---|---|---|---|
| EVT | Event | Registered, Attended, Met at Booth, No Show | Attended, Met at Booth |
| WBN | Webinar | Registered, Attended, Watched On-Demand, No Show | Attended, Watched On-Demand |
| CNT | Content | Downloaded | Downloaded |
| PAID | Paid media (incl. Influ2) | Clicked, Converted | Converted |
| OUT | Outbound play (Unify, Clay trigger plays) | Sent, Replied, Meeting Booked | Replied, Meeting Booked |
| PRT | Partner | Referred, Accepted | Referred |
| WEB | Website | Visited, Demo Requested, Chat Engaged | Demo Requested, Chat Engaged |

Statuses are created with the campaign (a Flow sets them by type), so nobody types them by hand.

## 2. UTMs

`utm_source` and `utm_medium` come from fixed lists (config `marketing_ops.utm`). HubSpot form hidden fields capture them; a HubSpot workflow normalises case and common typos before sync, and anything still off the list is flagged (M02). `utm_campaign` = the Salesforce campaign name.

## 3. Event and webinar lists

Imported, de-duplicated against existing leads and contacts, and routed within **48 hours** of the event end (config `list_import_sla_hours`). After that, speed-to-lead is gone and the SDR follow-up lands cold (M04). Import template: email, first, last, company, title, country, consent fields, member status.

## 4. Consent

| Rule | Where | Check |
|---|---|---|
| Lawful basis before marketing email | EU/UK (GDPR) | M05 |
| Express or implied consent, recorded with type and date | Canadian contacts (CASL) | M06 |
| Implied consent from an inquiry lapses after six months | CASL | M07 |
| No marketing email after opt-out | Everywhere | M08 (check the send logs) |

Consent fields live on Lead/Contact and sync both ways; HubSpot is the system of record for subscription status. Consent issues go to Marketing Ops and Legal the same day. *This is an operating checklist, not legal advice.*

## 5. Attribution

Two views, never mixed in one chart:

- **Sourced:** the opportunity's `Source__c` and the originating lead's first campaign. Answers "who created this pipeline".
- **Influenced, W-shaped:** 30% first touch, 30% the touch that made the lead an MQL, 30% the touch that created the opportunity, 10% spread across the rest; 180-day lookback (config `marketing_ops.attribution`). Answers "which programs moved it". SQL versions: [`multi_touch.sql`](../../shared_core/metrics/sql/attribution/multi_touch.sql) and [`w_shaped_attribution.sql`](../../shared_core/metrics/sql/attribution/w_shaped_attribution.sql).

## 6. Hygiene rules

| Rule | Owner |
|---|---|
| M01 Campaign name breaks convention | Campaign owner |
| M02 UTM value outside the taxonomy | Campaign owner |
| M03 Member status not valid for the campaign type | Marketing Ops |
| M04 Event or webinar list imported late | Marketing Ops |
| M05–M08 Consent | Marketing Ops + Legal, same day |
| M09 Leads with a lead source but no campaign member | Marketing Ops (attribution gap) |

## 7. What the reports answer

| Question | Output |
|---|---|
| Which channels make leads that become pipeline? | Channel funnel by first touch: MQL / SQL / opp rates |
| What does an MQL or an opp cost, by channel? | Spend ÷ outcomes |
| Which campaigns get credit for pipeline and revenue? | W-shaped attributed pipeline and won |
| How many leads does each channel need this quarter to hit next quarter's number? | [Demand plan](demand_plan.py) |
