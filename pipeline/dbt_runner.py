"""
dbt Transformation and Test Runner for RetailPulse.
Executes the staging and analytical mart SQL models and validates
schema/integrity tests against the SQLite and BigQuery warehouses.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pipeline.db_manager import get_connection, execute_query
from pipeline.bigquery_client import BigQueryWarehouse

logger = logging.getLogger("retailpulse.dbt_runner")

class DbtTransformationRunner:
    def __init__(self, run_id: str = None):
        self.run_id = run_id
        self.bq = BigQueryWarehouse()

    def run_transformations(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes the staging and dimensional mart transformations.
        Creates:
          1. stg_retail_sales (view)
          2. fct_sales (table)
          3. monthly_sales (table)
          4. product_performance (table)
          5. regional_sales (table)
        """
        logger.info("Executing RetailPulse SQL transformations (dbt equivalent)...")
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # 1. Staging View: stg_retail_sales
            cursor.execute("DROP VIEW IF EXISTS stg_retail_sales;")
            cursor.execute("""
            CREATE VIEW stg_retail_sales AS
            SELECT
                CAST(Row_ID AS INTEGER) AS row_id,
                CAST(Order_ID AS TEXT) AS order_id,
                CAST(Order_Date AS TEXT) AS order_date,
                CAST(Ship_Date AS TEXT) AS ship_date,
                TRIM(CAST(Ship_Mode AS TEXT)) AS ship_mode,
                CAST(Customer_ID AS TEXT) AS customer_id,
                TRIM(CAST(Customer_Name AS TEXT)) AS customer_name,
                TRIM(CAST(Segment AS TEXT)) AS segment,
                TRIM(CAST(Country AS TEXT)) AS country,
                TRIM(CAST(City AS TEXT)) AS city,
                TRIM(CAST(State AS TEXT)) AS state,
                COALESCE(CAST(Postal_Code AS TEXT), '00000') AS postal_code,
                TRIM(CAST(Region AS TEXT)) AS region,
                CAST(Product_ID AS TEXT) AS product_id,
                TRIM(CAST(Category AS TEXT)) AS category,
                TRIM(CAST(Sub_Category AS TEXT)) AS sub_category,
                TRIM(CAST(Product_Name AS TEXT)) AS product_name,
                ROUND(CAST(Sales AS REAL), 2) AS sales,
                CAST(Quantity AS INTEGER) AS quantity,
                ROUND(CAST(Discount AS REAL), 4) AS discount,
                ROUND(CAST(Profit AS REAL), 4) AS profit,
                SUBSTR(Order_Date, 1, 4) AS order_year,
                SUBSTR(Order_Date, 6, 2) AS order_month,
                SUBSTR(Order_Date, 1, 7) AS order_year_month,
                CASE 
                    WHEN SUBSTR(Order_Date, 6, 2) IN ('01', '02', '03') THEN 'Q1'
                    WHEN SUBSTR(Order_Date, 6, 2) IN ('04', '05', '06') THEN 'Q2'
                    WHEN SUBSTR(Order_Date, 6, 2) IN ('07', '08', '09') THEN 'Q3'
                    ELSE 'Q4'
                END AS order_quarter,
                CASE 
                    WHEN CAST(Sales AS REAL) > 0 THEN ROUND((CAST(Profit AS REAL) / CAST(Sales AS REAL)) * 100.0, 2)
                    ELSE 0.0
                END AS profit_margin_pct,
                CASE 
                    WHEN CAST(Profit AS REAL) > 0 THEN 1 
                    ELSE 0 
                END AS is_profitable
            FROM raw_data
            WHERE Sales IS NOT NULL 
              AND Quantity IS NOT NULL
              AND Sales > 0
              AND Quantity > 0;
            """)

            # 2. Fact Table: fct_sales
            cursor.execute("DROP TABLE IF EXISTS fct_sales;")
            cursor.execute("""
            CREATE TABLE fct_sales AS
            SELECT
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
                CASE
                    WHEN profit >= 100 THEN 'High Profit'
                    WHEN profit >= 20 AND profit < 100 THEN 'Moderate Profit'
                    WHEN profit >= 0 AND profit < 20 THEN 'Low Profit'
                    ELSE 'Loss'
                END AS profit_tier
            FROM stg_retail_sales;
            """)

            # 3. Monthly Sales Mart: monthly_sales
            cursor.execute("DROP TABLE IF EXISTS monthly_sales;")
            cursor.execute("""
            CREATE TABLE monthly_sales AS
            SELECT
                order_year,
                order_month,
                order_year_month,
                COUNT(DISTINCT order_id) AS total_orders,
                COUNT(row_id) AS total_line_items,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                SUM(quantity) AS total_quantity_sold,
                ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
                ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100.0, 2) AS profit_margin_pct,
                ROUND(AVG(discount), 4) AS avg_discount,
                SUM(is_profitable) AS profitable_lines_count
            FROM fct_sales
            GROUP BY order_year, order_month, order_year_month
            ORDER BY order_year_month ASC;
            """)

            # 4. Product Performance Mart: product_performance
            cursor.execute("DROP TABLE IF EXISTS product_performance;")
            cursor.execute("""
            CREATE TABLE product_performance AS
            SELECT
                product_id,
                product_name,
                category,
                sub_category,
                COUNT(DISTINCT order_id) AS total_orders,
                SUM(quantity) AS total_units_sold,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                CASE 
                    WHEN SUM(sales) > 0 THEN ROUND((SUM(profit) / SUM(sales)) * 100.0, 2)
                    ELSE 0.0
                END AS profit_margin_pct,
                ROUND(AVG(discount), 4) AS avg_discount,
                DENSE_RANK() OVER (ORDER BY SUM(sales) DESC) AS revenue_rank
            FROM fct_sales
            GROUP BY product_id, product_name, category, sub_category
            ORDER BY total_revenue DESC;
            """)

            # 5. Regional Sales Mart: regional_sales
            cursor.execute("DROP TABLE IF EXISTS regional_sales;")
            cursor.execute("""
            CREATE TABLE regional_sales AS
            SELECT
                region,
                state,
                country,
                COUNT(DISTINCT order_id) AS total_orders,
                COUNT(DISTINCT customer_id) AS unique_customers,
                SUM(quantity) AS total_units_sold,
                ROUND(SUM(sales), 2) AS total_revenue,
                ROUND(SUM(profit), 2) AS total_profit,
                ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
                CASE
                    WHEN SUM(sales) > 0 THEN ROUND((SUM(profit) / SUM(sales)) * 100.0, 2)
                    ELSE 0.0
                END AS profit_margin_pct,
                ROUND(AVG(discount), 4) AS avg_discount
            FROM fct_sales
            GROUP BY region, state, country
            ORDER BY total_revenue DESC;
            """)

            conn.commit()

            # Record row counts
            counts = {}
            for tbl in ["fct_sales", "monthly_sales", "product_performance", "regional_sales"]:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                counts[tbl] = cursor.fetchone()[0]

            logger.info(f"Transformations successful. Counts: {counts}")

            # Sync to BigQuery analytics dataset if configured
            if self.bq.is_configured:
                for tbl in ["fct_sales", "monthly_sales", "product_performance", "regional_sales"]:
                    df_mart = pd.read_sql_query(f"SELECT * FROM {tbl}", conn)
                    self.bq.upload_dataframe(df_mart, dataset=self.bq.analytics_dataset, table_name=tbl)

            return True, {
                "status": "SUCCESS",
                "models_built": ["stg_retail_sales", "fct_sales", "monthly_sales", "product_performance", "regional_sales"],
                "table_counts": counts
            }

        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            conn.rollback()
            return False, {"status": "FAILED", "error": str(e)}
        finally:
            conn.close()

    def run_tests(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes dbt integrity tests:
          - unique row_id in fct_sales
          - not_null row_id, sales, quantity in fct_sales
          - positive sales in fct_sales
          - positive quantity in fct_sales
          - non-empty monthly_sales, product_performance, regional_sales
        """
        logger.info("Running dbt data integrity tests...")
        test_results = {}
        all_passed = True

        tests = [
            ("fct_sales_row_id_unique", "SELECT row_id, COUNT(*) FROM fct_sales GROUP BY row_id HAVING COUNT(*) > 1"),
            ("fct_sales_not_null_critical", "SELECT COUNT(*) FROM fct_sales WHERE row_id IS NULL OR sales IS NULL OR quantity IS NULL"),
            ("assert_positive_sales", "SELECT COUNT(*) FROM fct_sales WHERE sales <= 0"),
            ("assert_positive_quantity", "SELECT COUNT(*) FROM fct_sales WHERE quantity <= 0"),
            ("monthly_sales_has_data", "SELECT COUNT(*) FROM monthly_sales"),
            ("product_performance_has_data", "SELECT COUNT(*) FROM product_performance"),
            ("regional_sales_has_data", "SELECT COUNT(*) FROM regional_sales")
        ]

        conn = get_connection()
        cursor = conn.cursor()
        try:
            for test_name, sql in tests:
                cursor.execute(sql)
                res = cursor.fetchall()
                if "has_data" in test_name:
                    count = res[0][0]
                    passed = (count > 0)
                    msg = f"Passed ({count} rows found)" if passed else "Failed (0 rows found)"
                else:
                    violations = len(res) if res else 0
                    if violations == 1 and isinstance(res[0][0], int):
                        violations = res[0][0]
                    passed = (violations == 0)
                    msg = "Passed (0 violations)" if passed else f"Failed ({violations} violations)"

                test_results[test_name] = {
                    "passed": passed,
                    "details": msg
                }
                if not passed:
                    all_passed = False

            return all_passed, {
                "overall_status": "PASSED" if all_passed else "FAILED",
                "tests_evaluated": len(tests),
                "test_results": test_results
            }
        finally:
            conn.close()

if __name__ == "__main__":
    runner = DbtTransformationRunner()
    ok, res = runner.run_transformations()
    print("Transformations Result:", res)
    ok_tests, test_res = runner.run_tests()
    print("Tests Result:", test_res)
