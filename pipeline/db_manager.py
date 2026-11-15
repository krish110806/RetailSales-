"""
Database Manager for RetailPulse.
Manages persistent local SQLite storage for raw ingestion, analytics marts,
and pipeline execution history.
"""
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import pandas as pd

from config import SQLITE_DB_PATH

logger = logging.getLogger("retailpulse.db_manager")

def get_connection(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    """Returns a connection to the SQLite warehouse database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: Path = SQLITE_DB_PATH) -> None:
    """Initializes tables for execution history, raw ingestion, and analytics."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Pipeline Execution History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_execution_history (
        run_id TEXT PRIMARY KEY,
        start_time TEXT NOT NULL,
        end_time TEXT,
        duration_seconds REAL,
        input_records INTEGER DEFAULT 0,
        processed_records INTEGER DEFAULT 0,
        rejected_records INTEGER DEFAULT 0,
        duplicate_records INTEGER DEFAULT 0,
        missing_values INTEGER DEFAULT 0,
        data_quality_pct REAL DEFAULT 100.0,
        execution_status TEXT NOT NULL,
        error_details TEXT,
        stage_metrics TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Ingestion Metadata Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_log (
        ingest_id TEXT PRIMARY KEY,
        source_file TEXT NOT NULL,
        file_hash TEXT,
        record_count INTEGER NOT NULL,
        ingested_at TEXT NOT NULL,
        target_table TEXT NOT NULL,
        status TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    logger.info("Initialized RetailPulse SQLite database tables.")

def record_pipeline_start(run_id: str, input_records: int) -> None:
    """Records the start of a pipeline run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pipeline_execution_history (
            run_id, start_time, input_records, execution_status
        ) VALUES (?, ?, ?, ?)
    """, (run_id, datetime.now(timezone.utc).isoformat(), input_records, "RUNNING"))
    conn.commit()
    conn.close()

def record_pipeline_complete(
    run_id: str,
    end_time: str,
    duration_seconds: float,
    processed_records: int,
    rejected_records: int,
    duplicate_records: int,
    missing_values: int,
    data_quality_pct: float,
    execution_status: str,
    error_details: Optional[str] = None,
    stage_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """Updates the pipeline execution record upon completion or failure."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE pipeline_execution_history SET
            end_time = ?,
            duration_seconds = ?,
            processed_records = ?,
            rejected_records = ?,
            duplicate_records = ?,
            missing_values = ?,
            data_quality_pct = ?,
            execution_status = ?,
            error_details = ?,
            stage_metrics = ?
        WHERE run_id = ?
    """, (
        end_time,
        duration_seconds,
        processed_records,
        rejected_records,
        duplicate_records,
        missing_values,
        data_quality_pct,
        execution_status,
        error_details,
        json.dumps(stage_metrics) if stage_metrics else None,
        run_id
    ))
    conn.commit()
    conn.close()

def get_latest_execution() -> Optional[Dict[str, Any]]:
    """Retrieves the most recent pipeline execution record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pipeline_execution_history 
        ORDER BY start_time DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_executions() -> List[Dict[str, Any]]:
    """Retrieves all historical pipeline runs ordered by time descending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pipeline_execution_history 
        ORDER BY start_time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def execute_query(query: str, params: tuple = ()) -> pd.DataFrame:
    """Executes a SQL query and returns a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialization verified.")
