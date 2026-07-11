"""
Sidebar — inventory stats, daily profit, target, sync button, auto-refresh.
"""
import pandas as pd
import streamlit as st

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd, is_today_timestamp, is_today_bulk_date
from _database import USE_SUPABASE, supabase_client


def render_sidebar(df, bulk_df, bulk_history, use_supabase):
    with st.sidebar:
        st.markdown("---")
        st.caption(f"{now_vn().strftime('%d/%m/%Y %H:%M')} (VN)")
        if use_supabase:
            st.success("Kết nối · Supabase Cloud", icon="✅")
        else:
            st.warning("Offline · Chế độ CSV cục bộ")

        # ── Ton kho real-time ──
        _con_hang = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        _von_le = float(pd.to_numeric(_con_hang["Giá Nhập"], errors="coerce").fillna(0).sum())
        _von_lo = float(pd.to_numeric(
            bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"]["Giá Nhập Tổng"], errors="coerce"
        ).fillna(0).sum())
        st.markdown('<span class="sidebar-heading">Tồn kho hiện tại</span>', unsafe_allow_html=True)
        st.metric("Có thể bán", f"{len(_con_hang):,} đơn vị", delta=None)
        st.metric("Vốn tồn — lẻ", fmt_vnd(_von_le))
        st.metric("Vốn tồn — lô", fmt_vnd(_von_lo))
        st.caption(f"Tổng vốn lưu động: **{fmt_vnd(_von_le + _von_lo)}**")
        st.markdown("---")

        # ── Dashboard hom nay ──
        _today_date = now_vn().date()
        _sold_today = df[df["time_ban"].apply(lambda ts: is_today_timestamp(ts, _today_date))] if "time_ban" in df.columns else pd.DataFrame(columns=df.columns)
        _today_count = len(_sold_today)
        _profit_le = float(pd.to_numeric(_sold_today["Lợi Nhuận"], errors="coerce").fillna(0).sum()) if "Lợi Nhuận" in _sold_today.columns else 0.0
        _bulk_today = bulk_history[bulk_history["Ngày Bán"].apply(lambda d: is_today_bulk_date(d, _today_date))] if (not bulk_history.empty and "Ngày Bán" in bulk_history.columns) else pd.DataFrame(columns=bulk_history.columns)
        _profit_bulk = float(pd.to_numeric(_bulk_today["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if "Lợi Nhuận Giao Dịch" in _bulk_today.columns else 0.0
        _today_profit = _profit_le + _profit_bulk
        st.markdown('<span class="sidebar-heading">Hôm nay</span>', unsafe_allow_html=True)
        _td1, _td2 = st.columns(2)
        _td1.metric("Giao dịch", f"{_today_count}")
        _td2.metric("Lợi nhuận", fmt_vnd(_today_profit))

        # ── Muc tieu loi nhuan ──
        st.number_input("Mục tiêu lợi nhuận (₫)", min_value=0, step=500_000,
                        value=5_000_000, key="daily_profit_target", format="%d")
        _daily_target_val = st.session_state["daily_profit_target"]
        if _daily_target_val > 0:
            _goal_pct = max(0, min(_today_profit / _daily_target_val, 1.0))
            st.progress(_goal_pct, text=f"{fmt_vnd(_today_profit)} / {fmt_vnd(_daily_target_val)} ({_goal_pct * 100:.0f}%)")
        st.markdown("---")

        # ── Copy Shop Description ──
        _SHOP_DESC = """👻Welcome to Nova Bolt - The Safest Way to Trade! 👻

Don't risk your items with "base-stealing" transfers. While others make you "steal" items from base to base, we use the "Trade Machine" for every order! 🚀

✅ Best Prices 💸

✅ Zero Risk (Trade Machine) 🔒

✅ Instant Delivery 🚚⚡

How to get your Brainrot 📦:

1️⃣ Send Username: Please provide your username after payment.

2️⃣ Stay Online: Stay active in-game to receive your trade invite.

3️⃣ Accept Invite: Our team will send you a request via the Trade Machine.

4️⃣ Confirm Trade: We transfer your Brainrot directly through the secure trade interface.

5️⃣ Secure the Loot: Once accepted, your Brainrot is 100% secured in your base—no risk of being intercepted!

Why Nova Bolt is Different?

In Steal a Brainrot, manual transfers are slow and dangerous. We skip the "stealing" hassle entirely! By utilizing the in-game Trade function, we guarantee your pets are protected during the entire process. No shared servers required, no risks taken.

Secure. Professional. Super Fast. 👻⚡"""
        st.session_state["_shop_desc"] = _SHOP_DESC
        st.markdown("---")

        if st.button("Đồng Bộ Dữ Liệu", use_container_width=True, type="primary"):
            with st.spinner("Đang đồng bộ..."):
                st.cache_data.clear()
                del st.session_state["initialized"]
            st.rerun()
