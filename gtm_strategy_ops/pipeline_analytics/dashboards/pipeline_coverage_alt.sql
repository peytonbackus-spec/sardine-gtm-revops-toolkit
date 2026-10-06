-- Pipeline Coverage & Weighted Forecast Model
WITH sales_quotas AS (
  SELECT rep_id, target_quota, period
  FROM {{ ref('stg_sales_quotas') }}
),
pipeline_summary AS (
  SELECT
    owner_id AS rep_id,
    SUM(amount) AS gross_pipeline,
    SUM(amount * probability) AS weighted_pipeline
  FROM {{ ref('stg_deals') }}
  WHERE stage NOT IN ('Closed Won', 'Closed Lost')
  GROUP BY 1
)
SELECT
  q.rep_id,
  q.target_quota,
  COALESCE(p.gross_pipeline, 0) AS gross_pipeline,
  COALESCE(p.weighted_pipeline, 0) AS weighted_pipeline,
  ROUND(COALESCE(p.gross_pipeline, 0) / NULLIF(q.target_quota, 0), 2) AS coverage_ratio
FROM sales_quotas q
LEFT JOIN pipeline_summary p ON q.rep_id = p.rep_id;
