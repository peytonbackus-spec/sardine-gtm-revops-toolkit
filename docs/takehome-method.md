# Take-home method note

How the figures in the Rev Ops Manager take-home (the PDF and the dashboard) are produced. The workbook is Sardine's data, so it and the scripts that read it stay in the gitignored `_private/takehome/` folder. This note and the loader are the public part: they show the rules, not the numbers.

## Pipeline

1. **Load.** [`gtm_strategy_ops/takehome/loader.py`](../gtm_strategy_ops/takehome/loader.py) reads the workbook into four tables (customer-product lines, a monthly long table, Firmographic rows, one row per invoiced customer) plus a data-quality report. Every rule lives in that file's docstring, so a changed assumption is a one-line change.
2. **Recompute independently.** `_private/takehome/review_fixes.py` re-reads the workbook with pandas alone, without the loader, and recomputes every figure the submission quotes, both the primary value and each sensitivity. It writes `review_fixes.md`. The PDF quotes only numbers that appear in that file.
3. **Dashboard.** `_private/takehome/analysis/build_dashboard.py` builds one self-contained HTML file from the loader tables, applying the same rules as step 2. `check_dashboard.py` opens the file with all network requests blocked at 1280, 375 and 320px and asserts that the default figures match `review_fixes.md`, and that the toggles, filters and Reset work.
4. **PDF.** `_private/takehome/analysis/build_pdf.py` renders the submission text and two dashboard screenshots to a four-page PDF.

## Definitions

| Term | Rule |
|---|---|
| Revenue, MRR | Units x unit price for the month, summed across a customer's products. Assumes the price is per unit per month. |
| One-off charge | A line billed in exactly one month at $50K or more is non-recurring and left out of MRR. One line qualifies; both builds assert that it is exactly one. Figures with it included are shown as a sensitivity and behind a dashboard toggle. |
| Pricing model | Not in the workbook. Primary: a fixed list of products is flat-rate and the rest are consumption. Alternative: inferred from usage (a line whose units change two or more times is consumption). A product whose lines don't fit its label is footnoted, with the effect of moving it. |
| Billing, attach | A customer bills a product in a month when it earns at least $0.01. Attach means billing a consumption product. Material attach is at least $500 a month. |
| New-logo attach window | "Within three months" means any of the three calendar months starting with the customer's first bill. |
| No-play attach | Flat-only accounts in a six-month window that reach material attach with no play, split by account age and applied by age to today's flat-only pool. |
| Churn | Billing in the first month and $0 in the last. |
| Net revenue retention, revenue kept | Last-month MRR over first-month MRR for the first-month cohort; revenue kept caps each customer at its first-month MRR. |
| Win rate, expected value per deal | Closed won / (won + lost); expected value is win rate x average revenue per customer, on four revenue bases. |
| Largest grower | The account with the largest change in MRR from the first to the last month. Not the same as the largest account by revenue. |

## Sensitivities run on every headline figure

- Four pricing definitions (product-based in the first month or any month; usage-inferred over the full year or a time-safe half year).
- With and without the largest grower.
- With and without the one-off charge.
- Attach thresholds of $0.01, $100, $500 and 10% of the account's MRR.

## Tests

[`tests/test_takehome_loader.py`](../tests/test_takehome_loader.py) runs the loader on a synthetic workbook with invented companies; the real workbook is never used in tests or CI.

## Reproduce (with the private files in place)

```bash
python3 -m gtm_strategy_ops.takehome.loader                       # data-quality report
python3 _private/takehome/review_fixes.py                         # every quoted figure -> review_fixes.md
python3 _private/takehome/analysis/build_dashboard.py             # dashboard.html
python3 _private/takehome/analysis/check_dashboard.py --shots     # offline checks + PDF screenshots
(cd _private/takehome && python3 analysis/build_pdf.py .)         # 4-page PDF
```

The loader needs `pandas` and `openpyxl` ([`requirements-takehome.txt`](../requirements-takehome.txt)); the dashboard checks and the PDF also need `playwright`, `markdown` and `pypdf`.
