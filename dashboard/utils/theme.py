"""
RetailPulse — Editorial Retail Theme and Design System.
Inspired by FXFlow's institutional wealth-management and market-intelligence UI.

Color Palette:
  • Main Background : #F7F5EF (Warm Cream)
  • Sidebar         : #142B3B (Midnight Navy)
  • Primary Accent  : #287D6B (Muted Deep Teal)
  • Secondary Accent: #C6A568 (Champagne Gold)
  • Card Background : #FFFEFA (Soft Ivory)
  • Primary Text    : #263746 (Midnight Slate)
  • Secondary Text  : #78838C (Muted Slate Grey)
  • Borders         : #E5DED0 (Subtle Warm Beige)
  • Green / Profit  : #1E7E5A
  • Red / Loss      : #C25447
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import streamlit as st
import plotly.graph_objects as go

# =====================================================================
# Centralised Colour Palette
# =====================================================================

COLORS: Dict[str, str] = {
    # Canvas & Surfaces
    "bg_canvas": "#F7F5EF",
    "surface_card": "#FFFEFA",
    "surface_hover": "#FDFBF7",
    "surface_alt": "#EDE7DC",

    # Sidebar (Midnight Navy)
    "sidebar": "#142B3B",
    "sidebar_border": "#1D3A4F",
    "sidebar_text": "#E2E8F0",
    "sidebar_muted": "#8C9DA8",

    # Typography
    "text": "#263746",
    "text_muted": "#78838C",
    "navy": "#142B3B",

    # Brand Accents
    "teal": "#287D6B",
    "teal_light": "#369B86",
    "teal_soft": "#E7F3F0",
    "gold": "#C6A568",
    "gold_light": "#D9BC85",
    "gold_soft": "#F9F4EB",

    # Movement / Telemetry
    "green": "#1E7E5A",
    "green_soft": "#EBF5F0",
    "red": "#C25447",
    "red_soft": "#FBF0EE",

    # Borders & Dividers
    "border": "#E5DED0",
    "border_dark": "#D1C7B7",
    "border_light": "#EFEAE0",

    # Aliases for compatibility
    "primary": "#287D6B",
    "secondary": "#C6A568",
    "background": "#F7F5EF",
    "cards": "#FFFEFA",
    "danger": "#C25447",
    "success": "#287D6B",
    "warning": "#C6A568",
}

THEME = {
    "bg": COLORS["bg_canvas"],
    "sidebar": COLORS["sidebar"],
    "primary": COLORS["teal"],
    "secondary": COLORS["gold"],
    "cards": COLORS["surface_card"],
    "text": COLORS["text"],
    "text_muted": COLORS["text_muted"],
    "danger": COLORS["red"],
    "success": COLORS["teal"],
    "border": COLORS["border"]
}

__all__ = [
    "COLORS",
    "THEME",
    "inject_custom_css",
    "render_page_header",
    "render_kpi_card",
    "get_plotly_layout"
]

CUSTOM_CSS = """
<style>
    /* ── Typography Imports ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    /* ── Global Layout & Canvas ────────────────────────────────────── */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F7F5EF !important;
        color: #263746 !important;
        letter-spacing: -0.01em;
    }

    .main .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1440px;
    }

    /* ── Editorial Headings ────────────────────────────────────────── */
    h1, .rp-title {
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 600 !important;
        color: #142B3B !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 0.25rem !important;
        line-height: 1.15 !important;
    }

    h2, .rp-subtitle {
        font-family: 'Newsreader', Georgia, serif !important;
        font-weight: 500 !important;
        color: #142B3B !important;
        letter-spacing: -0.02em !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }

    h3, .rp-section-header {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #142B3B !important;
        margin-bottom: 0.4rem !important;
    }

    .rp-eyebrow {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.68rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 700;
        color: #C6A568;
        display: inline-block;
        margin-bottom: 0.25rem;
    }

    .rp-subtext {
        font-size: 0.90rem;
        color: #78838C;
        line-height: 1.5;
        margin-top: 0;
        margin-bottom: 1.25rem;
    }

    /* ── Midnight Navy Sidebar ─────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #142B3B !important;
        border-right: 1px solid #1D3A4F !important;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.4rem;
        padding-left: 1.1rem;
        padding-right: 1.1rem;
    }

    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* Hide the default circular radio glyphs completely */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-of-type > div:first-child > div:first-child {
        display: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 5px !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 9px 12px !important;
        border-radius: 6px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: #8C9DA8 !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        cursor: pointer !important;
        margin: 0 !important;
        transition: all 0.15s ease !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        color: #FFFEFA !important;
        background: rgba(255, 254, 250, 0.06) !important;
    }

    /* Active Nav Item: Muted Teal background + Champagne Gold indicator */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        color: #FFFEFA !important;
        font-weight: 600 !important;
        background: rgba(40, 125, 107, 0.28) !important;
        border-left: 3px solid #C6A568 !important;
        border-radius: 2px 6px 6px 2px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) * {
        color: #FFFEFA !important;
        font-weight: 600 !important;
    }

    /* Lucide-style Outline SVG Icons for each menu item */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p::before {
        content: "";
        display: inline-block;
        width: 16px;
        height: 16px;
        margin-right: 10px;
        flex: 0 0 16px;
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        opacity: 0.8;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:hover [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        opacity: 1;
    }

    /* 1. Sales Overview – LayoutDashboard */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='9' x='14' y='12' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='7' height='9' x='3' y='3' rx='1'/%3E%3Crect width='7' height='5' x='14' y='3' rx='1'/%3E%3Crect width='7' height='5' x='3' y='16' rx='1'/%3E%3C/svg%3E") !important;
    }

    /* 2. Sales Analytics – ChartNoAxesCombined */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16v5'/%3E%3Cpath d='M16 14v7'/%3E%3Cpath d='M20 10v11'/%3E%3Cpath d='m22 3-8.646 8.646a.5.5 0 0 1-.708 0L9.354 8.354a.5.5 0 0 0-.707 0L2 15'/%3E%3Cpath d='M4 18v3'/%3E%3Cpath d='M8 14v7'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 16v5'/%3E%3Cpath d='M16 14v7'/%3E%3Cpath d='M20 10v11'/%3E%3Cpath d='m22 3-8.646 8.646a.5.5 0 0 1-.708 0L9.354 8.354a.5.5 0 0 0-.707 0L2 15'/%3E%3Cpath d='M4 18v3'/%3E%3Cpath d='M8 14v7'/%3E%3C/svg%3E") !important;
    }

    /* 3. Product Analytics – Package */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m7.5 4.27 9 5.15'/%3E%3Cpath d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/%3E%3Cpath d='m3.3 7 8.7 5 8.7-5'/%3E%3Cpath d='M12 22V12'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m7.5 4.27 9 5.15'/%3E%3Cpath d='M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z'/%3E%3Cpath d='m3.3 7 8.7 5 8.7-5'/%3E%3Cpath d='M12 22V12'/%3E%3C/svg%3E") !important;
    }

    /* 4. Regional Analytics – MapPin */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0'/%3E%3Ccircle cx='12' cy='10' r='3'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0'/%3E%3Ccircle cx='12' cy='10' r='3'/%3E%3C/svg%3E") !important;
    }

    /* 5. Ask Your Data – MessageCircle */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(5) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7.9 20A9 9 0 1 0 4 16.1L2 22Z'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7.9 20A9 9 0 1 0 4 16.1L2 22Z'/%3E%3C/svg%3E") !important;
    }

    /* 6. Data Pipeline – Workflow */
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(6) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(6) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%238C9DA8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E") !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > *:nth-child(6):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > div:nth-child(6):has(input:checked) [data-testid="stMarkdownContainer"] p::before,
    section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6):has(input:checked) [data-testid="stMarkdownContainer"] p::before {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23369B86' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect width='8' height='8' x='3' y='3' rx='2'/%3E%3Cpath d='M7 11v4a2 2 0 0 0 2 2h4'/%3E%3Crect width='8' height='8' x='13' y='13' rx='2'/%3E%3C/svg%3E") !important;
    }

    /* ── Streamlit Border Container Styling (FXFlow Cards) ────────── */
    div[data-testid="stVerticalBlock"] > div[style*="border:"] {
        background-color: #FFFEFA !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 10px !important;
        padding: 1.15rem 1.3rem !important;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03) !important;
    }

    /* ── Badges ────────────────────────────────────────────────────── */
    .rp-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-family: 'IBM Plex Mono', monospace;
    }
    .rp-badge-teal {
        background: #E7F3F0;
        color: #287D6B;
        border: 1px solid rgba(40, 125, 107, 0.3);
    }
    .rp-badge-gold {
        background: #F9F4EB;
        color: #C6A568;
        border: 1px solid rgba(198, 165, 104, 0.3);
    }
    .rp-badge-red {
        background: #FBF0EE;
        color: #C25447;
        border: 1px solid rgba(194, 84, 71, 0.3);
    }
    .rp-badge-navy {
        background: #EAE6DE;
        color: #142B3B;
        border: 1px solid #D5CEBF;
    }

    /* ── Pipeline Stage Card ───────────────────────────────────────── */
    .pipeline-stage-card {
        background: #FFFEFA;
        border: 1px solid #E5DED0;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 6px rgba(20, 43, 59, 0.03);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 145px;
    }
    .pipeline-stage-num {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        color: #78838C;
        font-weight: 600;
        letter-spacing: 0.06em;
    }
    .pipeline-stage-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: #142B3B;
        margin: 4px 0 2px 0;
    }
    .pipeline-stage-metrics {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #263746;
        padding-top: 8px;
        border-top: 1px solid #EFEAE0;
        margin-top: 8px;
        line-height: 1.5;
    }
    .pipeline-flow-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        font-size: 1.3rem;
        color: #C6A568;
        font-weight: 700;
        padding-top: 45px;
    }

    /* ── Button Styles ─────────────────────────────────────────────── */
    div.stButton > button[kind="primary"] {
        background-color: #287D6B !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.1rem !important;
        font-size: 0.88rem !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #216959 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #FFFEFA !important;
        color: #142B3B !important;
        border: 1px solid #E5DED0 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.45rem 1.1rem !important;
        font-size: 0.88rem !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #F7F5EF !important;
        border-color: #C6A568 !important;
    }

    /* ── Clean DataFrames ──────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E5DED0 !important;
        border-radius: 8px !important;
        background: #FFFEFA !important;
    }
</style>
"""

def inject_custom_css(dark_mode: bool = False):
    """Injects FXFlow-identical CSS design system into Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    if dark_mode:
        dark_override = """
        <style>
            html, body, [class*="css"], .stApp {
                background-color: #0F1A24 !important;
                color: #F1F5F9 !important;
            }
            h1, h2, h3, .rp-title, .rp-subtitle, .rp-section-header {
                color: #FFFEFA !important;
            }
            div[data-testid="stVerticalBlock"] > div[style*="border:"] {
                background-color: #192837 !important;
                border-color: #273D52 !important;
            }
            .pipeline-stage-card {
                background: #192837 !important;
                border-color: #273D52 !important;
            }
            .pipeline-stage-title {
                color: #FFFEFA !important;
            }
            .pipeline-stage-metrics {
                color: #CBD5E1 !important;
                border-color: #273D52 !important;
            }
        </style>
        """
        st.markdown(dark_override, unsafe_allow_html=True)

def render_page_header(eyebrow: str, title: str, subtitle: str):
    """Renders clean, editorial page header."""
    header_html = (
        '<div style="padding-bottom: 0.5rem; border-bottom: 1px solid #E5DED0; margin-bottom: 1.25rem;">'
        f'<div class="rp-eyebrow">{eyebrow}</div>'
        f'<h1 class="rp-title" style="margin: 0; font-size: 2.1rem; line-height: 1.15;">{title}</h1>'
        f'<p class="rp-subtext" style="margin: 0.25rem 0 0 0;">{subtitle}</p>'
        '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

def render_kpi_card(title: str, value: str, subtext: str = "", delta: str = None, dark_mode: bool = False):
    """
    Renders an editorial KPI card using Streamlit's native st.container(border=True).
    Guarantees NO raw HTML leaks, unclosed tags, or indentation parsing bugs.
    """
    with st.container(border=True):
        delta_html = ""
        if delta:
            is_pos = not delta.startswith("-")
            d_color = COLORS["teal"] if is_pos else COLORS["red"]
            arrow = "▲" if is_pos else "▼"
            delta_html = f'<span style="font-family:\'IBM Plex Mono\', monospace; font-size:0.75rem; font-weight:700; color:{d_color}; margin-left:8px;">{arrow} {delta}</span>'

        content = (
            f'<div style="min-height: 90px; display: flex; flex-direction: column; justify-content: space-between;">'
            f'<div>'
            f'<div style="font-size: 0.70rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.10em; color: #78838C; margin-bottom: 4px;">{title}</div>'
            f'<div style="display: flex; align-items: baseline;">'
            f'<span style="font-family:\'IBM Plex Mono\', monospace; font-size: 1.75rem; font-weight: 700; color: #287D6B; letter-spacing: -0.02em; line-height: 1.1;">{value}</span>'
            f'{delta_html}'
            f'</div>'
            f'</div>'
            f'<div style="font-size: 0.74rem; color: #78838C; margin-top: 6px;">{subtext}</div>'
            f'</div>'
        )
        st.markdown(content, unsafe_allow_html=True)

def get_plotly_layout(title: str = "", dark_mode: bool = False) -> dict:
    """Returns a clean Plotly layout adhering to FXFlow's minimal editorial principles."""
    bg_color = "#192837" if dark_mode else "#FFFEFA"
    plot_bg = "#142332" if dark_mode else "#FAF7F0"
    text_color = "#F1F5F9" if dark_mode else "#263746"
    grid_color = "#273D52" if dark_mode else "#EAE3D5"
    slate_color = "#94A3B8" if dark_mode else "#78838C"

    return {
        "title": {
            "text": f"<b>{title}</b>" if title else "",
            "font": {"size": 14, "color": text_color, "family": "Newsreader, Georgia, serif"}
        },
        "paper_bgcolor": bg_color,
        "plot_bgcolor": plot_bg,
        "font": {"family": "Plus Jakarta Sans, sans-serif", "color": text_color, "size": 11},
        "margin": {"l": 45, "r": 20, "t": 40 if title else 20, "b": 35},
        "xaxis": {
            "showgrid": True,
            "gridcolor": grid_color,
            "linecolor": grid_color,
            "zeroline": False,
            "tickfont": {"size": 10, "color": slate_color}
        },
        "yaxis": {
            "showgrid": True,
            "gridcolor": grid_color,
            "linecolor": grid_color,
            "zeroline": False,
            "tickfont": {"size": 10, "color": slate_color}
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"size": 10, "color": text_color}
        }
    }
