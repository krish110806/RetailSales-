"""
Page 5: Ask Your Data — Conversational Business Intelligence
Editorial Retail Design System inspired by FXFlow.
"""
from __future__ import annotations
import streamlit as st
import plotly.express as px
import pandas as pd

from dashboard.utils.bi_query_engine import ask_business_intelligence, PREDEFINED_QUESTIONS
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
        eyebrow="CONVERSATIONAL ANALYTICS",
        title="Ask Your Data",
        subtitle="Natural language business intelligence interface mapping English questions to safe warehouse SQL."
    )

    # 2. Suggested Questions Chips in a Card
    with st.container(border=True):
        st.markdown(
            '<div style="font-size:0.72rem; font-weight:700; color:#C6A568; letter-spacing:0.10em; text-transform:uppercase; margin-bottom:8px;">SUGGESTED ANALYTICAL INQUIRIES</div>',
            unsafe_allow_html=True
        )
        selected_question = None
        q_cols = st.columns(3)
        for i, q in enumerate(PREDEFINED_QUESTIONS):
            with q_cols[i % 3]:
                if st.button(q, key=f"bi_btn_{i}", use_container_width=True):
                    selected_question = q

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 3. Conversational Input
    user_query = st.text_input(
        "Enter your business question in plain English:",
        value=selected_question if selected_question else "",
        placeholder="e.g. Which category generates the highest profit?"
    )

    active_query = user_query if user_query else (selected_question if selected_question else PREDEFINED_QUESTIONS[0])

    if active_query:
        with st.spinner("Executing warehouse query …"):
            result = ask_business_intelligence(active_query)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 4. Direct Answer Card
        with st.container(border=True):
            st.markdown(
                '<div style="font-size:0.70rem; font-weight:700; color:#287D6B; letter-spacing:0.10em; text-transform:uppercase; margin-bottom:4px;">ANALYTICAL SYNTHESIS</div>',
                unsafe_allow_html=True
            )
            st.markdown(f"<div style='font-size: 1.15rem; font-weight: 500; line-height: 1.4; color: #142B3B;'>{result['answer']}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 5. Clean Simple Chart & Data Table
        df = result.get("data")
        if df is not None and not df.empty:
            c1, c2 = st.columns([7, 5])
            with c1:
                chart_type = result.get("chart_type", "bar")
                if chart_type == "line":
                    fig = px.line(
                        df, x=result["x"], y=result["y"],
                        markers=True,
                        labels={result["x"]: "Period", result["y"]: "Value"},
                        color_discrete_sequence=[COLORS["teal"]]
                    )
                elif chart_type == "bar_horizontal":
                    fig = px.bar(
                        df.sort_values(result["x"], ascending=True),
                        x=result["x"], y=result["y"],
                        orientation="h",
                        color_discrete_sequence=[COLORS["teal"]]
                    )
                    fig.update_layout(yaxis={"categoryorder": "total ascending", "tickfont": {"size": 10}})
                else:
                    fig = px.bar(
                        df, x=result["x"], y=result["y"],
                        color_discrete_sequence=[COLORS["teal"]]
                    )
                fig.update_layout(get_plotly_layout(f"Visualization: {result['question']}", dark_mode=dark_mode))
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                st.markdown(
                    '<div style="font-size:0.72rem; font-weight:700; color:#78838C; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:6px;">DATASET RESULT</div>',
                    unsafe_allow_html=True
                )
                st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 6. Executed SQL & Business Interpretation
        col_sql, col_interp = st.columns([6, 6])
        with col_sql:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:0.70rem; font-weight:700; color:#C6A568; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">EXECUTED SQL STATEMENT</div>',
                    unsafe_allow_html=True
                )
                st.code(result["sql"], language="sql")

        with col_interp:
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:0.70rem; font-weight:700; color:#287D6B; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">STRATEGIC INTERPRETATION</div>',
                    unsafe_allow_html=True
                )
                st.markdown(f"<p style='font-size:0.92rem; color:#263746; line-height:1.5; margin:0;'>{result['interpretation']}</p>", unsafe_allow_html=True)
