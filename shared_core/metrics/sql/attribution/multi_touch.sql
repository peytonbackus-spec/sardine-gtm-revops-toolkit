-- Multi-Touch Attribution: Linear & First/Last Touch
WITH touchpoints AS (
  SELECT 
    opportunity_id,
    touchpoint_id,
    channel,
    cost,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY opportunity_id ORDER BY created_at ASC) as first_touch,
    ROW_NUMBER() OVER (PARTITION BY opportunity_id ORDER BY created_at DESC) as last_touch,
    COUNT(*) OVER (PARTITION BY opportunity_id) as total_touches
  FROM {{ ref('stg_marketing_touchpoints') }}
)
SELECT 
  opportunity_id,
  touchpoint_id,
  channel,
  CASE WHEN first_touch = 1 THEN 1.0 ELSE 0.0 END as first_touch_weight,
  CASE WHEN last_touch = 1 THEN 1.0 ELSE 0.0 END as last_touch_weight,
  (1.0 / total_touches) as linear_weight
FROM touchpoints;
