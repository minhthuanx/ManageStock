"""
Hero banner — Purple→Fuchsia neon glow theme.
"""
import pandas as pd
import streamlit as st

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd, is_today_timestamp, is_today_bulk_date


def render_hero_banner(df, bulk_df, bulk_history):
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
      <div style="display:flex;align-items:center;gap:0.85rem;flex:1;min-width:180px;">
        <div class="logo">👻</div>
        <div>
          <h1 style="margin:0;">ManageStock{_badge_html}</h1>
          <p style="margin:0;color:#666;font-size:0.7rem;letter-spacing:0.02em;">Inventory Management · MINHTHUAN · 2026</p>
        </div>
      </div>
      <div style="display:flex;gap:0.55rem;flex-wrap:wrap;align-items:center;">
        <div style="display:flex;align-items:center;gap:0.55rem;background:rgba(139,92,246,0.18);border:1px solid rgba(139,92,246,0.3);border-radius:8px;padding:0.5rem 1rem;box-shadow:0 0 12px rgba(139,92,246,0.15),inset 0 0 15px rgba(139,92,246,0.05);transition:all 0.25s ease;">
          <div style="width:9px;height:9px;border-radius:50%;background:#8b5cf6;flex-shrink:0;box-shadow:0 0 8px rgba(139,92,246,0.6);"></div>
          <div>
            <div style="font-size:1.15rem;font-weight:700;color:#f0f0f0;line-height:1.2;">{_hb_con_hang_count}</div>
            <div style="font-size:0.65rem;color:#666;letter-spacing:0.04em;text-transform:uppercase;font-weight:500;">Còn hàng</div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:0.55rem;background:rgba(217,70,239,0.12);border:1px solid rgba(217,70,239,0.25);border-radius:8px;padding:0.5rem 1rem;box-shadow:0 0 12px rgba(217,70,239,0.1);transition:all 0.25s ease;">
          <div style="width:9px;height:9px;border-radius:50%;background:#d946ef;flex-shrink:0;box-shadow:0 0 8px rgba(217,70,239,0.5);"></div>
          <div>
            <div style="font-size:1.15rem;font-weight:700;color:#f0f0f0;line-height:1.2;">{_hb_da_ban}</div>
            <div style="font-size:0.65rem;color:#666;letter-spacing:0.04em;text-transform:uppercase;font-weight:500;">Đã bán</div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:0.55rem;background:rgba(52,211,153,0.15);border:1px solid rgba(52,211,153,0.3);border-radius:8px;padding:0.5rem 1rem;box-shadow:0 0 12px rgba(52,211,153,0.15),inset 0 0 15px rgba(52,211,153,0.05);transition:all 0.25s ease;">
          <div style="width:9px;height:9px;border-radius:50%;background:#34d399;flex-shrink:0;box-shadow:0 0 8px rgba(52,211,153,0.6);"></div>
          <div>
            <div style="font-size:1.15rem;font-weight:700;color:#f0f0f0;line-height:1.2;">{fmt_vnd(_hb_profit_today)}</div>
            <div style="font-size:0.65rem;color:#666;letter-spacing:0.04em;text-transform:uppercase;font-weight:500;">Hôm nay</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
