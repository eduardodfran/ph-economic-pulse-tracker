{{ config(
    materialized='table',
    partition_by={
        'field': 'report_year',
        'data_type': 'int64',
        'range': { 'start': 2006, 'end': 2035, 'interval': 1 }
        },
        cluster_by=["report_year"]
) }}
-- Build a year-aware correlation table. Use the food-prices mart as the
-- authoritative source of report years so the correlation table includes all
-- years observed in the price series (ensures referential tests against the
-- pulse mart pass even when some economic indicators are missing for a year).

with years as (
    select distinct extract(year from report_month) as report_year
    from {{ ref('fct_food_prices') }}
),

economic_context as (
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
    y.report_year,
    e.net_income_per_capita,
    e.income_growth_pct,
    e.agriculture_gdp_pct,
    e.slum_pop_pct,
    p.poverty_rate_pct,
    p.gini_index
from years y
left join economic_context e
    on y.report_year = e.report_year
left join poverty_stats p
    on y.report_year = p.report_year