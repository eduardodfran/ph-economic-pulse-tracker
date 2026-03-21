{{ config(materialized='table') }}

with monthly_prices as (
    select
        -- Group by month (truncating the date to the 1st of the month)
        date_trunc(price_date, MONTH) as report_month,
        region,
        item_name,
        food_category,
        quantity_unit,
        avg(price_php) as avg_price_php
    from {{ ref('stg_wfp_prices') }}
    group by 1, 2, 3, 4, 5
)

select
    *,
    -- Use a window function to get the price from the previous month for the same item/region
    lag(avg_price_php) over (
        partition by region, item_name 
        order by report_month
    ) as prev_month_price_php,
    
    -- Calculate Month-over-Month % change (Inflation Pulse)
    case 
        when lag(avg_price_php) over (partition by region, item_name order by report_month) is not null 
        then (avg_price_php - lag(avg_price_php) over (partition by region, item_name order by report_month)) 
             / lag(avg_price_php) over (partition by region, item_name order by report_month)
        else 0 
    end as mom_inflation_rate

from monthly_prices