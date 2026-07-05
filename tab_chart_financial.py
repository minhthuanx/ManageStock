from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from _timezone import VN_TZ
from _helpers import fmt_vnd, fmt_short
from _config import EXCHANGE_RATE


def render_financial(df, bulk_df, bulk_history, sold_df, pbd, has_data, total_cost, total_rev, net_profit):
    # ── Waterfall: Dòng Chảy Tài Chính ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Dòng Chảy Tài Chính</div>', unsafe_allow_html=True)

        if total_rev > 0 or total_cost > 0:
            _margin_pct = net_profit / total_rev * 100 if total_rev > 0 else 0
            _roi_pct    = net_profit / total_cost * 100 if total_cost > 0 else 0
            _sold_cnt   = len(sold_df)
            if not bulk_history.empty and "Số Lượng Bán" in bulk_history.columns:
                _sold_cnt += int(pd.to_numeric(bulk_history["Số Lượng Bán"], errors="coerce").fillna(0).sum())
            _cap_remain = float(
                pd.to_numeric(
                    df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]["Giá Nhập"],
                    errors="coerce"
                ).fillna(0).sum()
            )
            if not bulk_df.empty:
                _bdf2 = bulk_df.copy()
                _bdf2["_orig"] = pd.to_numeric(_bdf2["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
                _bdf2["_left"] = pd.to_numeric(_bdf2["Còn Lại"],       errors="coerce").fillna(0)
                _bdf2["_cost"] = pd.to_numeric(_bdf2["Giá Nhập Tổng"], errors="coerce").fillna(0)
                _cap_remain += float((_bdf2["_cost"] / _bdf2["_orig"] * _bdf2["_left"]).sum())

            _wr1, _wr2, _wr3, _wr4 = st.columns(4)
            _wr1.metric("📊 Margin",          f"{_margin_pct:.1f}%")
            _wr2.metric("💹 ROI",             f"{_roi_pct:.1f}%")
            _wr3.metric("🛒 Con đã bán",      f"{_sold_cnt:,}")
            _wr4.metric("🏦 Vốn còn tồn",    fmt_vnd(_cap_remain))

            _wf_labels = ["Tổng Doanh Thu", "Tổng Vốn", "Lợi Nhuận Ròng"]
            _wf_vals   = [total_rev, total_cost, abs(net_profit)]
            _wf_colors = ["#34d399", "#f87171", "#a78bfa" if net_profit >= 0 else "#f87171"]

            _fig_wf = go.Figure(go.Bar(
                x=_wf_labels,
                y=_wf_vals,
                marker_color=_wf_colors,
                text=[fmt_short(v) for v in _wf_vals],
                textposition="outside",
                textfont=dict(color="#e2e8f0", size=12, family="Inter"),
                hovertemplate="<b>%{x}</b><br>%{y:,.0f}₫<extra></extra>",
                width=[0.45, 0.45, 0.45],
            ))
            # Overlay a "+" or "-" annotation on LN bar to show sign
            _ln_sign_text = ("+" if net_profit >= 0 else "−") + fmt_short(abs(net_profit))
            _fig_wf.add_annotation(
                x="Lợi Nhuận Ròng", y=abs(net_profit),
                text=f"<b>{'+ ' if net_profit >= 0 else '- '}{fmt_short(abs(net_profit))}</b>",
                showarrow=False, yshift=22,
                font=dict(color="#a78bfa" if net_profit >= 0 else "#f87171", size=13)
            )
            _fig_wf.update_layout(
                paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf"),
                xaxis=dict(tickfont=dict(color="#e2e8f0", size=13), gridcolor="#1a1528", zeroline=False),
                yaxis=dict(tickfont=dict(color="#9d8fbf"), gridcolor="#1a1528",
                           tickformat=",.0f", zeroline=False),
                margin=dict(l=10, r=10, t=50, b=10),
                height=340,
                showlegend=False,
                bargap=0.35,
            )
            st.plotly_chart(_fig_wf, use_container_width=True)
            st.caption("🟢 Doanh thu · 🔴 Chi phí vốn · 🟣 Lợi nhuận ròng (tất cả các thanh bắt đầu từ 0)")
        else:
            st.info("Chưa có dữ liệu tài chính.")

        # ── Period selector ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Biểu Đồ Lợi Nhuận</div>', unsafe_allow_html=True)
        period_col, _ = st.columns([2, 3])
        period = period_col.radio(
            "Xem theo",
            ["Theo ngày", "Theo tuần", "Theo tháng"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if has_data and not pbd.empty:
            chart_df = pbd.copy()

            if period == "Theo ngày":
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("%d/%m/%Y")
                sort_key = chart_df["Ngày DT"].dt.normalize()
            elif period == "Theo tuần":
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("W%V/%Y")
                sort_key = (
                    chart_df["Ngày DT"]
                    - pd.to_timedelta(chart_df["Ngày DT"].dt.dayofweek, unit="d")
                ).dt.normalize()
            else:
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("%m/%Y")
                sort_key = chart_df["Ngày DT"].dt.strftime("%Y-%m")

            chart_df["SortKey"] = sort_key
            agg = (
                chart_df.groupby(["Period","SortKey"], as_index=False)["Lợi Nhuận"]
                .sum()
                .sort_values("SortKey")
            )
            # agg_real: chỉ các kỳ có giao dịch thật — dùng cho metrics (count, avg)
            agg_real = agg.copy()

            # Đảm bảo kỳ hiện tại luôn xuất hiện trên chart (dù chưa có giao dịch hôm nay)
            _now_vn = datetime.now(VN_TZ)
            if period == "Theo ngày":
                _cur_period  = _now_vn.strftime("%d/%m/%Y")
                _cur_sort    = pd.Timestamp(_now_vn.date())
            elif period == "Theo tuần":
                _cur_period  = _now_vn.strftime("W%V/%Y")
                _cur_sort    = pd.Timestamp(
                    _now_vn.date() - pd.Timedelta(days=_now_vn.weekday())
                )
            else:
                _cur_period  = _now_vn.strftime("%m/%Y")
                _cur_sort    = _now_vn.strftime("%Y-%m")

            if _cur_period not in agg["Period"].values:
                _today_row = pd.DataFrame([{
                    "Period":     _cur_period,
                    "SortKey":    _cur_sort,
                    "Lợi Nhuận": 0,
                }])
                agg = pd.concat([agg, _today_row], ignore_index=True).sort_values("SortKey")

            agg["Label"] = agg["Lợi Nhuận"].apply(fmt_short)

            # Dark bar chart like reference image
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=agg["Period"],
                y=agg["Lợi Nhuận"],
                text=agg["Label"],
                textposition="outside",
                textfont=dict(size=11, color="#e2e8f0", family="Inter"),
                marker=dict(
                    color="#c084fc",
                    line=dict(color="#c084fc", width=0),
                ),
                cliponaxis=False,
            ))
            fig.update_layout(
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf", size=11),
                xaxis=dict(
                    type="category",
                    tickfont=dict(size=10, color="#9d8fbf"),
                    gridcolor="#1a1528",
                    linecolor="#2d2540",
                ),
                yaxis=dict(
                    title="Lợi nhuận (VNĐ)",
                    tickfont=dict(size=10, color="#9d8fbf"),
                    gridcolor="#1a1528",
                    linecolor="#2d2540",
                    tickformat=",.0f",
                ),
                margin=dict(l=10, r=10, t=30, b=10),
                height=420,
                bargap=0.35,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Period stats below chart ──
            period_label = {"Theo ngày":"ngày","Theo tuần":"tuần","Theo tháng":"tháng"}[period]
            last_row = agg.iloc[-1] if not agg.empty else None
            prev_row = agg.iloc[-2] if len(agg) >= 2 else None

            c1, c2, c3 = st.columns(3)
            if last_row is not None:
                delta = None
                if prev_row is not None:
                    delta_val = last_row["Lợi Nhuận"] - prev_row["Lợi Nhuận"]
                    # Streamlit detects sign from string prefix — must put "-" before "₫"
                    _delta_cmp_lbl = {
                        "Theo ngày":  "so với hôm qua",
                        "Theo tuần":  "so với tuần trước",
                        "Theo tháng": "so với tháng trước",
                    }.get(period, "")
                    delta = ("-" if delta_val < 0 else "") + f"₫{abs(delta_val):,.0f}" + (f" {_delta_cmp_lbl}" if _delta_cmp_lbl else "")
                _period_delta_label = {
                    "Theo ngày":  "so với hôm qua",
                    "Theo tuần":  "so với tuần trước",
                    "Theo tháng": "so với tháng trước",
                }.get(period, "")
                _this_period_lbl = {
                    "Theo ngày":  "hôm nay",
                    "Theo tuần":  "tuần này",
                    "Theo tháng": "tháng này",
                }.get(period, period_label)
                c1.metric(
                    f"Lợi nhuận {_this_period_lbl} ({last_row['Period']})",
                    fmt_vnd(last_row["Lợi Nhuận"]),
                    delta=delta,
                    help=f"So sánh {_period_delta_label}",
                )
                c2.metric(f"Số {period_label} có giao dịch",  f"{len(agg_real):,}")
                c3.metric(f"Lợi nhuận trung bình mỗi {period_label}",  fmt_vnd(agg_real['Lợi Nhuận'].mean() if not agg_real.empty else 0))
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

        # ── Cumulative Profit Line ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Lợi Nhuận Tích Lũy</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            # Group by date → one data point per day
            _cum_daily = (
                pbd[["Ngày DT","Lợi Nhuận"]]
                .dropna(subset=["Ngày DT"])
                .assign(_date=lambda d: d["Ngày DT"].dt.date)
                .groupby("_date", as_index=False)["Lợi Nhuận"].sum()
                .sort_values("_date")
                .copy()
            )
            _cum_daily["Tích Lũy"] = _cum_daily["Lợi Nhuận"].cumsum()
            _cum_daily["Ngày DT"]  = pd.to_datetime(_cum_daily["_date"])

            # milestone annotations (only those reached) - auto generate every 10M
            _max_cum = float(_cum_daily["Tích Lũy"].max())
            _cum_milestones = [int(i * 10_000_000) for i in range(1, int(_max_cum / 10_000_000) + 2)]
            _annotations = []
            for _ms_val in _cum_milestones:
                _cross = _cum_daily[_cum_daily["Tích Lũy"] >= _ms_val]
                if not _cross.empty:
                    _ms_row = _cross.iloc[0]
                    _annotations.append(dict(
                        x=_ms_row["Ngày DT"], y=_ms_val,
                        text=f"🏆 {_ms_val//1_000_000}M",
                        showarrow=True, arrowhead=2, arrowcolor="#fef08a",
                        font=dict(color="#fef08a", size=10),
                        bgcolor="#1a1528", bordercolor="#fef08a", borderwidth=1,
                        ax=0, ay=-30,
                    ))

            _bar_colors = ["#34d399" if v >= 0 else "#f87171" for v in _cum_daily["Lợi Nhuận"]]

            _fig_cum = go.Figure()
            _fig_cum.add_trace(go.Bar(
                x=_cum_daily["Ngày DT"], y=_cum_daily["Lợi Nhuận"],
                name="LN ngày",
                yaxis="y2",
                marker=dict(color=_bar_colors, opacity=0.55),
                hovertemplate="%{x|%d/%m/%Y}<br>LN ngày: <b>%{y:,.0f}₫</b><extra></extra>",
            ))
            _fig_cum.add_trace(go.Scatter(
                x=_cum_daily["Ngày DT"], y=_cum_daily["Tích Lũy"],
                mode="lines",
                fill="tozeroy",
                fillcolor="rgba(167,139,250,0.12)",
                line=dict(color="#a78bfa", width=2.5),
                name="Tích lũy",
                hovertemplate="%{x|%d/%m/%Y}<br>Tích lũy: <b>%{y:,.0f}₫</b><extra></extra>",
            ))

            _fig_cum.update_layout(
                paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf"),
                annotations=_annotations,
                xaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#9d8fbf"), showgrid=False),
                yaxis=dict(
                    title="Tích lũy (₫)", gridcolor="#1a1528",
                    tickfont=dict(color="#9d8fbf"), tickformat=",.0f",
                    zeroline=True, zerolinecolor="#2d2040",
                ),
                yaxis2=dict(
                    title="LN ngày (₫)", overlaying="y", side="right",
                    showgrid=False, tickfont=dict(color="#9d8fbf"),
                    tickformat=",.0f",
                ),
                legend=dict(orientation="h", x=0, y=1.08, font=dict(color="#9d8fbf")),
                margin=dict(l=10, r=10, t=40, b=10),
                height=360,
                hovermode="x unified",
                bargap=0.2,
            )
            st.plotly_chart(_fig_cum, use_container_width=True)

            # Summary KPIs
            _cum_total     = float(_cum_daily["Tích Lũy"].iloc[-1])
            _cum_best_day  = float(_cum_daily["Lợi Nhuận"].max())
            _cum_worst_day = float(_cum_daily["Lợi Nhuận"].min())
            _cum_pos_days  = int((_cum_daily["Lợi Nhuận"] > 0).sum())
            _cum_total_days = len(_cum_daily)
            _kc1, _kc2, _kc3, _kc4 = st.columns(4)
            _kc1.metric("Tổng tích lũy", fmt_vnd(_cum_total))
            _kc2.metric("📈 Ngày đỉnh", fmt_vnd(_cum_best_day))
            _kc3.metric("📉 Ngày thấp nhất", fmt_vnd(_cum_worst_day))
            _kc4.metric("✅ Ngày có lời", f"{_cum_pos_days} / {_cum_total_days} ngày")
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")
