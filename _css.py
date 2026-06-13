"""
Global CSS string constant for the dark premium theme.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* --- Root variables --- */
:root {
  --bg:        #0a0a0f;
  --surface:   #110f1a;
  --surface2:  #1a1528;
  --border:    #2d2540;
  --accent:    #c084fc;
  --accent2:   #e879f9;
  --green:     #86efac;
  --red:       #f472b6;
  --text:      #f0e6ff;
  --muted:     #9d8fbf;
  --radius:    12px;
}

/* --- Base --- */
*, *::before, *::after { box-sizing: border-box; }
html {
  scrollbar-gutter: stable;
  overflow-y: scroll;
}
body {
  overflow-anchor: none;
}
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
.block-container { padding: 1rem 1rem 3rem !important; max-width: 1400px; }

/* --- FIX layout shift: giữ left fixed, scrollbar thay đổi bên phải --- */
[data-testid="stAppViewContainer"] > section.main {
  scrollbar-gutter: stable;
  position: relative;
}
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] {
  scrollbar-gutter: stable;
}

/* --- Main content area --- */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background: var(--surface2) !important;
  border-radius: 16px !important;
  border: 1px solid rgba(192,132,252,0.15) !important;
  box-shadow: 0 0 60px rgba(192,132,252,0.07) inset !important;
}

div[data-testid="stMetricValue"] { font-size: clamp(1rem, 2.5vw, 1.4rem) !important; font-weight: 700 !important; color: var(--text) !important; }
div[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: var(--muted) !important; letter-spacing: 0.03em; text-transform: uppercase; }

/* --- Buttons --- */
.stButton > button {
  border-radius: 8px !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: all 0.15s ease !important;
  width: 100%;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #0a0a0f !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 24px rgba(192,132,252,0.5) !important;
  filter: brightness(1.1) !important;
}

/* --- Tabs --- */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 2px solid var(--border) !important;
  background: transparent !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTab"] {
  border-radius: 0 !important;
  padding: 0.65rem 1.2rem !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.15s ease !important;
  position: relative !important;
  outline: none !important;
}
[data-testid="stTab"]::after {
  content: '' !important;
  display: block !important;
  position: absolute !important;
  bottom: -2px !important;
  left: 10% !important;
  width: 80% !important;
  height: 3px !important;
  border-radius: 999px !important;
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  opacity: 0 !important;
  transform: scaleX(0.4) !important;
  transition: opacity 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--text) !important;
  font-weight: 700 !important;
  background: transparent !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text) !important;
  background: transparent !important;
}
[data-testid="stTab"]:hover::after {
  opacity: 0.35 !important;
  transform: scaleX(0.7) !important;
}

/* --- Inputs --- */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
}

/* --- Containers --- */
[data-testid="stVerticalBlockBorderWrapper"] {
  --border-color-default: rgba(192,132,252,0.55) !important;
  border-color: rgba(192,132,252,0.55) !important;
  background: linear-gradient(160deg, rgba(192,132,252,0.07) 0%, rgba(17,15,26,0.97) 55%) !important;
  border-radius: var(--radius) !important;
  box-shadow:
    inset 0 1px 0 rgba(192,132,252,0.15),
    0 6px 32px rgba(0,0,0,0.35) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  --border-color-default: rgba(192,132,252,0.55) !important;
  border-color: rgba(192,132,252,0.55) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
  box-shadow: none !important;
}

/* --- Tab content --- */
[data-testid="stTabContent"] {
  background: rgba(17,15,26,0.6) !important;
  border: 1px solid rgba(192,132,252,0.12) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1rem !important;
}

/* --- DataFrames --- */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  border-top: 2px solid rgba(192,132,252,0.5) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
  background: var(--surface) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stDataFrame:hover {
  border-color: rgba(192,132,252,0.3) !important;
  border-top-color: var(--accent) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 0 transparent !important;
}
[data-testid="stElementToolbar"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--muted) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--accent) !important; }

/* --- Status badges --- */
.badge-sold   { color: var(--green); font-weight: 600; }
.badge-stock  { color: var(--accent); font-weight: 600; }

/* --- Hero banner --- */
.hero-banner {
  background: linear-gradient(135deg, rgba(192,132,252,0.08) 0%, rgba(232,121,249,0.05) 50%, rgba(192,132,252,0.08) 100%);
  border: 1px solid rgba(192,132,252,0.2);
  backdrop-filter: blur(12px);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.hero-banner .logo { font-size: 2rem; }
.hero-banner h1 { margin: 0; font-size: clamp(1.1rem, 3vw, 1.5rem); font-weight: 700; letter-spacing: -0.01em; }
.hero-banner p  { margin: 0; color: var(--muted); font-size: 0.82rem; }

/* --- Stats row --- */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.6rem;
  margin-bottom: 0.8rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 0.9rem;
  text-align: center;
}
.stat-card:hover { border-color: var(--accent); box-shadow: 0 8px 24px rgba(192,132,252,0.2); }
.stat-card .val  { font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.stat-card .lbl  { font-size: 0.7rem; color: var(--muted); margin-top: 0.1rem; letter-spacing: 0.04em; }

/* --- Section headings --- */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 2rem 0 1rem !important;
  padding: 0;
  width: 100%;
  position: relative;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--accent), var(--accent2));
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(192,132,252,0.3) 0%, transparent 100%);
  margin-left: 0.4rem;
}

/* --- Section card panels --- */
.stat-panel {
  background: linear-gradient(145deg, rgba(192,132,252,0.07) 0%, rgba(17,15,26,0.95) 100%);
  border: 1px solid rgba(192,132,252,0.2);
  border-radius: var(--radius);
  padding: 1.2rem 1.2rem 0.8rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25), inset 0 1px 0 rgba(192,132,252,0.08);
}

/* --- Metric cards --- */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.7rem 0.9rem !important;
  transition: all 0.2s;
  box-shadow: 0 2px 12px rgba(192,132,252,0.05) !important;
}
div[data-testid="stMetric"]:hover {
  border-color: var(--accent) !important;
  border-left-color: var(--accent2) !important;
  box-shadow: 0 6px 24px rgba(192,132,252,0.22) !important;
}

/* --- Expanders --- */
[data-testid="stExpander"] {
  border: 1px solid rgba(192,132,252,0.28) !important;
  border-radius: var(--radius) !important;
  background: linear-gradient(135deg, rgba(192,132,252,0.06) 0%, var(--surface) 55%) !important;
  overflow: hidden !important;
  box-shadow: 0 2px 16px rgba(192,132,252,0.07) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.6rem 0.9rem !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.01em !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* --- Progress bar --- */
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  border-radius: 999px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--surface2) !important;
  border-radius: 999px !important;
}

/* --- Scrollbar --- */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* --- Mobile responsive --- */
@media (max-width: 768px) {
  .block-container { padding: 0.4rem 0.4rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.68rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.3rem 0.5rem !important; font-size: 0.7rem !important; letter-spacing: 0.02em !important; }
  .hero-banner { padding: 0.6rem 0.8rem; gap: 0.5rem; }
  .hero-banner .logo { font-size: 1.5rem; }
  .hero-banner h1 { font-size: 1rem !important; }
  .hero-banner p { font-size: 0.72rem; }
  .sec-heading { font-size: 0.88rem; margin: 0.7rem 0 0.4rem; }
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.3rem !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }
  .stForm { padding: 0.5rem !important; }
  .stButton > button { padding: 0.5rem 0.8rem !important; font-size: 0.82rem !important; }
  .stDataFrame { max-height: 350px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.75rem !important; }
  [data-testid="stExpander"] summary { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }
  .stTextInput input, .stNumberInput input { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.85rem !important; }
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.2rem !important; }
  [data-testid="stRadio"] label { font-size: 0.75rem !important; padding: 0.25rem 0.5rem !important; }
  [data-testid="stSidebar"] { min-width: 260px !important; }
  .js-plotly-plot { min-height: 250px !important; }
}

/* --- Copy description button --- */
.copy-desc-btn {
  background: linear-gradient(135deg, #c084fc, #e879f9) !important;
  color: #0a0a0f !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
.copy-desc-btn:hover {
  box-shadow: 0 4px 24px rgba(192,132,252,0.5) !important;
}

/* --- Toast override --- */
[data-testid="stToast"] { font-size: 0.85rem !important; border-radius: 10px !important; }

/* --- Alert / Notification boxes --- */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.84rem !important;
  padding: 0.65rem 0.9rem !important;
}
[data-testid="stAlert"][kind="info"],
div[data-testid="stInfo"] > div {
  background: rgba(192,132,252,0.07) !important;
  border-color: rgba(192,132,252,0.3) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="success"],
div[data-testid="stSuccess"] > div {
  background: rgba(134,239,172,0.07) !important;
  border-color: rgba(134,239,172,0.3) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="warning"],
div[data-testid="stWarning"] > div {
  background: rgba(251,191,36,0.07) !important;
  border-color: rgba(251,191,36,0.25) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="error"],
div[data-testid="stError"] > div {
  background: rgba(244,114,182,0.07) !important;
  border-color: rgba(244,114,182,0.3) !important;
  color: var(--text) !important;
}

/* --- Secondary / default buttons --- */
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: rgba(192,132,252,0.07) !important;
  border-color: rgba(192,132,252,0.45) !important;
  color: var(--text) !important;
  transform: none !important;
  box-shadow: none !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--accent) !important;
  transform: none !important;
  box-shadow: none !important;
}

/* --- Form container --- */
[data-testid="stForm"] {
  background: rgba(192,132,252,0.08) !important;
  border: 1px solid rgba(192,132,252,0.28) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
  box-shadow: 0 2px 16px rgba(192,132,252,0.08) !important;
}

/* --- Selectbox / multiselect styled --- */
[data-baseweb="select"] > div:first-child {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: rgba(192,132,252,0.1) !important;
}
[data-baseweb="tag"] {
  background: rgba(192,132,252,0.15) !important;
  color: var(--accent) !important;
  border: none !important;
  border-radius: 6px !important;
}

/* --- Caption / small text --- */
[data-testid="stCaptionContainer"] p {
  color: var(--muted) !important;
  font-size: 0.76rem !important;
}

/* --- Divider --- */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.8rem 0 !important;
}

/* --- Sidebar section headings --- */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0.5rem 0 0.3rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.4rem;
  display: block;
}

/* --- Radio pill chip style --- */
[data-testid="stRadio"] > div {
  gap: 0.3rem !important;
  flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--muted) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(192,132,252,0.15) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: var(--accent) !important;
  color: var(--text) !important;
}
[data-testid="stRadio"] label input[type="radio"] {
  display: none !important;
}
[data-testid="stRadio"] label > div:first-child {
  display: none !important;
}

/* --- Ton lau badge --- */
.badge-warn {
  background: rgba(147,51,234,0.25);
  color: var(--accent2);
  border: 1px solid rgba(147,51,234,0.4);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.72rem;
  font-weight: 700;
  margin-left: 8px;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

/* --- Hide Streamlit branding --- */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* --- Ambient background orbs --- */
[data-testid="stAppViewContainer"] { overflow-x: hidden; }
body::before {
  content: '';
  position: fixed;
  top: -200px; left: -200px;
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(192,132,252,0.07) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}
body::after {
  content: '';
  position: fixed;
  bottom: -180px; right: -180px;
  width: 650px; height: 650px;
  background: radial-gradient(circle, rgba(232,121,249,0.05) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}

/* --- Skeleton shimmer --- */
.sk-line {
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface2) 50%, var(--surface) 75%);
  background-size: 200% 100%;
  animation: sk-shimmer 1.4s infinite;
}
@keyframes sk-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* --- Toast enhanced --- */
[data-testid="stToast"] {
  background: var(--surface2) !important;
  border: 1px solid rgba(192,132,252,0.22) !important;
  border-radius: 12px !important;
  font-size: 0.85rem !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(192,132,252,0.08) !important;
  backdrop-filter: blur(16px) !important;
  color: var(--text) !important;
}
[data-testid="stToastContainer"] {
  bottom: 2rem !important;
  right: 1.5rem !important;
}

/* --- Empty state --- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  gap: 0.45rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2.4rem; opacity: 0.45; }
.empty-state .es-title { font-size: 0.95rem; font-weight: 600; color: var(--muted); }
.empty-state .es-sub { font-size: 0.78rem; color: var(--muted); opacity: 0.65; }

/* --- Button loading spinner --- */
@keyframes btn-spin {
  to { transform: rotate(360deg); }
}
.btn-busy {
  opacity: 0.65 !important;
  pointer-events: none !important;
  cursor: wait !important;
}
</style>"""
