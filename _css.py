"""
Global CSS string — Pure Black + Purple→Fuchsia neon glow theme.
Background #000000, accent gradient #8b5cf6 → #d946ef.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Root — Neon Black + Purple/Fuchsia ── */
:root {
  --bg:        #000000;
  --surface:   #0a0a0a;
  --surface2:  #141414;
  --surface3:  #1f1f1f;
  --border:    #1a1a1a;
  --border-h:  #2a2a2a;
  --accent:    #8b5cf6;
  --accent-h:  #a78bfa;
  --accent2:   #d946ef;
  --accent2-h: #e879f9;
  --accent-bg: rgba(139,92,246,0.18);
  --accent-glow: 0 0 8px rgba(139,92,246,0.4), 0 0 20px rgba(139,92,246,0.15);
  --accent-glow-strong: 0 0 10px rgba(139,92,246,0.55), 0 0 28px rgba(139,92,246,0.25), 0 0 48px rgba(139,92,246,0.18);
  --gradient:  linear-gradient(90deg, #8b5cf6, #d946ef);
  --gradient-h: linear-gradient(90deg, #a78bfa, #e879f9);
  --green:     #34d399;
  --green-bg:  rgba(52,211,153,0.15);
  --green-glow: 0 0 8px rgba(52,211,153,0.35);
  --red:       #f87171;
  --red-bg:    rgba(248,113,113,0.15);
  --red-glow:  0 0 8px rgba(248,113,113,0.35);
  --purple:    #a78bfa;
  --purple-bg: rgba(167,139,250,0.15);
  --purple-glow: 0 0 8px rgba(167,139,250,0.35);
  --yellow:    #fbbf24;
  --yellow-bg: rgba(251,191,36,0.15);
  --yellow-glow: 0 0 8px rgba(251,191,36,0.35);
  --pink:      #f472b6;
  --pink-bg:   rgba(244,114,182,0.15);
  --pink-glow: 0 0 8px rgba(244,114,182,0.35);
  --blue:      #60a5fa;
  --blue-bg:   rgba(96,165,250,0.15);
  --blue-glow: 0 0 8px rgba(96,165,250,0.35);
  --text:      #f0f0f0;
  --text2:     #999999;
  --text3:     #666666;
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
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* ── Background — pure black ── */
[data-testid="stAppViewContainer"] {
  background: #000000 !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: #000000 !important;
  border-right: 1px solid var(--border) !important;
}
.block-container {
  padding: 1.2rem 2rem 3rem !important;
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

/* ── Metrics ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.3rem) !important;
  font-weight: 700 !important;
  background: var(--gradient) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  letter-spacing: -0.02em !important;
  filter: drop-shadow(0 0 8px rgba(139,92,246,0.35)) !important;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.75rem !important;
  color: var(--text2) !important;
  letter-spacing: 0.02em !important;
  text-transform: none !important;
  font-weight: 500 !important;
}

/* ── Buttons ── */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  transition: all 0.2s ease !important;
  width: 100%;
  border: 1px solid var(--border) !important;
  background: var(--surface2) !important;
  color: var(--text) !important;
  padding: 0.55rem 1rem !important;
}
.stButton > button:hover {
  background: var(--surface3) !important;
  border-color: var(--accent) !important;
  box-shadow: var(--accent-glow) !important;
}
.stButton > button:active { transform: scale(0.985); }
.stButton > button[kind="primary"] {
  background: var(--gradient) !important;
  color: #ffffff !important;
  border: none !important;
  font-weight: 700 !important;
  box-shadow: var(--accent-glow) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--gradient-h) !important;
  box-shadow: var(--accent-glow-strong) !important;
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--accent) !important;
  border: 1px solid rgba(139,92,246,0.3) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--accent-bg) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  box-shadow: var(--accent-glow) !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--text3) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--accent) !important;
  text-shadow: 0 0 10px rgba(139,92,246,0.4);
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
  padding: 0.65rem 1rem !important;
  font-weight: 500 !important;
  font-size: 0.82rem !important;
  color: var(--text3) !important;
  border: none !important;
  background: transparent !important;
  transition: all 0.2s ease !important;
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
  background: var(--gradient) !important;
  box-shadow: 0 0 8px rgba(139,92,246,0.5), 0 0 20px rgba(217,70,239,0.2) !important;
  opacity: 0 !important;
  transform: scaleX(0) !important;
  transition: opacity 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--accent) !important;
  font-weight: 600 !important;
  text-shadow: 0 0 10px rgba(139,92,246,0.3);
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text2) !important;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  transition: all 0.2s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(139,92,246,0.2), var(--accent-glow) !important;
}

/* ── Containers ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--border) !important;
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  transition: all 0.25s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: var(--border) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(139,92,246,0.35) !important;
  box-shadow: 0 0 12px rgba(139,92,246,0.1), inset 0 0 30px rgba(139,92,246,0.02) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: var(--border) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(139,92,246,0.3) !important;
  box-shadow: 0 0 10px rgba(139,92,246,0.08) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: var(--border) !important;
}

/* ── Tab content ── */
[data-testid="stTabContent"] {
  background: transparent !important;
  border: none !important;
  padding: 0.5rem 0 2rem 0 !important;
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
[data-testid="stElementToolbarButton"]:hover svg { color: var(--accent) !important; }

/* ── Status badges ── */
.badge-sold  { color: var(--green); font-weight: 600; text-shadow: 0 0 8px rgba(52,211,153,0.3); }
.badge-stock { color: var(--accent); font-weight: 600; text-shadow: 0 0 8px rgba(139,92,246,0.3); }

/* ── Hero banner ── */
.hero-banner {
  background: linear-gradient(135deg, #0a0015 0%, #0a0a0a 50%, #0a0015 100%);
  border: 1px solid rgba(139,92,246,0.2);
  border-radius: var(--radius);
  padding: 1.15rem 1.4rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(139,92,246,0.06), inset 0 1px 0 rgba(139,92,246,0.18);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.hero-banner:hover {
  border-color: rgba(139,92,246,0.35);
  box-shadow: 0 0 30px rgba(139,92,246,0.22), inset 0 1px 0 rgba(217,70,239,0.22);
}
.hero-banner .logo { font-size: 1.6rem; opacity: 0.95; filter: drop-shadow(0 0 6px rgba(139,92,246,0.3)); }
.hero-banner h1 {
  margin: 0;
  font-size: clamp(1.05rem, 2.5vw, 1.35rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  background: var(--gradient) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  filter: drop-shadow(0 0 12px rgba(139,92,246,0.4));
}
.hero-banner p {
  margin: 0;
  color: var(--text3);
  font-size: 0.75rem;
  letter-spacing: 0.02em;
}

/* ── Stat cards ── */
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
  transition: all 0.25s ease;
}
.stat-card:hover {
  border-color: rgba(139,92,246,0.35);
  box-shadow: 0 0 15px rgba(139,92,246,0.1), inset 0 0 20px rgba(139,92,246,0.03);
}
.stat-card .val {
  font-size: 1.1rem;
  font-weight: 700;
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 6px rgba(139,92,246,0.3));
}
.stat-card .lbl {
  font-size: 0.7rem;
  color: var(--text2);
  margin-top: 0.2rem;
  font-weight: 500;
}

/* ── Section headings ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 1.5rem 0 0.75rem !important;
  padding: 0;
  width: 100%;
  border-bottom: 1px solid rgba(139,92,246,0.15);
  padding-bottom: 0.6rem;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: var(--gradient);
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(139,92,246,0.5);
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(139,92,246,0.25), rgba(217,70,239,0.15), transparent);
  margin-left: 0.5rem;
}

/* ── Stat panels ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem 0.75rem;
  margin-bottom: 0.75rem;
  transition: all 0.25s ease;
}
.stat-panel:hover {
  border-color: rgba(139,92,246,0.3);
  box-shadow: 0 0 12px rgba(139,92,246,0.1);
}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.65rem 0.85rem !important;
  transition: all 0.25s ease !important;
}
div[data-testid="stMetric"]:hover {
  border-color: rgba(139,92,246,0.3) !important;
  border-left-color: var(--accent2) !important;
  box-shadow: 0 0 15px rgba(139,92,246,0.1), inset 0 0 20px rgba(139,92,246,0.03) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  overflow: hidden !important;
  transition: all 0.25s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(139,92,246,0.25) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.65rem 0.9rem !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  color: var(--text) !important;
  background: transparent !important;
}
[data-testid="stExpander"] summary:hover {
  color: var(--accent) !important;
  text-shadow: 0 0 8px rgba(139,92,246,0.3);
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
  background: var(--gradient) !important;
  border-radius: 999px !important;
  box-shadow: 0 0 10px rgba(139,92,246,0.4), 0 0 20px rgba(217,70,239,0.15) !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 999px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.25); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.45); }

/* ── Form ── */
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
  box-shadow: 0 0 0 3px rgba(139,92,246,0.2), var(--accent-glow) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: var(--accent-bg) !important;
  color: var(--accent) !important;
}
[data-baseweb="tag"] {
  background: var(--accent-bg) !important;
  color: var(--accent) !important;
  border: 1px solid rgba(139,92,246,0.25) !important;
  border-radius: 4px !important;
  box-shadow: 0 0 6px rgba(139,92,246,0.15);
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p {
  color: var(--text3) !important;
  font-size: 0.75rem !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.75rem 0 !important;
}

/* ── Sidebar headings ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.7rem;
  font-weight: 600;
  background: var(--gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  padding: 0.4rem 0 0.25rem;
  border-bottom: 1px solid rgba(139,92,246,0.15);
  margin-bottom: 0.35rem;
  display: block;
  filter: drop-shadow(0 0 6px rgba(139,92,246,0.3));
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
  color: var(--text3) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: var(--accent-bg) !important;
  border-color: rgba(139,92,246,0.5) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
  box-shadow: 0 0 10px rgba(139,92,246,0.2);
  text-shadow: 0 0 6px rgba(139,92,246,0.3);
}
[data-testid="stRadio"] label:hover {
  border-color: rgba(139,92,246,0.3) !important;
  color: var(--text) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Badge warn ── */
.badge-warn {
  background: var(--red-bg);
  color: var(--red);
  border: 1px solid rgba(248,113,113,0.3);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
  box-shadow: 0 0 8px rgba(248,113,113,0.2);
}

/* ── Alerts ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.82rem !important;
  padding: 0.6rem 0.85rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: var(--blue-bg) !important;
  border-color: rgba(96,165,250,0.3) !important;
  color: var(--text) !important;
  box-shadow: 0 0 10px rgba(96,165,250,0.08);
}
[data-testid="stAlert"][kind="success"], div[data-testid="stSuccess"] > div {
  background: var(--green-bg) !important;
  border-color: rgba(52,211,153,0.3) !important;
  color: var(--text) !important;
  box-shadow: 0 0 10px rgba(52,211,153,0.08);
}
[data-testid="stAlert"][kind="warning"], div[data-testid="stWarning"] > div {
  background: var(--yellow-bg) !important;
  border-color: rgba(251,191,36,0.3) !important;
  color: var(--text) !important;
  box-shadow: 0 0 10px rgba(251,191,36,0.08);
}
[data-testid="stAlert"][kind="error"], div[data-testid="stError"] > div {
  background: var(--red-bg) !important;
  border-color: rgba(248,113,113,0.3) !important;
  color: var(--text) !important;
  box-shadow: 0 0 10px rgba(248,113,113,0.08);
}

/* ── Plotly ── */
.js-plotly-plot {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}

/* ── Copy button ── */
.copy-desc-btn {
  background: var(--gradient) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-weight: 700 !important;
  box-shadow: var(--accent-glow) !important;
}
.copy-desc-btn:hover {
  background: var(--gradient-h) !important;
  box-shadow: var(--accent-glow-strong) !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
  font-size: 0.82rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface2) !important;
  border: 1px solid rgba(139,92,246,0.2) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 15px rgba(139,92,246,0.12) !important;
  color: var(--text) !important;
}
[data-testid="stToastContainer"] { bottom: 2rem !important; right: 1.5rem !important; }

/* ── Empty state ── */
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 2.5rem 1rem; gap: 0.4rem; text-align: center;
}
.empty-state .es-icon { font-size: 2rem; opacity: 0.4; filter: drop-shadow(0 0 8px rgba(139,92,246,0.3)); }
.empty-state .es-title { font-size: 0.85rem; font-weight: 500; color: var(--text3); }
.empty-state .es-sub { font-size: 0.75rem; color: var(--text3); opacity: 0.6; }

/* ── Utilities ── */
.btn-busy { opacity: 0.5 !important; pointer-events: none !important; }
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
.neon-cyan   { color: var(--accent);  text-shadow: 0 0 8px rgba(139,92,246,0.4); }
.neon-pink   { color: var(--pink);    text-shadow: 0 0 8px rgba(244,114,182,0.4); }
.neon-green  { color: var(--green);   text-shadow: 0 0 8px rgba(52,211,153,0.4); }
.neon-purple { color: var(--accent2); text-shadow: 0 0 8px rgba(217,70,239,0.4); }
.neon-yellow { color: var(--yellow);  text-shadow: 0 0 8px rgba(251,191,36,0.4); }
.cyber-line { height: 1px; background: linear-gradient(90deg, transparent, rgba(139,92,246,0.3), rgba(217,70,239,0.15), transparent); margin: 1rem 0; }

/* ── Hero stat dot ── */
.hero-stat-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.hero-stat-dot.cyan   { background: var(--accent);  box-shadow: 0 0 8px rgba(139,92,246,0.5); }
.hero-stat-dot.pink   { background: var(--pink);    box-shadow: 0 0 8px rgba(244,114,182,0.5); }
.hero-stat-dot.green  { background: var(--green);   box-shadow: 0 0 8px rgba(52,211,153,0.5); }
.hero-stat-dot.purple { background: var(--accent2);  box-shadow: 0 0 8px rgba(217,70,239,0.5); }
.hero-stat-dot.muted  { background: var(--text3); }

/* ── Neon pulse animation ── */
@keyframes neon-pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(139,92,246,0.3), 0 0 20px rgba(217,70,239,0.1); }
  50%      { box-shadow: 0 0 12px rgba(139,92,246,0.5), 0 0 30px rgba(217,70,239,0.2); }
}

/* ── Mobile ── */
@media (max-width: 768px) {
  .block-container { padding: 0.5rem 0.75rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.35rem 0.6rem !important; font-size: 0.75rem !important; }
  .hero-banner { padding: 0.55rem 0.65rem; gap: 0.35rem; flex-direction: column !important; align-items: flex-start !important; }
  .hero-banner > div:first-child { min-width: 0 !important; }
  .hero-banner .logo { font-size: 0.95rem; }
  .hero-banner h1 { font-size: 0.85rem !important; }
  .hero-banner p { font-size: 0.6rem; }
  .hero-banner > div:last-child { gap: 0.35rem !important; width: 100% !important; }
  .hero-banner > div:last-child > div { flex: 1 1 0 !important; min-width: 0 !important; padding: 0.35rem 0.5rem !important; }
  .hero-banner > div:last-child > div > div:first-child { font-size: 0.9rem !important; }
  .hero-banner > div:last-child > div > div:last-child { font-size: 0.55rem !important; }
  .sec-heading { font-size: 0.75rem; margin: 0.75rem 0 0.4rem; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 0.3rem !important; }
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
  ) > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; }
  .stForm { padding: 0.5rem !important; }
  .stButton > button { padding: 0.45rem 0.75rem !important; font-size: 0.8rem !important; }
  .stDataFrame { max-height: 350px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.75rem !important; }
  [data-testid="stExpander"] summary { font-size: 0.8rem !important; padding: 0.4rem 0.6rem !important; }
  .stTextInput input, .stNumberInput input { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.85rem !important; }
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.2rem !important; }
  [data-testid="stRadio"] label { font-size: 0.75rem !important; padding: 0.25rem 0.5rem !important; }
  [data-testid="stSidebar"] { min-width: 260px !important; }
  .js-plotly-plot { min-height: 250px !important; }
}
</style>"""
