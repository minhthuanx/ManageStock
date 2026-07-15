"""
Global CSS string — Cyberpunk Lite / Gaming UI theme.
Deep Navy palette, neon glow borders, grid + scanline background, futuristic gaming feel.
"""
CSS_STRING = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

/* ── Root — Cyberpunk Lite / Gaming UI ── */
:root {
  --bg:        #0b0e17;
  --surface:   #111827;
  --surface2:  #1a2035;
  --surface3:  #222b45;
  --border:    rgba(0,240,255,0.08);
  --border-h:  rgba(0,240,255,0.18);
  --accent:    #00f0ff;
  --accent-h:  #33f5ff;
  --accent-bg: rgba(0,240,255,0.06);
  --pink:      #ff2d75;
  --pink-bg:   rgba(255,45,117,0.08);
  --purple:    #7b61ff;
  --purple-bg: rgba(123,97,255,0.08);
  --green:     #00ff88;
  --green-bg:  rgba(0,255,136,0.06);
  --red:       #ff3355;
  --red-bg:    rgba(255,51,85,0.06);
  --yellow:    #ffaa00;
  --yellow-bg: rgba(255,170,0,0.06);
  --text:      #e8eaf0;
  --text2:     #8b93a7;
  --text3:     #5a6178;
  --radius:    10px;
  --radius-sm: 7px;
  --mono:      'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
  --display:   'Orbitron', 'Inter', sans-serif;
  --glow-cyan:   0 0 12px rgba(0,240,255,0.25), 0 0 30px rgba(0,240,255,0.08);
  --glow-pink:   0 0 12px rgba(255,45,117,0.25), 0 0 30px rgba(255,45,117,0.08);
  --glow-green:  0 0 12px rgba(0,255,136,0.25), 0 0 30px rgba(0,255,136,0.08);
  --glow-purple: 0 0 12px rgba(123,97,255,0.25), 0 0 30px rgba(123,97,255,0.08);
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

/* ── Background — deep navy with subtle gradient ── */
[data-testid="stAppViewContainer"] {
  background: linear-gradient(160deg, #0b0e17 0%, #0f1629 50%, #0b0e17 100%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0b0e17 0%, #111827 100%) !important;
  border-right: 1px solid rgba(0,240,255,0.1) !important;
}
.block-container {
  padding: 1.2rem 2rem 3rem !important;
  max-width: 1440px;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* ── Grid + Scanline overlay — futuristic gaming ── */
[data-testid="stAppViewContainer"] > section.main {
  position: relative;
}
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background:
    repeating-linear-gradient(0deg,rgba(0,240,255,0.015) 0px,transparent 1px,transparent 3px),
    linear-gradient(rgba(0,240,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,240,255,0.03) 1px, transparent 1px) !important;
  background-size: 100% 4px, 48px 48px, 48px 48px !important;
  background-position: 0 0, -1px -1px, -1px -1px !important;
}

/* ── Layout ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  margin-left: 0 !important;
  margin-right: auto !important;
}
[data-testid="stTabContent"] { scrollbar-gutter: stable; }
[data-testid="stAppViewContainer"] > section.main { scrollbar-gutter: stable; }

/* ── Metrics — gaming HUD style ── */
div[data-testid="stMetricValue"] {
  font-size: clamp(1rem, 2.5vw, 1.3rem) !important;
  font-weight: 800 !important;
  color: var(--accent) !important;
  letter-spacing: -0.02em !important;
  text-shadow: 0 0 18px rgba(0,240,255,0.25);
}
div[data-testid="stMetricLabel"] {
  font-size: 0.7rem !important;
  color: var(--text2) !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
  font-family: var(--mono) !important;
}

/* ── Buttons — gaming neon pill ── */
.stButton > button {
  border-radius: var(--radius) !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: all 0.2s ease !important;
  width: 100%;
  border: 1px solid var(--border) !important;
  background: var(--surface2) !important;
  color: var(--text) !important;
  padding: 0.55rem 1rem !important;
  position: relative;
}
.stButton > button:hover {
  background: var(--surface3) !important;
  border-color: var(--border-h) !important;
  box-shadow: 0 0 14px rgba(0,240,255,0.08);
}
.stButton > button:active {
  background: var(--border) !important;
  transform: scale(0.985);
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #00f0ff 0%, #7b61ff 100%) !important;
  color: #0b0e17 !important;
  border: none !important;
  border-radius: 999px !important;
  box-shadow: var(--glow-cyan), 0 0 50px rgba(0,240,255,0.1) !important;
  font-weight: 800 !important;
  letter-spacing: 0.04em !important;
  text-transform: uppercase !important;
  font-size: 0.8rem !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #33f5ff 0%, #9580ff 100%) !important;
  box-shadow: var(--glow-cyan), 0 0 60px rgba(0,240,255,0.18) !important;
  transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--text2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--surface2) !important;
  border-color: rgba(0,240,255,0.2) !important;
  color: var(--accent) !important;
  box-shadow: 0 0 10px rgba(0,240,255,0.06) !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--text3) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--accent) !important;
  box-shadow: none !important;
}

