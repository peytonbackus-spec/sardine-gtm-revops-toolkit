# Decision Log

Template decisions: [docs/overview/decision-log.md](https://github.com/peytonbackus-spec/sardine-gtm-revops-toolkit/blob/main/docs/overview/decision-log.md). Sardine-specific choices:

| # | Decision | Why |
|---|---|---|
| S1 | **Two product lines: compliance and fraud** | Different economic buyers and budgets; cross-sell between them is the main expansion motion |
| S2 | **A consumption module in 🟩** | With a minimum commit plus overage, expansion and churn signals are monthly, not annual |
| S3 | **`regulatory_action` as an intent signal with a long half-life** | An enforcement action is the strongest compliance buying trigger, and it stays relevant for months |
| S4 | **Model-risk review inside stage 4** | Bank buyers review how ML and agents decide; bringing that package early shortens the cycle |
| S5 | **11 segments from named customers and open sales roles** | Grounded in evidence rather than firmographic bands alone; weights are `[ASSUME]` until calibrated |
| S6 | **Five regions, including MENA and LATAM** | Matches Sardine's open roles (Dubai, Mexico, Brazil, EU/UK, Australia) |
| S7 | **Calendar fiscal year** | `[ASSUME]`: Sardine doesn't publish its fiscal calendar; one config line changes it |
