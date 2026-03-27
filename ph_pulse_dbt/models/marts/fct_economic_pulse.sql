WITH food_prices AS (
    SELECT 
        EXTRACT(YEAR FROM price_date) as year,
        region,
        AVG(price_php) as avg_price_kamote
    FROM {{ ref('stg_wfp_prices') }}
    WHERE item_name LIKE '%sweet potato%'
    GROUP BY 1, 2
),

economic_context AS (
    SELECT * FROM {{ ref('stg_economy_pivoted') }}
)

SELECT
    f.year,
    f.region,
    f.avg_price_kamote,
    e.net_income_per_capita,
    e.slum_pop_pct,
    
    -- THE "KAMOTE RATIO": How many kg of kamote can 1% of annual income buy?
    SAFE_DIVIDE(e.net_income_per_capita, f.avg_price_kamote) AS purchasing_power_index

FROM food_prices f
LEFT JOIN economic_context e ON f.year = e.year