# Sales Engagement Layer: Unify / HubSpot Sequences (assumed) · dialer (none confirmed) · HubSpot Chat (assumed) · LinkedIn Sales Navigator (assumed)

![GTM Engineer](https://img.shields.io/badge/role-GTM%20Engineer-1F6FEB)

**Scope:** administer the CRM, sequencer, data provider, enrichment tool, dialer, website chat and social-selling tool, and design the SDR process around them.

This is a design spec: how to configure each tool so it reinforces the [lead lifecycle](../lead_lifecycle/lead-lifecycle-spec.md) instead of running its own version of it. Cadence and activity-logging standards here directly affect forecast signals on the 🟩 Strategy & Ops side.

## Unify / HubSpot Sequences (assumed): cadence architecture

**Principle:** a small set of cadences keyed to *segment × product line × intent*. Not one per rep.

| Cadence | Entry | Steps (days) | Exit |
|---|---|---|---|
| `HR-Hand-Raise` | Demo request or website chat (any ICP) | Call + email within the first-touch SLA, then D1, D3, D6 (6 touches) | Meeting booked → SQL path; no response → `Working-Std` |
| `CORE-Direct` | Core-segment MQL, core product interest | 9 touches / 18 days | Meeting / Recycle |
| `CUSTOMER-XSell` | Existing customer, add-on signal | AE-owned, 5 touches, exec-sponsor email | Expansion opp |
| `VELOCITY-Std` | High-velocity vertical MQL | 8 touches / 14 days | Meeting / Recycle |
| `ABM-Tier1` | Top-tier target account, A3/A4 | Multi-thread: 3 personas in parallel, social steps | Meeting / quarterly re-enroll |

Rename these to the company's own plays. The keys (segment × product × intent) stay.

**Config standards**

- Cadence enrollment writes `Status = Working` and a `Cadence__c` stamp through the CRM sync. Cadence membership is reportable.
- Personalization variables (`{{use_case}}`, `{{persona_angle}}`) are populated from the [AI research brief](../ai_research/account_research.py) **after human acceptance only**.
- Bounce or opt-out removes the person from every cadence and sets the opt-out flag. Apply the regional rules that govern your senders and recipients (for example CASL, GDPR).
- Auto-enrollment (rules that add MQLs to a cadence) is the riskiest piece. Pilot it on `HR-Hand-Raise` first, with SDR override, and measure speed-to-lead before and after.

## dialer (none confirmed)

- Call lists are generated from CRM views sorted by `Lead_Grade__c`, never from static CSVs.
- Dispositions map 1:1 to CRM task outcomes (`Connected-Meeting`, `Connected-NotNow`, `Wrong Number`, `Gatekeeper`…). The connect rate per data provider feeds the [waterfall](enrichment-waterfall.md) review.
- Power-hour blocks are aligned to regional calling windows by pod.

## HubSpot Chat (assumed)

- Routing on chat uses the same pod rules. A known customer visiting goes to the AE, a known open opp goes to the opp owner, and an ICP fit goes to the live SDR.
- The chat "engaged" event writes `chat_engaged@date` to the signal log, which carries the highest intent weight after a demo request.
- Meetings booked in chat skip MQL and go straight to SAL with the hand-raiser first-touch SLA.

## LinkedIn Sales Navigator (assumed)

- Saved account lists mirror the CRM segments: one list per pod.
- Job-change alerts for economic-buyer personas at ICP accounts feed the enrichment tool as `champion_job_change`.
- CRM sync is on, so InMail and connection activity logs to the CRM as activity.
