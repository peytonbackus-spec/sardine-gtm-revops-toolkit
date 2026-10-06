# ICP, Segments & Buying Committee

![Shared](https://img.shields.io/badge/supports-BOTH%20tracks-7B61FF)

One segment model that every system shares: lead scoring and routing on the 🟦 side, pipeline, win-rate and renewal cuts on the 🟩 side. The machine-readable copy is `segments` and `personas` in [`config/company.yaml`](../../config/company.yaml); the code reads that, so keep this page in step with it.

> **Status:** segments are built from Sardine's named customers and the shape of its open sales roles (see the [company brief](sardine-company-brief.md)). Fit points and persona weights are `[ASSUME]` starting values. The first job is to test them against Sardine's closed-won history with [`calibrate_scoring.py`](../../gtm_engineer/lead_scoring/calibrate_scoring.py).

## Segments

"Lines" says which product lines the segment typically buys: regulated financial institutions buy both fraud and compliance; digital businesses mostly buy fraud.

| Segment key | Definition | Fit pts | Motion | Lines | Default pain hypothesis |
|---|---|---|---|---|---|
| `tier1_bank` | Tier-1 & large banks | 30 | enterprise abm | both | Real-time fraud and AML on instant payments without adding friction for good customers; consolidate point vendors |
| `sponsor_bank_baas` | Sponsor banks & BaaS platforms | 28 | partner led | both | Program-level fraud and BSA/AML oversight across fintech partners and payment rails |
| `fintech_neobank` | Fintechs & neobanks | 28 | velocity | both | Onboarding conversion with KYC/KYB plus fraud controls that scale with growth |
| `payments_issuing` | Payments, card issuers & acquirers | 28 | enterprise abm | both | Card and payment fraud at authorization speed; merchant monitoring |
| `regional_bank_cu` | Regional & community banks, credit unions | 24 | enterprise abm | both | Examiner-ready AML automation and faster fraud rule changes with a lean team |
| `crypto` | Crypto & digital assets | 24 | velocity | both | On/off-ramp fraud, sanctions exposure and Travel Rule-ready compliance |
| `marketplace_commerce` | Marketplaces, commerce & ticketing | 22 | velocity | fraud | Payment fraud, refund and policy abuse, bot and account-takeover defense |
| `b2b_saas_payroll` | Payroll, HR & B2B SaaS platforms | 22 | velocity | fraud | KYB on new customers, payout fraud and job-applicant fraud |
| `gaming_prediction` | Gaming & prediction markets | 18 | velocity | fraud | Identity, bonus abuse and payment fraud at signup and withdrawal |
| `public_sector` | Federal & public sector | 16 | enterprise abm | fraud | Benefits and payments fraud detection with an auditable decision trail |
| `other` | Non-ICP | 0 | nurture | — | Nurture or disqualify |

Example customers by segment (public logos, see brief): banks (National Bank of Canada, First Federal Bank of Kansas City, Coastal, LHV), fintech (Nubank, Brex), payments (FIS, Checkout.com), commerce (GoDaddy, Whop, SeatGeek, Prezzee), B2B/payroll (Gusto, Deel, Paylocity, Xero, Intuit, ZoomInfo), prediction markets (Kalshi).

## Anti-ICP

- No money movement and no onboarding risk: nothing for the platform to score.
- Pre-revenue startups without a sponsor bank or processor requirement driving the purchase.
- Researchers, students, job seekers and vendors.
- An open opportunity already exists on the account: route to the owner, don't create a new lead.

## Buying committee

Fraud and compliance usually report to different executives with different budgets. A deal that only has one of them engaged is a single-line deal, however many contacts it has.

| Persona key | Typical titles | Role | Pts | Default angle |
|---|---|---|---|---|
| `head_of_fraud` | Head of Fraud, VP Fraud Strategy | economic buyer | 25 | Lower fraud losses without raising false positives; one platform instead of five point tools |
| `bsa_aml_officer` | BSA/AML Officer, Chief Compliance Officer | economic buyer | 24 | Clear the alert backlog with agents a regulator can audit; examiner-ready SAR narratives |
| `chief_risk_officer` | Chief Risk Officer, SVP Enterprise Risk | economic buyer | 22 | One view of fraud and financial-crime risk; fewer vendors, one model-governance story |
| `head_of_payments_product` | VP Payments, Head of Product (Onboarding / Cards) | champion | 18 | Launch new rails and products faster without opening fraud holes; protect onboarding conversion |
| `risk_data_science` | Head of Risk Analytics, Fraud Data Science lead | influencer | 16 | Consortium data and device signals your models can't see; rules shipped in hours, not sprints |
| `ciso_security` | CISO, Head of Trust & Safety | influencer | 15 | Account-takeover and bot defense that shares signals with fraud ops |
| `fraud_ops_manager` | Fraud Ops Manager, AML Investigations Lead | champion | 12 | Fewer manual reviews per analyst; agents that pre-work every case |
| `blocker_procurement` | Vendor Risk, Third-Party Risk, Model Risk Management | blocker | 5 | Complete third-party risk and model-governance package up front |
| `unknown` | — | none | 0 | Confirm role and whether they own fraud or compliance outcomes |

**Bank-specific gate:** at banks and credit unions, `blocker_procurement` includes model risk management, which reviews how ML models and AI agents make decisions. Bring the model-governance package to stage 3, not stage 4.

**For the 🟩 side:** stage 3+ deals without an economic buyer are flagged by the [data-quality monitor](../data_quality/dq_monitor.py) (rule O06) and the [deal-risk model](../../gtm_strategy_ops/ai_deal_risk/deal_risk.py).

**For the 🟦 side:** persona points feed the fit axis of the [lead score](../../gtm_engineer/lead_scoring/score_leads.py); persona is derived from title in the [enrichment waterfall](../../gtm_engineer/platform_admin/enrichment-waterfall.md).
