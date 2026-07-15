"""
Global CSS string — shadcn/ui dark theme for Streamlit.
Based on shadcn dark zinc palette with semantic CSS variables.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── shadcn semantic tokens (dark zinc) ── */
:root {
  --background:      240 10% 3.9%;
  --foreground:      0 0% 98%;
  --card:            240 10% 3.9%;
  --card-foreground: 0 0% 98%;
  --popover:         240 10% 3.9%;
  --popover-foreground: 0 0% 98%;
  --primary:         0 0% 98%;
  --primary-foreground: 240 5.9% 10%;
  --secondary:       240 3.7% 15.9%;
  --secondary-foreground: 0 0% 98%;
  --muted:           240 3.7% 15.9%;
  --muted-foreground: 240 5% 64.9%;
  --accent:          240 3.7% 15.9%;
  --accent-foreground: 0 0% 98%;
  --destructive:     0 62.8% 30.6%;
  --destructive-foreground: 0 0% 98%;
  --border:          240 3.7% 15.9%;
  --input:           240 3.7% 15.9%;
  --ring:            240 4.9% 83.9%;
  --radius:          0.5rem;

  /* convenience aliases */
  --bg:        hsl(var(--background));
  --fg:        hsl(var(--foreground));
  --card-bg:   hsl(var(--card));
  --muted-bg:  hsl(var(--muted));
  --muted-fg:  hsl(var(--muted-foreground));
  --border-c:  hsl(var(--border));
  --input-bg:  hsl(var(--input));
  --ring-c:    hsl(var(--ring));
}

/* ── Base reset ── */
*, *::before, *::after { box-sizing: border-box; }
html { scrollbar-gutter: stable; overflow-y: scroll; }
body { overflow-anchor: none; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', system-ui, sans-serif !important;
  background: var(--bg) !important;
  color: var(--fg) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: hsl(240 10% 5.5%) !important;
  border-right: 1px solid var(--border-c) !important;
}
.block-container { padding: 1rem 1rem 3rem !important; max-width: 1400px; }

/* ── Layout fix ── */
[data-testid="stAppViewContainer"] > section.main {
  scrollbar-gutter: stable;
  position: relative;
}
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] { scrollbar-gutter: stable; }

/* ── Main content area ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background: hsl(240 10% 5%) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--border-c) !important;
}

/* ── Metric ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.4rem) !important;
  font-weight: 700 !important;
  color: var(--fg) !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  color: var(--muted-fg) !important;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

/* ── Buttons ── */
.stButton > button {
  border-radius: calc(var(--radius) - 2px) !important;
  font-size: 0.84rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.01em !important;
  transition: background-color 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
  width: 100%;
}
.stButton > button[kind="primary"] {
  background: var(--fg) !important;
  color: hsl(var(--background)) !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover {
  background: hsl(0 0% 83%) !important;
  box-shadow: none !important;
}

/* ── Secondary / tertiary buttons ── */
.stButton > button[kind="secondary"] {
  background: var(--muted-bg) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border-c) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: hsl(240 3.7% 20%) !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--muted-fg) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--fg) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 1px solid var(--border-c) !important;
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
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  color: var(--muted-fg) !important;
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
  bottom: -1px !important;
  left: 0 !important;
  width: 100% !important;
  height: 2px !important;
  border-radius: 1px !important;
  background: var(--foreground) !important;
  opacity: 0 !important;
  transform: scaleX(0) !important;
  transition: opacity 0.15s ease, transform 0.15s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--fg) !important;
  font-weight: 600 !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--muted-fg) !important;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--input-bg) !important;
  border: 1px solid var(--input-bg) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  color: var(--fg) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--ring-c) !important;
  box-shadow: 0 0 0 1px var(--ring-c) !important;
  outline: none !important;
}

/* ── Select / Multiselect ── */
[data-baseweb="select"] > div:first-child {
  background: var(--input-bg) !important;
  border: 1px solid var(--input-bg) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  color: var(--fg) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--ring-c) !important;
  box-shadow: 0 0 0 1px var(--ring-c) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--popover) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: calc(var(--radius) - 2px) !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--accent) !important;
}
[data-baseweb="tag"] {
  background: hsl(240 3.7% 20%) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: calc(var(--radius) - 2px) !important;
}

/* ── Containers (expander/form wrappers) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border-c) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: var(--border-c) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}

/* ── Tab content ── */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: 1px solid var(--border-c) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1rem !important;
}

/* ── DataFrames ── */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border-c) !important;
  background: var(--card-bg) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--muted-bg) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: calc(var(--radius) - 2px) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--muted-fg) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--fg) !important; }

/* ── Status badges ── */
.badge-sold   { color: hsl(142 76% 60%); font-weight: 600; }
.badge-stock  { color: hsl(var(--ring)); font-weight: 600; }

/* ── Hero banner ── */
.hero-banner {
  background: var(--card-bg);
  border: 1px solid var(--border-c);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.hero-banner .logo { font-size: 2rem; }
.hero-banner h1 { margin: 0; font-size: clamp(1.1rem, 3vw, 1.5rem); font-weight: 600; letter-spacing: -0.01em; }
.hero-banner p  { margin: 0; color: var(--muted-fg); font-size: 0.82rem; }

/* ── Stats grid ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.6rem;
  margin-bottom: 0.8rem;
}
.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-c);
  border-radius: var(--radius);
  padding: 0.75rem 0.9rem;
  text-align: center;
  transition: border-color 0.15s ease;
}
.stat-card:hover { border-color: hsl(240 3.7% 25%); }
.stat-card .val { font-size: 1.2rem; font-weight: 700; color: var(--fg); }
.stat-card .lbl { font-size: 0.7rem; color: var(--muted-fg); margin-top: 0.1rem; letter-spacing: 0.04em; text-transform: uppercase; }

/* ── Section headings ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted-fg);
  margin: 2rem 0 1rem !important;
  padding: 0;
  width: 100%;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: var(--foreground);
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-c);
  margin-left: 0.4rem;
}

/* ── Section card panels ── */
.stat-panel {
  background: var(--card-bg);
  border: 1px solid var(--border-c);
  border-radius: var(--radius);
  padding: 1.2rem 1.2rem 0.8rem;
  margin-bottom: 1rem;
}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: var(--radius) !important;
  padding: 0.7rem 0.9rem !important;
  transition: border-color 0.15s ease;
}
div[data-testid="stMetric"]:hover {
  border-color: hsl(240 3.7% 25%) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border-c) !important;
  border-radius: var(--radius) !important;
  background: var(--card-bg) !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  padding: 0.6rem 0.9rem !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.01em !important;
  color: var(--fg) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--muted-fg) !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: var(--foreground) !important;
  border-radius: 999px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--muted-bg) !important;
  border-radius: 999px !important;
}

/* ── Alerts / Notifications ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.84rem !important;
  padding: 0.65rem 0.9rem !important;
}
[data-testid="stAlert"][kind="info"],
div[data-testid="stInfo"] > div {
  background: hsl(213 94% 12%) !important;
  border-color: hsl(213 94% 25%) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="success"],
div[data-testid="stSuccess"] > div {
  background: hsl(142 72% 8%) !important;
  border-color: hsl(142 72% 20%) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="warning"],
div[data-testid="stWarning"] > div {
  background: hsl(38 80% 8%) !important;
  border-color: hsl(38 80% 20%) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="error"],
div[data-testid="stError"] > div {
  background: hsl(0 62% 12%) !important;
  border-color: hsl(0 62% 22%) !important;
  color: var(--fg) !important;
}

/* ── Form ── */
[data-testid="stForm"] {
  background: var(--card-bg) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}

/* ── Radio pill chips ── */
[data-testid="stRadio"] > div {
  gap: 0.3rem !important;
  flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
  background: var(--muted-bg) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: 999px !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--muted-fg) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: var(--foreground) !important;
  border-color: var(--foreground) !important;
  color: var(--background) !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: hsl(240 3.7% 30%) !important;
  color: var(--fg) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--muted-fg) !important;
  font-size: 0.76rem !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border-c) !important;
  margin: 0.8rem 0 !important;
}

/* ── Sidebar section headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted-fg);
  padding: 0.5rem 0 0.3rem;
  border-bottom: 1px solid var(--border-c);
  margin-bottom: 0.4rem;
  display: block;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: hsl(240 3.7% 20%); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: hsl(240 3.7% 30%); }

/* ── Copy description button ── */
.copy-desc-btn {
  background: var(--foreground) !important;
  color: var(--background) !important;
  border: none !important;
  border-radius: calc(var(--radius) - 2px) !important;
  font-weight: 500 !important;
}
.copy-desc-btn:hover {
  background: hsl(0 0% 83%) !important;
  box-shadow: none !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
  background: var(--popover) !important;
  border: 1px solid var(--border-c) !important;
  border-radius: var(--radius) !important;
  font-size: 0.85rem !important;
  color: var(--fg) !important;
}
[data-testid="stToastContainer"] {
  bottom: 2rem !important;
  right: 1.5rem !important;
}

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  gap: 0.45rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2.4rem; opacity: 0.3; }
.empty-state .es-title { font-size: 0.95rem; font-weight: 500; color: var(--muted-fg); }
.empty-state .es-sub { font-size: 0.78rem; color: var(--muted-fg); opacity: 0.65; }

/* ── Ton lau badge ── */
.badge-warn {
  background: hsl(0 62% 15%);
  color: hsl(0 84% 70%);
  border: 1px solid hsl(0 62% 25%);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.72rem;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

/* ── Skeleton shimmer ── */
.sk-line {
  border-radius: calc(var(--radius) - 2px);
  background: linear-gradient(90deg, var(--muted-bg) 25%, hsl(240 3.7% 18%) 50%, var(--muted-bg) 75%);
  background-size: 200% 100%;
  animation: sk-shimmer 1.4s infinite;
}
@keyframes sk-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Button loading spinner ── */
@keyframes btn-spin { to { transform: rotate(360deg); } }
.btn-busy {
  opacity: 0.65 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Mobile responsive ── */
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
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.3rem !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
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
</style>"""
