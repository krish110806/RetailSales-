"""
Configuration module for RetailPulse.
Loads environment variables and defines paths, database settings, and UI themes.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REJECTED_DATA_DIR = DATA_DIR / "rejected"
ARCHIVE_DATA_DIR = DATA_DIR / "archive"
REPORTS_DATA_DIR = DATA_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
for path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, REJECTED_DATA_DIR, ARCHIVE_DATA_DIR, REPORTS_DATA_DIR, LOGS_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Dataset Files
ORIGINAL_CSV_PATH = RAW_DATA_DIR / "Sample-Superstore.csv"
SAMPLE_CSV_PATH = RAW_DATA_DIR / "superstore_sample_1000.csv"
DEFAULT_INPUT_CSV = SAMPLE_CSV_PATH if SAMPLE_CSV_PATH.exists() else ORIGINAL_CSV_PATH

# SQLite Database
SQLITE_DB_PATH = DATA_DIR / "retailpulse.db"

# BigQuery Settings (configured via environment variables)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
BIGQUERY_DATASET_RAW = os.getenv("BIGQUERY_DATASET_RAW", "raw_data")
BIGQUERY_DATASET_ANALYTICS = os.getenv("BIGQUERY_DATASET_ANALYTICS", "analytics")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Airbyte Settings
AIRBYTE_SERVER_URL = os.getenv("AIRBYTE_SERVER_URL", "http://localhost:8000")
AIRBYTE_WORKSPACE_ID = os.getenv("AIRBYTE_WORKSPACE_ID", "")
AIRBYTE_API_KEY = os.getenv("AIRBYTE_API_KEY", "")

# Pipeline Settings
MAX_SAMPLE_RECORDS = int(os.getenv("MAX_SAMPLE_RECORDS", "1000"))
PIPELINE_LOCK_FILE = DATA_DIR / ".pipeline_lock"

# Theme & Palette Constants
THEME_COLORS = {
    "background": "#F7F5EF",
    "sidebar": "#142B3B",
    "primary": "#287D6B",
    "secondary": "#C6A568",
    "cards": "#FFFEFA",
    "text": "#263746",
    "text_muted": "#6E7A8A",
    "border": "#E5E2D9",
    "danger": "#D9534F",
    "success": "#287D6B",
    "warning": "#C6A568",
    "info": "#20638F"
}
