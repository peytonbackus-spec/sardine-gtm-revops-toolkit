-- =============================================================================
-- Pipeline coverage, segmentation and win rates (GTM Strategy & Ops).
-- Builds on the shared semantic layer (v_opportunities).
-- Run: python -m shared_core.metrics.run_sql gtm_strategy_ops/pipeline_analytics/sql/pipeline_coverage.sql
-- =============================================================================

-- 1. Open pipeline for the current fiscal quarter by region, product line, forecast category
SELECT
    region,
    product_line,
    COUNT(*)                                                         AS opps,
    CAST(SUM(amount) AS INT)                                         AS pipeline_usd,
    CAST(SUM(CASE WHEN forecast_category = 'Commit' THEN amount ELSE 0 END) AS INT)    AS commit_usd,
    CAST(SUM(CASE WHEN forecast_category = 'Best Case' THEN amount ELSE 0 END) AS INT) AS best_case_usd
FROM v_opportunities
WHERE is_closed = 0
  AND forecast_category <> 'Omitted'
  AND close_fiscal_quarter = '{{CURRENT_FISCAL_QUARTER}}'
GROUP BY region, product_line
ORDER BY pipeline_usd DESC;

-- 2. Win rate ($ and count) and average won-deal cycle by source and product line, closed deals
SELECT
    source,
    product_line,
    COUNT(*)                                                         AS closed,
    SUM(is_won)                                                      AS won,
    ROUND(100.0 * SUM(is_won) / COUNT(*), 1)                         AS win_rate_pct,
    ROUND(100.0 * SUM(amount * is_won) / SUM(amount), 1)             AS win_rate_usd_pct,
    ROUND(AVG(CASE WHEN is_won = 1 THEN cycle_days END), 0)          AS avg_won_cycle_days
FROM v_opportunities
WHERE is_closed = 1
GROUP BY source, product_line
ORDER BY closed DESC;

-- 3. Pipeline by owner with hygiene flags (feeds the manager 1:1 view)
SELECT
    owner,
    COUNT(*)                                                         AS open_opps,
    CAST(SUM(amount) AS INT)                                         AS pipeline_usd,
    SUM(CASE WHEN close_date < '{{AS_OF}}' THEN 1 ELSE 0 END)       AS past_close_date,
    SUM(CASE WHEN stage IN ('3 - Technical Validation', '4 - Business Case & Security Review',
                            '5 - Negotiate & Contract') AND eb_engaged = 0 THEN 1 ELSE 0 END) AS late_stage_no_eb,
    SUM(CASE WHEN contacts_engaged < 3 THEN 1 ELSE 0 END)            AS single_threaded
FROM v_opportunities
WHERE is_closed = 0
GROUP BY owner
ORDER BY pipeline_usd DESC;
