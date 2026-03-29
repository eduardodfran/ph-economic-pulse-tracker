{{ config(materialized='view') }}

{% if var('use_seed', false) %}
with raw_economy as (
    select
        country_name,
        country_iso3,
        safe_cast(year as int64) as year,
        indicator_name,
        indicator_code,
        safe_cast(value as float64) as value
    from {{ ref('economy_sample') }}
)
{% else %}
with raw_economy as (
    select
        country_name,
        country_iso3,
        safe_cast(year as int64) as year,
        indicator_name,
        indicator_code,
        safe_cast(value as float64) as value
    from {{ source('staging', 'stg_economy') }}
)
{% endif %}

select
    year,
    max(case when indicator_code = 'NY.GDP.PCAP.CD' then value end) as gdp_per_capita,
    max(case when indicator_code = 'FP.CPI.TOTL.ZG' then value end) as inflation_rate_cpi
from raw_economy
where year is not null
group by year

