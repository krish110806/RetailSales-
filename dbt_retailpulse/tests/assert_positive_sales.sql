-- assert_positive_sales.sql
-- dbt singular test: returns any record with non-positive sales
select
    row_id,
    sales
from {{ ref('fct_sales') }}
where sales <= 0
