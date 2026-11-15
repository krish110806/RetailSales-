"""
Page 4: Regional Analytics — Geographic Penetration & State-Level Sales
Editorial Retail Design System inspired by FXFlow.
"""
from __future__ import annotations
import streamlit as st
import plotly.express as px
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

    # 1. Header
    render_page_header(
        eyebrow="GEOGRAPHIC SURVEILLANCE",
        title="Regional Analytics",
        subtitle="Territorial distribution, state sales rankings, and geographic margin efficiency."
    )

    try:
        reg_df = execute_query("SELECT * FROM regional_sales")
    except Exception:
        st.warning("Please execute the pipeline to populate regional marts.")
        return

    if reg_df.empty:
        st.info("No regional data available. Run the pipeline to populate.")
        return

    # Aggregate by Region
    region_totals = reg_df.groupby("region").agg(
        total_rev=("total_revenue", "sum"),
        total_prof=("total_profit", "sum"),
        total_orders=("total_orders", "sum")
    ).reset_index().sort_values("total_rev", ascending=False)

    top_reg = region_totals.iloc[0]
    total_sales_all = region_totals["total_rev"].sum()
    lead_share = (top_reg["total_rev"] / total_sales_all * 100) if total_sales_all > 0 else 0
    active_states = reg_df["state"].nunique()

    # 2. KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Leading Territory", top_reg["region"], f"${top_reg['total_rev']:,.2f} sales", dark_mode=dark_mode)
    with k2:
        render_kpi_card("Territory Share", f"{lead_share:.1f}%", "National sales share", dark_mode=dark_mode)
    with k3:
        render_kpi_card("Active States", f"{active_states}", "States with transactions", dark_mode=dark_mode)
    with k4:
        best_margin_reg = reg_df.groupby("region")["profit_margin_pct"].mean().idxmax()
        render_kpi_card("Highest Margin Region", best_margin_reg, "Optimal profitability", dark_mode=dark_mode)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Clean Simple Charts: Row 1
    # Chart 1: Region-wise Revenue (Horizontal Bar Chart)
    # Chart 2: Region-wise Profit (Bar Chart)
    c1, c2 = st.columns([6, 6])

    with c1:
        reg_rev_sorted = region_totals.sort_values("total_rev", ascending=True)
        fig_reg_rev = px.bar(
            reg_rev_sorted,
            x="total_rev",
            y="region",
            orientation="h",
            color_discrete_sequence=[COLORS["teal"]],
            labels={"total_rev": "Revenue ($)", "region": "Territory"}
        )
        fig_reg_rev.update_layout(get_plotly_layout("Region-wise Revenue", dark_mode=dark_mode))
        fig_reg_rev.update_layout(xaxis_title="Revenue ($)", yaxis_title="")
        st.plotly_chart(fig_reg_rev, use_container_width=True)

    with c2:
        fig_reg_prof = px.bar(
            region_totals,
            x="region",
            y="total_prof",
            color_discrete_sequence=[COLORS["gold"]],
            labels={"total_prof": "Profit ($)", "region": "Territory"}
        )
        fig_reg_prof.update_layout(get_plotly_layout("Region-wise Net Profit", dark_mode=dark_mode))
        fig_reg_prof.update_layout(xaxis_title="Territory", yaxis_title="Profit ($)")
        st.plotly_chart(fig_reg_prof, use_container_width=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 4. Chart 3: State-wise Sales (Simple Horizontal Bar Chart)
    state_totals = reg_df.groupby("state").agg(
        state_rev=("total_revenue", "sum"),
        state_prof=("total_profit", "sum")
    ).reset_index().sort_values("state_rev", ascending=True).tail(10)

    fig_state = px.bar(
        state_totals,
        x="state_rev",
        y="state",
        orientation="h",
        color_discrete_sequence=[COLORS["teal"]],
        labels={"state_rev": "Revenue ($)", "state": "State"}
    )
    fig_state.update_layout(get_plotly_layout("Top 10 States by Sales Volume", dark_mode=dark_mode))
    fig_state.update_layout(xaxis_title="Revenue ($)", yaxis_title="")
    st.plotly_chart(fig_state, use_container_width=True)

    # 5. State-wise Detail Table
    with st.expander("📄 State Sales & Profit Performance Table", expanded=False):
        state_table = reg_df[["state", "region", "total_revenue", "total_profit", "total_orders", "avg_order_value"]].sort_values("total_revenue", ascending=False).copy()
        state_table["total_revenue"] = state_table["total_revenue"].apply(lambda x: f"${x:,.2f}")
        state_table["total_profit"] = state_table["total_profit"].apply(lambda x: f"${x:,.2f}")
        state_table["avg_order_value"] = state_table["avg_order_value"].apply(lambda x: f"${x:,.2f}")
        state_table.columns = ["State", "Region", "Revenue", "Profit", "Orders", "Avg Order Value"]
        st.dataframe(state_table, use_container_width=True, hide_index=True)
