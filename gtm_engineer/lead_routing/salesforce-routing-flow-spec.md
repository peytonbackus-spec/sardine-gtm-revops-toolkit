# CRM Routing Flow Spec

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

**Scope:** translate GTM policy into CRM configuration, and connect AI capabilities to GTM systems via low-code tools and APIs. Written for Salesforce; the pattern ports to any CRM with record-triggered automation.

How [`route_leads.py`](route_leads.py) becomes CRM config. The Python is the testable spec. The Flow is the production implementation. Both apply the same rule order.

## Objects & fields

| Item | Type | Notes |
|---|---|---|
| `Routing_Pod__c` (Lead) | Text | Pod key from the company config (`lead_routing.pods`) |
| `Routing_Rule__c` (Lead) | Text | R1–R7, so you can see why a lead landed where it did |
| `Routing_Reason__c` (Lead) | Text(255) | Plain-English reason |
| `SDR_Pod_Member__c` | Custom object | SDR ↔ pod membership, `Active__c`, `Max_Open_Leads__c`, `Out_Of_Office__c` |
| `Routing_Config__mdt` | Custom metadata | Pod → segments/regions. Deployable, versioned, no hardcoded IDs. |

## Flow: `Lead_Routing_After_Score` (record-triggered, after save)

**Trigger:** `Lead_Grade__c` changed **or** `Status` = MQL **and** `Routing_Rule__c` is blank.

| Step | Element | Logic |
|---|---|---|
| 1 | Decision **R1** | `Segment__c = 'other'` or email invalid → owner = Disqualify queue, Status = Disqualified, reason set |
| 2 | Get Records | Open Opportunity on the matched Account? → **R2**: owner = Opp owner, create Contact Role task |
| 3 | Decision **R3** | `Account.Customer_Status__c = 'Customer'` → owner = Account owner, `Type` hint = Expansion |
| 4 | Decision **R4** | `Partner__c` not blank → owner = Partner Manager queue, notify the partner manager (chat or email) |
| 5 | Decision **R5** | Grade not in MQL set and no hand-raise → Status = Nurture, owner = Marketing queue |
| 6 | Subflow **R6** | Look up pod from `Routing_Config__mdt`; Get `SDR_Pod_Member__c` (active, not OOO, under cap) sorted by open-lead count; assign the first |
| 7 | Fault path **R7** | No match or pod full → Ops Review queue, plus an alert to the ops channel with the lead link |

**Lead-to-account matching** runs before the Flow: a domain match from the enrichment waterfall writes `Matched_Account__c`, with a fallback to a fuzzy name match flagged for review. Without it, rules R2 and R3 can't fire.

## Testing & release

- The Python version carries the unit tests ([`tests/test_gtm_engineer.py`](../../tests/test_gtm_engineer.py)). Each rule has a fixture lead.
- Flow changes ship through a sandbox. Replay the last 200 real MQLs through both versions and diff the owners before deploying.
- Weekly: `Routing_Rule__c = 'R7'` count. Every R7 is a gap in the policy or the data. The target is zero.
