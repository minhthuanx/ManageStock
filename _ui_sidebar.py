"""
Sidebar — inventory stats, daily profit, target, sync button, auto-refresh.
"""
import os
import time

import pandas as pd
import psutil
import streamlit as st

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd
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
        _sold_today = st.session_state.get("_sold_today", pd.DataFrame())
        _today_count = len(_sold_today)
        _profit_le = float(pd.to_numeric(_sold_today["Lợi Nhuận"], errors="coerce").fillna(0).sum()) if not _sold_today.empty and "Lợi Nhuận" in _sold_today.columns else 0.0
        _bulk_today = st.session_state.get("_bulk_today", pd.DataFrame())
        _profit_bulk = float(pd.to_numeric(_bulk_today["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if (not _bulk_today.empty and "Lợi Nhuận Giao Dịch" in _bulk_today.columns) else 0.0
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

        # ── System Monitor ──
        st.markdown("---")
        st.markdown('<span class="sidebar-heading">🖥 System Monitor</span>', unsafe_allow_html=True)

        _mem = psutil.virtual_memory()
        _swap = psutil.swap_memory()
        _disk = psutil.disk_usage("/")
        _cpu_pct = psutil.cpu_percent(interval=0.1)
        _load1, _load5, _load15 = psutil.getloadavg()
        _proc = psutil.Process(os.getpid())
        _proc_mem = _proc.memory_info()
        _proc_mb = _proc_mem.rss / 1024**2
        _proc_threads = _proc.num_threads()
        _n_conn = len(psutil.net_connections())

        # RAM
        _ram_color = "#00ff88" if _mem.percent < 60 else "#fb923c" if _mem.percent < 85 else "#ff4444"
        st.markdown(f"**RAM** `{_mem.used/1024**3:.1f}` / `{_mem.total/1024**3:.1f} GB` **({_mem.percent}%)**")
        st.progress(_mem.percent / 100)

        # CPU
        st.markdown(f"**CPU** `{_cpu_pct}%` · Load `{_load1:.1f}` / `{_load5:.1f}` / `{_load15:.1f}`")

        # Disk
        st.markdown(f"**Disk** `{_disk.used/1024**3:.1f}` / `{_disk.total/1024**3:.1f} GB` **({_disk.percent}%)**")
        st.progress(_disk.percent / 100)

        # Swap
        if _swap.total > 0:
            st.markdown(f"**Swap** `{_swap.used/1024**3:.1f}` / `{_swap.total/1024**3:.1f} GB` ({_swap.percent}%)")

        # App process
        st.markdown("---")
        st.markdown(f"**🐍 App**")
        st.caption(f"Memory: **{_proc_mb:.0f} MB** · Threads: **{_proc_threads}** · PID: `{_proc.pid}`")
        st.caption(f"Connections: {_n_conn}")
