{{ config(materialized='view') }}

{% if var('use_seed', false) %}
with base_econ as (
    select
        year,
        indicator_code,
        value,
        country_iso3
    from {{ ref('economy_sample') }}
    where country_iso3 = 'PHL'
)
{% else %}
with base_econ as (
    select
        year,
        indicator_code,
        value
    from {{ source('staging', 'stg_economy') }}
    where country_iso3 = 'PHL'
)
{% endif %}

SELECT
    year,
    -- Pivot logic using the codes you just found
    MAX(CASE WHEN indicator_code = 'NY.ADJ.NNTY.PC.CD' THEN value END) AS net_income_per_capita,
    MAX(CASE WHEN indicator_code = 'NY.ADJ.NNTY.KD.ZG' THEN value END) AS income_growth_pct,
    MAX(CASE WHEN indicator_code = 'NV.AGR.TOTL.ZS' THEN value END) AS agriculture_gdp_pct,
    MAX(CASE WHEN indicator_code = 'EN.POP.SLUM.UR.ZS' THEN value END) AS slum_pop_pct
FROM base_econ
GROUP BY 1