"""
Chart color palette for ManageStock dark theme (#0b1120 background).

Usage:
    from _colors import PAL, CLR, MUT_COLORS, PP_PAL, MUT_PALETTE
    marker_color = PAL  # cycle through for bars
    scatter = MUT_COLORS["Gold"]  # mutation-specific
"""

# ── Background & grid ──
BG      = "#0b1120"
BG_PLOT = "#0b1120"
GRID    = "#1e293b"
GRID_ZERO = "#1f1f1f"

# ── Text ──
FG      = "#f1f5f9"
MUTED   = "#94a3b8"
LABEL   = "#64748b"

# ── Semantic ──
POS     = "#22c55e"   # green — positive / success
NEG     = "#ef4444"   # red — negative / loss
NEUTRAL = "#60a5fa"   # blue — neutral / info
GOLD    = "#fbbf24"   # amber — accent / milestone
ACCENT  = "#f43f5e"   # rose — primary accent (matches CSS)

# ── Main categorical palette (high contrast on dark bg) ──
PAL = [
    "#38bdf8",  # sky-400  — cyan-blue
    "#f472b6",  # pink-400 — pink
    "#a78bfa",  # violet-400 — purple
    "#fb923c",  # orange-400 — orange
    "#34d399",  # emerald-400 — green
    "#facc15",  # yellow-400 — yellow
    "#f87171",  # red-400 — light red
    "#2dd4bf",  # teal-400 — teal
    "#c084fc",  # purple-400 — light purple
    "#e879f9",  # fuchsia-400 — fuchsia
    "#818cf8",  # indigo-400 — indigo
    "#fb7185",  # rose-400 — rose
    "#a3e635",  # lime-400 — lime
    "#22d3ee",  # cyan-400 — cyan
    "#fca5a5",  # red-300 — light coral
    "#86efac",  # green-300 — mint
]

# ── Mutation-specific colors ──
MUT_COLORS = {
    "Normal":      "#60a5fa",  # blue
    "Gold":        "#fbbf24",  # amber
    "Diamond":     "#a78bfa",  # violet
    "Bloodrot":    "#ef4444",  # red
    "Candy":       "#f472b6",  # pink
    "Divine":      "#c084fc",  # purple
    "Lava":        "#fb923c",  # orange
    "Galaxy":      "#818cf8",  # indigo
    "Yin-Yang":    "#f1f5f9",  # near white
    "Radioactive": "#34d399",  # emerald
    "Cursed":      "#f87171",  # light red
    "Rainbow":     "#e879f9",  # fuchsia
    "Chaos":       "#2dd4bf",  # teal
    "Frozen":      "#22d3ee",  # cyan
    "Neon":        "#a3e635",  # lime
    "Toxic":       "#86efac",  # mint
    "Sakura":      "#fb7185",  # rose
    "Eclipse":     "#c4b5fd",  # violet-300
    "Shadow":      "#94a3b8",  # slate-400
    "Mech":        "#7dd3fc",  # sky-300
    "Kitsune":     "#fdba74",  # orange-300
    "Angel":       "#e9d5ff",  # purple-200
    "Inferno":     "#dc2626",  # red-600
    "Venom":       "#059669",  # emerald-600
    "Blaze":       "#ea580c",  # orange-600
    "Phantom":     "#475569",  # slate-600
    "Void":        "#1e293b",  # slate-800
    "Không rõ":    "#64748b",  # slate-500
}

# Alias for backward compat
MUT_PALETTE = {k: v for k, v in MUT_COLORS.items()}

# ── Pet scatter palette ──
PP_PAL = [
    "#38bdf8", "#f472b6", "#a78bfa", "#fb923c", "#34d399",
    "#facc15", "#f87171", "#2dd4bf", "#c084fc", "#e879f9",
    "#818cf8", "#fb7185", "#a3e635", "#22d3ee", "#fca5a5",
    "#86efac", "#7dd3fc", "#fdba74", "#c4b5fd", "#e9d5ff",
]

# ── Sankey node palette ──
SANKEY_PAL = [
    "#38bdf8", "#f472b6", "#a78bfa", "#fb923c", "#34d399",
    "#facc15", "#f87171", "#2dd4bf", "#c084fc", "#e879f9",
    "#818cf8", "#fb7185", "#a3e635", "#22d3ee",
]

# ── Sankey link color ──
SANKEY_LINK = "rgba(56,189,248,0.22)"

# ── Heatmap scales ──
HEATMAP_TRADE = [
    [0.0,  BG],
    [0.01, "#064e3b"],
    [0.3,  "#047857"],
    [0.6,  "#10b981"],
    [1.0,  "#34d399"],
]

HEATMAP_HOUR = "YlOrRd"

# ── Gauge chart ──
GAUGE_STEPS = [
    {"range": [0,  40], "color": "rgba(248,113,113,0.15)"},
    {"range": [40, 70], "color": "rgba(251,191,36,0.12)"},
    {"range": [70,100], "color": "rgba(34,211,153,0.12)"},
]

# ── Helper: get color for trait bar ──
def trait_color(trait_name, index):
    if trait_name in ("None", "nan", "0", ""):
        return "#475569"  # slate — unknown
    return PAL[index % len(PAL)]
