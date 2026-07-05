"""
Global CSS string — TinyFish minimalist dark theme.
Clean cards, orange glow borders, grid background, monospace labels.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Root — TinyFish minimalist ── */
:root {
  --bg:        #0a0a0f;
  --surface:   #0e0e14;
  --surface2:  #13131a;
  --surface3:  #1a1a22;
  --border:    rgba(255,255,255,0.06);
  --border-h:  rgba(255,255,255,0.10);
  --accent:    #ff6a00;
  --accent-h:  #ff8533;
  --accent-bg: rgba(255,106,0,0.06);
  --green:     #22c55e;
  --green-bg:  rgba(34,197,94,0.06);
  --red:       #ef4444;
  --red-bg:    rgba(239,68,68,0.06);
  --yellow:    #eab308;
  --yellow-bg: rgba(234,179,8,0.06);
  --text:      #e8e8e8;
  --text2:     #999999;
  --text3:     #555555;
  --radius:    8px;
  --radius-sm: 6px;
  --mono:      'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
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
  background: var(--bg) !important;
  border-right: 1px solid var(--border) !important;
}
.block-container {
  padding: 1.2rem 2rem 3rem !important;
  max-width: 1440px;
}

/* ── Grid pattern overlay ── */
[data-testid="stAppViewContainer"] > section.main {
  position: relative;
}
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px) !important;
  background-size: 48px 48px !important;
  background-position: -1px -1px !important;
}

/* ── Layout ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] { scrollbar-gutter: stable; }
[data-testid="stAppViewContainer"] > section.main { scrollbar-gutter: stable; }

/* ── Metrics — original sizes, clean ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.3rem) !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  letter-spacing: -0.02em !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.7rem !important;
  color: var(--text3) !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  font-weight: 500 !important;
  font-family: var(--mono) !important;
}

/* ── Buttons — minimalist pill ── */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.005em !important;
  transition: all 0.15s ease !important;
  width: 100%;
  border: 1px solid var(--border) !important;
  background: var(--surface2) !important;
  color: var(--text) !important;
  padding: 0.55rem 1rem !important;
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
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;
  box-shadow: 0 0 20px rgba(255,106,0,0.2), 0 0 40px rgba(255,106,0,0.06) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  text-transform: uppercase !important;
  font-size: 0.8rem !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--accent-h) !important;
  box-shadow: 0 0 24px rgba(255,106,0,0.3), 0 0 48px rgba(255,106,0,0.1) !important;
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

/* ── Tabs — clean minimal with orange accent ── */
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
  padding: 0.65rem 1.1rem !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.02em !important;
  color: var(--text3) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.15s ease !important;
  position: relative !important;
  outline: none !important;
  text-transform: none !important;
  font-family: var(--mono) !important;
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

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(255,106,0,0.08) !important;
}

/* ── Containers — clean dark cards, orange glow on hover ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: rgba(255,106,0,0.12) !important;
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: rgba(255,106,0,0.12) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(255,106,0,0.35) !important;
  box-shadow: 0 0 16px rgba(255,106,0,0.06), 0 1px 4px rgba(0,0,0,0.3) !important;
}

/* ── Tab content — minimal panel ── */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: none !important;
  border-top: none !important;
  border-radius: 0 !important;
  padding: 0.5rem 0 2rem 0 !important;
  box-shadow: none !important;
}

/* ── DataFrames ── */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--text3) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--text) !important; }

/* ── Status badges ── */
.badge-sold  { color: var(--green); font-weight: 600; }
.badge-stock { color: var(--accent); font-weight: 600; }

/* ── Hero banner — TinyFish style ── */
.hero-banner {
  background: var(--surface);
  border: 1px solid rgba(255,106,0,0.2);
  border-radius: var(--radius);
  padding: 1.15rem 1.4rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 0 24px rgba(255,106,0,0.04), 0 1px 3px rgba(0,0,0,0.3);
  position: relative;
}
.hero-banner .logo { font-size: 1.6rem; opacity: 0.9; }
.hero-banner h1 {
  margin: 0;
  font-size: clamp(1.05rem, 2.5vw, 1.35rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #ffffff;
}
.hero-banner p  { margin: 0; color: var(--text3); font-size: 0.78rem; letter-spacing: 0.04em; font-family: var(--mono); }

/* ── Stat cards — minimal with orange glow ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.55rem;
  margin-bottom: 0.8rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 0.9rem;
  text-align: center;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.stat-card:hover {
  border-color: rgba(255,106,0,0.25);
  box-shadow: 0 0 12px rgba(255,106,0,0.05);
}
.stat-card .val { font-size: 1.1rem; font-weight: 700; color: var(--text); }
.stat-card .lbl {
  font-size: 0.66rem;
  color: var(--text3);
  margin-top: 0.2rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  font-weight: 500;
  font-family: var(--mono);
}

/* ── Section headings — monospace caps, orange accent ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  font-weight: 700;
  font-family: var(--mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 1.5rem 0 0.75rem !important;
  padding: 0;
  width: 100%;
  border-bottom: 1px solid rgba(255,106,0,0.12);
  padding-bottom: 0.5rem;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: var(--accent);
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255,106,0,0.08);
  margin-left: 0.5rem;
}

/* ── Stat panels — minimal card ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem 0.75rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.15s ease;
}
.stat-panel:hover {
  border-color: rgba(255,106,0,0.25);
}

/* ── Metric cards — minimal with orange left accent ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.65rem 0.85rem !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
div[data-testid="stMetric"]:hover {
  border-color: rgba(255,106,0,0.25) !important;
  border-left-color: var(--accent-h) !important;
  box-shadow: 0 0 14px rgba(255,106,0,0.05) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  overflow: hidden !important;
  transition: border-color 0.15s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(255,106,0,0.2) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.65rem 0.9rem !important;
  font-weight: 500 !important;
  font-size: 0.84rem !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: var(--accent) !important;
  border-radius: 4px !important;
  box-shadow: 0 0 8px rgba(255,106,0,0.2);
}
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 4px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-h); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,106,0,0.3); }

/* ── Form container ── */
[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}

/* ── Selectbox / multiselect ── */
[data-baseweb="select"] > div:first-child {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(255,106,0,0.08) !important;
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
  background: rgba(255,106,0,0.1) !important;
  color: var(--accent) !important;
  border: none !important;
  border-radius: 4px !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--text3) !important;
  font-size: 0.74rem !important;
  font-family: var(--mono) !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.75rem 0 !important;
}

/* ── Sidebar section headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 700;
  font-family: var(--mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  padding: 0.4rem 0 0.25rem;
  border-bottom: 1px solid rgba(255,106,0,0.12);
  margin-bottom: 0.35rem;
  display: block;
}

/* ── Radio pill chips ── */
[data-testid="stRadio"] > div { gap: 0.25rem !important; flex-wrap: wrap !important; }
[data-testid="stRadio"] label {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  font-family: var(--mono) !important;
  color: var(--text3) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(255,106,0,0.1) !important;
  border-color: rgba(255,106,0,0.35) !important;
  color: var(--accent) !important;
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
  background: rgba(255,106,0,0.1);
  color: var(--accent);
  border: 1px solid rgba(255,106,0,0.25);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  font-family: var(--mono);
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.82rem !important;
  padding: 0.6rem 0.85rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: rgba(255,106,0,0.04) !important;
  border-color: rgba(255,106,0,0.15) !important;
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

/* ── Plotly chart containers — clean ── */
.js-plotly-plot {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}

/* ── Copy description button ── */
.copy-desc-btn {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  box-shadow: 0 0 14px rgba(255,106,0,0.18) !important;
}
.copy-desc-btn:hover { background: var(--accent-h) !important; }

/* ── Toast ── */
[data-testid="stToast"] {
  font-size: 0.84rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface2) !important;
  border: 1px solid rgba(255,106,0,0.15) !important;
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
  padding: 2.5rem 1rem;
  gap: 0.4rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2rem; opacity: 0.35; }
.empty-state .es-title { font-size: 0.9rem; font-weight: 500; color: var(--text3); }
.empty-state .es-sub { font-size: 0.76rem; color: var(--text3); opacity: 0.6; }

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
  .block-container { padding: 0.5rem 0.75rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.35rem 0.6rem !important; font-size: 0.72rem !important; }
  .hero-banner { padding: 0.7rem 0.85rem; gap: 0.5rem; }
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
</style>"""
