# Enrichment Waterfall Design (Clay + ZoomInfo)

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

**Scope:** administer the enrichment stack, design production-ready AI workflows for account research and enrichment, and connect them to GTM systems through low-code tools and APIs. The engine that runs this cascade in code is [`enrichment/rules_engine.py`](../enrichment/rules_engine.py), driven by [`config/waterfall_rules.yaml`](../../config/waterfall_rules.yaml).

The goal: turn a raw lead into a routable, scorable record within 15 minutes of creation, at the lowest cost per verified contact.

## Table: `Inbound Lead Enrichment` (triggered by a CRM webhook on Lead create)

| # | Column | Provider / method | Runs when | Writes to CRM |
|---|---|---|---|---|
| 1 | Normalize domain | Formula (strip www, map personal domains to blank) | always | — |
| 2 | Account match | CRM lookup by domain → fuzzy name ([`l2a_matcher.py`](../enrichment/l2a_matcher.py)) | domain present | `Matched_Account__c` |
| 3 | Firmographics | Clay company enrichment | no matched account, or account fields empty | `Segment__c`, `NumberOfEmployees`, `Region__c` |
| 4 | Segment classifier | AI column: classify into the segment keys in config, with a confidence output | step 3 returned an industry | `Segment__c` if confidence ≥ 0.8, otherwise flag |
| 5 | Title → persona | AI column: map title to the persona keys in config (prompt pinned, eval'd on ~50 labelled titles) | title present | `Persona__c` |
| 6 | Email verify | Native verification | email present | `Email_Status__c` |
| 7 | Contact data | **ZoomInfo** (direct dial + verified email) | persona is an economic buyer or champion **and** fit ≥ B | `Phone`, `MobilePhone` |
| 8 | Fallback contact | Second provider in the waterfall | step 7 miss | same fields |
| 9 | Signals | Job postings, news, LinkedIn Sales Navigator (assumed) job changes | ICP segment | `Intent_Signals__c` |
| 10 | Score + route | HTTP column → scoring service ([`score_leads.py`](../lead_scoring/score_leads.py)) | 1–9 done | `Fit_Score__c`, `Intent_Score__c`, `Lead_Grade__c` |

Add vertical-specific columns here (for example a public-registry size lookup for a regulated vertical) and note which segments trigger them.

## Cost guardrails

- **Paid contact data runs only on leads worth calling** (step 7 condition). Spending phone credits on D-grade leads is the most common avoidable waterfall cost.
- **Empty-field-only writes.** The tool never overwrites a rep-entered value. Conflicts go to a suffixed field for review.
- **Credit budget per lead source**, reviewed monthly against pipeline per lead from the [funnel report](../funnel_analytics/funnel_report.py). A source with low pipeline per lead gets a cheaper waterfall.

## Quality checks (weekly)

| Check | Target |
|---|---|
| Segment classifier agreement with AE-corrected segment | ≥ 90% |
| Persona mapping accuracy on the labelled set | ≥ 92% |
| ZoomInfo direct-dial connect rate (from dialer (none confirmed) outcomes) | Track per segment; drop the provider for any segment below the fallback |
| Leads stuck in Enriching > 15 min | 0 |
