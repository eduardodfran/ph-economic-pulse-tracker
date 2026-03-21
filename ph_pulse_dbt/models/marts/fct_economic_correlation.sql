{{ config(materialized='table') }}

with food_prices as (
    select 
        *,
        extract(YEAR from price_date) as report_year 
    from {{ ref('stg_wfp_prices') }}
),

poverty_stats as (
    select * from {{ ref('stg_poverty') }}
)

select
    f.*,
    p.poverty_rate_pct,
    p.gini_index
from food_prices f
left join poverty_stats p
    on f.report_year = p.report_year