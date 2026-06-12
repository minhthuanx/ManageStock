# =============================================================================
# TAB 1: KHO LE — Orchestrator
# =============================================================================
# Delegates rendering to sub-modules; sets up two-column layout and passes
# shared data (df, reference DBs, eld_client) through to each render fn.
# =============================================================================

import streamlit as st

from tab_kho_ai import render_ai_vision
from tab_kho_json import render_json_import
from tab_kho_form import render_manual_import
from tab_kho_sell import render_sell_single
from tab_kho_table import render_inventory_table
from tab_kho_bulk import render_bulk_sell, render_resell


def render_tab_kho(df, bulk_df, bulk_history, pet_db, ns_db, trait_db, eld_client):
    """Render the full 'Kho Le' tab (Tab 1).

    Layout
    ------
    col_in  (1.15) : AI Vision, JSON import, manual form
    col_sell (1)   : Single-pet sell
    (full width)   : Inventory table (copy title + delete rows)
    (full width)   : Bulk sell cart
    (full width)   : Re-sell workflow
    """

    col_in, col_sell = st.columns([1.15, 1], gap="medium")

    # ── NHAP KHO (left column) ──
    with col_in:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">Nhập Kho</div>', unsafe_allow_html=True)

            # AI Vision — multi-image upload + Groq API
            render_ai_vision(df, pet_db, ns_db, trait_db)

            # JSON Import — paste JSON from game
            render_json_import(pet_db, ns_db, trait_db, eld_client)

            # Manual form — always visible
            render_manual_import(df, pet_db, ns_db, trait_db)

    # ── BAN LE (right column) ──
    with col_sell:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">Bán Pet Lẻ</div>', unsafe_allow_html=True)
            render_sell_single(df)

    # ── BANG TON KHO (full width, below both columns) ──
    render_inventory_table(df)

    # ── BULK SELL + RE-SELL (full width, below table) ──
    render_bulk_sell(df)
    render_resell(df)
