"""
Page 3: Product Analytics — Catalog SKU Performance & Category Margin Audits
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
        eyebrow="MERCHANDISING INTELLIGENCE",
        title="Product Analytics",
        subtitle="Catalog revenue ranking, volume leaders, and SKU-level profitability diagnostics."
    )

    try:
        prod_df = execute_query("SELECT * FROM product_performance")
        cat_df = execute_query("""
            SELECT category, ROUND(SUM(sales), 2) AS sales, ROUND(SUM(profit), 2) AS profit,
                   ROUND((SUM(profit)/SUM(sales))*100.0, 2) AS margin_pct
            FROM fct_sales
            GROUP BY category
            ORDER BY sales DESC;
        """)
    except Exception:
        st.warning("Please execute the pipeline to populate product marts.")
        return

    if prod_df.empty:
        st.info("No product performance data available. Execute the pipeline first.")
        return

    # 2. KPI Cards
    total_skus = len(prod_df)
    profitable_skus = (prod_df["total_profit"] > 0).sum()
    top_sku = prod_df.sort_values("total_revenue", ascending=False).iloc[0]["product_name"]
    top_margin_cat = cat_df.sort_values("margin_pct", ascending=False).iloc[0]["category"]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Active Catalog SKUs", f"{total_skus:,}", "Distinct items sold", dark_mode=dark_mode)
    with k2:
        render_kpi_card("Profitable SKUs", f"{profitable_skus:,}", f"{(profitable_skus/total_skus*100):.1f}% profitable ratio", dark_mode=dark_mode)
    with k3:
        render_kpi_card("Top Grossing SKU", top_sku[:16] + "…", "Highest grossing product", dark_mode=dark_mode)
    with k4:
        render_kpi_card("Top Margin Category", top_margin_cat, "Optimal unit margin", dark_mode=dark_mode)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Clean Simple Charts
    # Chart 1: Top 10 Products by Revenue (Horizontal Bar Chart)
    # Chart 2: Category Performance (Simple Bar Chart)
    c1, c2 = st.columns([6, 6])

    with c1:
        top10_prods = prod_df.sort_values("total_revenue", ascending=True).tail(10)
        # Clean product display name
        top10_prods["short_name"] = top10_prods["product_name"].apply(lambda x: x[:34] + "…" if len(x) > 34 else x)
        fig_top = px.bar(
            top10_prods,
            x="total_revenue",
            y="short_name",
            orientation="h",
            color_discrete_sequence=[COLORS["teal"]],
            labels={"total_revenue": "Revenue ($)", "short_name": "Product SKU"}
        )
        fig_top.update_layout(get_plotly_layout("Top 10 Products by Revenue", dark_mode=dark_mode))
        fig_top.update_layout(yaxis={"categoryorder": "total ascending", "tickfont": {"size": 10}}, xaxis_title="Revenue ($)", yaxis_title="")
        st.plotly_chart(fig_top, use_container_width=True)

    with c2:
        if not cat_df.empty:
            fig_cat = px.bar(
                cat_df,
                x="category",
                y="sales",
                color_discrete_sequence=[COLORS["gold"]],
                labels={"category": "Category", "sales": "Sales ($)"}
            )
            fig_cat.update_layout(get_plotly_layout("Category Sales Volume", dark_mode=dark_mode))
            fig_cat.update_layout(xaxis_title="Category", yaxis_title="Revenue ($)")
            st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Chart 3: Top 10 Products by Profitability (Simple Bar Chart)
    st.markdown(
        """
        <div style="font-family:'Newsreader', Georgia, serif; font-size:1.15rem; font-weight:600; color:#142B3B; margin-bottom: 0.3rem;">
            Top 10 SKU Profitability Leaders
        </div>
        """,
        unsafe_allow_html=True
    )
    top10_profit = prod_df.sort_values("total_profit", ascending=False).head(10).copy()
    top10_profit["short_name"] = top10_profit["product_name"].apply(lambda x: x[:30] + "…" if len(x) > 30 else x)

    fig_prof_bar = px.bar(
        top10_profit,
        x="short_name",
        y="total_profit",
        color_discrete_sequence=[COLORS["teal"]],
        labels={"short_name": "Product", "total_profit": "Net Profit ($)"}
    )
    fig_prof_bar.update_layout(get_plotly_layout("Highest Net Profit Generating Products", dark_mode=dark_mode))
    fig_prof_bar.update_layout(xaxis_tickangle=-35, xaxis_title="", yaxis_title="Net Profit ($)")
    st.plotly_chart(fig_prof_bar, use_container_width=True)

    # 4. Detail Table
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    with st.expander("📄 View Catalog Performance Data Table", expanded=False):
        table_view = prod_df[["product_name", "category", "sub_category", "total_revenue", "total_profit", "profit_margin_pct", "total_units_sold"]].head(15).copy()
        table_view["total_revenue"] = table_view["total_revenue"].apply(lambda x: f"${x:,.2f}")
        table_view["total_profit"] = table_view["total_profit"].apply(lambda x: f"${x:,.2f}")
        table_view["profit_margin_pct"] = table_view["profit_margin_pct"].apply(lambda x: f"{x:.1f}%")
        table_view.columns = ["Product Name", "Category", "Sub-Category", "Revenue", "Profit", "Margin %", "Units Sold"]
        st.dataframe(table_view, use_container_width=True, hide_index=True)
