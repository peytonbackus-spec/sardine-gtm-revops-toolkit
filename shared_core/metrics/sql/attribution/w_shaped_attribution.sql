-- ---
-- type: resource
-- category: code
-- tags:
--   - resource
--   - sql
--   - attribution
--   - revops
-- status: active
-- last_updated: 2026-08-21
-- ---

-- W-Shaped Multi-Touch Attribution Model
-- Weight Distribution: First Touch (30%), Opportunity Creation (30%), Lead Conversion (30%), Middle Touches (10%)

WITH touchpoints AS (
    SELECT 
        opportunity_id,
        touchpoint_id,
        touchpoint_type,
        timestamp,
        ROW_NUMBER() OVER (PARTITION BY opportunity_id ORDER BY timestamp ASC) as first_touch,
        ROW_NUMBER() OVER (PARTITION BY opportunity_id ORDER BY timestamp DESC) as last_touch
    FROM gtm_data.touchpoint_attribution
),
weighted_touches AS (
    SELECT 
        t.opportunity_id,
        t.touchpoint_id,
        t.touchpoint_type,
        CASE 
            WHEN t.first_touch = 1 THEN 0.30  -- First Touch (30%)
            WHEN t.touchpoint_type = Lead_Conversion THEN 0.30  -- Lead Conversion (30%)
            WHEN t.touchpoint_type = Opp_Creation THEN 0.30  -- Opportunity Creation (30%)
            ELSE 0.10 / NULLIF((COUNT(*) OVER (PARTITION BY t.opportunity_id) - 3), 0)  -- Split remaining 10%
        END as weight
    FROM touchpoints t
)
SELECT 
    wt.touchpoint_type,
    SUM(o.amount * wt.weight) as attributed_pipeline_arr
FROM weighted_touches wt
JOIN gtm_data.opportunities o ON wt.opportunity_id = o.id
WHERE o.is_won = TRUE
GROUP BY 1
ORDER BY 2 DESC;
