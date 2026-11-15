-- assert_positive_quantity.sql
-- dbt singular test: returns any record with non-positive quantity
select
    row_id,
    quantity
from {{ ref('fct_sales') }}
where quantity <= 0
