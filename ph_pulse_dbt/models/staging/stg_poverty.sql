{{ config(materialized='view') }}

{% if var('use_seed', false) %}
with poverty_indicators as (
    select
        safe_cast(year as INT64) as report_year,
        indicator_code,
        safe_cast(value as FLOAT64) as indicator_value
    from {{ ref('poverty_sample') }}
    where safe_cast(year as INT64) >= 2000
      and country_iso3 = 'PHL'
      and indicator_code in ('SI.POV.NAHC', 'SI.POV.GINI')
)
{% else %}
with poverty_indicators as (
    select
        safe_cast(year as INT64) as report_year,
        indicator_code,
        safe_cast(value as FLOAT64) as indicator_value
    from {{ source('staging', 'stg_poverty') }}
    where safe_cast(year as INT64) >= 2000
      and country_iso3 = 'PHL'
      and indicator_code in ('SI.POV.NAHC', 'SI.POV.GINI')
)
{% endif %}

, poverty_by_year as (
    select
        report_year,
        max(case when indicator_code = 'SI.POV.NAHC' then indicator_value end) as poverty_rate_pct,
        max(case when indicator_code = 'SI.POV.GINI' then indicator_value end) as gini_index
    from poverty_indicators
    group by report_year
)

, year_spine as (
    select report_year
    from unnest(generate_array(2000, 2026)) as report_year
)

, joined as (
    select
        y.report_year,
        p.poverty_rate_pct,
        p.gini_index
    from year_spine y
    left join poverty_by_year p
        on y.report_year = p.report_year
)

select
    report_year,
    last_value(poverty_rate_pct ignore nulls) over (
        order by report_year
        rows between unbounded preceding and current row
    ) as poverty_rate_pct,
    last_value(gini_index ignore nulls) over (
        order by report_year
        rows between unbounded preceding and current row
    ) as gini_index
from joined
order by report_year