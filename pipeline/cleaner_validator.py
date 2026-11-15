"""
Data Cleaning and Validation Engine for RetailPulse.
Validates retail sales records, detects real missing values, duplicates,
invalid dates and numeric anomalies. Generates cleaned records, rejected records
with specific rejection reasons, and persistent quality reports without double-counting.
"""
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from config import (
    PROCESSED_DATA_DIR,
    REJECTED_DATA_DIR,
    REPORTS_DATA_DIR
)

logger = logging.getLogger("retailpulse.validator")

# Critical columns required for transaction validity
CRITICAL_COLUMNS = [
    "Order ID", "Order Date", "Customer ID", "Sales", "Quantity", 
    "Product ID", "Category", "Region"
]

VALID_CATEGORIES = {"Furniture", "Office Supplies", "Technology"}
VALID_REGIONS = {"East", "West", "Central", "South"}
VALID_SEGMENTS = {"Consumer", "Corporate", "Home Office"}

class DataQualityValidator:
    def __init__(self, run_id: str = None):
        utc_now = datetime.now(timezone.utc)
        self.run_id = run_id or utc_now.strftime("%Y%m%d_%H%M%S")
        self.timestamp_str = utc_now.strftime("%Y%m%d_%H%M%S")

    def clean_and_validate(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Cleans and validates the raw DataFrame.
        Returns:
            clean_df: Cleaned and standardized DataFrame
            rejected_df: Rejected records with rejection reasons
            quality_report: Comprehensive quality metrics dictionary
        """
        total_input_records = len(df_raw)
        logger.info(f"Starting data validation on {total_input_records} input records.")

        # Compute initial missing values count across all columns
        missing_by_column = {col: int(df_raw[col].isnull().sum()) for col in df_raw.columns}
        total_missing_cells = sum(missing_by_column.values())

        # Track rejection reasons for each index (one primary reason to avoid double-counting)
        rejection_map = {}  # index -> list of reasons
        
        # 1. Duplicate Detection (Full row duplicates)
        duplicated_rows = df_raw.duplicated(keep="first")
        for idx in df_raw[duplicated_rows].index:
            rejection_map.setdefault(idx, []).append("Duplicate record (entire row matches previous transaction)")

        # 2. Critical Column Missing Value Check
        for col in CRITICAL_COLUMNS:
            if col in df_raw.columns:
                null_mask = df_raw[col].isnull()
                for idx in df_raw[null_mask].index:
                    if idx not in rejection_map:
                        rejection_map.setdefault(idx, []).append(f"Missing critical attribute '{col}'")

        # 3. Numeric Validation: Sales & Quantity
        # Parse Sales
        sales_numeric = pd.to_numeric(df_raw["Sales"], errors="coerce")
        for idx in df_raw[sales_numeric.isnull() & ~df_raw.index.isin(rejection_map)].index:
            rejection_map.setdefault(idx, []).append("Non-numeric or NaN Sales value")
        
        invalid_sales_mask = (sales_numeric <= 0) & sales_numeric.notnull()
        for idx in df_raw[invalid_sales_mask].index:
            if idx not in rejection_map:
                rejection_map.setdefault(idx, []).append(f"Invalid non-positive Sales amount ({sales_numeric.loc[idx]})")

        # Parse Quantity
        quantity_numeric = pd.to_numeric(df_raw["Quantity"], errors="coerce")
        for idx in df_raw[quantity_numeric.isnull() & ~df_raw.index.isin(rejection_map)].index:
            rejection_map.setdefault(idx, []).append("Non-numeric or NaN Quantity value")

        invalid_qty_mask = (quantity_numeric <= 0) & quantity_numeric.notnull()
        for idx in df_raw[invalid_qty_mask].index:
            if idx not in rejection_map:
                rejection_map.setdefault(idx, []).append(f"Invalid non-positive Quantity ({quantity_numeric.loc[idx]})")

        # Parse Discount
        if "Discount" in df_raw.columns:
            discount_numeric = pd.to_numeric(df_raw["Discount"], errors="coerce")
            invalid_discount_mask = ((discount_numeric < 0) | (discount_numeric > 1)) & discount_numeric.notnull()
            for idx in df_raw[invalid_discount_mask].index:
                if idx not in rejection_map:
                    rejection_map.setdefault(idx, []).append(f"Invalid Discount rate out of bounds [0, 1] ({discount_numeric.loc[idx]})")

        # 4. Date Validation & Logical Date Ordering
        parsed_order_date = pd.to_datetime(df_raw["Order Date"], errors="coerce")
        for idx in df_raw[parsed_order_date.isnull() & ~df_raw.index.isin(rejection_map)].index:
            rejection_map.setdefault(idx, []).append("Invalid or unparseable Order Date format")

        if "Ship Date" in df_raw.columns:
            parsed_ship_date = pd.to_datetime(df_raw["Ship Date"], errors="coerce")
            for idx in df_raw[parsed_ship_date.isnull() & ~df_raw.index.isin(rejection_map)].index:
                rejection_map.setdefault(idx, []).append("Invalid or unparseable Ship Date format")
            
            # Chronological consistency check: Ship Date must not be prior to Order Date
            chronology_mask = (parsed_ship_date < parsed_order_date) & parsed_ship_date.notnull() & parsed_order_date.notnull()
            for idx in df_raw[chronology_mask].index:
                if idx not in rejection_map:
                    rejection_map.setdefault(idx, []).append(f"Chronology anomaly: Ship Date precedes Order Date")

        # Split into Valid and Rejected indices
        rejected_indices = list(rejection_map.keys())
        valid_indices = [i for i in df_raw.index if i not in rejection_map]

        # Build Rejected DataFrame
        if rejected_indices:
            rejected_df = df_raw.loc[rejected_indices].copy()
            rejected_df["rejection_reason"] = ["; ".join(rejection_map[i]) for i in rejected_indices]
            rejected_df["rejected_at"] = datetime.now(timezone.utc).isoformat()
        else:
            rejected_df = pd.DataFrame(columns=list(df_raw.columns) + ["rejection_reason", "rejected_at"])

        # Build Clean DataFrame
        clean_df = df_raw.loc[valid_indices].copy()

        # Standardize cleaned data
        clean_df["Order Date"] = pd.to_datetime(clean_df["Order Date"]).dt.strftime("%Y-%m-%d")
        if "Ship Date" in clean_df.columns:
            clean_df["Ship Date"] = pd.to_datetime(clean_df["Ship Date"]).dt.strftime("%Y-%m-%d")
        
        clean_df["Sales"] = pd.to_numeric(clean_df["Sales"]).round(2)
        clean_df["Quantity"] = pd.to_numeric(clean_df["Quantity"]).astype(int)
        
        if "Discount" in clean_df.columns:
            clean_df["Discount"] = pd.to_numeric(clean_df["Discount"]).round(4)
        if "Profit" in clean_df.columns:
            clean_df["Profit"] = pd.to_numeric(clean_df["Profit"]).round(4)

        # Standardize strings (strip whitespace)
        for col in clean_df.columns:
            if clean_df[col].dtype == object or clean_df[col].dtype.name.startswith("string"):
                clean_df[col] = clean_df[col].astype(str).str.strip()

        # Fill non-critical missing Postal Code if any with "00000" or Unknown
        if "Postal Code" in clean_df.columns:
            clean_df["Postal Code"] = clean_df["Postal Code"].fillna("00000").astype(str).str.replace(".0", "", regex=False)

        # Compute Quality Statistics
        valid_count = len(clean_df)
        rejected_count = len(rejected_df)
        duplicate_count = int(duplicated_rows.sum())
        data_quality_pct = round((valid_count / total_input_records * 100), 2) if total_input_records > 0 else 0.0

        # Tally reason frequencies
        reason_counts = {}
        for reasons in rejection_map.values():
            for r in reasons:
                # Group by broad category
                cat = r.split("(")[0].strip()
                reason_counts[cat] = reason_counts.get(cat, 0) + 1

        quality_report = {
            "run_id": self.run_id,
            "validation_timestamp": self.timestamp_str,
            "input_records": total_input_records,
            "valid_records": valid_count,
            "rejected_records": rejected_count,
            "duplicate_records": duplicate_count,
            "total_missing_cells": total_missing_cells,
            "data_quality_percentage": data_quality_pct,
            "missing_by_column": missing_by_column,
            "rejection_reasons_breakdown": reason_counts,
            "status": "PASSED" if data_quality_pct >= 95.0 else "WARNING"
        }

        # Persist artifacts
        self._persist_artifacts(clean_df, rejected_df, quality_report)
        logger.info(f"Validation complete: {valid_count} valid, {rejected_count} rejected. Score: {data_quality_pct}%")

        return clean_df, rejected_df, quality_report

    def _persist_artifacts(self, clean_df: pd.DataFrame, rejected_df: pd.DataFrame, report: Dict[str, Any]):
        """Saves clean data, rejected records, and quality reports persistently."""
        # 1. Clean Data
        clean_snapshot = PROCESSED_DATA_DIR / f"cleaned_sales_{self.timestamp_str}.csv"
        clean_latest = PROCESSED_DATA_DIR / "latest_cleaned_sales.csv"
        clean_df.to_csv(clean_snapshot, index=False, encoding="utf-8")
        clean_df.to_csv(clean_latest, index=False, encoding="utf-8")

        # 2. Rejected Records
        rejected_snapshot = REJECTED_DATA_DIR / f"rejected_records_{self.timestamp_str}.csv"
        rejected_latest = REJECTED_DATA_DIR / "latest_rejected_records.csv"
        rejected_df.to_csv(rejected_snapshot, index=False, encoding="utf-8")
        rejected_df.to_csv(rejected_latest, index=False, encoding="utf-8")

        # 3. Quality Report
        report_snapshot = REPORTS_DATA_DIR / f"data_quality_report_{self.timestamp_str}.json"
        report_latest = REPORTS_DATA_DIR / "latest_quality_report.json"
        with open(report_snapshot, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        with open(report_latest, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

def validate_dataset(df_raw: pd.DataFrame, run_id: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    validator = DataQualityValidator(run_id=run_id)
    return validator.clean_and_validate(df_raw)

if __name__ == "__main__":
    from config import DEFAULT_INPUT_CSV
    print(f"Testing validator with {DEFAULT_INPUT_CSV}...")
    df = pd.read_csv(DEFAULT_INPUT_CSV)
    c, r, rep = validate_dataset(df)
    print("Report:", json.dumps(rep, indent=2))
