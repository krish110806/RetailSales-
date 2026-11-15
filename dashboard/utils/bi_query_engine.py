"""
Conversational Business Intelligence Engine for RetailPulse.
Maps natural language user questions to safe, validated SQL queries against
actual analytics tables (fct_sales, monthly_sales, product_performance, regional_sales).
Executes queries dynamically and generates data-driven answers, SQL syntax, charts, and interpretations.
"""
import re
from typing import Dict, Any, List
import pandas as pd
from pipeline.db_manager import execute_query

PREDEFINED_QUESTIONS = [
    "Which product generated the highest revenue?",
    "Which region has the highest sales?",
    "What is the monthly revenue trend?",
    "Which category generates the highest profit?",
    "Which month had the lowest sales?",
    "Show the top 10 products by revenue.",
    "Which customer has the highest total spend?",
    "What is the average order value by region?"
]

def ask_business_intelligence(question: str) -> Dict[str, Any]:
    """
    Parses natural language question, executes real SQL against analytics tables,
    and returns answer, query, chart configuration, and interpretation.
    """
    q_lower = question.lower().strip()

    # Query 1: Highest revenue product
    if "highest revenue" in q_lower and "product" in q_lower or "best product" in q_lower:
        sql = """
        SELECT product_name, category, sub_category, total_revenue, total_units_sold, total_profit, profit_margin_pct
        FROM product_performance
        ORDER BY total_revenue DESC
        LIMIT 1;
        """
        df = execute_query(sql)
        if not df.empty:
            prod = df.iloc[0]["product_name"]
            rev = df.iloc[0]["total_revenue"]
            profit = df.iloc[0]["total_profit"]
            margin = df.iloc[0]["profit_margin_pct"]
            answer = f"**{prod}** generated the highest revenue at **${rev:,.2f}**, delivering **${profit:,.2f}** in net profit ({margin:.1f}% margin)."
            interpretation = "This product serves as the primary revenue anchor. Ensuring uninterrupted inventory and vendor SLA compliance for this SKU is critical to maintaining top-line performance."
        else:
            answer = "No product data available."
            interpretation = "Warehouse tables are empty."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "metric",
            "x": "product_name",
            "y": "total_revenue"
        }

    # Query 2: Region with highest sales
    elif "region" in q_lower and ("highest" in q_lower or "best" in q_lower or "sales" in q_lower):
        sql = """
        SELECT region, ROUND(SUM(total_revenue), 2) as total_sales, ROUND(SUM(total_profit), 2) as total_profit,
               ROUND((SUM(total_profit) / SUM(total_revenue)) * 100.0, 2) as profit_margin_pct
        FROM regional_sales
        GROUP BY region
        ORDER BY total_sales DESC;
        """
        df = execute_query(sql)
        if not df.empty:
            top_region = df.iloc[0]["region"]
            top_sales = df.iloc[0]["total_sales"]
            margin = df.iloc[0]["profit_margin_pct"]
            answer = f"The **{top_region}** region leads all territories with **${top_sales:,.2f}** in total sales and a **{margin:.1f}%** profit margin."
            interpretation = f"{top_region} displays strong customer acquisition and volume. Marketing spend should capitalize on high regional demand while optimizing freight logistics."
        else:
            answer = "No regional data available."
            interpretation = "Run pipeline to populate regional analytics."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "bar",
            "x": "region",
            "y": "total_sales"
        }

    # Query 3: Monthly revenue trend
    elif "monthly" in q_lower or "revenue trend" in q_lower or "trend" in q_lower:
        sql = """
        SELECT order_year_month, total_revenue, total_profit, total_orders, avg_order_value
        FROM monthly_sales
        ORDER BY order_year_month ASC;
        """
        df = execute_query(sql)
        if not df.empty:
            peak_month = df.loc[df["total_revenue"].idxmax()]["order_year_month"]
            peak_val = df["total_revenue"].max()
            answer = f"The monthly revenue spans {len(df)} recorded periods, peaking in **{peak_month}** at **${peak_val:,.2f}**."
            interpretation = "Clear seasonal and promotional spikes appear towards year-end cycles (Q4), driven by holiday retail demand."
        else:
            answer = "No monthly data available."
            interpretation = "Execute the pipeline to calculate monthly trends."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "line",
            "x": "order_year_month",
            "y": "total_revenue"
        }

    # Query 4: Category generating highest profit
    elif "category" in q_lower and ("profit" in q_lower or "highest profit" in q_lower):
        sql = """
        SELECT category, ROUND(SUM(sales), 2) as total_sales, ROUND(SUM(profit), 2) as total_profit,
               ROUND((SUM(profit) / SUM(sales)) * 100.0, 2) as profit_margin_pct
        FROM fct_sales
        GROUP BY category
        ORDER BY total_profit DESC;
        """
        df = execute_query(sql)
        if not df.empty:
            top_cat = df.iloc[0]["category"]
            top_profit = df.iloc[0]["total_profit"]
            top_margin = df.iloc[0]["profit_margin_pct"]
            answer = f"**{top_cat}** generates the highest net profit at **${top_profit:,.2f}** with an overall profit margin of **{top_margin:.1f}%**."
            interpretation = f"{top_cat} provides superior unit economics compared to heavily discounted categories like Furniture, making it the most lucrative product pillar."
        else:
            answer = "No category data available."
            interpretation = "Run pipeline to refresh category analytics."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "bar",
            "x": "category",
            "y": "total_profit"
        }

    # Query 5: Month with lowest sales
    elif "lowest" in q_lower and ("sales" in q_lower or "month" in q_lower or "revenue" in q_lower):
        sql = """
        SELECT order_year_month, total_revenue, total_orders, total_profit
        FROM monthly_sales
        ORDER BY total_revenue ASC
        LIMIT 1;
        """
        df = execute_query(sql)
        if not df.empty:
            low_m = df.iloc[0]["order_year_month"]
            low_rev = df.iloc[0]["total_revenue"]
            answer = f"The month with the lowest sales was **{low_m}**, registering **${low_rev:,.2f}** across {df.iloc[0]['total_orders']} orders."
            interpretation = "Post-holiday contraction or inventory clearance typically causes lower volume in early Q1 months. Targeted retention campaigns could balance this trough."
        else:
            answer = "No monthly data available."
            interpretation = "Populate data through the pipeline."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "metric",
            "x": "order_year_month",
            "y": "total_revenue"
        }

    # Query 6: Top 10 products by revenue
    elif "top" in q_lower and ("10" in q_lower or "product" in q_lower or "revenue" in q_lower):
        sql = """
        SELECT product_name, category, total_revenue, total_units_sold, total_profit, profit_margin_pct
        FROM product_performance
        ORDER BY total_revenue DESC
        LIMIT 10;
        """
        df = execute_query(sql)
        if not df.empty:
            total_top10 = df["total_revenue"].sum()
            answer = f"Here are the **Top 10 Products by Revenue**, accounting for **${total_top10:,.2f}** in aggregate sales."
            interpretation = "The top 10 SKUs contribute heavily to gross margin. Maintaining healthy stock levels and minimizing stockouts for these items is paramount."
        else:
            answer = "No product performance data found."
            interpretation = "Execute the pipeline."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "bar_horizontal",
            "x": "total_revenue",
            "y": "product_name"
        }

    # Query 7: Customer with highest spend
    elif "customer" in q_lower and ("spend" in q_lower or "highest" in q_lower or "value" in q_lower):
        sql = """
        SELECT customer_name, segment, count(distinct order_id) as orders_count,
               round(sum(sales), 2) as total_spend, round(sum(profit), 2) as total_profit
        FROM fct_sales
        GROUP BY customer_name, segment
        ORDER BY total_spend DESC
        LIMIT 5;
        """
        df = execute_query(sql)
        if not df.empty:
            top_cust = df.iloc[0]["customer_name"]
            top_val = df.iloc[0]["total_spend"]
            answer = f"**{top_cust}** ({df.iloc[0]['segment']}) is the highest spending customer with **${top_val:,.2f}** across {df.iloc[0]['orders_count']} orders."
            interpretation = "Key account management and tiered loyalty perks should be prioritized for high-LTV customers to drive repeat enterprise purchases."
        else:
            answer = "No customer data available."
            interpretation = "Execute the pipeline."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "bar",
            "x": "customer_name",
            "y": "total_spend"
        }

    # Fallback: General category breakdown
    else:
        sql = """
        SELECT category, COUNT(DISTINCT order_id) as total_orders, ROUND(SUM(sales), 2) as total_sales,
               ROUND(SUM(profit), 2) as total_profit, ROUND((SUM(profit)/SUM(sales))*100.0, 2) as margin_pct
        FROM fct_sales
        GROUP BY category
        ORDER BY total_sales DESC;
        """
        df = execute_query(sql)
        answer = f"Showing overall category performance for your query '{question}'."
        interpretation = "Evaluating sales, profit, and margins across high-level categories provides holistic visibility into portfolio health."
        return {
            "question": question,
            "sql": sql.strip(),
            "data": df,
            "answer": answer,
            "interpretation": interpretation,
            "chart_type": "bar",
            "x": "category",
            "y": "total_sales"
        }
