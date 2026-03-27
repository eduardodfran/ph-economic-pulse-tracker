{{ config(materialized='view') }}

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

select
    report_year,
    max(case when indicator_code = 'SI.POV.NAHC' then indicator_value end) as poverty_rate_pct,
    max(case when indicator_code = 'SI.POV.GINI' then indicator_value end) as gini_index
from poverty_indicators
group by report_year
order by report_year