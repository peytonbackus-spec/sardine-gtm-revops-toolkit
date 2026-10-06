-- =============================================================================
-- Semantic layer: typed, de-duplicated views every dashboard reads from.
-- Implements shared_core/metrics/metric-definitions.md.
--
-- Dialect: SQLite, so it runs locally against sample_data/ via run_sql.py.
-- Port to Snowflake/BigQuery: julianday(a) - julianday(b) -> DATEDIFF('day', b, a),
-- CAST(strftime('%m', x) AS INT) -> MONTH(x).
-- Source tables mirror the Salesforce objects synced to the warehouse
-- (Fivetran/Salesforce connector naming would be salesforce.lead, salesforce.opportunity).
-- =============================================================================

-- Leads: typed, duplicates flagged, fiscal cohort attached --------------------
DROP VIEW IF EXISTS v_leads;
CREATE VIEW v_leads AS
WITH ranked AS (
    SELECT l.*,
           ROW_NUMBER() OVER (PARTITION BY LOWER(NULLIF(email, '')) ORDER BY created_date, lead_id) AS email_rank
    FROM leads l
)
SELECT
    lead_id,
    DATE(created_date)                                   AS created_date,
    STRFTIME('%Y-%m', created_date)                      AS created_month,
    segment, persona, region, lead_source, partner, product_interest, status, owner,
    NULLIF(mql_date, '')                                 AS mql_date,
    NULLIF(sal_date, '')                                 AS sal_date,
    NULLIF(sql_date, '')                                 AS sql_date,
    NULLIF(converted_date, '')                           AS converted_date,
    CAST(NULLIF(mql_to_sal_hours, '') AS REAL)           AS mql_to_sal_hours,
    NULLIF(opportunity_id, '')                           AS opportunity_id,
    CASE WHEN email IS NOT NULL AND email <> '' AND email_rank > 1 THEN 1 ELSE 0 END AS is_duplicate
FROM ranked;

-- Opportunities: typed, fiscal quarter of close (FY start month from config: {{FY_START_MONTH}}) --
DROP VIEW IF EXISTS v_opportunities;
CREATE VIEW v_opportunities AS
SELECT
    opportunity_id, account_id, account_name, segment, region, type, product_line, source,
    NULLIF(partner, '')                                  AS partner,
    owner,
    CAST(amount AS REAL)                                 AS amount,
    stage, forecast_category,
    DATE(created_date)                                   AS created_date,
    DATE(close_date)                                     AS close_date,
    'FY' || SUBSTR(CAST(CAST(STRFTIME('%Y', close_date) AS INT)
            + ({{FY_START_MONTH}} > 1 AND CAST(STRFTIME('%m', close_date) AS INT) >= {{FY_START_MONTH}}) AS TEXT), 3, 2)
         || '-Q' || ((CAST(STRFTIME('%m', close_date) AS INT) - {{FY_START_MONTH}} + 12) % 12 / 3 + 1)  AS close_fiscal_quarter,
    CASE WHEN is_closed = 'True' THEN 1 ELSE 0 END       AS is_closed,
    CASE WHEN is_won    = 'True' THEN 1 ELSE 0 END       AS is_won,
    NULLIF(closed_lost_reason, '')                       AS closed_lost_reason,
    CAST(julianday(close_date) - julianday(created_date) AS INT) AS cycle_days,
    CASE WHEN economic_buyer_engaged = 'True' THEN 1 ELSE 0 END AS eb_engaged,
    CAST(contacts_engaged AS INT)                        AS contacts_engaged,
    NULLIF(originating_lead_id, '')                      AS originating_lead_id
FROM opportunities;
