{{ config(materialized='table') }}

with food as (
    select *, extract(YEAR from report_month) as report_year
    from {{ ref('fct_food_prices') }}
),

poverty as (
    select * from {{ ref('stg_poverty') }}
)

select
    f.*,
    p.poverty_rate_pct,
    p.gini_index
from food f
left join poverty p 
    on f.report_year = p.report_year