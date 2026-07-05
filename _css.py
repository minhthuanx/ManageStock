"""
Global CSS string — Brix-inspired dark theme.
Dark bg + floating glass cards, purple gradient accent, large readable elements.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root — Brix-inspired ── */
:root {
  --bg:        #08080c;
  --surface:   #0f0f15;
  --surface2:  #15151e;
  --surface3:  #1c1c28;
  --border:    rgba(255,255,255,0.06);
  --border-h:  rgba(255,255,255,0.12);
  --accent:    #7c5cfc;
  --accent-h:  #9b7eff;
  --accent-bg: rgba(124,92,252,0.08);
  --accent2:   #c084fc;
  --accent2-bg:rgba(192,132,252,0.08);
  --green:     #34d399;
  --green-bg:  rgba(52,211,153,0.08);
  --green-dim: rgba(52,211,153,0.15);
  --red:       #f87171;
  --red-bg:    rgba(248,113,113,0.08);
  --red-dim:   rgba(248,113,113,0.15);
  --yellow:    #fbbf24;
  --yellow-bg: rgba(251,191,36,0.08);
  --text:      #f0f0f5;
  --text2:     #a8a8b8;
  --text3:     #6b6b80;
  --radius:    14px;
  --radius-sm: 8px;
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }
html { scrollbar-gutter: stable; overflow-y: scroll; }
body { overflow-anchor: none; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  color: var(--text) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* ── Background ── */
[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
.block-container {
  padding: 1.2rem 2rem 3rem !important;
  max-width: 1500px;
}

/* ── Layout fix ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] { scrollbar-gutter: stable; }
[data-testid="stAppViewContainer"] > section.main {
  scrollbar-gutter: stable;
}

/* ── Metrics — Brix large readable ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1.15rem, 2.8vw, 1.65rem) !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  letter-spacing: -0.025em !important;
  line-height: 1.3 !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.78rem !important;
  color: var(--text3) !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  margin-bottom: 0.15rem !important;
}
div[data-testid="stMetricDelta"] {
  font-size: 0.82rem !important;
  font-weight: 600 !important;
}

/* ── Buttons — Brix style ── */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.88rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.005em !important;
  transition: all 0.15s ease !important;
  width: 100%;
  border: 1px solid var(--border) !important;
  background: var(--surface2) !important;
  color: var(--text) !important;
  padding: 0.65rem 1.1rem !important;
}
.stButton > button:hover {
  background: var(--surface3) !important;
  border-color: var(--border-h) !important;
}
.stButton > button:active {
  background: var(--border) !important;
  transform: scale(0.985);
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #7c5cfc, #c084fc) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;
  box-shadow: 0 0 24px rgba(124,92,252,0.3), 0 4px 12px rgba(0,0,0,0.3) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  text-transform: uppercase !important;
  font-size: 0.85rem !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #9b7eff, #d4a5ff) !important;
  box-shadow: 0 0 30px rgba(124,92,252,0.4), 0 6px 16px rgba(0,0,0,0.35) !important;
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--surface2) !important;
  border-color: var(--border-h) !important;
  color: var(--text) !important;
  box-shadow: none !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--text3) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--text) !important;
  box-shadow: none !important;
}

/* ── Tabs — Brix clean ── */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 1px solid var(--border) !important;
  background: transparent !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTab"] {
  border-radius: 0 !important;
  padding: 0.75rem 1.3rem !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.02em !important;
  color: var(--text3) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.15s ease !important;
  position: relative !important;
  outline: none !important;
  text-transform: none !important;
}
[data-testid="stTab"]::after {
  content: '' !important;
  display: block !important;
  position: absolute !important;
  bottom: -1px !important;
  left: 0 !important;
  width: 100% !important;
  height: 2px !important;
  border-radius: 1px !important;
  background: linear-gradient(90deg, #7c5cfc, #c084fc) !important;
  opacity: 0 !important;
  transform: scaleX(0) !important;
  transition: opacity 0.15s ease, transform 0.15s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--text) !important;
  font-weight: 600 !important;
  background: transparent !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text2) !important;
  background: transparent !important;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
  font-size: 0.9rem !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(124,92,252,0.12) !important;
}

/* ── Containers — Brix glass card ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: rgba(255,255,255,0.06) !important;
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.2) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: rgba(255,255,255,0.06) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(124,92,252,0.25) !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 32px rgba(124,92,252,0.08) !important;
}

/* ── Tab content — Brix panel ── */
[data-testid="stTabContent"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1.5rem !important;
  box-shadow: 0 0 24px rgba(124,92,252,0.03) !important;
}

/* ── DataFrames ── */
.stDataFrame {
  border-radius: var(--radius-sm) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--text3) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--text) !important; }

/* ── Status badges ── */
.badge-sold  { color: var(--green); font-weight: 600; }
.badge-stock { color: var(--accent); font-weight: 600; }

/* ── Hero banner — Brix floating card ── */
.hero-banner {
  background: var(--surface);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius);
  padding: 1.4rem 1.8rem;
  margin-bottom: 1.2rem;
  display: flex;
  align-items: center;
  gap: 1.2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.2);
  position: relative;
}
.hero-banner .logo { font-size: 1.8rem; opacity: 0.9; }
.hero-banner h1 {
  margin: 0;
  font-size: clamp(1.15rem, 2.8vw, 1.55rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #ffffff;
}
.hero-banner p  { margin: 0; color: var(--text3); font-size: 0.85rem; letter-spacing: 0.04em; }

/* ── Stat cards — Brix large ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.7rem;
  margin-bottom: 1rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  text-align: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stat-card:hover {
  border-color: rgba(124,92,252,0.25);
  box-shadow: 0 0 16px rgba(124,92,252,0.06);
}
.stat-card .val { font-size: 1.35rem; font-weight: 700; color: var(--text); }
.stat-card .lbl {
  font-size: 0.72rem;
  color: var(--text3);
  margin-top: 0.25rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-weight: 600;
}

/* ── Section headings — Brix style ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text2);
  margin: 1.5rem 0 0.85rem !important;
  padding: 0;
  width: 100%;
  border-bottom: 1px solid rgba(124,92,252,0.15);
  padding-bottom: 0.55rem;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, #7c5cfc, #c084fc);
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(124,92,252,0.2), transparent);
  margin-left: 0.5rem;
}

/* ── Stat panels — Brix card ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.1rem 1.3rem 0.85rem;
  margin-bottom: 0.85rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  transition: border-color 0.15s ease;
}
.stat-panel:hover {
  border-color: rgba(124,92,252,0.25);
}

/* ── Metric cards — Brix glass with gradient accent ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.85rem 1rem !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}
div[data-testid="stMetric"]:hover {
  border-color: rgba(124,92,252,0.3) !important;
  border-left-color: var(--accent-h) !important;
  box-shadow: 0 0 20px rgba(124,92,252,0.08) !important;
}

/* ── Expanders — Brix panel ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
  transition: border-color 0.15s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(124,92,252,0.25) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.7rem 1rem !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, #7c5cfc, #c084fc) !important;
  border-radius: 6px !important;
  box-shadow: 0 0 12px rgba(124,92,252,0.25);
}
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 6px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-h); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,92,252,0.35); }

/* ── Form container — Brix floating ── */
[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1.2rem !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
}

/* ── Selectbox / multiselect ── */
[data-baseweb="select"] > div:first-child {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(124,92,252,0.12) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--surface3) !important;
}
[data-baseweb="tag"] {
  background: rgba(124,92,252,0.12) !important;
  color: var(--accent2) !important;
  border: none !important;
  border-radius: 6px !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--text3) !important;
  font-size: 0.8rem !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.85rem 0 !important;
}

/* ── Sidebar section headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
  padding: 0.45rem 0 0.3rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.4rem;
  display: block;
}

/* ── Radio pill chips ── */
[data-testid="stRadio"] > div { gap: 0.3rem !important; flex-wrap: wrap !important; }
[data-testid="stRadio"] label {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  padding: 0.35rem 0.9rem !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  color: var(--text3) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(124,92,252,0.1) !important;
  border-color: rgba(124,92,252,0.35) !important;
  color: var(--accent2) !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: var(--border-h) !important;
  color: var(--text) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Ton lau badge ── */
.badge-warn {
  background: rgba(124,92,252,0.1);
  color: var(--accent2);
  border: 1px solid rgba(124,92,252,0.25);
  border-radius: 999px;
  padding: 3px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.88rem !important;
  padding: 0.7rem 0.95rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: rgba(124,92,252,0.04) !important;
  border-color: rgba(124,92,252,0.18) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="success"], div[data-testid="stSuccess"] > div {
  background: var(--green-bg) !important;
  border-color: rgba(52,211,153,0.2) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="warning"], div[data-testid="stWarning"] > div {
  background: var(--yellow-bg) !important;
  border-color: rgba(251,191,36,0.2) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="error"], div[data-testid="stError"] > div {
  background: var(--red-bg) !important;
  border-color: rgba(248,113,113,0.2) !important;
  color: var(--text) !important;
}

/* ── Plotly chart containers — Brix glass ── */
.js-plotly-plot {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  overflow: hidden !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25) !important;
}

/* ── Copy description button ── */
.copy-desc-btn {
  background: linear-gradient(135deg, #7c5cfc, #c084fc) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  box-shadow: 0 0 18px rgba(124,92,252,0.25) !important;
}
.copy-desc-btn:hover { background: linear-gradient(135deg, #9b7eff, #d4a5ff) !important; }

/* ── Toast ── */
[data-testid="stToast"] {
  font-size: 0.88rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
  color: var(--text) !important;
}
[data-testid="stToastContainer"] { bottom: 2rem !important; right: 1.5rem !important; }

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  gap: 0.5rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2.2rem; opacity: 0.35; }
.empty-state .es-title { font-size: 0.95rem; font-weight: 500; color: var(--text3); }
.empty-state .es-sub { font-size: 0.82rem; color: var(--text3); opacity: 0.6; }

/* ── Button loading spinner ── */
.btn-busy {
  opacity: 0.5 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
  .block-container { padding: 0.6rem 0.85rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 1.15rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.72rem !important; }
  .stat-card .val { font-size: 1.15rem; }
  [data-testid="stTab"] { padding: 0.45rem 0.7rem !important; font-size: 0.78rem !important; }
  .hero-banner { padding: 0.8rem 1rem; gap: 0.6rem; }
  .hero-banner .logo { font-size: 1.4rem; }
  .hero-banner h1 { font-size: 1.05rem !important; }
  .hero-banner p { font-size: 0.78rem; }
  .sec-heading { font-size: 0.74rem; margin: 0.85rem 0 0.5rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.4rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
  .stForm { padding: 0.6rem !important; }
  .stButton > button { padding: 0.55rem 0.85rem !important; font-size: 0.85rem !important; }
  .stDataFrame { max-height: 400px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.8rem !important; }
  [data-testid="stExpander"] summary { font-size: 0.88rem !important; padding: 0.5rem 0.7rem !important; }
  .stTextInput input, .stNumberInput input { font-size: 0.9rem !important; padding: 0.45rem 0.7rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.9rem !important; }
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.25rem !important; }
  [data-testid="stRadio"] label { font-size: 0.8rem !important; padding: 0.3rem 0.6rem !important; }
  [data-testid="stSidebar"] { min-width: 280px !important; }
  .js-plotly-plot { min-height: 280px !important; }
}
</style>"""
