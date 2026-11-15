"""
Data Profiling & Sampling Script for RetailPulse.
Preserves the original Sample-Superstore.csv, generates a representative 1,000-record sample,
and produces a comprehensive data profiling report.
"""
import os
import json
import pandas as pd
import numpy as np

def generate_profile_and_sample(
    raw_path="data/raw/Sample-Superstore.csv",
    sample_path="data/raw/superstore_sample_1000.csv",
    report_json="data/reports/data_profiling_report.json",
    report_md="data/reports/data_profiling_report.md",
    sample_size=1000,
    random_state=42
):
    print(f"Reading original raw dataset from: {raw_path}")
    df_raw = pd.read_csv(raw_path, encoding="utf-8")
    total_raw_rows = len(df_raw)
    
    # Analyze raw dataset
    column_profiles = {}
    for col in df_raw.columns:
        null_count = int(df_raw[col].isnull().sum())
        dtype_str = str(df_raw[col].dtype)
        unique_vals = int(df_raw[col].nunique(dropna=True))
        
        sample_vals = [str(x) for x in df_raw[col].dropna().head(3).tolist()]
        
        col_prof = {
            "dtype": dtype_str,
            "null_count": null_count,
            "null_percentage": round((null_count / total_raw_rows) * 100, 3),
            "unique_count": unique_vals,
            "samples": sample_vals
        }
        
        if pd.api.types.is_numeric_dtype(df_raw[col]):
            clean_series = df_raw[col].dropna()
            if len(clean_series) > 0:
                col_prof["min"] = float(clean_series.min())
                col_prof["max"] = float(clean_series.max())
                col_prof["mean"] = float(round(clean_series.mean(), 2))
                col_prof["median"] = float(round(clean_series.median(), 2))
                col_prof["negative_count"] = int((clean_series < 0).sum())
                col_prof["zero_count"] = int((clean_series == 0).sum())
                
        column_profiles[col] = col_prof

    # Identify date columns
    date_cols = ["Order Date", "Ship Date"]
    date_profiles = {}
    for dc in date_cols:
        if dc in df_raw.columns:
            parsed = pd.to_datetime(df_raw[dc], errors='coerce')
            invalid_count = int(parsed.isnull().sum())
            min_date = str(parsed.min()) if parsed.notnull().any() else None
            max_date = str(parsed.max()) if parsed.notnull().any() else None
            date_profiles[dc] = {
                "invalid_dates": invalid_count,
                "earliest_date": min_date,
                "latest_date": max_date
            }

    # Duplicate check
    exact_duplicates = int(df_raw.duplicated().sum())
    row_id_duplicates = int(df_raw['Row ID'].duplicated().sum()) if 'Row ID' in df_raw.columns else 0

    # Create representative sample
    # Make sure we include records with nulls / edge cases first, then stratify by Category and Region
    null_indices = df_raw[df_raw.isnull().any(axis=1)].index.tolist()
    remaining_indices = [idx for idx in df_raw.index if idx not in null_indices]
    
    # Sample remaining to fill up to sample_size
    needed_sample = sample_size - len(null_indices)
    df_remaining = df_raw.loc[remaining_indices]
    
    # Stratified sampling on Category and Region
    try:
        sample_remaining = df_remaining.groupby(['Category', 'Region'], group_keys=False).apply(
            lambda x: x.sample(n=max(1, int(np.round(len(x) / len(df_remaining) * needed_sample))), random_state=random_state)
        )
    except Exception:
        sample_remaining = df_remaining.sample(n=needed_sample, random_state=random_state)
        
    # Combine and trim to exact sample_size
    combined_indices = null_indices + sample_remaining.index.tolist()
    if len(combined_indices) > sample_size:
        combined_indices = combined_indices[:sample_size]
    elif len(combined_indices) < sample_size:
        extra_needed = sample_size - len(combined_indices)
        extra_pool = [i for i in df_raw.index if i not in combined_indices]
        combined_indices += extra_pool[:extra_needed]
        
    df_sample = df_raw.loc[combined_indices].copy().reset_index(drop=True)
    
    # Save the sample separately without modifying original
    df_sample.to_csv(sample_path, index=False, encoding="utf-8")
    print(f"Representative sample of {len(df_sample)} records saved to: {sample_path}")

    # Build profiling report object
    report = {
        "dataset_name": "Sample Superstore Sales Dataset",
        "original_file": raw_path,
        "sample_file": sample_path,
        "total_original_records": total_raw_rows,
        "sample_records": len(df_sample),
        "total_columns": len(df_raw.columns),
        "columns": list(df_raw.columns),
        "exact_duplicates": exact_duplicates,
        "row_id_duplicates": row_id_duplicates,
        "date_profiles": date_profiles,
        "column_profiles": column_profiles,
        "detected_quality_issues": {
            "missing_values": {
                "Postal Code": int(df_raw['Postal Code'].isnull().sum()),
                "Row ID 3295 (completely corrupted row)": 1
            },
            "unusual_numeric": {
                "negative_profits_count": int((df_raw['Profit'] < 0).sum()),
                "note": "Negative profit reflects valid business operational losses on heavily discounted items."
            }
        }
    }

    # Save JSON report
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"JSON profiling report saved to: {report_json}")

    # Generate Markdown report
    md_content = f"""# RetailPulse Data Profiling & Quality Assessment Report

## 1. Executive Summary
- **Original Source Dataset:** `{raw_path}` ({total_raw_rows:,} records, {len(df_raw.columns)} columns)
- **Representative Sample:** `{sample_path}` ({len(df_sample):,} records)
- **Encoding:** UTF-8
- **Duplicate Records (Full Row):** {exact_duplicates}
- **Row ID Duplicates:** {row_id_duplicates}

## 2. Column-Level Profiling
| Column Name | Data Type | Missing Count | Missing % | Unique Values | Sample Values |
|-------------|-----------|---------------|-----------|---------------|---------------|
"""
    for col, p in column_profiles.items():
        sample_preview = ", ".join(p['samples'])
        md_content += f"| **{col}** | `{p['dtype']}` | {p['null_count']} | {p['null_percentage']}% | {p['unique_count']} | `{sample_preview}` |\n"

    md_content += f"""
## 3. Date & Numeric Quality Checks
- **Order Date Range:** {date_profiles.get('Order Date', {}).get('earliest_date', 'N/A')} to {date_profiles.get('Order Date', {}).get('latest_date', 'N/A')} (Invalid dates: {date_profiles.get('Order Date', {}).get('invalid_dates', 0)})
- **Ship Date Range:** {date_profiles.get('Ship Date', {}).get('earliest_date', 'N/A')} to {date_profiles.get('Ship Date', {}).get('latest_date', 'N/A')} (Invalid dates: {date_profiles.get('Ship Date', {}).get('invalid_dates', 0)})
- **Sales Metrics:** Min = ${column_profiles.get('Sales', {}).get('min', 0):,.2f}, Max = ${column_profiles.get('Sales', {}).get('max', 0):,.2f}, Mean = ${column_profiles.get('Sales', {}).get('mean', 0):,.2f}
- **Profit Metrics:** Min = ${column_profiles.get('Profit', {}).get('min', 0):,.2f}, Max = ${column_profiles.get('Profit', {}).get('max', 0):,.2f}, Negative Profits (Losses) = {column_profiles.get('Profit', {}).get('negative_count', 0)}
- **Quantity Metrics:** Min = {column_profiles.get('Quantity', {}).get('min', 0)}, Max = {column_profiles.get('Quantity', {}).get('max', 0)}

## 4. Identified Real Quality Issues
1. **Missing Postal Codes:** Burlington, Vermont records (e.g. Row ID 2235) have null postal codes.
2. **Corrupted / Empty Record:** Row ID 3295 is missing sales, profit, quantity, customer, and category data.
3. **No Double-Counting:** The dataset provides pre-computed line-item `Sales`. Transformations must NOT multiply `Sales` by `Quantity`.
"""
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Markdown profiling report saved to: {report_md}")
    return report

if __name__ == "__main__":
    generate_profile_and_sample()
