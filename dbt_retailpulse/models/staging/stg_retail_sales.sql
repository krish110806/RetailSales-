-- stg_retail_sales.sql
-- Staging model: standardizes names, types, and computes derived temporal and margin metrics

with source as (
    select
        cast(Row_ID as integer) as row_id,
        cast(Order_ID as string) as order_id,
        cast(Order_Date as string) as order_date,
        cast(Ship_Date as string) as ship_date,
        trim(cast(Ship_Mode as string)) as ship_mode,
        cast(Customer_ID as string) as customer_id,
        trim(cast(Customer_Name as string)) as customer_name,
        trim(cast(Segment as string)) as segment,
        trim(cast(Country as string)) as country,
        trim(cast(City as string)) as city,
        trim(cast(State as string)) as state,
        coalesce(cast(Postal_Code as string), '00000') as postal_code,
        trim(cast(Region as string)) as region,
        cast(Product_ID as string) as product_id,
        trim(cast(Category as string)) as category,
        trim(cast(Sub_Category as string)) as sub_category,
        trim(cast(Product_Name as string)) as product_name,
        round(cast(Sales as real), 2) as sales,
        cast(Quantity as integer) as quantity,
        round(cast(Discount as real), 4) as discount,
        round(cast(Profit as real), 4) as profit
    from {{ source('raw_data', 'superstore_raw') }}
    where Sales is not null 
      and Quantity is not null
      and Sales > 0
      and Quantity > 0
),

transformed as (
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
        -- Note: Sales is already line-item revenue. Do NOT multiply by quantity.
        sales,
        quantity,
        discount,
        profit,
        substr(order_date, 1, 4) as order_year,
        substr(order_date, 6, 2) as order_month,
        substr(order_date, 1, 7) as order_year_month,
        case 
            when substr(order_date, 6, 2) in ('01', '02', '03') then 'Q1'
            when substr(order_date, 6, 2) in ('04', '05', '06') then 'Q2'
            when substr(order_date, 6, 2) in ('07', '08', '09') then 'Q3'
            else 'Q4'
        end as order_quarter,
        case 
            when sales > 0 then round((profit / sales) * 100.0, 2)
            else 0.0
        end as profit_margin_pct,
        case 
            when profit > 0 then 1 
            else 0 
        end as is_profitable
    from source
)

select * from transformed
