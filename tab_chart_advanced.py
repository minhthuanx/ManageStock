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
                _colors = ["hsl(217, 91%, 60%)" if h == _peak_hour else "#0088aa" for h in _hour_count["Giờ"]]

                fig_hour = go.Figure(go.Bar(
                    x=[f"{h:02d}:00" for h in _hour_count["Giờ"]],
                    y=_hour_count["Đơn"],
                    marker_color=_colors,
                    text=_hour_count["Đơn"].apply(lambda v: str(v) if v > 0 else ""),
                    textposition="outside",
                    textfont=dict(size=11, color="hsl(210, 40%, 98%)"),
                ))
                fig_hour.update_layout(
                    xaxis_title="Khung giờ (giờ VN)",
                    yaxis_title="Số đơn bán",
                    margin=dict(t=35, b=45),
                    plot_bgcolor="hsl(222.2, 84%, 4.9%)",
                    paper_bgcolor="hsl(222.2, 84%, 4.9%)",
                    font=dict(family="Inter", color="hsl(215, 20.2%, 65.1%)", size=11),
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="hsl(215, 20.2%, 65.1%)")),
                    yaxis=dict(tickfont=dict(size=10, color="hsl(215, 20.2%, 65.1%)"), gridcolor="hsl(217.2, 32.6%, 12%)"),
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
                    plot_bgcolor="hsl(222.2, 84%, 4.9%)",
                    paper_bgcolor="hsl(222.2, 84%, 4.9%)",
                    font=dict(family="Inter", color="hsl(215, 20.2%, 65.1%)", size=11),
                    height=380,
                    xaxis=dict(tickangle=-45, tickfont=dict(size=10, color="hsl(215, 20.2%, 65.1%)")),
                    yaxis=dict(tickfont=dict(size=10, color="hsl(215, 20.2%, 65.1%)")),
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
        _ln_col_ch = pd.to_numeric(_all_sold_ch.get("Lợi Nhuận", pd.Series(dtype=float)), errors="coerce").fillna(0) if not _all_sold_ch.empty else pd.Series(dtype=float)

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

        # ── Dynamic achievement levels based on actual total ──
        _ACH_BASES = [
            (1,    "🌱 First Sale"),
            (10,   "🥉 Starter"),
            (50,   "🥈 Half Century"),
            (100,  "🥇 Century Club"),
            (250,  "💎 Quarter K"),
            (500,  "🏆 Legend"),
            (1000, "👑 Master"),
            (2500, "⚡ Elite"),
            (5000, "🌟 Grandmaster"),
            (10000,"🔥 Immortal"),
        ]
        # Pick the 4 levels surrounding current count (2 passed, current, 1 next)
        _ach_passed  = [(n, b) for n, b in _ACH_BASES if _total_sold_ch >= n]
        _ach_pending = [(n, b) for n, b in _ACH_BASES if _total_sold_ch < n]
        _badge_ch    = _ach_passed[-1][1] if _ach_passed else None
        _next_sell_ms = _ach_pending[0] if _ach_pending else None
        # Show 2 levels above current for context
        _ach_display = _ach_passed[-2:] + _ach_pending[:2] if len(_ach_passed) >= 2 else _ach_passed + _ach_pending[:3]
        _streak_icon_ch = "🔥" if _streak_ch >= 3 else ("✨" if _streak_ch >= 1 else "💤")

        _ach_c1, _ach_c2, _ach_c3 = st.columns(3)
        _ach_c1.metric("Chuỗi ngày", f"{_streak_icon_ch} {_streak_ch} ngày")
        _ach_c2.metric("Tổng giao dịch", f"{_total_sold_ch}")
        _ach_c3.metric("Cấp độ", _badge_ch or "—")
        if _next_sell_ms:
            _prev_ms = _ach_passed[-1][0] if _ach_passed else 0
            _range_total = _next_sell_ms[0] - _prev_ms
            _progress = (_total_sold_ch - _prev_ms) / _range_total if _range_total > 0 else 1.0
            st.progress(min(_progress, 1.0),
                        text=f"→ {_next_sell_ms[1]}: {_total_sold_ch} / {_next_sell_ms[0]} giao dịch ({_progress*100:.0f}%)")
        # Achievement level track
        _ach_track_cols = st.columns(len(_ach_display) if _ach_display else 1)
        for _ai, (_an, _ab) in enumerate(_ach_display):
            _done = _total_sold_ch >= _an
            _ach_track_cols[_ai].markdown(
                f"<div style='text-align:center;padding:6px 2px;border-radius:6px;"
                f"background:{'hsl(142, 76%, 56% / 0.12)' if _done else 'hsl(210, 40%, 98% / 0.03)'};"
                f"border:1px solid {'hsl(142, 76%, 56% / 0.3)' if _done else 'hsl(210, 40%, 98% / 0.06)'};'>"
                f"<div style='font-size:1.1rem;'>{'✅' if _done else '⬜'}</div>"
                f"<div style='font-size:0.65rem;color:{'hsl(142, 76%, 56%)' if _done else 'hsl(217.2, 20%, 45%)'};font-weight:600;'>{_ab}</div>"
                f"<div style='font-size:0.6rem;color:hsl(217.2, 20%, 40%);'>{_an}</div></div>",
                unsafe_allow_html=True,
            )

        # ── AK: Personal Records ──
        st.markdown("**Kỷ Lục**")
        if not _all_sold_ch.empty:
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

        # ── Mốc lợi nhuận tích lũy (dynamic) ──
        st.markdown("**Cột Mốc Lợi Nhuận**")
        # Dùng pbd (lẻ + lô) để tính tổng lợi nhuận chính xác
        _total_ln_ch = float(pbd["Lợi Nhuận"].sum()) if has_data and not pbd.empty else (float(_ln_col_ch.sum()) if not _all_sold_ch.empty else 0.0)
        _ln_m_ch = _total_ln_ch / 1_000_000

        # Dynamic milestones: generate steps that bracket current value
        def _gen_profit_milestones(current_m):
            if current_m <= 0:
                return [0.5, 1, 2, 3, 5, 10]
            import math
            mag = 10 ** math.floor(math.log10(max(current_m, 0.1)))
            if current_m < mag * 1.5:
                base_steps = [0.5, 1, 2, 3, 5]
            elif current_m < mag * 3:
                base_steps = [1, 2, 3, 5, 10]
            elif current_m < mag * 7:
                base_steps = [1, 2, 5, 10, 20]
            else:
                base_steps = [1, 2, 5, 10, 20, 50]
            candidates = sorted(set(s * mag for s in base_steps))
            return [c for c in candidates if c > 0]

        _LN_MS = _gen_profit_milestones(_ln_m_ch)
        _nxt_ln_ms = next((m for m in _LN_MS if _ln_m_ch < m), None)
        _lst_ln_ms = next((m for m in reversed(_LN_MS) if _ln_m_ch >= m), None)

        st.caption(f"Lợi nhuận tích lũy: **{fmt_vnd(_total_ln_ch)}**")
        if _nxt_ln_ms:
            _prev_ms_val = _lst_ln_ms if _lst_ln_ms else 0
            _range_ln    = _nxt_ln_ms - _prev_ms_val
            _pct_ln      = (_ln_m_ch - _prev_ms_val) / _range_ln if _range_ln > 0 else 1.0
            _pct_ln      = max(0.0, min(_pct_ln, 1.0))
            st.progress(_pct_ln,
                        text=f"Mốc {_nxt_ln_ms}M: {fmt_vnd(_total_ln_ch)} / {fmt_vnd(_nxt_ln_ms * 1_000_000)} ({_pct_ln*100:.0f}%)")
        else:
            _top = _LN_MS[-1] if _LN_MS else 100
            st.progress(1.0, text=f"🏆 Đã vượt {_top}M tích lũy!")
        # Milestone grid — show all, highlight next target
        _n_cols = min(len(_LN_MS), 5)
        _ms_rows = [_LN_MS[i:i+_n_cols] for i in range(0, len(_LN_MS), _n_cols)]
        for _ms_row in _ms_rows:
            _row_cols = st.columns(_n_cols)
            for _ci, _ms in enumerate(_ms_row):
                _done = _ln_m_ch >= _ms
                _is_next = (_nxt_ln_ms is not None and _ms == _nxt_ln_ms)
                _row_cols[_ci].markdown(
                    f"<div style='text-align:center;padding:5px 2px;border-radius:6px;"
                    f"background:{'hsl(142, 76%, 56% / 0.12)' if _done else ('hsl(217, 91%, 60% / 0.10)' if _is_next else 'hsl(210, 40%, 98% / 0.03)')};"
                    f"border:1px solid {'hsl(142, 76%, 56% / 0.3)' if _done else ('hsl(217, 91%, 60% / 0.3)' if _is_next else 'hsl(210, 40%, 98% / 0.06)')};"
                    f"{'font-weight:700;' if _is_next else ''}'>"
                    f"<div style='font-size:0.75rem;color:{'hsl(142, 76%, 56%)' if _done else ('hsl(217, 91%, 60%)' if _is_next else 'hsl(217.2, 20%, 45%)')};'>"
                    f"{'✅' if _done else ('🎯' if _is_next else '⬜')} {_ms}M</div></div>",
                    unsafe_allow_html=True,
                )