/* ── Tabs — gaming neon underline ── */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 1px solid rgba(0,240,255,0.1) !important;
  background: transparent !important;
  padding: 0 !important;
}
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTab"] {
  border-radius: 0 !important;
  padding: 0.65rem 1.1rem !important;
  font-weight: 600 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.04em !important;
  color: var(--text3) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.2s ease, text-shadow 0.2s ease !important;
  position: relative !important;
  outline: none !important;
  text-transform: uppercase !important;
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
  background: linear-gradient(90deg, var(--accent), var(--purple)) !important;
  opacity: 0 !important;
  transform: scaleX(0) !important;
  transition: opacity 0.2s ease, transform 0.2s ease !important;
  box-shadow: 0 0 8px rgba(0,240,255,0.3);
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--accent) !important;
  font-weight: 700 !important;
  background: transparent !important;
  text-shadow: 0 0 12px rgba(0,240,255,0.3);
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text2) !important;
  background: transparent !important;
}

/* ── Inputs — neon focus ring ── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(0,240,255,0.1), 0 0 12px rgba(0,240,255,0.08) !important;
}

/* ── Containers — cyberpunk card with cyan glow ── */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: rgba(0,240,255,0.1) !important;
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(0,240,255,0.03) !important;
  transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: rgba(0,240,255,0.1) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(0,240,255,0.28) !important;
  box-shadow: var(--glow-cyan), 0 2px 8px rgba(0,0,0,0.4) !important;
}
/* Nested bordered containers — transparent */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: rgba(0,240,255,0.06) !important;
  box-shadow: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(0,240,255,0.12) !important;
  box-shadow: none !important;
}
/* 3rd-level nested — invisible */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: transparent !important;
  border-color: transparent !important;
  box-shadow: none !important;
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
[data-testid="stElementToolbarButton"]:hover svg { color: var(--accent) !important; }

/* ── Status badges ── */
.badge-sold  { color: var(--green); font-weight: 600; text-shadow: 0 0 8px rgba(0,255,136,0.3); }
.badge-stock { color: var(--accent); font-weight: 600; text-shadow: 0 0 8px rgba(0,240,255,0.3); }

/* ── Hero banner — cyberpunk gaming card ── */
.hero-banner {
  background: linear-gradient(135deg, rgba(17,24,39,0.95) 0%, rgba(26,32,53,0.95) 100%);
  border: 1px solid rgba(0,240,255,0.15);
  border-radius: var(--radius);
  padding: 1.15rem 1.4rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--glow-cyan), 0 4px 16px rgba(0,0,0,0.5);
  position: relative;
  overflow: hidden;
}
.hero-banner::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), var(--purple), transparent);
  opacity: 0.8;
}
.hero-banner .logo {
  font-size: 1.6rem;
  opacity: 0.95;
  filter: drop-shadow(0 0 8px rgba(0,240,255,0.4));
}
.hero-banner h1 {
  margin: 0;
  font-size: clamp(1.05rem, 2.5vw, 1.35rem);
  font-weight: 900;
  letter-spacing: 0.02em;
  color: #ffffff;
  text-shadow: 0 0 20px rgba(0,240,255,0.2);
}
.hero-banner p {
  margin: 0;
  color: var(--text3);
  font-size: 0.78rem;
  letter-spacing: 0.08em;
  font-family: var(--mono);
}

/* ── Stat cards — gaming HUD panel ── */
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
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.2s ease;
}
.stat-card:hover {
  border-color: rgba(0,240,255,0.25);
  box-shadow: 0 0 16px rgba(0,240,255,0.08);
  transform: translateY(-2px);
}
.stat-card:hover::before { opacity: 1; }
.stat-card .val {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--accent);
  text-shadow: 0 0 10px rgba(0,240,255,0.2);
}
.stat-card .lbl {
  font-size: 0.66rem;
  color: var(--text3);
  margin-top: 0.2rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 600;
  font-family: var(--mono);
}

