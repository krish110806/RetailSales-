-- fct_sales.sql
-- Core fact table containing transaction-level data with profit categorization

with stg as (
    select * from {{ ref('stg_retail_sales') }}
),

fact as (
    select
        row_id,
        order_id,
        order_date,
        ship_date,
        ship_mode,
        customer_id,
        customer_name,
        segment,
        country,
        city,
        state,
        postal_code,
        region,
        product_id,
        category,
        sub_category,
        product_name,
        sales,
        quantity,
        discount,
        profit,
        order_year,
        order_month,
        order_year_month,
        order_quarter,
        profit_margin_pct,
        is_profitable,
        case
            when profit >= 100 then 'High Profit'
            when profit >= 20 and profit < 100 then 'Moderate Profit'
            when profit >= 0 and profit < 20 then 'Low Profit'
            else 'Loss'
        end as profit_tier
    from stg
)

select * from fact
