"""
Hero banner — top stats bar, Linear-style minimal design.
"""
import pandas as pd
import streamlit as st
from datetime import datetime

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd, is_today_timestamp, is_today_bulk_date


def render_hero_banner(df, bulk_df, bulk_history):
    """Render a flat, minimal hero banner with inventory stats."""
    today = now_vn().date()

    _hb_con_hang = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
    _badge_count = int(_hb_con_hang[pd.to_numeric(_hb_con_hang["Ngày Tồn"], errors="coerce").fillna(0) >= 7].shape[0])
    _hb_con_hang_count = len(_hb_con_hang)
    _hb_da_ban_le = int(df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False).sum())
    _hb_da_ban_bk = int(pd.to_numeric(bulk_history["Số Lượng Bán"], errors="coerce").fillna(0).sum()) if not bulk_history.empty and "Số Lượng Bán" in bulk_history.columns else 0
    _hb_da_ban = _hb_da_ban_le + _hb_da_ban_bk

    _hb_sold_today = df[df["time_ban"].apply(lambda ts: is_today_timestamp(ts, today))] if "time_ban" in df.columns else pd.DataFrame(columns=df.columns)
    _hb_profit_le = float(pd.to_numeric(_hb_sold_today["Lợi Nhuận"], errors="coerce").fillna(0).sum()) if "Lợi Nhuận" in _hb_sold_today.columns else 0.0
    _hb_bulk_today = bulk_history[bulk_history["Ngày Bán"].apply(lambda d: is_today_bulk_date(d, today))] if (not bulk_history.empty and "Ngày Bán" in bulk_history.columns) else pd.DataFrame()
    _hb_profit_bulk = float(pd.to_numeric(_hb_bulk_today["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if (not _hb_bulk_today.empty and "Lợi Nhuận Giao Dịch" in _hb_bulk_today.columns) else 0.0
    _hb_profit_today = _hb_profit_le + _hb_profit_bulk

    _badge_html = f'<span class="badge-warn">{_badge_count} tồn lâu</span>' if _badge_count > 0 else ""

    st.markdown(f"""
    <div class="hero-banner">
      <div style="display:flex;align-items:center;gap:0.75rem;flex:1;min-width:180px;">
        <div class="logo">👻</div>
        <div>
          <h1 style="margin:0;">ManageStock{_badge_html}</h1>
          <p style="margin:0;">MINHTHUAN · 2026</p>
        </div>
      </div>
      <div style="display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center;">
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:0.35rem 0.75rem;text-align:center;min-width:60px;">
          <div style="font-size:1.1rem;font-weight:600;color:var(--text);line-height:1.2;">{_hb_con_hang_count}</div>
          <div style="font-size:0.62rem;color:var(--text3);letter-spacing:0.05em;text-transform:uppercase;font-weight:500;">Còn hàng</div>
        </div>
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:0.35rem 0.75rem;text-align:center;min-width:60px;">
          <div style="font-size:1.1rem;font-weight:600;color:var(--text);line-height:1.2;">{_hb_da_ban}</div>
          <div style="font-size:0.62rem;color:var(--text3);letter-spacing:0.05em;text-transform:uppercase;font-weight:500;">Đã bán</div>
        </div>
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:0.35rem 0.75rem;text-align:center;min-width:60px;">
          <div style="font-size:1.05rem;font-weight:600;color:var(--green);line-height:1.2;">{fmt_vnd(_hb_profit_today)}</div>
          <div style="font-size:0.62rem;color:var(--text3);letter-spacing:0.05em;text-transform:uppercase;font-weight:500;">Hôm nay</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
