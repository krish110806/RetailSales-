"""
Google BigQuery Client module for RetailPulse.
Manages connections, datasets ('raw_data' and 'analytics'), table creation,
and data syncs. Handles missing credentials transparently without faking syncs.
"""
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import logging
from typing import Optional, Dict, Any, Tuple
import pandas as pd

from config import (
    GCP_PROJECT_ID,
    BIGQUERY_DATASET_RAW,
    BIGQUERY_DATASET_ANALYTICS,
    GOOGLE_APPLICATION_CREDENTIALS
)

logger = logging.getLogger("retailpulse.bigquery")

class BigQueryWarehouse:
    def __init__(self):
        self.project_id = GCP_PROJECT_ID or os.getenv("GCP_PROJECT_ID")
        self.raw_dataset = BIGQUERY_DATASET_RAW
        self.analytics_dataset = BIGQUERY_DATASET_ANALYTICS
        self.credentials_path = GOOGLE_APPLICATION_CREDENTIALS or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self._client = None
        self._is_configured = False
        self._init_client()

    def _init_client(self):
        """Initializes the BigQuery client if credentials and project are provided."""
        if not self.project_id:
            logger.info("BigQuery: GCP_PROJECT_ID not set. Running in Local Persistent Warehouse mode.")
            self._is_configured = False
            return

        if self.credentials_path and not os.path.exists(self.credentials_path):
            logger.warning(f"BigQuery credentials file not found at: {self.credentials_path}")
            self._is_configured = False
            return

        try:
            from google.cloud import bigquery
            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
            self._client = bigquery.Client(project=self.project_id)
            self._is_configured = True
            logger.info(f"BigQuery: Successfully authenticated with GCP project '{self.project_id}'.")
        except ImportError:
            logger.info("google-cloud-bigquery package not installed. Local SQLite warehouse active.")
            self._is_configured = False
        except Exception as e:
            logger.warning(f"BigQuery connection failed: {e}. Falling back to local warehouse.")
            self._is_configured = False

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def get_status(self) -> Dict[str, Any]:
        """Returns the current connection and configuration status."""
        return {
            "is_configured": self._is_configured,
            "project_id": self.project_id if self.project_id else "Not Set",
            "raw_dataset": self.raw_dataset,
            "analytics_dataset": self.analytics_dataset,
            "credentials_present": bool(self.credentials_path and os.path.exists(self.credentials_path)),
            "mode": "Live Google BigQuery" if self._is_configured else "Local Persistent SQLite Warehouse (BigQuery Ready)"
        }

    def ensure_datasets(self) -> Tuple[bool, str]:
        """Creates 'raw_data' and 'analytics' datasets in BigQuery if not present."""
        if not self._is_configured:
            return False, "BigQuery not configured. Skipping cloud dataset creation."
        
        from google.cloud import bigquery
        try:
            for ds_name in [self.raw_dataset, self.analytics_dataset]:
                dataset_id = f"{self.project_id}.{ds_name}"
                dataset = bigquery.Dataset(dataset_id)
                dataset.location = "US"
                self._client.create_dataset(dataset, exists_ok=True)
                logger.info(f"Verified BigQuery dataset: {dataset_id}")
            return True, "BigQuery datasets verified."
        except Exception as e:
            logger.error(f"Error creating BigQuery datasets: {e}")
            return False, str(e)

    def upload_dataframe(self, df: pd.DataFrame, dataset: str, table_name: str, if_exists: str = "replace") -> Tuple[bool, str]:
        """Uploads a pandas DataFrame to a BigQuery table."""
        if not self._is_configured:
            return False, "BigQuery not configured. Data safely persisted in local warehouse."

        from google.cloud import bigquery
        try:
            table_id = f"{self.project_id}.{dataset}.{table_name}"
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE if if_exists == "replace" else bigquery.WriteDisposition.WRITE_APPEND
            )
            job = self._client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for completion
            logger.info(f"Loaded {len(df)} rows into BigQuery table: {table_id}")
            return True, f"Loaded {len(df)} rows into {table_id}"
        except Exception as e:
            logger.error(f"Failed to load table {table_name} into BigQuery: {e}")
            return False, str(e)
