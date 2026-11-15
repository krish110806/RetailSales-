-- product_performance.sql
-- Product and category dimensional analytics with revenue and margin metrics

with fact as (
    select * from {{ ref('fct_sales') }}
),

product_summary as (
    select
        product_id,
        product_name,
        category,
        sub_category,
        count(distinct order_id) as total_orders,
        sum(quantity) as total_units_sold,
        round(sum(sales), 2) as total_revenue,
        round(sum(profit), 2) as total_profit,
        case 
            when sum(sales) > 0 then round((sum(profit) / sum(sales)) * 100.0, 2)
            else 0.0
        end as profit_margin_pct,
        round(avg(discount), 4) as avg_discount
    from fact
    group by 1, 2, 3, 4
)

select 
    *,
    dense_rank() over (order by total_revenue desc) as revenue_rank
from product_summary
order by total_revenue desc
