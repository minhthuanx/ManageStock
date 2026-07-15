"""
Global CSS string — Cool Slate dark theme for Streamlit.
Font: Space Grotesk  |  Accent: Rose #f43f5e  |  Danger: Orange #f97316
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Cool Slate tokens ── */
:root {
  --background:      #0b1120;
  --surface:         #111827;
  --surface2:        #1a2332;
  --border:          #1e293b;
  --fg:              #f1f5f9;
  --muted:           #94a3b8;
  --accent:          #f43f5e;
  --danger:          #f97316;
  --success:         #22c55e;
  --radius:          0.5rem;
}

/* ══════════════════════════════════════════════
   FONT: Space Grotesk — body + targeted overrides
   Never touch: pseudo-elements, svg, * selectors
   ══════════════════════════════════════════════ */
* { box-sizing: border-box; }
html {
  scrollbar-gutter: stable;
  overflow-y: scroll;
}
body {
  overflow-anchor: none;
  font-family: 'Space Grotesk', system-ui, sans-serif !important;
  background: var(--background) !important;
  color: var(--fg) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
/* Targeted overrides — Streamlit sets font-family on these elements */
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stHeader"],
h1, h2, h3, h4, h5, h6, p, label, button, input, textarea, select,
[data-testid="stTab"],
[data-testid="stMetricValue"], [data-testid="stMetricLabel"],
[data-testid="stAlert"], [data-testid="stToast"],
[data-testid="stCaptionContainer"] p,
[data-testid="stExpander"] summary,
.stMarkdown,
div[data-testid="stVerticalBlockBorderWrapper"] {
  font-family: 'Space Grotesk', system-ui, sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: #0f1729 !important;
  border-right: 1px solid var(--border) !important;
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
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  border: 1px solid var(--border) !important;
}

/* ══════════════════════════════════════════════
   INPUTS: Single border, no double-border
   ══════════════════════════════════════════════ */

/* --- Text input --- */
.stTextInput input,
[data-baseweb="input"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--fg) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  box-shadow: none !important;
  outline: none !important;
}
.stTextInput input:focus,
[data-baseweb="input"]:focus,
[data-baseweb="input"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: none !important;
  outline: none !important;
}

/* --- Number input --- */
.stNumberInput input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--fg) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  box-shadow: none !important;
  outline: none !important;
}
.stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}

/* --- Select / Multiselect --- */
.stSelectbox,
.stMultiSelect,
[data-baseweb="select"] {
  color: var(--fg) !important;
}
[data-baseweb="select"] > div:first-child {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  color: var(--fg) !important;
  box-shadow: none !important;
}
[data-baseweb="select"] > div:first-child:focus-within,
[data-baseweb="select"] > div:first-child[data-focus="true"] {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}
[data-baseweb="select"][aria-expanded="true"] > div:first-child {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}
[data-baseweb="select"] svg { color: var(--muted) !important; }

/* --- Popover / dropdown --- */
[data-baseweb="popover"] {
  background: var(--surface) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="listbox"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 2px) !important;
}
[data-baseweb="menu"] [role="option"],
[data-baseweb="listbox"] [role="option"] {
  background: transparent !important;
  color: var(--fg) !important;
}
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"][aria-selected="true"],
[data-baseweb="listbox"] [role="option"]:hover {
  background: var(--border) !important;
}
[data-baseweb="menu"] [aria-selected="true"],
[data-baseweb="listbox"] [aria-selected="true"] {
  background: var(--border) !important;
}

/* --- Tag input (multiselect tags) --- */
[data-baseweb="tag"] {
  background: var(--border) !important;
  color: var(--fg) !important;
  border: 1px solid #2d3a4f !important;
  border-radius: calc(var(--radius) - 2px) !important;
}
[data-baseweb="tag"] span { color: var(--fg) !important; }
[data-baseweb="input"]::placeholder,
[data-baseweb="input"] [placeholder] {
  color: var(--muted) !important;
}

/* --- DatePicker / Calendar --- */
[data-baseweb="datepicker"] [data-baseweb="input"],
[data-baseweb="calendar"] {
  background: var(--surface) !important;
  color: var(--fg) !important;
}

/* --- Textarea --- */
[data-baseweb="textarea"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  color: var(--fg) !important;
  border-radius: calc(var(--radius) - 2px) !important;
  box-shadow: none !important;
}
[data-baseweb="textarea"]:focus-within {
  border-color: var(--accent) !important;
  box-shadow: none !important;
}

/* --- Checkbox --- */
[data-baseweb="checkbox"] svg { color: var(--fg) !important; }
[data-baseweb="checkbox"][aria-checked="true"] svg { color: var(--accent) !important; }

/* --- Slider --- */
[data-baseweb="slider"] [role="slider"] {
  background: var(--fg) !important;
}

/* --- Toggle / Switch --- */
[data-baseweb="toggle"] svg { color: var(--muted) !important; }

/* ══════════════════════════════════════════════
   Streamlit widget labels
   ══════════════════════════════════════════════ */

/* --- Labels --- */
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stTextArea label,
.stDateInput label {
  color: var(--muted) !important;
  font-size: 0.78rem !important;
  font-weight: 500 !important;
}

/* ── Metric ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.4rem) !important;
  font-weight: 700 !important;
  color: var(--fg) !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  color: var(--muted) !important;
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
  color: var(--background) !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover {
  background: #cbd5e1 !important;
  box-shadow: none !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface) !important;
  color: var(--fg) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--border) !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--fg) !important;
}

/* ── Tabs ── */
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
  padding: 0.65rem 1.2rem !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.04em !important;
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
  bottom: -1px !important;
  left: 0 !important;
  width: 100% !important;
  height: 2px !important;
  border-radius: 1px !important;
  background: var(--fg) !important;
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
  color: var(--muted) !important;
}

/* ── Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: var(--border) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}

/* ── Tab content ── */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1rem !important;
}

/* ── DataFrames ── */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
}
[data-testid="stElementToolbar"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: calc(var(--radius) - 2px) !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--muted) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--fg) !important; }

/* ── Status badges ── */
.badge-sold   { color: var(--danger); font-weight: 600; }
.badge-stock  { color: var(--success); font-weight: 600; }

/* ── Hero banner ── */
.hero-banner {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.hero-banner .logo { font-size: 2rem; }
.hero-banner h1 { margin: 0; font-size: clamp(1.1rem, 3vw, 1.5rem); font-weight: 600; letter-spacing: -0.01em; }
.hero-banner p  { margin: 0; color: var(--muted); font-size: 0.82rem; }

/* ── Stats grid ── */
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
  transition: border-color 0.15s ease;
}
.stat-card:hover { border-color: #334155; }
.stat-card .val { font-size: 1.2rem; font-weight: 700; color: var(--fg); }
.stat-card .lbl { font-size: 0.7rem; color: var(--muted); margin-top: 0.1rem; letter-spacing: 0.04em; text-transform: uppercase; }

/* ── Section headings ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
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
  background: var(--accent);
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
  margin-left: 0.4rem;
}

/* ── Section card panels ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.2rem 1.2rem 0.8rem;
  margin-bottom: 1rem;
}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 0.7rem 0.9rem !important;
  transition: border-color 0.15s ease;
}
div[data-testid="stMetric"]:hover {
  border-color: #334155 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
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
[data-testid="stExpander"] summary:hover { color: var(--muted) !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: var(--accent) !important;
  border-radius: 999px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--border) !important;
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
  background: rgba(14,165,233,0.08) !important;
  border-color: rgba(14,165,233,0.25) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="success"],
div[data-testid="stSuccess"] > div {
  background: rgba(34,197,94,0.08) !important;
  border-color: rgba(34,197,94,0.25) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="warning"],
div[data-testid="stWarning"] > div {
  background: rgba(245,158,11,0.08) !important;
  border-color: rgba(245,158,11,0.25) !important;
  color: var(--fg) !important;
}
[data-testid="stAlert"][kind="error"],
div[data-testid="stError"] > div {
  background: rgba(249,115,22,0.08) !important;
  border-color: rgba(249,115,22,0.25) !important;
  color: var(--fg) !important;
}

/* ── Form ── */
[data-testid="stForm"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}

/* ── Radio pill chips ── */
[data-testid="stRadio"] > div {
  gap: 0.3rem !important;
  flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
  background: var(--surface) !important;
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
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: #334155 !important;
  color: var(--fg) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--muted) !important;
  font-size: 0.76rem !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.8rem 0 !important;
}

/* ── Sidebar section headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0.5rem 0 0.3rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.4rem;
  display: block;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* ── Copy description button ── */
.copy-desc-btn {
  background: var(--fg) !important;
  color: var(--background) !important;
  border: none !important;
  border-radius: calc(var(--radius) - 2px) !important;
  font-weight: 500 !important;
}
.copy-desc-btn:hover {
  background: #cbd5e1 !important;
  box-shadow: none !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
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
.empty-state .es-title { font-size: 0.95rem; font-weight: 500; color: var(--muted); }
.empty-state .es-sub { font-size: 0.78rem; color: var(--muted); opacity: 0.65; }

/* ── Ton lau badge ── */
.badge-warn {
  background: rgba(249,115,22,0.12);
  color: var(--danger);
  border: 1px solid rgba(249,115,22,0.3);
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
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface2) 50%, var(--surface) 75%);
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
