-- =============================================================================
-- Stage velocity and slippage for the VP of Sales brief.
-- Builds on the semantic layer (v_opportunities, v_stage_history, v_close_date_pushes).
-- Run: python -m shared_core.metrics.run_sql gtm_strategy_ops/sales_leadership/sql/stage_velocity.sql
-- Python equivalent: gtm_strategy_ops/sales_leadership/stage_velocity.py (a test checks they agree).
-- =============================================================================

-- 1. Stage conversion and time in stage. advanced = moved to a later stage or won, lost = closed lost here.
--    SQLite has no MEDIAN, so this shows the average, and the Python report shows the median.
SELECT
    stage,
    COUNT(*)                                                                         AS entered,
    SUM(CASE WHEN next_stage IS NOT NULL AND next_stage <> 'Closed Lost' THEN 1 ELSE 0 END) AS advanced,
    SUM(CASE WHEN next_stage = 'Closed Lost' THEN 1 ELSE 0 END)                      AS lost_here,
    SUM(CASE WHEN next_stage IS NULL THEN 1 ELSE 0 END)                              AS open_now,
    ROUND(100.0 * SUM(CASE WHEN next_stage IS NOT NULL AND next_stage <> 'Closed Lost' THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN next_stage IS NOT NULL THEN 1 ELSE 0 END), 0), 1)   AS conversion_pct,
    ROUND(AVG(CASE WHEN next_stage IS NOT NULL AND next_stage <> 'Closed Lost' THEN days_in_stage END), 1) AS avg_days_advanced
FROM v_stage_history
GROUP BY stage
ORDER BY stage;

-- 2. First hop (Qualify -> Discovery) by source: where the intro-to-discovery delay sits.
SELECT
    o.source,
    COUNT(*)                          AS deals_advanced,
    ROUND(AVG(s.days_in_stage), 1)    AS avg_days_in_qualify
FROM v_stage_history s
JOIN v_opportunities o ON o.opportunity_id = s.opportunity_id
WHERE s.stage = '1 - Qualify' AND s.next_stage IS NOT NULL AND s.next_stage <> 'Closed Lost'
GROUP BY o.source
ORDER BY avg_days_in_qualify DESC;

-- 3. Open deals by owner with close-date pushes: slippage per rep.
SELECT
    o.owner,
    COUNT(DISTINCT o.opportunity_id)  AS open_deals,
    COUNT(DISTINCT p.opportunity_id)  AS deals_pushed,
    COALESCE(SUM(p.days_pushed), 0)   AS total_days_pushed
FROM v_opportunities o
LEFT JOIN v_close_date_pushes p ON p.opportunity_id = o.opportunity_id
WHERE o.is_closed = 0
GROUP BY o.owner
ORDER BY deals_pushed DESC;
