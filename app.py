"""
RetailPulse — Retail Intelligence Platform
Main Application Entrypoint with FXFlow-Inspired Design & Navigation.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# ── page config (must be first Streamlit call) ───────────────────────
st.set_page_config(
    page_title="RetailPulse – Retail Intelligence Platform",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from dashboard.utils.theme import inject_custom_css, COLORS
from pipeline.pipeline_engine import PipelineEngine
from pipeline.db_manager import init_database, get_latest_execution
from pipeline.bigquery_client import BigQueryWarehouse

# Ensure database tables exist
init_database()

# Session State Initialization
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

# Auto-run pipeline once on initial load if database has no tables yet
if get_latest_execution() is None:
    try:
        engine = PipelineEngine()
        engine.run_pipeline()
    except Exception:
        pass

# Inject Theme Styling
inject_custom_css(dark_mode=st.session_state["dark_mode"])

# Sidebar Branding & Navigation
with st.sidebar:
    # Editorial Brand Monogram & Title (matching FXFlow's custom SVG style)
    st.markdown(
        """
        <div style="padding: 10px 4px 16px 4px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                <!-- Professional SVG Logo: Retail Pulse Bag, Upward Sales Trend & Gold Embellishments -->
                <svg width="42" height="42" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg" style="flex-shrink: 0; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.25));">
                    <defs>
                        <linearGradient id="rpEmblemBg" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#1A384D"/>
                            <stop offset="100%" stop-color="#0E1E2A"/>
                        </linearGradient>
                        <linearGradient id="rpTealGrad" x1="0" y1="0" x2="44" y2="0" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#287D6B"/>
                            <stop offset="100%" stop-color="#3EB89B"/>
                        </linearGradient>
                    </defs>
                    <!-- Background Squircle Container -->
                    <rect x="1" y="1" width="42" height="42" rx="10" fill="url(#rpEmblemBg)" stroke="#C6A568" stroke-width="1.2" stroke-opacity="0.5"/>
                    <!-- Geometry Orbit -->
                    <circle cx="22" cy="22" r="16.5" stroke="#287D6B" stroke-width="0.75" stroke-dasharray="2.5 3" stroke-opacity="0.35"/>
                    <!-- Retail Bag Silhouette (Champagne Gold) -->
                    <path d="M14 17C14 13.5 17.5 11 22 11C26.5 11 30 13.5 30 17" stroke="#C6A568" stroke-width="2" stroke-linecap="round"/>
                    <rect x="12" y="17" width="20" height="17" rx="3" stroke="#C6A568" stroke-width="2.2"/>
                    <!-- Pulse / Trend Line through the Bag (Teal) -->
                    <path d="M8 26H15L18 20L23 30L27 24L30 26H36" stroke="url(#rpTealGrad)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- Upward Arrowhead -->
                    <path d="M33 23L36 26L33 29" stroke="#3EB89B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <div>
                    <div style="
                        font-family: 'Newsreader', Georgia, serif;
                        font-size: 1.45rem;
                        font-weight: 600;
                        color: #FFFEFA;
                        letter-spacing: -0.02em;
                        line-height: 1.1;
                    ">RetailPulse</div>
                    <div style="
                        font-family: 'Plus Jakarta Sans', sans-serif;
                        font-size: 0.65rem;
                        color: #C6A568;
                        letter-spacing: 0.12em;
                        text-transform: uppercase;
                        font-weight: 700;
                    ">RETAIL INTELLIGENCE PLATFORM</div>
                </div>
            </div>
            <div style="
                font-size: 0.76rem;
                color: #8C9DA8;
                line-height: 1.4;
                padding-top: 4px;
            ">
                Automated retail ELT pipeline, warehouse analytics, and demand intelligence.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<hr style='margin: 4px 0 14px 0; border-color: rgba(229, 222, 208, 0.12);'>", unsafe_allow_html=True)

    # Navigation Section Header
    st.markdown(
        """
        <div style="
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 700;
            color: #C6A568;
            margin-bottom: 8px;
            padding-left: 4px;
        ">ANALYTICS MODULES</div>
        """,
        unsafe_allow_html=True
    )

    navigation_pages = [
        "Sales Overview",
        "Sales Analytics",
        "Product Analytics",
        "Regional Analytics",
        "Ask Your Data",
        "Data Pipeline"
    ]

    selected_nav = st.radio(
        "Navigation",
        navigation_pages,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<hr style='margin: 20px 0 14px 0; border-color: rgba(229, 222, 208, 0.12);'>", unsafe_allow_html=True)

    # Dark Mode Toggle
    dark_mode_toggle = st.toggle("🌙 Dark Mode", value=st.session_state["dark_mode"])
    if dark_mode_toggle != st.session_state["dark_mode"]:
        st.session_state["dark_mode"] = dark_mode_toggle
        st.rerun()

    # System Health Status Widget (Actual status, no dummy values)
    latest_exec = get_latest_execution()
    bq = BigQueryWarehouse()
    status_str = "● Pipeline Ready & Healthy" if latest_exec and latest_exec.get("execution_status") == "SUCCESS" else "● Pipeline Standby"
    color_code = "#4ADE80" if latest_exec and latest_exec.get("execution_status") == "SUCCESS" else "#C6A568"
    warehouse_label = "BigQuery Live" if bq.is_configured else "Local SQLite Warehouse"

    st.markdown(f"""
    <div style="margin-top: 18px; padding: 12px 14px; background: rgba(255,255,255,0.04); border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
        <div style="font-size: 0.70rem; color: #8C9DA8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600; margin-bottom: 4px;">SYSTEM HEALTH</div>
        <div style="font-size: 0.80rem; font-weight: 700; color: {color_code};">{status_str}</div>
        <div style="font-size: 0.72rem; color: #64748B; margin-top: 3px; font-family: 'IBM Plex Mono', monospace;">Storage: {warehouse_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # Version Footer
    st.markdown("""
    <div style="
        margin-top: 24px;
        padding-top: 12px;
        font-size: 0.70rem;
        color: #728492;
        border-top: 1px solid rgba(229, 222, 208, 0.08);
        line-height: 1.4;
    ">
        RetailPulse v1.0.0 Enterprise<br>
        <span style="color: #4B6375;">Automated ELT & Business Intelligence</span>
    </div>
    """, unsafe_allow_html=True)

# ── Page Router ──────────────────────────────────────────────────────
if selected_nav == "Sales Overview":
    from dashboard.pages import page_1_sales_overview as page1
    page1.render()
elif selected_nav == "Sales Analytics":
    from dashboard.pages import page_2_sales_analytics as page2
    page2.render()
elif selected_nav == "Product Analytics":
    from dashboard.pages import page_3_product_analytics as page3
    page3.render()
elif selected_nav == "Regional Analytics":
    from dashboard.pages import page_4_regional_analytics as page4
    page4.render()
elif selected_nav == "Ask Your Data":
    from dashboard.pages import page_5_ask_your_data as page5
    page5.render()
elif selected_nav == "Data Pipeline":
    from dashboard.pages import page_6_data_pipeline as page6
    page6.render()
