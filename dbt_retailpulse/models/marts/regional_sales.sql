-- regional_sales.sql
-- Geographic and regional aggregation for spatial analytics

with fact as (
    select * from {{ ref('fct_sales') }}
),

regional_summary as (
    select
        region,
        state,
        country,
        count(distinct order_id) as total_orders,
        count(distinct customer_id) as unique_customers,
        sum(quantity) as total_units_sold,
        round(sum(sales), 2) as total_revenue,
        round(sum(profit), 2) as total_profit,
        round(sum(sales) / count(distinct order_id), 2) as avg_order_value,
        case
            when sum(sales) > 0 then round((sum(profit) / sum(sales)) * 100.0, 2)
            else 0.0
        end as profit_margin_pct,
        round(avg(discount), 4) as avg_discount
    from fact
    group by 1, 2, 3
)

select * from regional_summary
order by total_revenue desc
