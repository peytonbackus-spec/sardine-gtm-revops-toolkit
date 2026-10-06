# Sardine: Company Brief

![Shared](https://img.shields.io/badge/supports-BOTH%20tracks-7B61FF)

Public facts only, each with a source. Anything not stated in a source is tagged `[ASSUME]` and lives in [`config/company.yaml`](../../config/company.yaml), not here. Researched October 2026. Numbers move fast at this company (network stats changed between press releases a few months apart), so re-check before quoting.

## Snapshot

| | Fact | Source |
|---|---|---|
| **What it is** | "The agentic risk platform for fighting financial crime": fraud prevention and AML compliance on one platform | [sardine.ai](https://www.sardine.ai/) |
| **Founded** | 2020, by former leaders from Coinbase, Revolut, Uber and PayPal | [Series C post](https://www.sardine.ai/blog/series-c-announcement) |
| **Funding** | $170M raised in total. $70M Series C led by Activant (Feb 2025); $25M extension led by National Bank of Canada (May 2026) | [About](https://www.sardine.ai/about), [fintech.global](https://fintech.global/2026/05/21/sardine-lands-25m-as-national-bank-of-canada-deepens-bet/) |
| **Investors named** | Andreessen Horowitz, Visa, Experian, Google, XYZ Venture Capital, Cross Creek, FIS, Moody's, among others | [About](https://www.sardine.ai/about) |
| **Growth (as of Series C)** | Customer base doubled and ARR grew 130% in the prior year; 300+ enterprises across 70 countries | [Series C post](https://www.sardine.ai/blog/series-c-announcement) |
| **Customers (Sep 2026)** | 500+ global enterprise customers | [AI Labs release](https://www.sardine.ai/press/pr/sardine-ai-labs) |
| **Network (Sep 2026)** | 6.5B devices, 441M consumers, 3.4M businesses, 6.6B transactions, $1.8T in payments tracked | [AI Labs release](https://www.sardine.ai/press/pr/sardine-ai-labs) |
| **Named customers** | FIS, Experian, National Bank of Canada, Nubank, GoDaddy, Deel, Gusto, Paylocity, Xero, ZoomInfo, Intuit, Kalshi, SeatGeek, Whop, Coastal, LHV, Prezzee, First Federal Bank of Kansas City, Checkout.com, Brex, Edward Jones | [sardine.ai](https://www.sardine.ai/), [AI Labs release](https://www.sardine.ai/press/pr/sardine-ai-labs), [Helix release](https://www.businesswire.com/news/home/20251217509767/en), RevOps posting |
| **Recognition** | Leader, The Forrester Wave: Financial Crime Management Solutions, Q3 2026; G2 4.9/5 | [Aug 2026 product update](https://www.sardine.ai/blog/product-updates-august-2026), [sardine.ai](https://www.sardine.ai/) |
| **HQ** | San Francisco; remote-first | `[VERIFY]` third-party directory; postings say remote-first |

## Leadership

From the [About page](https://www.sardine.ai/about): Soups Ranjan (CEO, co-founder), Aditya Goel (co-founder), Kazuki Nishiura (CTO), Zahid Shaikh (CPO), Ben Cook (CFO), Bil Corry (CISO), **Myles Blumberg (Global Head of Revenue)**, Andres Benvenuto (Global Head of Data Strategy). Also quoted publicly: Ravi Loganathan (Head of Banking & Policy) and Niranjan Shetty (Head of Data Science).

The RevOps Manager posting does not state a reporting line. The revenue org is led by the Global Head of Revenue, so RevOps most likely sits in that org. `[ASSUME]`

## Products

Sardine groups its platform into five areas ([sardine.ai](https://www.sardine.ai/)). This repo models them as two product lines, because that is how a buyer budgets them: fraud budgets and compliance budgets usually sit with different executives.

| Area | Modules | Repo product line |
|---|---|---|
| Device & Behavior | Device Intelligence, Behavior Biometrics, True Piercing | `fraud` |
| Fraud Prevention | Agentic Fraud Ops, Payment Fraud, Bank Transactions, Card Issuing Fraud, Merchant Monitoring, Refund Fraud, Policy Abuse | `fraud` |
| Cyber Security | Account Takeovers, Bot Detection, Job Applicant Fraud | `fraud` |
| Onboarding | Global KYC, Global KYB, Identity / Document / Bank Verification, Credit Underwriting | `compliance` |
| AML Compliance | Agentic AML Ops, Transaction Monitoring, Customer Risk Rating, Sanctions Screening, Case Management, Sponsor Banking | `compliance` |

**Platform:** Sardine Flow (orchestration), Agent Hub, Rules Engine, ML models, Connections Graph, and the Sonar data consortium.

**Agents:** OSINT Search, Data Analyst, Rule Assistant, Transaction Monitoring, Business Due Diligence, Doc KYC, PEP Screening, Graph Analyst, Sanctions Screening and SAR Generation. Earlier launches cited an 88% auto-resolution rate for the KYC agent ([Series C post](https://www.sardine.ai/blog/series-c-announcement)). The CEO has cited 55–75% auto-resolution on sanctions alerts and 95% automation on onboarding reviews ([McKinsey interview, Nov 2025](https://www.mckinsey.com/industries/financial-services/our-insights/talking-with-soups-ranjan-cofounder-and-ceo-of-sardineai)).

**Recent:** Sardine AI Labs and a $375K research fellowship (Sep 2026), plus a transformer-based card-fraud foundation model reporting a 68% detection improvement for consumer card issuers ([release](https://www.sardine.ai/press/pr/sardine-ai-labs)). Partnerships include Helix by Q2 for sponsor banks (Dec 2025, [release](https://www.businesswire.com/news/home/20251217509767/en)) and Modulr for automated payments (Apr 2026, [release](https://www.sardine.ai/press/pr/real-time-fraud-detection)).

## Go-to-market

| Signal | What it says | Source |
|---|---|---|
| **Who they sell to** | "Wherever there's money movement": banks, fintechs, payment processors, card issuers, acquirers, crypto exchanges, ticketing, merchants | [McKinsey interview](https://www.mckinsey.com/industries/financial-services/our-insights/talking-with-soups-ranjan-cofounder-and-ceo-of-sardineai) |
| **Positioning** | One platform for fraud and compliance instead of vendor sprawl; real-time for instant payments; AI-written rules "within a minute" | Same |
| **Sales org shape** | Open roles for a crypto AE, a federal strategic AE (Washington, DC), strategic account managers in NA and Dubai, a GM for Mexico, an MENA sales engineer, and forward-deployed integration engineers in the US and UK | [a16z job board](https://jobs.a16z.com/jobs/sardine) |
| **Pricing model** | Consumption-based with a minimum monthly commit drawn down by usage; platform access fee plus per-product consumption rates; overages billed monthly. Third-party median contract about $95K/yr (range about $15K–$255K) | `[VERIFY]` [Vendr](https://vendr.com/marketplace/sardine) |
| **Competitors named in comparisons** | Socure, SEON, Sift, Feedzai, Unit21, BioCatch, Fingerprint, Bureau | [Bureau comparison](https://bureau.id/resources/blog/sardine-competitors), G2 |

**Implications for RevOps.** These shape the design choices in this repo:

1. **Consumption revenue makes lead-to-cash the hard part.** Bookings (minimum commit) and billed revenue (commit plus overage) diverge every month. Overage is an expansion signal and under-use is a churn signal, and both are visible long before renewal. That is why this repo adds a [commit burn-down module](../../gtm_strategy_ops/consumption/commit_burndown.py) and a [lead-to-cash map](../../gtm_strategy_ops/consumption/lead-to-cash.md).
2. **Two budgets, one platform.** Fraud and compliance usually have different economic buyers. Cross-sell between the two lines is the main expansion motion, and the CEO's "one platform" pitch depends on it.
3. **Bank sales cycles have extra gates.** Third-party risk management, model risk management and InfoSec reviews add a stage-4 gate that fintech deals often skip. Stage time limits and the deal-risk model account for this.
4. **Regulatory triggers are the strongest intent signal for compliance.** A consent order or enforcement action against a prospect outranks a demo request. It is modelled as the `regulatory_action` signal.
5. **A global, vertical sales org needs routing by segment and region.** The vertical AEs (crypto, federal) and regional teams (EU/UK, MENA, Mexico, Australia) are the routing pods in config.
