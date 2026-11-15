"""
Page 1: Sales Overview — Executive Financial Summary
Editorial Retail Design System inspired by FXFlow.
"""
from __future__ import annotations
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from pipeline.db_manager import execute_query
from dashboard.utils.theme import (
    render_page_header,
    render_kpi_card,
    get_plotly_layout,
    COLORS
)

def render():
    dark_mode = st.session_state.get("dark_mode", False)

    # 1. Editorial Header
    render_page_header(
        eyebrow="EXECUTIVE SUMMARY",
        title="Sales Overview",
        subtitle="High-level commercial performance, monthly revenue velocity, and categorical retail insights."
    )

    # 2. Fetch Verified Macro Metrics
    try:
        kpi_df = execute_query("""
        SELECT 
            ROUND(SUM(sales), 2) AS total_revenue,
            COUNT(DISTINCT order_id) AS total_orders,
            ROUND(SUM(profit), 2) AS total_profit,
            SUM(quantity) AS total_quantity,
            ROUND(SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
            ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100.0, 2) AS profit_margin_pct
        FROM fct_sales;
        """)
    except Exception:
        st.warning("Please execute the pipeline from the Data Pipeline page to populate data tables.")
        return

    if kpi_df.empty or kpi_df.iloc[0]["total_revenue"] is None:
        st.info("No sales transactions detected. Navigate to Data Pipeline and click 'Run Pipeline Now'.")
        return

    kpi = kpi_df.iloc[0]
    rev = kpi["total_revenue"] or 0.0
    orders = kpi["total_orders"] or 0
    profit = kpi["total_profit"] or 0.0
    qty = kpi["total_quantity"] or 0
    aov = kpi["avg_order_value"] or 0.0
    margin = kpi["profit_margin_pct"] or 0.0

    # 3. KPI Cards Row (Clean, bug-free, perfectly aligned)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Total Revenue", f"${rev:,.2f}", "Total line-item sales", dark_mode=dark_mode)
    with c2:
        render_kpi_card("Total Orders", f"{orders:,}", "Unique retail transactions", dark_mode=dark_mode)
    with c3:
        render_kpi_card("Total Profit", f"${profit:,.2f}", f"Net Margin: {margin:.1f}%", dark_mode=dark_mode)
    with c4:
        render_kpi_card("Units Sold", f"{qty:,}", "Physical units delivered", dark_mode=dark_mode)
    with c5:
        render_kpi_card("Avg Order Value", f"${aov:,.2f}", "Revenue per order", dark_mode=dark_mode)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Clean, Simple Charts: Row 1
    # Chart 1: Monthly Revenue (Simple Line Chart)
    # Chart 2: Sales by Category (Vertical Bar Chart)
    r1_col1, r1_col2 = st.columns([7, 5])

    with r1_col1:
        monthly_df = execute_query("""
            SELECT order_year_month, total_revenue
            FROM monthly_sales
            ORDER BY order_year_month ASC;
        """)
        if not monthly_df.empty:
            fig_rev = px.line(
                monthly_df,
                x="order_year_month",
                y="total_revenue",
                markers=True,
                labels={"order_year_month": "Month", "total_revenue": "Revenue ($)"}
            )
            fig_rev.update_traces(
                line=dict(color=COLORS["teal"], width=2.5),
                marker=dict(size=5, color=COLORS["teal"])
            )
            fig_rev.update_layout(get_plotly_layout("Monthly Revenue Trajectory", dark_mode=dark_mode))
            fig_rev.update_layout(xaxis_title="Billing Month", yaxis_title="Sales ($)")
            st.plotly_chart(fig_rev, use_container_width=True)

    with r1_col2:
        cat_df = execute_query("""
            SELECT category, ROUND(SUM(sales), 2) AS sales
            FROM fct_sales
            GROUP BY category
            ORDER BY sales DESC;
        """)
        if not cat_df.empty:
            fig_cat = px.bar(
                cat_df,
                x="category",
                y="sales",
                color_discrete_sequence=[COLORS["teal"]],
                labels={"category": "Category", "sales": "Sales ($)"}
            )
            fig_cat.update_layout(get_plotly_layout("Sales by Category", dark_mode=dark_mode))
            fig_cat.update_layout(xaxis_title="", yaxis_title="Sales ($)")
            st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 5. Clean, Simple Charts: Row 2
    # Chart 3: Revenue by Region (Horizontal Bar Chart)
    # Chart 4: Profit Overview by Category (Simple Bar Chart)
    r2_col1, r2_col2 = st.columns([6, 6])

    with r2_col1:
        reg_df = execute_query("""
            SELECT region, ROUND(SUM(sales), 2) AS sales
            FROM fct_sales
            GROUP BY region
            ORDER BY sales ASC;
        """)
        if not reg_df.empty:
            fig_reg = px.bar(
                reg_df,
                x="sales",
                y="region",
                orientation="h",
                color_discrete_sequence=[COLORS["gold"]],
                labels={"sales": "Revenue ($)", "region": "Region"}
            )
            fig_reg.update_layout(get_plotly_layout("Revenue by Region", dark_mode=dark_mode))
            fig_reg.update_layout(xaxis_title="Revenue ($)", yaxis_title="")
            st.plotly_chart(fig_reg, use_container_width=True)

    with r2_col2:
        prof_df = execute_query("""
            SELECT category, ROUND(SUM(profit), 2) AS total_profit
            FROM fct_sales
            GROUP BY category
            ORDER BY total_profit DESC;
        """)
        if not prof_df.empty:
            fig_prof = px.bar(
                prof_df,
                x="category",
                y="total_profit",
                color_discrete_sequence=[COLORS["teal"]],
                labels={"category": "Category", "total_profit": "Net Profit ($)"}
            )
            fig_prof.update_layout(get_plotly_layout("Profit Overview by Category", dark_mode=dark_mode))
            fig_prof.update_layout(xaxis_title="", yaxis_title="Profit ($)")
            st.plotly_chart(fig_prof, use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 6. Recent Transaction Feed
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.15rem; font-weight:600; color:#142B3B; margin-bottom: 0.4rem;">
            Recent Verified Transactions
        </div>
        """,
        unsafe_allow_html=True
    )
    recent_df = execute_query("""
        SELECT order_id, order_date, customer_name, region, category, sub_category, sales, quantity, discount, profit, profit_tier
        FROM fct_sales
        ORDER BY order_date DESC, row_id DESC
        LIMIT 10;
    """)
    if not recent_df.empty:
        recent_df["sales"] = recent_df["sales"].apply(lambda x: f"${x:,.2f}")
        recent_df["profit"] = recent_df["profit"].apply(lambda x: f"${x:,.2f}")
        recent_df["discount"] = recent_df["discount"].apply(lambda x: f"{x*100:.0f}%")
        recent_df.columns = ["Order ID", "Date", "Customer", "Region", "Category", "Sub-Category", "Sales", "Qty", "Discount", "Profit", "Profit Tier"]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
