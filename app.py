"""
Management Dashboard — Entry Point.
Refactored from 6465-line monolith into modular architecture.
"""
import pandas as pd
import streamlit as st

# Page Config MUST be first Streamlit call
st.set_page_config(
    page_title="Management Dashboard",
    page_icon="👻",
    layout="wide",
)

from _css import CSS_STRING
from _database import USE_SUPABASE
from _session import init_session
from _eldorado_helpers import init_eldorado_client
from _ui_hero import render_hero_banner
from _ui_sidebar import render_sidebar

# ── Inject CSS ──
st.markdown(CSS_STRING, unsafe_allow_html=True)

# ── Initialize session state & load data ──
init_session()

# ── Eldorado client ──
eld_client = init_eldorado_client()

# ── Get current data from session state ──
df           = st.session_state.df
bulk_df      = st.session_state.bulk_df
bulk_history = st.session_state.bulk_history

# ── Pre-compute shared filters (avoid 3x redundant apply per rerun) ──
from _helpers import is_today_timestamp, is_today_bulk_date
from _timezone import now_vn as _now_vn
_today = _now_vn().date()
st.session_state["_sold_today"] = (
    df[df["time_ban"].apply(lambda ts: is_today_timestamp(ts, _today))]
    if "time_ban" in df.columns else pd.DataFrame(columns=df.columns)
)
st.session_state["_bulk_today"] = (
    bulk_history[bulk_history["Ngày Bán"].apply(lambda d: is_today_bulk_date(d, _today))]
    if (not bulk_history.empty and "Ngày Bán" in bulk_history.columns) else pd.DataFrame()
)

# ── Load category lists (cached — no disk read on rerun) ──
from _database import load_csv
from _config import PET_LIST_FILE, NS_LIST_FILE, TRAIT_LIST, LIST_SCHEMA

@st.cache_data(ttl=300, show_spinner=False)
def _load_cat_lists():
    return (
        load_csv(PET_LIST_FILE, LIST_SCHEMA),
        load_csv(NS_LIST_FILE,  LIST_SCHEMA),
        load_csv(TRAIT_LIST,    LIST_SCHEMA),
    )

pet_db, ns_db, trait_db = _load_cat_lists()

# ── Owner mapping (cached — reads file only when content changes) ──
from _helpers import _load_owner_ns_map
st.session_state["_owner_ns_map"] = _load_owner_ns_map()

# ── Eldorado settings ──
from _eldorado_helpers import _load_eld_settings
if "eld_settings" not in st.session_state:
    st.session_state.eld_settings = _load_eld_settings()

# ── Render Hero Banner ──
render_hero_banner(df, bulk_df, bulk_history)

# ── Render Sidebar ──
render_sidebar(df, bulk_df, bulk_history, USE_SUPABASE)

# ── Main Tabs ──
from tab_kho    import render_tab_kho
from tab_chart  import render_tab_chart
from tab_tonlau import render_tab_tonlau
from tab_lopack import render_tab_lopack

tab_kho, tab_pack, tab_chart, tab_ton, tab_eldo, tab_settings = st.tabs([
    "Kho Lẻ", "Lô Pack", "Thống Kê", "Tồn Lâu", "Eldorado", "Cài Đặt",
], key="main_tabs")

with tab_kho:
    render_tab_kho(df, bulk_df, bulk_history, pet_db, ns_db, trait_db, eld_client)

with tab_pack:
    render_tab_lopack(df, bulk_df, bulk_history, pet_db, ns_db, trait_db)

with tab_chart:
    render_tab_chart(df, bulk_df, bulk_history)

with tab_ton:
    render_tab_tonlau(df, bulk_df, bulk_history)

with tab_eldo:
    from tab_eldorado import render_tab_eldorado
    render_tab_eldorado(eld_client)

with tab_settings:
    from tab_caidat import render_tab_caidat
    render_tab_caidat(pet_db, ns_db, trait_db, eld_client)
