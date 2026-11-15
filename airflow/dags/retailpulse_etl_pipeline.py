"""
Apache Airflow DAG: retailpulse_etl_pipeline
Orchestrates the end-to-end RetailPulse ELT pipeline:
Start -> Airbyte Sync -> Data Validation -> dbt Run -> dbt Test -> BigQuery Validation -> End.
"""
from datetime import datetime, timedelta
import logging
import os
import sys

# Airflow imports
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.empty import EmptyOperator
except ImportError:
    # Graceful fallback mock for local environments without Airflow installed
    class DAG:
        def __init__(self, *args, **kwargs):
            self.dag_id = kwargs.get('dag_id', args[0] if args else 'dag')
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class PythonOperator:
        def __init__(self, task_id, python_callable, **kwargs):
            self.task_id = task_id
            self.python_callable = python_callable
        def __rshift__(self, other): return other
    class EmptyOperator:
        def __init__(self, task_id, **kwargs):
            self.task_id = task_id
        def __rshift__(self, other): return other

# Add workspace path to sys.path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

logger = logging.getLogger("airflow.retailpulse")

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'execution_timeout': timedelta(minutes=15)
}

def run_airbyte_sync(**context):
    """Executes Airbyte file ingestion or idempotent snapshot loading."""
    from pipeline.ingestion import IngestionEngine
    logger.info("Executing Airbyte Sync Task...")
    engine = IngestionEngine()
    df, meta = engine.run_ingestion()
    logger.info(f"Airbyte Ingestion Completed: {meta.get('record_count')} records ingested.")
    return meta

def run_data_validation(**context):
    """Runs data cleaning, validation checks, and generates quality report."""
    from pipeline.cleaner_validator import DataQualityValidator
    from pipeline.db_manager import execute_query
    logger.info("Executing Data Validation Task...")
    raw_df = execute_query("SELECT * FROM raw_data")
    validator = DataQualityValidator()
    clean_df, rejected_df, report = validator.clean_and_validate(raw_df)
    logger.info(f"Validation Score: {report.get('data_quality_percentage')}% | Clean: {len(clean_df)} | Rejected: {len(rejected_df)}")
    if report.get("data_quality_percentage", 0) < 80.0:
        raise ValueError(f"Data Quality Gate Failed: Score {report.get('data_quality_percentage')}% is below threshold.")
    return report

def run_dbt_transformations(**context):
    """Executes dbt staging and mart transformations."""
    from pipeline.dbt_runner import DbtTransformationRunner
    logger.info("Executing dbt Transformation Run...")
    runner = DbtTransformationRunner()
    success, res = runner.run_transformations()
    if not success:
        raise RuntimeError(f"dbt run failed: {res.get('error')}")
    logger.info(f"dbt Models Built: {res.get('models_built')}")
    return res

def run_dbt_tests(**context):
    """Executes dbt integrity tests."""
    from pipeline.dbt_runner import DbtTransformationRunner
    logger.info("Executing dbt Test Suite...")
    runner = DbtTransformationRunner()
    passed, res = runner.run_tests()
    if not passed:
        raise AssertionError(f"dbt Test Suite Violations Detected: {res}")
    logger.info("All dbt tests passed successfully.")
    return res

def run_bigquery_validation(**context):
    """Verifies that analytics tables in the warehouse have valid non-empty records."""
    from pipeline.db_manager import execute_query
    from pipeline.bigquery_client import BigQueryWarehouse
    logger.info("Validating BigQuery / Warehouse Tables...")
    for table in ["fct_sales", "monthly_sales", "product_performance", "regional_sales"]:
        count_df = execute_query(f"SELECT COUNT(*) AS cnt FROM {table}")
        count = count_df.iloc[0]["cnt"]
        if count == 0:
            raise ValueError(f"Warehouse validation failed: table '{table}' is empty.")
        logger.info(f"Verified warehouse table '{table}' has {count} rows.")
    
    bq = BigQueryWarehouse()
    status = bq.get_status()
    logger.info(f"Cloud Warehouse Status: {status['mode']}")
    return {"status": "SUCCESS", "cloud_mode": status['mode']}

with DAG(
    dag_id='retailpulse_etl_pipeline',
    default_args=default_args,
    description='Automated RetailPulse ETL Pipeline: Airbyte -> Validation -> dbt -> BigQuery',
    schedule_interval='@daily',
    catchup=False,
    tags=['retailpulse', 'etl', 'dbt', 'airbyte', 'bigquery']
) as dag:

    start_task = EmptyOperator(task_id='start')

    airbyte_sync_task = PythonOperator(
        task_id='airbyte_sync',
        python_callable=run_airbyte_sync,
        provide_context=True
    )

    data_validation_task = PythonOperator(
        task_id='data_validation',
        python_callable=run_data_validation,
        provide_context=True
    )

    dbt_run_task = PythonOperator(
        task_id='dbt_run',
        python_callable=run_dbt_transformations,
        provide_context=True
    )

    dbt_test_task = PythonOperator(
        task_id='dbt_test',
        python_callable=run_dbt_tests,
        provide_context=True
    )

    bigquery_validation_task = PythonOperator(
        task_id='bigquery_validation',
        python_callable=run_bigquery_validation,
        provide_context=True
    )

    end_task = EmptyOperator(task_id='end')

    # Define Workflow Pipeline Dependencies
    start_task >> airbyte_sync_task >> data_validation_task >> dbt_run_task >> dbt_test_task >> bigquery_validation_task >> end_task
