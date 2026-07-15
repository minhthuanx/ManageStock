"""
Global CSS string — shadcn/ui Dark Mode design system.
Clean, minimal, neutral palette with subtle borders and proper typography.
Based on shadcn/ui design tokens for dark theme.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Root — shadcn/ui Dark Tokens ── */
:root {
  --background:        222.2 84% 4.9%;
  --foreground:        210 40% 98%;
  --card:              222.2 84% 4.9%;
  --card-foreground:   210 40% 98%;
  --popover:           222.2 84% 4.9%;
  --popover-foreground:210 40% 98%;
  --primary:           210 40% 98%;
  --primary-foreground:222.2 47.4% 11.2%;
  --secondary:         217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;
  --muted:             217.2 32.6% 17.5%;
  --muted-foreground:  215 20.2% 65.1%;
  --accent:            217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  --destructive:       0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border:            217.2 32.6% 17.5%;
  --input:             217.2 32.6% 17.5%;
  --ring:              212.7 26.8% 83.9%;
  --radius:            0.5rem;

  /* Semantic colors */
  --bg:                hsl(222.2 84% 4.9%);
  --bg-subtle:         hsl(222.2 84% 6.9%);
  --surface:           hsl(222.2 84% 5.9%);
  --surface-hover:     hsl(217.2 32.6% 14.5%);
  --border-color:      hsl(217.2 32.6% 17.5%);
  --border-hover:      hsl(217.2 32.6% 22%);
  --text-primary:      hsl(210 40% 98%);
  --text-secondary:    hsl(215 20.2% 65.1%);
  --text-muted:        hsl(217.2 20% 45%);
  --ring-color:        hsl(212.7 26.8% 83.9%);

  /* Accent colors */
  --green:             hsl(142 76% 56%);
  --green-bg:          hsl(142 76% 56% / 0.1);
  --red:               hsl(0 84% 60%);
  --red-bg:            hsl(0 84% 60% / 0.1);
  --yellow:            hsl(38 92% 50%);
  --yellow-bg:         hsl(38 92% 50% / 0.1);
  --blue:              hsl(217 91% 60%);
  --blue-bg:           hsl(217 91% 60% / 0.1);
  --purple:            hsl(280 67% 60%);
  --purple-bg:         hsl(280 67% 60% / 0.1);
}

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }
html { scrollbar-gutter: stable; overflow-y: scroll; }
body { overflow-anchor: none; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  color: var(--text-primary) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* ── Background ── */
[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: var(--bg) !important;
  border-right: 1px solid var(--border-color) !important;
}
.block-container {
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1440px;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* ── Layout ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] { scrollbar-gutter: stable; }
[data-testid="stAppViewContainer"] > section.main { scrollbar-gutter: stable; }

/* ── Metrics — shadcn card style ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.5rem) !important;
  font-weight: 700 !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.025em !important;
  line-height: 1.2 !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.8rem !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.01em !important;
  text-transform: none !important;
  font-weight: 500 !important;
}
div[data-testid="stMetric"] {
  font-size: 0.875rem !important;
}

/* ── Buttons — shadcn style ── */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  letter-spacing: 0 !important;
  transition: all 0.15s ease !important;
  width: 100%;
  border: 1px solid var(--border-color) !important;
  background: var(--secondary) !important;
  color: var(--text-primary) !important;
  padding: 0.5rem 1rem !important;
  height: 2.25rem !important;
  line-height: 1.25 !important;
}
.stButton > button:hover {
  background: var(--surface-hover) !important;
  border-color: var(--border-hover) !important;
}
.stButton > button:active {
  transform: scale(0.98);
}
.stButton > button:focus-visible {
  outline: 2px solid var(--ring-color) !important;
  outline-offset: 2px !important;
}
.stButton > button[kind="primary"] {
  background: var(--text-primary) !important;
  color: var(--bg) !important;
  border: none !important;
  font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
  background: hsl(210 40% 90%) !important;
  opacity: 0.9;
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border-color) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--secondary) !important;
  color: var(--text-primary) !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--text-primary) !important;
  background: var(--secondary) !important;
}

/* ── Tabs — shadcn underline style ── */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 1px solid var(--border-color) !important;
  background: transparent !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTab"] {
  border-radius: 0 !important;
  padding: 0.75rem 1rem !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  letter-spacing: 0 !important;
  color: var(--text-muted) !important;
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
  background: var(--text-primary) !important;
  opacity: 0 !important;
  transform: scaleX(0) !important;
  transition: opacity 0.15s ease, transform 0.15s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--text-primary) !important;
  font-weight: 600 !important;
  background: transparent !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text-secondary) !important;
  background: transparent !important;
}

/* ── Inputs — shadcn style ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--bg) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  color: var(--text-primary) !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
  font-size: 0.875rem !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--ring-color) !important;
  box-shadow: 0 0 0 2px hsl(212.7 26.8% 83.9% / 0.2) !important;
  outline: none !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label {
  color: var(--text-primary) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
}

/* ── Containers — shadcn card ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border-color) !important;
  background: var(--bg) !important;
  border-radius: var(--radius) !important;
  transition: border-color 0.15s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: var(--border-color) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--border-hover) !important;
}
/* Nested bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: var(--border-color) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: var(--border-hover) !important;
}
/* 3rd-level nested */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: var(--border-color) !important;
}

/* ── Tab content ── */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: none !important;
  border-top: none !important;
  border-radius: 0 !important;
  padding: 0.5rem 0 2rem 0 !important;
  box-shadow: none !important;
}

/* ── DataFrames — shadcn table style ── */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border-color) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--secondary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--text-muted) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--text-primary) !important; }

/* ── Status badges — shadcn badge ── */
.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 9999px;
  padding: 0.125rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.25rem;
  transition: colors 0.15s ease;
  white-space: nowrap;
}
.badge-default {
  background: var(--secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
.badge-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}
.badge-outline {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}
.badge-success {
  background: var(--green-bg);
  color: var(--green);
  border: 1px solid hsl(142 76% 56% / 0.2);
}
.badge-danger {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid hsl(0 84% 60% / 0.2);
}
.badge-warning {
  background: var(--yellow-bg);
  color: var(--yellow);
  border: 1px solid hsl(38 92% 50% / 0.2);
}
.badge-info {
  background: var(--blue-bg);
  color: var(--blue);
  border: 1px solid hsl(217 91% 60% / 0.2);
}
.badge-purple {
  background: var(--purple-bg);
  color: var(--purple);
  border: 1px solid hsl(280 67% 60% / 0.2);
}
/* Legacy class mappings */
.badge-sold  { color: var(--green); font-weight: 500; }
.badge-stock { color: var(--blue); font-weight: 500; }

/* ── Hero banner — shadcn card ── */
.hero-banner {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  overflow: hidden;
}
.hero-banner .logo {
  font-size: 1.5rem;
  opacity: 0.9;
}
.hero-banner h1 {
  margin: 0;
  font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--text-primary);
}
.hero-banner p {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.75rem;
  letter-spacing: 0.02em;
}

/* ── Stat cards — shadcn card ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem;
  text-align: center;
  transition: border-color 0.15s ease;
}
.stat-card:hover {
  border-color: var(--border-hover);
}
.stat-card .val {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}
.stat-card .lbl {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  font-weight: 500;
}

/* ── Section headings — shadcn style ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  margin: 1.5rem 0 0.75rem !important;
  padding: 0;
  width: 100%;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.75rem;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 2px;
  height: 16px;
  border-radius: 1px;
  background: var(--text-primary);
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-color);
  margin-left: 0.5rem;
}

/* ── Stat panels — shadcn card ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 1rem 1.25rem 0.75rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.15s ease;
}
.stat-panel:hover {
  border-color: var(--border-hover);
}

/* ── Metric cards — shadcard with subtle left border ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border-color) !important;
  border-left: 3px solid var(--text-muted) !important;
  border-radius: var(--radius) !important;
  padding: 0.75rem 1rem !important;
  transition: border-color 0.15s ease !important;
}
div[data-testid="stMetric"]:hover {
  border-color: var(--border-hover) !important;
  border-left-color: var(--text-secondary) !important;
}

/* ── Expanders — shadcn collapsible ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  background: transparent !important;
  overflow: hidden !important;
  transition: border-color 0.15s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: var(--border-hover) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.75rem 1rem !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  color: var(--text-primary) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover {
  color: var(--text-secondary) !important;
}

/* ── Progress bar — shadcn style ── */
[data-testid="stProgressBar"] > div > div {
  background: var(--text-primary) !important;
  border-radius: 9999px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--secondary) !important;
  border-radius: 9999px !important;
}

/* ── Scrollbar — subtle ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: hsl(217.2 32.6% 25%); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: hsl(217.2 32.6% 35%); }

/* ── Form container — shadcn card ── */
[data-testid="stForm"] {
  background: transparent !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  padding: 1.25rem !important;
}

/* ── Selectbox / multiselect — shadcn style ── */
[data-baseweb="select"] > div:first-child {
  background: var(--bg) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  color: var(--text-primary) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--ring-color) !important;
  box-shadow: 0 0 0 2px hsl(212.7 26.8% 83.9% / 0.2) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--surface-hover) !important;
}
[data-baseweb="tag"] {
  background: var(--secondary) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--text-muted) !important;
  font-size: 0.8rem !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border-color) !important;
  margin: 1rem 0 !important;
}

/* ── Sidebar section headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  padding: 0.5rem 0 0.35rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 0.5rem;
  display: block;
}

/* ── Radio pill chips — shadcn toggle style ── */
[data-testid="stRadio"] > div { gap: 0.25rem !important; flex-wrap: wrap !important; }
[data-testid="stRadio"] label {
  background: transparent !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  padding: 0.375rem 0.75rem !important;
  font-size: 0.8125rem !important;
  font-weight: 500 !important;
  color: var(--text-muted) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: var(--secondary) !important;
  border-color: var(--border-hover) !important;
  color: var(--text-primary) !important;
  font-weight: 500 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: var(--border-hover) !important;
  color: var(--text-secondary) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Badge warn — shadcn danger badge ── */
.badge-warn {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid hsl(0 84% 60% / 0.2);
  border-radius: 9999px;
  padding: 0.125rem 0.625rem;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
  white-space: nowrap;
}

/* ── Alerts — shadcn alert ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.875rem !important;
  padding: 0.75rem 1rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: var(--blue-bg) !important;
  border-color: hsl(217 91% 60% / 0.2) !important;
  color: var(--text-primary) !important;
}
[data-testid="stAlert"][kind="success"], div[data-testid="stSuccess"] > div {
  background: var(--green-bg) !important;
  border-color: hsl(142 76% 56% / 0.2) !important;
  color: var(--text-primary) !important;
}
[data-testid="stAlert"][kind="warning"], div[data-testid="stWarning"] > div {
  background: var(--yellow-bg) !important;
  border-color: hsl(38 92% 50% / 0.2) !important;
  color: var(--text-primary) !important;
}
[data-testid="stAlert"][kind="error"], div[data-testid="stError"] > div {
  background: var(--red-bg) !important;
  border-color: hsl(0 84% 60% / 0.2) !important;
  color: var(--text-primary) !important;
}

/* ── Plotly chart containers ── */
.js-plotly-plot {
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}

/* ── Copy description button ── */
.copy-desc-btn {
  background: var(--text-primary) !important;
  color: var(--bg) !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-weight: 600 !important;
  padding: 0.5rem 1rem !important;
  font-size: 0.875rem !important;
}
.copy-desc-btn:hover {
  opacity: 0.9;
}

/* ── Toast — shadcn toast ── */
[data-testid="stToast"] {
  font-size: 0.875rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
  color: var(--text-primary) !important;
}
[data-testid="stToastContainer"] { bottom: 1.5rem !important; right: 1.5rem !important; }

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
.empty-state .es-icon { font-size: 2.5rem; opacity: 0.3; }
.empty-state .es-title { font-size: 0.875rem; font-weight: 500; color: var(--text-secondary); }
.empty-state .es-sub { font-size: 0.8rem; color: var(--text-muted); }

/* ── Button load spinner ── */
.btn-busy {
  opacity: 0.5 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Separator line utility ── */
.cyber-line {
  height: 1px;
  background: var(--border-color);
  margin: 1rem 0;
}

/* ── Text utility classes ── */
.text-primary   { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted     { color: var(--text-muted); }
.text-green     { color: var(--green); }
.text-red       { color: var(--red); }
.text-yellow    { color: var(--yellow); }
.text-blue      { color: var(--blue); }
.text-purple    { color: var(--purple); }

/* Legacy neon classes → shadcn mappings */
.neon-cyan   { color: var(--blue); }
.neon-pink   { color: var(--red); }
.neon-green  { color: var(--green); }
.neon-purple { color: var(--purple); }
.neon-yellow { color: var(--yellow); }

/* ── Hero stat dot ── */
.hero-stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.hero-stat-dot.cyan   { background: var(--blue); }
.hero-stat-dot.pink   { background: var(--red); }
.hero-stat-dot.green  { background: var(--green); }
.hero-stat-dot.purple { background: var(--purple); }
.hero-stat-dot.muted  { background: var(--text-muted); }

/* ── Shadcn-style inline badge for chart dates ── */
.shadcn-badge-inline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 0.375rem 0.75rem;
  margin-bottom: 0.75rem;
}
.shadcn-badge-inline .badge-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}
.shadcn-badge-inline .badge-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* ── Mobile responsive ── */
@media (max-width: 768px) {
  .block-container { padding: 0.5rem 0.75rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 1rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
  .stat-card .val { font-size: 1rem; }
  [data-testid="stTab"] { padding: 0.5rem 0.75rem !important; font-size: 0.8125rem !important; }
  .hero-banner { padding: 0.75rem 1rem; gap: 0.5rem; flex-direction: column !important; align-items: flex-start !important; }
  .hero-banner > div:first-child { min-width: 0 !important; }
  .hero-banner .logo { font-size: 1.25rem; }
  .hero-banner h1 { font-size: 1rem !important; }
  .hero-banner p { font-size: 0.7rem; }
  .hero-banner > div:last-child { gap: 0.5rem !important; width: 100% !important; }
  .hero-banner > div:last-child > div { flex: 1 1 0 !important; min-width: 0 !important; padding: 0.5rem 0.75rem !important; }
  .hero-banner > div:last-child > div > div:first-child { font-size: 1rem !important; }
  .hero-banner > div:last-child > div > div:last-child { font-size: 0.7rem !important; }
  .sec-heading { font-size: 0.8125rem; margin: 0.75rem 0 0.4rem; }

  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.5rem !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(2):last-child)
    > [data-testid="stColumn"] { flex: 1 1 45% !important; min-width: 45% !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3):last-child)
    > [data-testid="stColumn"]:nth-child(-n+2) { flex: 1 1 45% !important; min-width: 45% !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(3):last-child)
    > [data-testid="stColumn"]:nth-child(3) { flex: 1 1 100% !important; min-width: 100% !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(4):last-child)
    > [data-testid="stColumn"] { flex: 1 1 45% !important; min-width: 45% !important; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"]:nth-child(5))
    > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
  [data-testid="stHorizontalBlock"]:has(.stForm) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(
    > [data-testid="stColumn"] > [data-testid="stHorizontalBlock"]
  ) > [data-testid="stColumn"] {
    flex: 1 1 100% !important; min-width: 100% !important;
  }

  .stForm { padding: 0.75rem !important; }
  .stButton > button { padding: 0.375rem 0.75rem !important; font-size: 0.8125rem !important; }
  .stDataFrame { max-height: 350px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.8125rem !important; }
  [data-testid="stExpander"] summary { font-size: 0.8125rem !important; padding: 0.5rem 0.75rem !important; }
  .stTextInput input, .stNumberInput input { font-size: 0.875rem !important; padding: 0.5rem 0.75rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.875rem !important; }
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.25rem !important; }
  [data-testid="stRadio"] label { font-size: 0.8125rem !important; padding: 0.25rem 0.5rem !important; }
  [data-testid="stSidebar"] { min-width: 260px !important; }
  .js-plotly-plot { min-height: 250px !important; }
}
</style>"""
