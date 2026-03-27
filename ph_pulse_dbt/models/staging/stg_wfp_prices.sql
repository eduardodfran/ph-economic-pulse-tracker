{{ config(materialized='view') }}

with raw_data as (
    select * from {{ source('staging', 'stg_wfp_prices') }}
)

select
    -- 1. Identifiers
    cast(date as DATE) as price_date,
    lower(admin1) as region,
    lower(market) as market_name,
    lower(category) as food_category,
    lower(commodity) as item_name,
    
    -- 2. Pricing Info
    cast(price as FLOAT64) as price_php,
    cast(usdprice as FLOAT64) as price_usd,
    lower(unit) as quantity_unit,
    
    -- 3. Metadata
    lower(pricetype) as price_type,
    lower(currency) as currency_code

from raw_data
where price is not null