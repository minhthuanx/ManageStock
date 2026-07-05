import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd, fmt_short, fmt_ngay_ton


def render_advanced(sold_df, pbd, has_data):
    # ── Phân tích theo NameStock ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Phân Tích Theo NameStock</div>', unsafe_allow_html=True)

        if not sold_df.empty and "NameStock" in sold_df.columns:
            _ns_grp = sold_df.copy()
            _ns_grp["LN"] = pd.to_numeric(_ns_grp["Lợi Nhuận"], errors="coerce").fillna(0)
            _ns_grp["DT"] = pd.to_numeric(_ns_grp["Doanh Thu"], errors="coerce").fillna(0)
            _ns_grp["NS"] = _ns_grp["NameStock"].astype(str).str.strip().replace("", "(trống)")
            _ns_perf = (
                _ns_grp.groupby("NS", as_index=False)
                .agg(LN_total=("LN","sum"), DT_total=("DT","sum"), Count=("LN","count"))
                .sort_values("LN_total", ascending=False)
            )
            _ns_disp = _ns_perf.rename(columns={"NS":"NameStock","Count":"Số con"}).copy()
            _ns_disp["Lợi nhuận"] = _ns_disp["LN_total"].apply(fmt_vnd)
            _ns_disp["Doanh thu"] = _ns_disp["DT_total"].apply(fmt_vnd)
            st.dataframe(_ns_disp[["NameStock","Số con","Lợi nhuận","Doanh thu"]], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu bán.")

    # ── Phân tích khung giờ bán hàng ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Phân Tích Khung Giờ Bán Hàng</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            def _extract_hour(ts_str):
                if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                    return None
                try:
                    dt = datetime.fromisoformat(str(ts_str))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=VN_TZ)
                    return dt.astimezone(VN_TZ).hour
                except Exception:
                    return None

            _hour_df = sold_df.copy()
            _hour_df["Giờ"] = _hour_df["time_ban"].apply(_extract_hour)
            _hour_df = _hour_df.dropna(subset=["Giờ"])
            _hour_df["Giờ"] = _hour_df["Giờ"].astype(int)

            if not _hour_df.empty:
                _hour_count = (
                    _hour_df.groupby("Giờ", as_index=False)
                    .agg(Đơn=("Giờ", "count"))
                )
                # Fill missing hours with 0 for full 0-23 axis
                _all_hours = pd.DataFrame({"Giờ": range(24)})
                _hour_count = _all_hours.merge(_hour_count, on="Giờ", how="left").fillna(0)
                _hour_count["Đơn"] = _hour_count["Đơn"].astype(int)

                _peak_hour = int(_hour_count.loc[_hour_count["Đơn"].idxmax(), "Giờ"])
                _colors = ["#f97316" if h == _peak_hour else "#c2410c" for h in _hour_count["Giờ"]]

                fig_hour = go.Figure(go.Bar(
                    x=[f"{h:02d}:00" for h in _hour_count["Giờ"]],
                    y=_hour_count["Đơn"],
                    marker_color=_colors,
                    text=_hour_count["Đơn"].apply(lambda v: str(v) if v > 0 else ""),
                    textposition="outside",
                    textfont=dict(size=11, color="#f0f0f5"),
                ))
                fig_hour.update_layout(
                    xaxis_title="Khung giờ (giờ VN)",
                    yaxis_title="Số đơn bán",
                    margin=dict(t=35, b=45),
                    plot_bgcolor="#0a0a0f",
                    paper_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#a8a8b8", size=11),
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="#a8a8b8")),
                    yaxis=dict(tickfont=dict(size=10, color="#a8a8b8"), gridcolor="#1a1a24"),
                    height=430,
                )
                st.plotly_chart(fig_hour, use_container_width=True)
                st.caption(f"Cao điểm: **{_peak_hour:02d}:00 – {_peak_hour:02d}:59** · {int(_hour_count.loc[_hour_count['Giờ']==_peak_hour,'Đơn'].values[0])} giao dịch")
            else:
                st.info("Chưa có dữ liệu thời gian bán hàng.")
        else:
            st.info("Chưa có dữ liệu bán.")

    # ── #27 Heatmap ngày × giờ ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Heatmap: Thứ × Giờ</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            def _extract_dt_parts(ts_str):
                """Returns (hour, weekday) or (None, None)."""
                if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                    return None, None
                try:
                    dt = datetime.fromisoformat(str(ts_str))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=VN_TZ)
                    dt = dt.astimezone(VN_TZ)
                    return dt.hour, dt.weekday()  # weekday: 0=Mon … 6=Sun
                except Exception:
                    return None, None

            _hmap_rows = sold_df["time_ban"].apply(_extract_dt_parts)
            _hmap_df2 = pd.DataFrame(_hmap_rows.tolist(), columns=["Giờ_h", "Thứ_w"])
            _hmap_df2 = _hmap_df2.dropna()
            _hmap_df2["Giờ_h"] = _hmap_df2["Giờ_h"].astype(int)
            _hmap_df2["Thứ_w"] = _hmap_df2["Thứ_w"].astype(int)

            if not _hmap_df2.empty:
                _pivot_hm = _hmap_df2.groupby(["Thứ_w", "Giờ_h"]).size().unstack(fill_value=0)
                for _hc in range(24):
                    if _hc not in _pivot_hm.columns:
                        _pivot_hm[_hc] = 0
                _pivot_hm = _pivot_hm[[c for c in range(24)]]
                for _rd in range(7):
                    if _rd not in _pivot_hm.index:
                        _pivot_hm.loc[_rd] = 0
                _pivot_hm = _pivot_hm.sort_index()
                _days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
                fig_hmap = go.Figure(go.Heatmap(
                    z=_pivot_hm.values,
                    x=[f"{h:02d}:00" for h in range(24)],
                    y=[_days_vn[i] for i in _pivot_hm.index],
                    colorscale="YlOrRd",
                    text=_pivot_hm.values,
                    texttemplate="%{text}",
                    showscale=True,
                ))
                fig_hmap.update_layout(
                    xaxis_title="Giờ (giờ VN)",
                    yaxis_title="Thứ",
                    margin=dict(t=35, b=55),
                    plot_bgcolor="#0a0a0f",
                    paper_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#a8a8b8", size=11),
                    height=380,
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="#a8a8b8")),
                    yaxis=dict(tickfont=dict(size=10, color="#a8a8b8")),
                )
                st.plotly_chart(fig_hmap, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu thời gian bán hàng.")
        else:
            st.info("Chưa có dữ liệu bán.")

    # ── AJ: Streak & Thành tích ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Thành Tích & Kỷ Lục</div>', unsafe_allow_html=True)

        _all_sold_ch = sold_df.copy()

        def _parse_ban_date_ch(ts_str):
            if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                return None
            try:
                dt = datetime.fromisoformat(str(ts_str))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=VN_TZ)
                return dt.astimezone(VN_TZ).date()
            except Exception:
                return None

        _today_ch = now_vn().date()
        _ban_dates_ch = _all_sold_ch["time_ban"].apply(_parse_ban_date_ch).dropna()
        _unique_days_ch = sorted(set(_ban_dates_ch), reverse=True)
        _streak_ch = 0
        if _unique_days_ch:
            _chk = _today_ch
            for _d in _unique_days_ch:
                if _d == _chk:
                    _streak_ch += 1
                    _chk = _chk - __import__("datetime").timedelta(days=1)
                elif _d < _chk:
                    break

        _total_sold_ch = len(pbd) if has_data else len(_all_sold_ch)
        _SELL_MILESTONES = [
            (500, "🏆 Legend Trader"),
            (200, "💎 Diamond Seller"),
            (100, "🥇 Century Club"),
            (50,  "🥈 Half Century"),
            (20,  "🥉 Getting Started"),
            (1,   "🌱 First Sale"),
        ]
        _badge_ch = next((b for n, b in _SELL_MILESTONES if _total_sold_ch >= n), None)
        _next_sell_ms = next(((n, b) for n, b in reversed(_SELL_MILESTONES) if _total_sold_ch < n), None)
        _streak_icon_ch = "🔥" if _streak_ch >= 3 else ("✨" if _streak_ch >= 1 else "💤")

        _ach_c1, _ach_c2, _ach_c3 = st.columns(3)
        _ach_c1.metric("Chuỗi ngày", f"{_streak_icon_ch} {_streak_ch} ngày")
        _ach_c2.metric("Tổng giao dịch", f"{_total_sold_ch}")
        _ach_c3.metric("Cấp độ", _badge_ch or "—")
        if _next_sell_ms:
            st.caption(f"Cột mốc tiếp theo · **{_next_sell_ms[1]}**: còn **{_next_sell_ms[0] - _total_sold_ch}** giao dịch")

        # ── AK: Personal Records ──
        st.markdown("**Kỷ Lục**")
        if not _all_sold_ch.empty:
            _ln_col_ch = pd.to_numeric(_all_sold_ch["Lợi Nhuận"], errors="coerce").fillna(0)
            _ton_col_ch = pd.to_numeric(_all_sold_ch["Ngày Tồn"], errors="coerce").fillna(999)

            _best_ln_row_ch = _all_sold_ch.loc[_ln_col_ch.idxmax()]
            _best_ln_val_ch = float(_ln_col_ch.max())
            _fast_valid = _ton_col_ch[_ton_col_ch >= 0]
            _fast_row_ch = _all_sold_ch.loc[_fast_valid.idxmin()] if not _fast_valid.empty else None
            _fast_days_ch = float(_fast_valid.min()) if not _fast_valid.empty else 0.0

            _day_df_ch = _all_sold_ch.copy()
            _day_df_ch["_bd"] = _day_df_ch["time_ban"].apply(_parse_ban_date_ch)
            _day_df_ch["_ln"] = pd.to_numeric(_day_df_ch["Lợi Nhuận"], errors="coerce").fillna(0)
            _day_profit_ch = _day_df_ch.dropna(subset=["_bd"]).groupby("_bd")["_ln"].sum()
            _best_day_ch = _day_profit_ch.idxmax() if not _day_profit_ch.empty else None
            _best_day_val_ch = float(_day_profit_ch.max()) if not _day_profit_ch.empty else 0.0

            _rec_c1, _rec_c2, _rec_c3 = st.columns(3)
            _rec_c1.metric("Giao dịch tốt nhất", fmt_vnd(_best_ln_val_ch),
                           help=str(_best_ln_row_ch.get('Tên Pet','?')))
            _rec_c2.metric("Chốt nhanh nhất", fmt_ngay_ton(_fast_days_ch),
                           help=str(_fast_row_ch.get('Tên Pet','?')) if _fast_row_ch is not None else "")
            _rec_c3.metric("Ngày đỉnh cao", fmt_vnd(_best_day_val_ch),
                           help=str(_best_day_ch) if _best_day_ch else "")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── Mốc lợi nhuận tích lũy ──
        st.markdown("**Cột Mốc Lợi Nhuận**")
        # Dùng pbd (lẻ + lô) để tính tổng lợi nhuận chính xác
        _total_ln_ch = float(pbd["Lợi Nhuận"].sum()) if has_data and not pbd.empty else (float(_ln_col_ch.sum()) if not _all_sold_ch.empty else 0.0)
        _ln_m_ch = _total_ln_ch / 1_000_000
        _LN_MS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        _nxt_ln_ms = next((m for m in _LN_MS if _ln_m_ch < m), None)
        _lst_ln_ms = next((m for m in reversed(_LN_MS) if _ln_m_ch >= m), None)
        st.caption(f"Lợi nhuận tích lũy: **{fmt_vnd(_total_ln_ch)}**")
        if _nxt_ln_ms:
            _tgt_ch = _nxt_ln_ms * 1_000_000
            _pct_ch = min(_total_ln_ch / _tgt_ch, 1.0) if _tgt_ch > 0 else 1.0
            st.progress(max(_pct_ch, 0.0),
                        text=f"Mốc {_nxt_ln_ms}M: {fmt_vnd(_total_ln_ch)} / {fmt_vnd(_tgt_ch)} ({_pct_ch*100:.0f}%)")
        else:
            st.progress(1.0, text="🏆 Đã vượt 100M tích lũy!")
        _ms_row1, _ms_row2 = st.columns(5), st.columns(5)
        for _ci, _ms in enumerate(_LN_MS):
            _done = _ln_m_ch >= _ms
            (_ms_row1 if _ci < 5 else _ms_row2)[_ci % 5].markdown(
                f"{'✅' if _done else '⬜'} **{_ms}M**"
            )
