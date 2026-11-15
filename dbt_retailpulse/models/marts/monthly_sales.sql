-- monthly_sales.sql
-- Monthly aggregated sales, order volume, revenue and profit metrics

with fact as (
    select * from {{ ref('fct_sales') }}
),

monthly_aggregates as (
    select
        order_year,
        order_month,
        order_year_month,
        count(distinct order_id) as total_orders,
        count(row_id) as total_line_items,
        round(sum(sales), 2) as total_revenue,
        round(sum(profit), 2) as total_profit,
        sum(quantity) as total_quantity_sold,
        round(sum(sales) / count(distinct order_id), 2) as avg_order_value,
        round((sum(profit) / sum(sales)) * 100.0, 2) as profit_margin_pct,
        round(avg(discount), 4) as avg_discount,
        sum(is_profitable) as profitable_lines_count
    from fact
    group by 1, 2, 3
)

select * from monthly_aggregates
order by order_year_month asc
