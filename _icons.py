"""
Inline SVG icons — Lucide style (24x24 viewBox, stroke-based, round caps).
All icons: stroke=currentColor, fill=none, stroke-width=1.5.
Usage: st.markdown(f'{IC.check} Saved', unsafe_allow_html=True)
"""


def _svg(paths: str, extra: str = "", size: int = 16) -> str:
    cls = f' width="{size}" height="{size}"'
    if extra:
        cls += f" {extra}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"'
        f' fill="none" stroke="currentColor" stroke-width="1.5"'
        f' stroke-linecap="round" stroke-linejoin="round"{cls}>'
        f"{paths}</svg>"
    )


# ── Status & Feedback ────────────────────────────────────────────────────────

check_circle = _svg(
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
    '<polyline points="22 4 12 14.01 9 11.01"/>',
)

x_circle = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="15" y1="9" x2="9" y2="15"/>'
    '<line x1="9" y1="9" x2="15" y2="15"/>',
)

alert_triangle = _svg(
    '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
    '<line x1="12" y1="9" x2="12" y2="13"/>'
    '<line x1="12" y1="17" x2="12.01" y2="17"/>',
)

info = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" y1="16" x2="12" y2="12"/>'
    '<line x1="12" y1="8" x2="12.01" y2="8"/>',
)

refresh = _svg(
    '<polyline points="23 4 23 10 17 10"/>'
    '<polyline points="1 20 1 14 7 14"/>'
    '<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
)

clock = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<polyline points="12 6 12 12 16 14"/>',
)

bell = _svg(
    '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>'
    '<path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
)

rotate_ccw = _svg(
    '<polyline points="9 14 4 9 9 4"/>'
    '<path d="M20 20v-7a4 4 0 0 0-4-4H4"/>',
)

# ── Actions ───────────────────────────────────────────────────────────────────

search = _svg(
    '<circle cx="11" cy="11" r="8"/>'
    '<line x1="21" y1="21" x2="16.65" y2="16.65"/>',
)

trash = _svg(
    '<polyline points="3 6 5 6 21 6"/>'
    '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    '<line x1="10" y1="11" x2="10" y2="17"/>'
    '<line x1="14" y1="11" x2="14" y2="17"/>',
)

download = _svg(
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="7 10 12 15 17 10"/>'
    '<line x1="12" y1="15" x2="12" y2="3"/>',
)

link = _svg(
    '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
    '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
)

rocket = _svg(
    '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>'
    '<path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
    '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>'
    '<path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
)

upload = _svg(
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
    '<polyline points="17 8 12 3 7 8"/>'
    '<line x1="12" y1="3" x2="12" y2="15"/>',
)

pin = _svg(
    '<line x1="12" y1="17" x2="12" y2="22"/>'
    '<path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.89A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.89A2 2 0 0 0 5 15.24Z"/>',
)

key = _svg(
    '<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>',
)

log_out = _svg(
    '<path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>'
    '<line x1="12" y1="2" x2="12" y2="12"/>',
)

# ── Inventory & Data ──────────────────────────────────────────────────────────

box = _svg(
    '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/>'
    '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
    '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
    '<line x1="12" y1="22.08" x2="12" y2="12"/>',
)

clipboard = _svg(
    '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
    '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>',
)

bar_chart = _svg(
    '<line x1="18" y1="20" x2="18" y2="10"/>'
    '<line x1="12" y1="20" x2="12" y2="4"/>'
    '<line x1="6" y1="20" x2="6" y2="14"/>',
)

activity = _svg(
    '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
)

shopping_cart = _svg(
    '<circle cx="9" cy="21" r="1"/>'
    '<circle cx="20" cy="21" r="1"/>'
    '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>',
)

save = _svg(
    '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>'
    '<polyline points="17 21 17 13 7 13 7 21"/>'
    '<polyline points="7 3 7 8 15 8"/>',
)

settings = _svg(
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-2.82 1.18V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15H4.09A2 2 0 1 1 2 12.09V12a1.65 1.65 0 0 0 1.09-1.54 1.65 1.65 0 0 0-1.51-1H2.09A2 2 0 1 1 2 6.46v-.37"/>',
)

# ── Category & UI ─────────────────────────────────────────────────────────────

paw = _svg(
    '<circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/><circle cx="20" cy="16" r="2"/>'
    '<path d="M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-6.84 1.045Q6.52 17.48 4.46 16.84A3.5 3.5 0 0 1 5.5 10z"/>',
)

tag = _svg(
    '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>'
    '<line x1="7" y1="7" x2="7.01" y2="7"/>',
)

dna = _svg(
    '<path d="M2 15c6.667-6 13.333 0 20-6"/>'
    '<path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"/>'
    '<path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"/>'
    '<path d="M17 6l-2.5-2.5"/><path d="M14 8l-1-1"/>'
    '<path d="M7 18l2.5 2.5"/><path d="M3.5 14.5l.5.5"/>'
    '<path d="M20 9l.5.5"/><path d="M6.5 12.5l1 1"/>'
    '<path d="M16.5 10.5l1 1"/><path d="M10 16l1.5 1.5"/>',
)

flame = _svg(
    '<path d="M12 2c1 3 2.5 3.5 3.5 4.5A5 5 0 0 1 17 10c0 3-2 6-5 8-3-2-5-5-5-8a5 5 0 0 1 1.5-3.5C8.5 5.5 10 5 12 2z"/>',
)

target = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<circle cx="12" cy="12" r="6"/>'
    '<circle cx="12" cy="12" r="2"/>',
)

check = _svg('<polyline points="20 6 9 17 4 12"/>')

database = _svg(
    '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
    '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
    '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
)

# ── Combined icon + text helper (for markdown sections) ───────────────────────

def icon_text(icon_svg: str, text: str, cls: str = "") -> str:
    """Wrap an SVG icon + text span in a flex row for use in st.markdown."""
    attr = f' class="{cls}"' if cls else ""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:0.35rem;vertical-align:middle;">'
        f'{icon_svg}'
        f'<span{attr}>{text}</span></span>'
    )
