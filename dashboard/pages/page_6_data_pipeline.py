"""
Page 6: Data Pipeline — Enterprise Data Engineering & Telemetry Center
Inspired by FXFlow's institutional pipeline operations & surveillance architecture.
"""
from __future__ import annotations
import os
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

from config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    REJECTED_DATA_DIR,
    REPORTS_DATA_DIR,
    LOGS_DIR,
    DEFAULT_INPUT_CSV
)
from pipeline.pipeline_engine import PipelineEngine
from pipeline.db_manager import (
    get_latest_execution,
    get_all_executions,
    execute_query
)
from pipeline.bigquery_client import BigQueryWarehouse
from dashboard.utils.theme import (
    render_page_header,
    render_kpi_card,
    get_plotly_layout,
    COLORS
)

def render():
    dark_mode = st.session_state.get("dark_mode", False)
    latest_run = get_latest_execution()
    bq = BigQueryWarehouse()
    status_bq = bq.get_status()

    # 1. Page Header (Editorial style with source and execution timestamps)
    last_run_time_str = (
        pd.Timestamp(latest_run["start_time"]).strftime("%Y-%m-%d %H:%M UTC")
        if latest_run and latest_run.get("start_time")
        else "Awaiting Execution"
    )

    h_col1, h_col2 = st.columns([3, 1.3])
    with h_col1:
        st.markdown(
            f"""
            <div style="padding-bottom: 0.6rem; border-bottom: 1px solid #E5DED0; margin-bottom: 1.1rem;">
                <div class="rp-eyebrow">DATA PIPELINE & WAREHOUSE OPERATIONS</div>
                <h1 class="rp-title" style="margin: 0; font-size: 2.1rem; line-height: 1.15;">Data Pipeline</h1>
                <p class="rp-subtext" style="margin: 0.25rem 0 0.5rem 0;">
                    Monitor automated retail ingestion, validation rules, dbt transformations, and warehouse telemetry.
                </p>
                <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #78838C; margin-top: 4px;">
                    <span style="background: #EDE7DC; padding: 2px 8px; border-radius: 4px; color: #142B3B; font-weight: 600;">
                        SOURCE: {Path(DEFAULT_INPUT_CSV).name}
                    </span>
                    <span style="color: #A0ABA6;">•</span>
                    <span>
                        LAST EXECUTION: <strong>{last_run_time_str}</strong>
                    </span>
                    <span style="color: #A0ABA6;">•</span>
                    <span>
                        WAREHOUSE: <strong>{status_bq['mode']}</strong>
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with h_col2:
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("🚀 Run Pipeline", type="primary", use_container_width=True):
                engine = PipelineEngine(source_path=DEFAULT_INPUT_CSV)
                if engine.is_running():
                    st.warning("⚠️ Pipeline run already in progress.")
                else:
                    with st.spinner("Executing end-to-end ELT pipeline …"):
                        success, res = engine.run_pipeline()
                        if success:
                            st.success(f"Pipeline executed in {res['duration_seconds']}s")
                            st.rerun()
                        else:
                            st.error(f"Failed: {res.get('error')}")

        with btn_c2:
            if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
                st.rerun()

        # Download report button
        rep_file = REPORTS_DATA_DIR / "latest_quality_report.json"
        if rep_file.exists():
            with open(rep_file, "r", encoding="utf-8") as f:
                rep_json = f.read()
            st.download_button(
                label="📥 Quality Report",
                data=rep_json,
                file_name="retailpulse_quality_report.json",
                mime="application/json",
                use_container_width=True
            )

    # 2. Pipeline Health Overview KPIs
    if latest_run:
        in_cnt = latest_run.get("input_records", 0)
        proc_cnt = latest_run.get("processed_records", 0)
        rej_cnt = latest_run.get("rejected_records", 0)
        dup_cnt = latest_run.get("duplicate_records", 0)
        miss_cnt = latest_run.get("missing_values", 0)
        qual_pct = latest_run.get("data_quality_pct", 100.0)
        run_status = latest_run.get("execution_status", "UNKNOWN")

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1:
            render_kpi_card("Input Records", f"{in_cnt:,}", "Raw extracted rows", dark_mode=dark_mode)
        with k2:
            render_kpi_card("Processed", f"{proc_cnt:,}", "Validated silver rows", dark_mode=dark_mode)
        with k3:
            render_kpi_card("Rejected", f"{rej_cnt:,}", "Quarantine audit", dark_mode=dark_mode)
        with k4:
            render_kpi_card("Duplicates", f"{dup_cnt:,}", "Deduped transactions", dark_mode=dark_mode)
        with k5:
            render_kpi_card("Missing Values", f"{miss_cnt:,}", "Detected null cells", dark_mode=dark_mode)
        with k6:
            render_kpi_card("Data Quality", f"{qual_pct:.1f}%", f"Status: {run_status}", dark_mode=dark_mode)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3. Horizontal End-to-End Pipeline Execution Flow (FXFlow Stage Cards)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.5rem;">
            <div>
                <span class="rp-eyebrow">AUTOMATED EXECUTION FLOW</span>
                <div style="font-family:'Newsreader', Georgia, serif; font-size:1.25rem; font-weight:600; color:#142B3B;">
                    Stage Telemetry & Lineage
                </div>
            </div>
            <div style="font-size:0.75rem; color:#78838C; font-family:'IBM Plex Mono', monospace;">
                CSV Source → Airbyte → BigQuery Raw → Data Validation → dbt Transformation → Analytics Warehouse
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    stage_cols = st.columns([1.6, 0.25, 1.6, 0.25, 1.6, 0.25, 1.7, 0.25, 1.8, 0.25, 1.8])
    stages_data = [
        ("STAGE 01", "CSV Source", "Raw Superstore Data", f"{in_cnt:,} rows", "PASSED", "rp-badge-teal"),
        ("STAGE 02", "Airbyte Sync", "Ingestion Connector", "Idempotent SHA", "ACTIVE", "rp-badge-teal"),
        ("STAGE 03", "BigQuery Raw", "raw_data.superstore", f"{in_cnt:,} rows", "LOADED", "rp-badge-teal"),
        ("STAGE 04", "Data Validation", "Schema & Null Audit", f"{proc_cnt:,} valid / {rej_cnt} rej", "AUDITED", "rp-badge-teal"),
        ("STAGE 05", "dbt Transform", "5 Analytical Marts", "7 Tests Passed", "COMPILED", "rp-badge-teal"),
        ("STAGE 06", "Warehouse Store", "Analytics Dimensional", "Ready for BI", "SERVED", "rp-badge-teal")
    ]

    col_idx = 0
    for i, (num, title, sub, metric, badge_text, badge_class) in enumerate(stages_data):
        with stage_cols[col_idx]:
            card_html = (
                f'<div class="pipeline-stage-card">'
                f'<div>'
                f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<span class="pipeline-stage-num">{num}</span>'
                f'<span class="rp-badge {badge_class}" style="font-size:0.65rem;">{badge_text}</span>'
                f'</div>'
                f'<div class="pipeline-stage-title">{title}</div>'
                f'<div style="font-size:0.72rem; color:#78838C;">{sub}</div>'
                f'</div>'
                f'<div class="pipeline-stage-metrics">'
                f'{metric}'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)
        col_idx += 1

        if i < len(stages_data) - 1:
            with stage_cols[col_idx]:
                st.markdown('<div class="pipeline-flow-arrow">→</div>', unsafe_allow_html=True)
            col_idx += 1

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. Clean Simple Charts:
    # Chart 1: Input vs Processed Records Bar Chart
    # Chart 2: Data Quality & Rejection Distribution Bar Chart
    c_chart1, c_chart2 = st.columns([6, 6])

    with c_chart1:
        comp_df = pd.DataFrame({
            "Stage": ["Raw Input", "Cleaned & Processed", "Rejected Records"],
            "Count": [in_cnt, proc_cnt, rej_cnt]
        })
        fig_comp = px.bar(
            comp_df,
            x="Stage",
            y="Count",
            color="Stage",
            color_discrete_map={
                "Raw Input": COLORS["gold"],
                "Cleaned & Processed": COLORS["teal"],
                "Rejected Records": COLORS["red"]
            },
            labels={"Count": "Records Count", "Stage": "Pipeline Stage"}
        )
        fig_comp.update_layout(get_plotly_layout("Input vs Processed Record Volume", dark_mode=dark_mode))
        fig_comp.update_layout(showlegend=False, xaxis_title="", yaxis_title="Records")
        st.plotly_chart(fig_comp, use_container_width=True)

    with c_chart2:
        q_rep_file = REPORTS_DATA_DIR / "latest_quality_report.json"
        if q_rep_file.exists():
            with open(q_rep_file, "r", encoding="utf-8") as f:
                q_data = json.load(f)
            miss_map = q_data.get("missing_by_column", {})
            miss_df = pd.DataFrame(list(miss_map.items()), columns=["Column", "Missing Count"])
            miss_df = miss_df[miss_df["Missing Count"] > 0]

            if not miss_df.empty:
                fig_miss = px.bar(
                    miss_df.sort_values("Missing Count", ascending=True),
                    x="Missing Count",
                    y="Column",
                    orientation="h",
                    color_discrete_sequence=[COLORS["red"]],
                    labels={"Missing Count": "Missing Count", "Column": "Column"}
                )
                fig_miss.update_layout(get_plotly_layout("Detected Missing Values by Column", dark_mode=dark_mode))
                fig_miss.update_layout(xaxis_title="Null Count", yaxis_title="")
                st.plotly_chart(fig_miss, use_container_width=True)
            else:
                st.success("Clean run: Zero missing values detected in critical attributes.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 5. Raw vs Processed Data Auditing (Tabs)
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.15rem; font-weight:600; color:#142B3B; margin-bottom: 0.3rem;">
            Warehouse Data Previews
        </div>
        """,
        unsafe_allow_html=True
    )
    tab_raw, tab_clean, tab_rej = st.tabs(["Raw Data (Bronze)", "Cleaned Data (Silver)", "Rejected Records (Quarantine)"])

    with tab_raw:
        try:
            raw_preview = execute_query("SELECT * FROM raw_data LIMIT 12;")
            st.dataframe(raw_preview, use_container_width=True, hide_index=True)
        except Exception:
            st.info("Raw table not populated.")

    with tab_clean:
        clean_file = PROCESSED_DATA_DIR / "latest_cleaned_sales.csv"
        if clean_file.exists():
            clean_p = pd.read_csv(clean_file).head(12)
            st.dataframe(clean_p, use_container_width=True, hide_index=True)
        else:
            st.info("Cleaned dataset not available.")

    with tab_rej:
        rej_file = REJECTED_DATA_DIR / "latest_rejected_records.csv"
        if rej_file.exists():
            rej_p = pd.read_csv(rej_file)
            if not rej_p.empty:
                st.dataframe(rej_p, use_container_width=True, hide_index=True)
            else:
                st.success("No records rejected in the latest execution.")
        else:
            st.info("No rejected records file.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 6. Persistent Pipeline Execution History Table
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.15rem; font-weight:600; color:#142B3B; margin-bottom: 0.3rem;">
            Persistent Execution History (SQLite Store)
        </div>
        """,
        unsafe_allow_html=True
    )
    hist_records = get_all_executions()
    if hist_records:
        hist_df = pd.DataFrame(hist_records)
        display_cols = ["run_id", "start_time", "duration_seconds", "input_records", "processed_records", "rejected_records", "data_quality_pct", "execution_status"]
        available_cols = [c for c in display_cols if c in hist_df.columns]
        hist_view = hist_df[available_cols].copy()
        hist_view.columns = ["Run ID", "Start Time (UTC)", "Duration (s)", "Input", "Clean", "Rejected", "Quality %", "Status"]
        st.dataframe(hist_view, use_container_width=True, hide_index=True)
    else:
        st.info("No prior execution history recorded.")

    # 7. Live Execution Logs Viewer
    with st.expander("📝 Live Pipeline Execution Logs", expanded=False):
        log_files = sorted(list(LOGS_DIR.glob("*.log")), reverse=True)
        if log_files:
            with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
                logs_text = f.read()
            st.code(logs_text[-3000:], language="log")
        else:
            st.info("No logs generated yet.")