/* ── Section headings — neon accent with glow ── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  font-weight: 700;
  font-family: var(--mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 1.5rem 0 0.75rem !important;
  padding: 0;
  width: 100%;
  border-bottom: 1px solid rgba(0,240,255,0.1);
  padding-bottom: 0.5rem;
  text-shadow: 0 0 10px rgba(0,240,255,0.2);
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--accent), var(--purple));
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(0,240,255,0.4);
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(0,240,255,0.12), transparent);
  margin-left: 0.5rem;
}

/* ── Stat panels — cyberpunk card ── */
.stat-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem 0.75rem;
  margin-bottom: 0.75rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.stat-panel:hover {
  border-color: rgba(0,240,255,0.2);
  box-shadow: 0 0 12px rgba(0,240,255,0.05);
}

/* ── Metric cards — neon left accent bar ── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.65rem 0.85rem !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
div[data-testid="stMetric"]:hover {
  border-color: rgba(0,240,255,0.2) !important;
  border-left-color: var(--accent-h) !important;
  box-shadow: 0 0 18px rgba(0,240,255,0.08) !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
  overflow: hidden !important;
  transition: border-color 0.2s ease !important;
}
[data-testid="stExpander"]:hover {
  border-color: rgba(0,240,255,0.18) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.65rem 0.9rem !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* ── Progress bar — neon glow ── */
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--accent), var(--purple)) !important;
  border-radius: 4px !important;
  box-shadow: 0 0 10px rgba(0,240,255,0.3), 0 0 20px rgba(123,97,255,0.15);
}
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 4px !important;
}

/* ── Scrollbar — neon accent ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,240,255,0.15); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,240,255,0.3); }

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
  box-shadow: 0 0 0 3px rgba(0,240,255,0.1), 0 0 12px rgba(0,240,255,0.06) !important;
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
  background: rgba(0,240,255,0.1) !important;
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
  border-top: 1px solid rgba(0,240,255,0.08) !important;
  margin: 0.75rem 0 !important;
}

/* ── Sidebar section headings — neon accent ── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 700;
  font-family: var(--mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  padding: 0.4rem 0 0.25rem;
  border-bottom: 1px solid rgba(0,240,255,0.1);
  margin-bottom: 0.35rem;
  display: block;
  text-shadow: 0 0 8px rgba(0,240,255,0.15);
}

/* ── Radio pill chips — neon selection ── */
[data-testid="stRadio"] > div { gap: 0.25rem !important; flex-wrap: wrap !important; }
[data-testid="stRadio"] label {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--text2) !important;
  cursor: pointer !important;
  transition: all 0.2s ease !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(0,240,255,0.1) !important;
  border-color: rgba(0,240,255,0.35) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
  box-shadow: 0 0 10px rgba(0,240,255,0.08);
}
[data-testid="stRadio"] label:hover {
  border-color: var(--border-h) !important;
  color: var(--text) !important;
}
[data-testid="stRadio"] label input[type="radio"] { display: none !important; }
[data-testid="stRadio"] label > div:first-child { display: none !important; }

/* ── Ton lau badge — warning neon pink ── */
.badge-warn {
  background: rgba(255,45,117,0.12);
  color: var(--pink);
  border: 1px solid rgba(255,45,117,0.3);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.7rem;
  font-weight: 600;
  font-family: var(--mono);
  margin-left: 8px;
  vertical-align: middle;
  display: inline-block;
  box-shadow: 0 0 8px rgba(255,45,117,0.15);
  text-shadow: 0 0 6px rgba(255,45,117,0.3);
  animation: pulse-warn 2s ease-in-out infinite;
}
@keyframes pulse-warn {
  0%, 100% { box-shadow: 0 0 8px rgba(255,45,117,0.15); }
  50% { box-shadow: 0 0 16px rgba(255,45,117,0.3); }
}

