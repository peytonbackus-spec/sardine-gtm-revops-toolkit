-- =============================================================================
-- Lead-to-opportunity funnel (GTM Engineer). Builds on shared_core semantic layer.
-- Run: python -m shared_core.metrics.run_sql gtm_engineer/funnel_analytics/sql/lead_funnel.sql
-- =============================================================================

-- 1. Monthly cohort funnel (cohort-based conversion, per metric-definitions.md)
SELECT
    created_month                                                   AS cohort,
    COUNT(*)                                                        AS leads,
    ROUND(100.0 * SUM(mql_date IS NOT NULL) / COUNT(*), 1)          AS mql_pct,
    ROUND(100.0 * SUM(sal_date IS NOT NULL) / COUNT(*), 1)          AS sal_pct,
    ROUND(100.0 * SUM(sql_date IS NOT NULL) / COUNT(*), 1)          AS sql_pct,
    ROUND(100.0 * SUM(converted_date IS NOT NULL) / COUNT(*), 1)    AS opp_pct
FROM v_leads
WHERE is_duplicate = 0
GROUP BY created_month
ORDER BY created_month;

-- 2. Source performance: conversion, velocity, pipeline value
SELECT
    l.lead_source,
    COUNT(*)                                                        AS leads,
    ROUND(100.0 * SUM(l.converted_date IS NOT NULL) / COUNT(*), 1)  AS lead_to_opp_pct,
    ROUND(AVG(CASE WHEN l.sql_date IS NOT NULL
                   THEN julianday(l.sql_date) - julianday(l.created_date) END), 1) AS avg_days_to_sql,
    CAST(COALESCE(SUM(o.amount), 0) AS INT)                         AS pipeline_usd,
    CAST(COALESCE(SUM(o.amount), 0) / COUNT(*) AS INT)              AS pipeline_per_lead_usd
FROM v_leads l
LEFT JOIN v_opportunities o ON o.opportunity_id = l.opportunity_id
WHERE l.is_duplicate = 0
GROUP BY l.lead_source
ORDER BY pipeline_usd DESC;

-- 3. MQL -> SAL SLA compliance by SDR (4h SLA from config/company.yaml)
SELECT
    owner,
    COUNT(*)                                                        AS accepted,
    ROUND(100.0 * SUM(mql_to_sal_hours <= 4) / COUNT(*), 1)         AS within_sla_pct,
    ROUND(AVG(mql_to_sal_hours), 1)                                 AS avg_hours
FROM v_leads
WHERE mql_to_sal_hours IS NOT NULL
GROUP BY owner
ORDER BY within_sla_pct;
