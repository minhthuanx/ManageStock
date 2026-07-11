"""
Session state initialization — data loading and skeleton UI.
"""
import pandas as pd
import streamlit as st

from _timezone import now_vn
from _database import (
    USE_SUPABASE, load_inventory, load_bulk, load_bulk_history,
    _load_groq_key_from_supabase, _load_pinned_resell_from_supabase,
)
from _helpers import _load_owner_ns_map, _save_owner_ns_map, normalize_df
from _config import MAIN_SCHEMA, BULK_SCHEMA, HISTORY_SCHEMA


def init_session():
    if "initialized" not in st.session_state:
        _sk_ph = st.empty()
        _sk_ph.markdown(
            '<style>@keyframes _sk{0%{background-position:200% 0}100%{background-position:-200% 0}}</style>'
            '<div style="padding:1.2rem 0;display:flex;flex-direction:column;gap:0.65rem;">'
            '<div style="height:22px;width:38%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1a22 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.55rem;margin:0.3rem 0;">'
            + ('<div style="height:68px;border-radius:10px;background:linear-gradient(90deg,#110f1a 25%,#1a1a22 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>' * 4) +
            '</div>'
            '<div style="height:130px;border-radius:10px;background:linear-gradient(90deg,#110f1a 25%,#1a1a22 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="height:13px;width:55%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1a22 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="height:13px;width:75%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1a22 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        _inv_df   = load_inventory()
        _bulk_r   = load_bulk()
        _hist_r   = load_bulk_history()
        _groq_r   = _load_groq_key_from_supabase()
        _pinned_r = _load_pinned_resell_from_supabase()

        from _helpers import apply_ngay_ton
        st.session_state.df           = apply_ngay_ton(_inv_df)
        st.session_state.bulk_df      = _bulk_r
        st.session_state.bulk_history = _hist_r
        if not st.session_state.get("groq_key") and _groq_r:
            st.session_state.groq_key = _groq_r
        if "pinned_resell" not in st.session_state:
            st.session_state.pinned_resell = _pinned_r
        _sk_ph.empty()
        st.session_state.initialized = True
    else:
        st.session_state.df = normalize_df(st.session_state.get("df", pd.DataFrame()), MAIN_SCHEMA)
        st.session_state.bulk_df = normalize_df(st.session_state.get("bulk_df", pd.DataFrame()), BULK_SCHEMA)
        st.session_state.bulk_history = normalize_df(st.session_state.get("bulk_history", pd.DataFrame()), HISTORY_SCHEMA)