/* ── Alerts — neon borders ── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.82rem !important;
  padding: 0.6rem 0.85rem !important;
}
[data-testid="stAlert"][kind="info"], div[data-testid="stInfo"] > div {
  background: rgba(0,240,255,0.04) !important;
  border-color: rgba(0,240,255,0.18) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="success"], div[data-testid="stSuccess"] > div {
  background: var(--green-bg) !important;
  border-color: rgba(0,255,136,0.25) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="warning"], div[data-testid="stWarning"] > div {
  background: var(--yellow-bg) !important;
  border-color: rgba(255,170,0,0.25) !important;
  color: var(--text) !important;
}
[data-testid="stAlert"][kind="error"], div[data-testid="stError"] > div {
  background: var(--red-bg) !important;
  border-color: rgba(255,51,85,0.25) !important;
  color: var(--text) !important;
}

/* ── Plotly chart containers — clean neon border ── */
.js-plotly-plot {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden !important;
}

/* ── Copy description button — neon gradient ── */
.copy-desc-btn {
  background: linear-gradient(135deg, var(--accent), var(--purple)) !important;
  color: #0b0e17 !important;
  border: none !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  box-shadow: var(--glow-cyan) !important;
}
.copy-desc-btn:hover {
  background: linear-gradient(135deg, var(--accent-h), #9580ff) !important;
}

/* ── Toast ── */
[data-testid="stToast"] {
  font-size: 0.84rem !important;
  border-radius: var(--radius) !important;
  background: var(--surface2) !important;
  border: 1px solid rgba(0,240,255,0.15) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5), 0 0 12px rgba(0,240,255,0.06) !important;
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
.empty-state .es-icon { font-size: 2rem; opacity: 0.35; filter: grayscale(0.5); }
.empty-state .es-title { font-size: 0.9rem; font-weight: 500; color: var(--text3); }
.empty-state .es-sub { font-size: 0.76rem; color: var(--text3); opacity: 0.6; }

/* ── Button load spinner ── */
.btn-busy {
  opacity: 0.5 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ── Gaming accent decorations ── */
.cyber-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), var(--purple), transparent);
  margin: 1rem 0;
  opacity: 0.5;
}

/* ── Neon text utility classes ── */
.neon-cyan { color: var(--accent); text-shadow: 0 0 10px rgba(0,240,255,0.3); }
.neon-pink { color: var(--pink); text-shadow: 0 0 10px rgba(255,45,117,0.3); }
.neon-green { color: var(--green); text-shadow: 0 0 10px rgba(0,255,136,0.3); }
.neon-purple { color: var(--purple); text-shadow: 0 0 10px rgba(123,97,255,0.3); }
.neon-yellow { color: var(--yellow); text-shadow: 0 0 10px rgba(255,170,0,0.3); }

/* ── Hero stat dot glow ── */
.hero-stat-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}
.hero-stat-dot.cyan { background: var(--accent); box-shadow: 0 0 10px rgba(0,240,255,0.5); }
.hero-stat-dot.pink { background: var(--pink); box-shadow: 0 0 10px rgba(255,45,117,0.5); }
.hero-stat-dot.green { background: var(--green); box-shadow: 0 0 10px rgba(0,255,136,0.5); }
.hero-stat-dot.purple { background: var(--purple); box-shadow: 0 0 10px rgba(123,97,255,0.5); }
.hero-stat-dot.muted { background: var(--text3); }

/* ── Mobile responsive ── */
@media (max-width: 768px) {
  .block-container { padding: 0.5rem 0.75rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.65rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.35rem 0.6rem !important; font-size: 0.72rem !important; }
  .hero-banner { padding: 0.55rem 0.65rem; gap: 0.35rem; flex-direction: column !important; align-items: flex-start !important; }
  .hero-banner > div:first-child { min-width: 0 !important; }
  .hero-banner .logo { font-size: 0.95rem; }
  .hero-banner h1 { font-size: 0.85rem !important; }
  .hero-banner p { font-size: 0.6rem; }
  .hero-banner > div:last-child { gap: 0.35rem !important; width: 100% !important; }
  .hero-banner > div:last-child > div { flex: 1 1 0 !important; min-width: 0 !important; padding: 0.35rem 0.5rem !important; }
  .hero-banner > div:last-child > div > div:first-child { font-size: 0.9rem !important; }
  .hero-banner > div:last-child > div > div:last-child { font-size: 0.55rem !important; }
  .sec-heading { font-size: 0.68rem; margin: 0.75rem 0 0.4rem; }

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
  ) > [data-testid="stColumn"] {
    flex: 1 1 100% !important; min-width: 100% !important;
  }

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
