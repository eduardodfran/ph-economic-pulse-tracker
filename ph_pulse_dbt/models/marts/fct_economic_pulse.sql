with food_prices as (
    select
        report_month,
        extract(year from report_month) as report_year,
        region,
        item_name,
        food_category,
        quantity_unit,
        avg_price_php,
        prev_month_price_php,
        mom_inflation_rate
    from {{ ref('fct_food_prices') }}
    where lower(item_name) like '%sweet potato%'
),

economic_context as (
    select
        year as report_year,
        net_income_per_capita,
        slum_pop_pct
    from {{ ref('stg_economy_pivoted') }}
),

poverty_stats as (
    select
        report_year,
        poverty_rate_pct,
        gini_index
    from {{ ref('stg_poverty') }}
)

select
    f.report_month,
    f.report_year,
    f.region,
    f.item_name,
    f.food_category,
    f.quantity_unit,
    f.avg_price_php,
    f.prev_month_price_php,
    f.mom_inflation_rate,
    e.net_income_per_capita,
    e.slum_pop_pct,
    p.poverty_rate_pct,
    p.gini_index,

    -- The "Kamote Ratio": how many pesos of annual income buy one peso of kamote
    safe_divide(e.net_income_per_capita, f.avg_price_php) as affordability_index

from food_prices f
left join economic_context e
    on f.report_year = e.report_year
left join poverty_stats p
    on f.report_year = p.report_year