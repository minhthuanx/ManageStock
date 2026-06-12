"""
Management Dashboard — Entry Point.
Refactored from 6465-line monolith into modular architecture.
"""
import streamlit as st

# Page Config MUST be first Streamlit call
st.set_page_config(
    page_title="Management Dashboard",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="collapsed",
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

# ── Load category lists ──
from _database import load_csv
from _config import PET_LIST_FILE, NS_LIST_FILE, TRAIT_LIST, LIST_SCHEMA
pet_db   = load_csv(PET_LIST_FILE, LIST_SCHEMA)
ns_db    = load_csv(NS_LIST_FILE,  LIST_SCHEMA)
trait_db = load_csv(TRAIT_LIST,    LIST_SCHEMA)

# ── Owner mapping ──
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
    "📦 Kho Lẻ", "🗃️ Lô Pack", "📊 Thống Kê", "⏳ Tồn Lâu", "🎮 Eldorado", "⚙️ Cài Đặt",
])

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
