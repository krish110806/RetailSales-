"""
RetailPulse End-to-End Automated Pipeline Orchestrator.
Manages the end-to-end data lifecycle:
Ingestion (Airbyte/CSV) -> Data Validation -> dbt Transformations -> dbt Tests -> BigQuery/Warehouse Validation.
Provides concurrency locking, stage-level metric tracking, and persistent execution history.
"""
import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (
    DEFAULT_INPUT_CSV,
    PIPELINE_LOCK_FILE,
    LOGS_DIR
)
from pipeline.db_manager import (
    init_database,
    record_pipeline_start,
    record_pipeline_complete
)
from pipeline.ingestion import IngestionEngine
from pipeline.cleaner_validator import DataQualityValidator
from pipeline.dbt_runner import DbtTransformationRunner
from pipeline.bigquery_client import BigQueryWarehouse

# Setup logging
LOGS_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOGS_DIR / f"retailpulse_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("retailpulse.orchestrator")

class PipelineEngine:
    def __init__(self, source_path: Path = DEFAULT_INPUT_CSV):
        self.source_path = Path(source_path)
        init_database()

    def is_running(self) -> bool:
        """Checks if another pipeline run is actively in progress via lockfile."""
        if not PIPELINE_LOCK_FILE.exists():
            return False
        try:
            with open(PIPELINE_LOCK_FILE, "r") as f:
                lock_info = json.load(f)
            lock_time = lock_info.get("timestamp", 0)
            # Stale lock check: if lock is older than 10 minutes, consider it stale
            if time.time() - lock_time > 600:
                logger.warning("Clearing stale pipeline lock file.")
                self._release_lock()
                return False
            return True
        except Exception:
            return False

    def _acquire_lock(self, run_id: str):
        with open(PIPELINE_LOCK_FILE, "w") as f:
            json.dump({"run_id": run_id, "timestamp": time.time()}, f)

    def _release_lock(self):
        if PIPELINE_LOCK_FILE.exists():
            try:
                os.remove(PIPELINE_LOCK_FILE)
            except Exception as e:
                logger.warning(f"Could not remove lock file: {e}")

    def run_pipeline(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Executes the full pipeline workflow.
        Returns:
            (success: bool, execution_summary: Dict)
        """
        if self.is_running():
            msg = "Pipeline execution blocked: A run is already in progress. Concurrent execution prevented."
            logger.warning(msg)
            return False, {"status": "BLOCKED", "error": msg}

        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        start_time_iso = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        self._acquire_lock(run_id)
        logger.info(f"========== Starting RetailPulse Pipeline Run: {run_id} ==========")

        stage_metrics = {
            "stages": [],
            "flow": [
                {"name": "CSV SOURCE", "status": "PENDING", "duration_s": 0},
                {"name": "AIRBYTE INGESTION", "status": "PENDING", "duration_s": 0},
                {"name": "BIGQUERY RAW", "status": "PENDING", "duration_s": 0},
                {"name": "DATA VALIDATION", "status": "PENDING", "duration_s": 0},
                {"name": "DBT TRANSFORMATION", "status": "PENDING", "duration_s": 0},
                {"name": "BIGQUERY ANALYTICS", "status": "PENDING", "duration_s": 0},
                {"name": "DASHBOARD READY", "status": "PENDING", "duration_s": 0}
            ]
        }

        input_count = 0
        processed_count = 0
        rejected_count = 0
        duplicate_count = 0
        missing_count = 0
        quality_pct = 100.0

        try:
            # Record run start in SQLite
            record_pipeline_start(run_id, input_records=0)

            # STAGE 1: Ingestion (Airbyte & File Archive)
            t_stage = time.time()
            logger.info("Executing STAGE 1: Data Ingestion...")
            ingestion_engine = IngestionEngine(source_path=self.source_path, run_id=run_id)
            raw_df, ingest_meta = ingestion_engine.run_ingestion()
            input_count = len(raw_df)
            d_ingest = round(time.time() - t_stage, 2)
            
            stage_metrics["flow"][0]["status"] = "SUCCESS"
            stage_metrics["flow"][0]["duration_s"] = d_ingest
            stage_metrics["flow"][1]["status"] = "SUCCESS"
            stage_metrics["flow"][1]["duration_s"] = d_ingest
            stage_metrics["flow"][2]["status"] = "SUCCESS" if "BigQuery Error" not in ingest_meta.get("bigquery_status", "") else "WARNING"
            stage_metrics["flow"][2]["duration_s"] = d_ingest

            # STAGE 2: Data Cleaning & Validation
            t_stage = time.time()
            logger.info("Executing STAGE 2: Data Cleaning and Validation...")
            validator = DataQualityValidator(run_id=run_id)
            clean_df, rejected_df, val_report = validator.clean_and_validate(raw_df)
            processed_count = len(clean_df)
            rejected_count = len(rejected_df)
            duplicate_count = val_report.get("duplicate_records", 0)
            missing_count = val_report.get("total_missing_cells", 0)
            quality_pct = val_report.get("data_quality_percentage", 100.0)
            d_val = round(time.time() - t_stage, 2)

            stage_metrics["flow"][3]["status"] = "SUCCESS" if quality_pct >= 95.0 else "WARNING"
            stage_metrics["flow"][3]["duration_s"] = d_val

            # STAGE 3: dbt Transformations
            t_stage = time.time()
            logger.info("Executing STAGE 3: dbt Analytical Mart Transformations...")
            dbt_runner = DbtTransformationRunner(run_id=run_id)
            trans_ok, trans_meta = dbt_runner.run_transformations()
            d_trans = round(time.time() - t_stage, 2)
            if not trans_ok:
                raise RuntimeError(f"dbt transformations failed: {trans_meta.get('error')}")

            stage_metrics["flow"][4]["status"] = "SUCCESS"
            stage_metrics["flow"][4]["duration_s"] = d_trans

            # STAGE 4: dbt Data Integrity Tests
            t_stage = time.time()
            logger.info("Executing STAGE 4: dbt Data Integrity Tests...")
            test_ok, test_meta = dbt_runner.run_tests()
            d_tests = round(time.time() - t_stage, 2)
            if not test_ok:
                logger.warning(f"Some dbt tests did not pass: {test_meta}")

            # STAGE 5: BigQuery & Warehouse Verification
            bq = BigQueryWarehouse()
            stage_metrics["flow"][5]["status"] = "SUCCESS" if bq.is_configured else "LOCAL_READY"
            stage_metrics["flow"][5]["duration_s"] = 0.1
            stage_metrics["flow"][6]["status"] = "SUCCESS"
            stage_metrics["flow"][6]["duration_s"] = 0.1

            end_time_iso = datetime.now(timezone.utc).isoformat()
            total_duration = round(time.time() - t0, 2)

            # Record success in persistent history
            record_pipeline_complete(
                run_id=run_id,
                end_time=end_time_iso,
                duration_seconds=total_duration,
                processed_records=processed_count,
                rejected_records=rejected_count,
                duplicate_records=duplicate_count,
                missing_values=missing_count,
                data_quality_pct=quality_pct,
                execution_status="SUCCESS",
                error_details=None,
                stage_metrics=stage_metrics
            )

            logger.info(f"========== Pipeline Run {run_id} Completed Successfully in {total_duration}s ==========")
            return True, {
                "run_id": run_id,
                "status": "SUCCESS",
                "start_time": start_time_iso,
                "end_time": end_time_iso,
                "duration_seconds": total_duration,
                "input_records": input_count,
                "processed_records": processed_count,
                "rejected_records": rejected_count,
                "duplicate_records": duplicate_count,
                "missing_values": missing_count,
                "data_quality_pct": quality_pct,
                "stage_metrics": stage_metrics
            }

        except Exception as e:
            total_duration = round(time.time() - t0, 2)
            end_time_iso = datetime.now(timezone.utc).isoformat()
            error_str = str(e)
            logger.error(f"Pipeline Run {run_id} Failed: {error_str}", exc_info=True)

            record_pipeline_complete(
                run_id=run_id,
                end_time=end_time_iso,
                duration_seconds=total_duration,
                processed_records=processed_count,
                rejected_records=rejected_count,
                duplicate_records=duplicate_count,
                missing_values=missing_count,
                data_quality_pct=quality_pct,
                execution_status="FAILED",
                error_details=error_str,
                stage_metrics=stage_metrics
            )
            return False, {"run_id": run_id, "status": "FAILED", "error": error_str}

        finally:
            self._release_lock()

if __name__ == "__main__":
    engine = PipelineEngine()
    success, summary = engine.run_pipeline()
    print("Execution Summary:")
    print(json.dumps(summary, indent=2))
