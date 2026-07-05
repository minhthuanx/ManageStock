"""
Global CSS string constant — Linear-style minimal dark theme.
Flat surfaces, subtle borders, muted palette, no gradients/glassmorphism.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* --- Root variables — Linear-inspired --- */
:root {
  --bg:        #0f0f0f;
  --surface:   #171717;
  --surface2:  #1e1e1e;
  --surface3:  #252525;
  --border:    #262626;
  --border-h:  #333333;
  --accent:    #8b5cf6;
  --accent-h:  #a78bfa;
  --green:     #22c55e;
  --green-bg:  rgba(34,197,94,0.08);
  --red:       #ef4444;
  --red-bg:    rgba(239,68,68,0.08);
  --yellow:    #eab308;
  --yellow-bg: rgba(234,179,8,0.08);
  --text:      #e5e5e5;
  --text2:     #a3a3a3;
  --text3:     #737373;
  --radius:    8px;
}

/* --- Base --- */
*, *::before, *::after { box-sizing: border-box; }
html { scrollbar-gutter: stable; overflow-y: scroll; }
body { overflow-anchor: none; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
.block-container { padding: 1rem 1.5rem 3rem !important; max-width: 1400px; }

/* --- Layout shift fix --- */
[data-testid="stAppViewContainer"] > section.main { scrollbar-gutter: stable; position: relative; }
[data-testid="stAppViewContainer"] > section.main > div.block-container { margin-left: 0 !important; margin-right: auto !important; }
[data-testid="stTabContent"] { scrollbar-gutter: stable; }

/* --- Main content area --- */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}

/* --- Metrics --- */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.3rem) !important;
  font-weight: 600 !important;
  color: var(--text) !important;
  letter-spacing: -0.01em !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.7rem !important;
  color: var(--text3) !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  font-weight: 500 !important;
}

/* --- Buttons --- */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.005em !important;
  transition: background 0.12s ease, color 0.12s ease, border-color 0.12s ease !important;
  width: 100%;
  border: 1px solid var(--border) !important;
  background: var(--surface2) !important;
  color: var(--text) !important;
}
.stButton > button:hover {
  background: var(--surface3) !important;
  border-color: var(--border-h) !important;
}
.stButton > button:active { background: var(--border) !important; }

.stButton > button[kind="primary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent-h) !important;
  border-color: var(--accent-h) !important;
}

/* --- Secondary / tertiary buttons --- */
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text2) !important;
  border: 1px solid var(--border) !important;
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

/* --- Tabs --- */
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
  padding: 0.6rem 1rem !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.02em !important;
  color: var(--text3) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.12s ease !important;
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
  background: var(--accent) !important;
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

/* --- Inputs --- */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  transition: border-color 0.12s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}

/* --- Containers / borders --- */
[data-testid="stVerticalBlockBorderWrapper"] {
  --border-color-default: var(--border) !important;
  border-color: var(--border) !important;
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  box-shadow: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  --border-color-default: var(--border) !important;
  border-color: var(--border) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
  box-shadow: none !important;
}

/* --- Tab content --- */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1.25rem !important;
}

/* --- DataFrames --- */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
  background: var(--surface) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--text3) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--text) !important; }

/* --- Status badges --- */
.badge-sold  { color: var(--green); font-weight: 600; }
.badge-stock { color: var(--accent); font-weight: 600; }

/* --- Hero banner — flat, minimal --- */
.hero-banner {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.hero-banner .logo { font-size: 1.6rem; opacity: 0.85; }
.hero-banner h1 { margin: 0; font-size: clamp(1rem, 2.5vw, 1.3rem); font-weight: 600; letter-spacing: -0.01em; }
.hero-banner p  { margin: 0; color: var(--text3); font-size: 0.78rem; }

/* --- Stat cards — flat pills --- */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 0.9rem;
  text-align: center;
}
.stat-card:hover { border-color: var(--border-h); }
.stat-card .val { font-size: 1.1rem; font-weight: 600; color: var(--text); }
.stat-card .lbl { font-size: 0.68rem; color: var(--text3); margin-top: 0.15rem; letter-spacing: 0.04em; text-transform: uppercase; font-weight: 500; }

/* --- Section headings — simple, clean --- */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text3);
  margin: 1.5rem 0 0.75rem !important;
  padding: 0;
  width: 100%;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
  margin-left: 0.5rem;
}

/* --- Stat panels — flat --- */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem 0.75rem;
  margin-bottom: 0.75rem;
}

/* --- Metric cards — flat with subtle left accent --- */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 2px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.6rem 0.8rem !important;
  transition: border-color 0.15s ease !important;
}
div[data-testid="stMetric"]:hover {
  border-color: var(--border-h) !important;
  border-left-color: var(--accent) !important;
}

/* --- Expanders — flat --- */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  overflow: hidden !important;
  box-shadow: none !important;
}
[data-testid="stExpander"] summary {
  padding: 0.6rem 0.85rem !important;
  font-weight: 500 !important;
  font-size: 0.84rem !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* --- Progress bar — flat --- */
[data-testid="stProgressBar"] > div > div {
  background: var(--accent) !important;
  border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 4px !important;
}

/* --- Scrollbar --- */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-h); }

/* --- Mobile responsive --- */
@media (max-width: 768px) {
  .block-container { padding: 0.5rem 0.75rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.35rem 0.6rem !important; font-size: 0.72rem !important; }
  .hero-banner { padding: 0.6rem 0.8rem; gap: 0.5rem; }
  .hero-banner .logo { font-size: 1.2rem; }
  .hero-banner h1 { font-size: 0.95rem !important; }
  .hero-banner p { font-size: 0.7rem; }
  .sec-heading { font-size: 0.68rem; margin: 0.75rem 0 0.4rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.3rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
  .stForm { padding: 0.5rem !important; }
  .stButton > button { padding: 0.45rem 0.75rem !important; font-size: 0.8rem !important; }
  .stDataFrame { max-height: 350px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.75rem !important; }
  [data-testid="stExpander"] summary { font-size: 0.82rem !important; padding: 0.4rem 0.6rem !important; }
  .stTextInput input, .stNumberInput input { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.85rem !important; }
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.2rem !important; }
  [data-testid="stRadio"] label { font-size: 0.75rem !important; padding: 0.25rem 0.5rem !important; }
  [data-testid="stSidebar"] { min-width: 260px !important; }
  .js-plotly-plot { min-height: 250px !important; }
}

/* --- Copy description button --- */
.copy-desc-btn {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-weight: 500 !important;
}
.copy-desc-btn:hover { background: var(--accent-h) !important; }

/* --- Toast --- */
[data-testid="stToast"] {
  font-size: 0.84rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
  color: var(--text) !important;
}
[data-testid="stToastContainer"] { bottom: 2rem !important; right: 1.5rem !important; }

/* --- Alerts --- */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.82rem !important;
  padding: 0.6rem 0.85rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: rgba(139,92,246,0.06) !important;
  border-color: rgba(139,92,246,0.2) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="success"], div[data-testid="stSuccess"] > div {
  background: var(--green-bg) !important;
  border-color: rgba(34,197,94,0.2) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="warning"], div[data-testid="stWarning"] > div {
  background: var(--yellow-bg) !important;
  border-color: rgba(234,179,8,0.2) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="error"], div[data-testid="stError"] > div {
  background: var(--red-bg) !important;
  border-color: rgba(239,68,68,0.2) !important;
  color: var(--text) !important;
}

/* --- Form container --- */
[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}

/* --- Selectbox / multiselect --- */
[data-baseweb="select"] > div:first-child {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--surface3) !important;
}
[data-baseweb="tag"] {
  background: rgba(139,92,246,0.12) !important;
  color: var(--accent) !important;
  border: none !important;
  border-radius: 4px !important;
}

/* --- Caption --- */
[data-testid="stCaptionContainer"] p {
  color: var(--text3) !important;
  font-size: 0.74rem !important;
}

/* --- Divider --- */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.75rem 0 !important;
}

/* --- Sidebar section headings --- */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
  padding: 0.4rem 0 0.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.35rem;
  display: block;
}

/* --- Radio pill chips — minimal --- */
[data-testid="stRadio"] > div { gap: 0.25rem !important; flex-wrap: wrap !important; }
[data-testid="stRadio"] label {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  padding: 0.25rem 0.7rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--text3) !important;
  cursor: pointer !important;
  transition: all 0.12s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(139,92,246,0.1) !important;
  border-color: rgba(139,92,246,0.3) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: var(--border-h) !important;
  color: var(--text) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* --- Ton lau badge --- */
.badge-warn {
  background: rgba(234,179,8,0.1);
  color: var(--yellow);
  border: 1px solid rgba(234,179,8,0.2);
  border-radius: 6px;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
}

/* --- Hide Streamlit branding --- */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* --- Empty state --- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  gap: 0.4rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2rem; opacity: 0.35; }
.empty-state .es-title { font-size: 0.9rem; font-weight: 500; color: var(--text3); }
.empty-state .es-sub { font-size: 0.76rem; color: var(--text3); opacity: 0.6; }

/* --- Button loading spinner --- */
.btn-busy {
  opacity: 0.5 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* --- Plotly chart containers --- */
.js-plotly-plot {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}
</style>"""
