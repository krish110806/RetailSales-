"""
Unit & Integration Test Suite for RetailPulse.
Validates the data cleaning engine, dbt transformation logic,
data integrity constraints, conversational BI queries, and persistent history.
"""
import os
import sys
import unittest
import pandas as pd
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_INPUT_CSV
from pipeline.cleaner_validator import DataQualityValidator
from pipeline.dbt_runner import DbtTransformationRunner
from pipeline.pipeline_engine import PipelineEngine
from pipeline.db_manager import execute_query, get_latest_execution
from dashboard.utils.bi_query_engine import ask_business_intelligence

class TestRetailPulsePipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Run the pipeline once to populate tables for testing."""
        cls.engine = PipelineEngine(source_path=DEFAULT_INPUT_CSV)
        cls.success, cls.summary = cls.engine.run_pipeline()

    def test_pipeline_execution_succeeded(self):
        """Verify pipeline executes without exceptions."""
        self.assertTrue(self.success, "Pipeline execution failed.")
        self.assertEqual(self.summary.get("status"), "SUCCESS")

    def test_data_cleaning_and_validation(self):
        """Verify data cleaning identifies valid and rejected records accurately."""
        df_raw = pd.read_csv(DEFAULT_INPUT_CSV)
        validator = DataQualityValidator()
        clean_df, rejected_df, report = validator.clean_and_validate(df_raw)

        self.assertGreater(len(clean_df), 0, "Cleaned dataset should not be empty.")
        self.assertEqual(len(clean_df) + len(rejected_df), len(df_raw), "Sum of clean and rejected must equal total input.")
        self.assertGreaterEqual(report["data_quality_percentage"], 95.0, "Quality score should exceed 95%.")
        self.assertIn("rejection_reasons_breakdown", report)

    def test_dbt_models_populated(self):
        """Verify that all core dbt analytical tables have data."""
        tables = ["fct_sales", "monthly_sales", "product_performance", "regional_sales"]
        for tbl in tables:
            df = execute_query(f"SELECT COUNT(*) AS cnt FROM {tbl}")
            count = df.iloc[0]["cnt"]
            self.assertGreater(count, 0, f"Table {tbl} must not be empty.")

    def test_dbt_integrity_tests(self):
        """Verify dbt data constraints: positive sales, positive quantity, unique row IDs."""
        runner = DbtTransformationRunner()
        passed, results = runner.run_tests()
        self.assertTrue(passed, f"dbt tests failed: {results}")

    def test_conversational_bi_engine(self):
        """Verify conversational BI maps questions to valid SQL and produces non-empty responses."""
        res = ask_business_intelligence("Which product generated the highest revenue?")
        self.assertIsNotNone(res)
        self.assertIn("answer", res)
        self.assertIn("sql", res)
        self.assertFalse(res["data"].empty, "BI query should return records.")

        res_reg = ask_business_intelligence("Which region has the highest sales?")
        self.assertIn("sales", res_reg["sql"].lower())

    def test_persistent_execution_history(self):
        """Verify execution history is stored in SQLite."""
        latest = get_latest_execution()
        self.assertIsNotNone(latest, "Execution history record must exist.")
        self.assertEqual(latest["execution_status"], "SUCCESS")
        self.assertGreater(latest["processed_records"], 0)

if __name__ == "__main__":
    unittest.main()
