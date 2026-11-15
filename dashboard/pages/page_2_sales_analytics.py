"""
Page 2: Sales Analytics — Temporal Trends & Filtered Portfolio Analysis
Editorial Retail Design System inspired by FXFlow.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px

from pipeline.db_manager import execute_query
from dashboard.utils.theme import (
    render_page_header,
    render_kpi_card,
    get_plotly_layout,
    COLORS
)

def render():
    dark_mode = st.session_state.get("dark_mode", False)

    # 1. Header
    render_page_header(
        eyebrow="COMMERCIAL INTELLIGENCE",
        title="Sales Analytics",
        subtitle="Granular temporal trajectories, monthly profitability dynamics, and multi-dimensional filtering."
    )

    try:
        df_all = execute_query("SELECT * FROM fct_sales")
    except Exception:
        st.warning("Please execute the pipeline to populate analytics tables.")
        return

    if df_all.empty:
        st.info("No transaction data available. Run the pipeline to populate.")
        return

    # 2. Clean Filter Bar in a Card Container
    with st.container(border=True):
        st.markdown(
            '<div style="font-size:0.72rem; font-weight:700; color:#C6A568; letter-spacing:0.10em; text-transform:uppercase; margin-bottom:8px;">SURVEILLANCE FILTERS</div>',
            unsafe_allow_html=True
        )
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            all_cats = ["All Categories"] + sorted(df_all["category"].dropna().unique().tolist())
            selected_cat = st.selectbox("Product Category", all_cats)
        with f_col2:
            all_regs = ["All Regions"] + sorted(df_all["region"].dropna().unique().tolist())
            selected_reg = st.selectbox("Geographic Region", all_regs)
        with f_col3:
            min_date = pd.to_datetime(df_all["order_date"]).min().date()
            max_date = pd.to_datetime(df_all["order_date"]).max().date()
            date_range = st.date_input("Order Date Range", (min_date, max_date))

    # Apply Filters
    filtered_df = df_all.copy()
    if selected_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["category"] == selected_cat]
    if selected_reg != "All Regions":
        filtered_df = filtered_df[filtered_df["region"] == selected_reg]
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_d, end_d = date_range
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df["order_date"]).dt.date >= start_d) &
            (pd.to_datetime(filtered_df["order_date"]).dt.date <= end_d)
        ]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3. Filtered KPI Summary
    tot_rev = filtered_df["sales"].sum() if not filtered_df.empty else 0.0
    tot_prof = filtered_df["profit"].sum() if not filtered_df.empty else 0.0
    tot_orders = filtered_df["order_id"].nunique() if not filtered_df.empty else 0
    margin_pct = (tot_prof / tot_rev * 100) if tot_rev > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Filtered Sales", f"${tot_rev:,.2f}", f"{len(filtered_df):,} line items", dark_mode=dark_mode)
    with k2:
        render_kpi_card("Filtered Profit", f"${tot_prof:,.2f}", f"{margin_pct:.1f}% net margin", dark_mode=dark_mode)
    with k3:
        render_kpi_card("Distinct Orders", f"{tot_orders:,}", "Completed transactions", dark_mode=dark_mode)
    with k4:
        avg_basket = (tot_rev / tot_orders) if tot_orders > 0 else 0.0
        render_kpi_card("Avg Order Value", f"${avg_basket:,.2f}", "Revenue per order", dark_mode=dark_mode)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 4. Clean, Simple Charts
    # Chart 1: Monthly Sales Trend (Simple Line Chart)
    # Chart 2: Monthly Profit (Simple Bar Chart)
    monthly_grp = filtered_df.groupby("order_year_month").agg(
        rev=("sales", "sum"),
        prof=("profit", "sum")
    ).reset_index().sort_values("order_year_month")

    c_chart1, c_chart2 = st.columns([6, 6])
    with c_chart1:
        if not monthly_grp.empty:
            fig_trend = px.line(
                monthly_grp,
                x="order_year_month",
                y="rev",
                markers=True,
                labels={"order_year_month": "Month", "rev": "Sales ($)"}
            )
            fig_trend.update_traces(
                line=dict(color=COLORS["teal"], width=2.5),
                marker=dict(size=5, color=COLORS["teal"])
            )
            fig_trend.update_layout(get_plotly_layout("Monthly Sales Trend", dark_mode=dark_mode))
            fig_trend.update_layout(xaxis_title="Billing Cycle", yaxis_title="Revenue ($)")
            st.plotly_chart(fig_trend, use_container_width=True)

    with c_chart2:
        if not monthly_grp.empty:
            # Color positive profits in teal, negative in terracotta red
            monthly_grp["profit_color"] = monthly_grp["prof"].apply(
                lambda x: COLORS["teal"] if x >= 0 else COLORS["red"]
            )
            fig_prof = px.bar(
                monthly_grp,
                x="order_year_month",
                y="prof",
                color="prof",
                color_continuous_scale=[[0, COLORS["red"]], [0.5, COLORS["gold"]], [1.0, COLORS["teal"]]],
                labels={"order_year_month": "Month", "prof": "Profit ($)"}
            )
            fig_prof.update_layout(get_plotly_layout("Monthly Profit Trajectory", dark_mode=dark_mode))
            fig_prof.update_layout(xaxis_title="Billing Cycle", yaxis_title="Net Profit ($)", coloraxis_showscale=False)
            st.plotly_chart(fig_prof, use_container_width=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Chart 3: Category-wise Sales (Bar Chart)
    cat_grp = filtered_df.groupby("category").agg(
        cat_sales=("sales", "sum"),
        cat_profit=("profit", "sum")
    ).reset_index().sort_values("cat_sales", ascending=False)

    if not cat_grp.empty:
        fig_cat_bar = px.bar(
            cat_grp,
            x="category",
            y="cat_sales",
            color_discrete_sequence=[COLORS["teal"]],
            labels={"category": "Product Category", "cat_sales": "Sales ($)"}
        )
        fig_cat_bar.update_layout(get_plotly_layout("Category-wise Sales Volume", dark_mode=dark_mode))
        fig_cat_bar.update_layout(xaxis_title="Category", yaxis_title="Sales ($)")
        st.plotly_chart(fig_cat_bar, use_container_width=True)
