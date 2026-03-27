{{ config(materialized='table') }}

with economic_context as (
    select
        year as report_year,
        net_income_per_capita,
        income_growth_pct,
        agriculture_gdp_pct,
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
    e.report_year,
    e.net_income_per_capita,
    e.income_growth_pct,
    e.agriculture_gdp_pct,
    e.slum_pop_pct,
    p.poverty_rate_pct,
    p.gini_index
from economic_context e
left join poverty_stats p
    on e.report_year = p.report_year