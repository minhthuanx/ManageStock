import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import datetime as _dtm

from _timezone import VN_TZ, now_vn
from _helpers import fmt_vnd, fmt_short


def render_extra(df, bulk_df, bulk_history, sold_df, pbd, has_data):
        # ── SANKEY: Dòng chảy vốn theo Mutation ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Sankey — Dòng Chạy Vốn Theo Mutation</div>', unsafe_allow_html=True)

        _sk_src, _sk_tgt, _sk_val, _sk_labels, _sk_muts = [], [], [], [], []
        if not df.empty and "Mutation" in df.columns:
            _sk_all = df.copy()
            _sk_all["_mut"] = _sk_all["Mutation"].astype(str).str.strip().replace("", "Không rõ")
            _sk_all["_gn"]  = pd.to_numeric(_sk_all["Giá Nhập"], errors="coerce").fillna(0)
            _sk_all["_st"]  = _sk_all["Trạng Thái"].astype(str)
            _sk_muts   = sorted(_sk_all["_mut"].dropna().unique().tolist())
            _sk_labels = ["Tổng vốn nhập"] + _sk_muts + ["Đã bán", "Còn tồn"]
            _sk_n_sold  = 1 + len(_sk_muts)
            _sk_n_stock = 2 + len(_sk_muts)
            for _i, _m in enumerate(_sk_muts):
                _mdf = _sk_all[_sk_all["_mut"] == _m]
                _v_all = float(_mdf["_gn"].sum())
                if _v_all > 0:
                    _sk_src.append(0);       _sk_tgt.append(1 + _i);      _sk_val.append(_v_all)
                _v_sold = float(_mdf[_mdf["_st"].str.contains("Đã bán",   na=False)]["_gn"].sum())
                if _v_sold > 0:
                    _sk_src.append(1 + _i); _sk_tgt.append(_sk_n_sold);  _sk_val.append(_v_sold)
                _v_stock = float(_mdf[_mdf["_st"].str.contains("Còn hàng", na=False)]["_gn"].sum())
                if _v_stock > 0:
                    _sk_src.append(1 + _i); _sk_tgt.append(_sk_n_stock); _sk_val.append(_v_stock)

        if _sk_src:
            _mut_palette = ["#ff6a00","#22c55e","#f472b6","#a78bfa","#e879f9",
                            "#d8b4fe","#c4b5fd","#a5b4fc","#f0abfc","#ddd6fe"]
            _sk_node_colors = (
                ["#c2410c"]
                + [_mut_palette[i % len(_mut_palette)] for i in range(len(_sk_muts))]
                + ["#ff6a00", "#22c55e"]
            )
            fig_sk = go.Figure(go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18, thickness=22,
                    label=_sk_labels,
                    color=_sk_node_colors,
                    hovertemplate="%{label}: %{value:,.0f}₫<extra></extra>",
                ),
                link=dict(
                    source=_sk_src,
                    target=_sk_tgt,
                    value=_sk_val,
                    color="rgba(255,106,0,0.18)",
                ),
            ))
            fig_sk.update_layout(
                paper_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#f0f0f5", size=11),
                margin=dict(l=10, r=10, t=25, b=10),
                height=380,
            )
            st.plotly_chart(fig_sk, use_container_width=True)
            st.caption("Chiều rộng luồng = giá trị vốn nhập (₫)")
        else:
            st.info("Chưa đủ dữ liệu.")

        # ── CALENDAR HEATMAP: GitHub-style lợi nhuận ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Lịch Lợi Nhuận — 1 Năm Gần Nhất</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            _cal_today = now_vn().date()
            _cal_start = _cal_today - _dtm.timedelta(days=364)
            _cal_pbd = pbd.copy()
            _cal_pbd["_date"] = _cal_pbd["Ngày DT"].dt.date
            _cal_pbd["_ln"]   = pd.to_numeric(_cal_pbd["Lợi Nhuận"], errors="coerce").fillna(0)
            _day_map = _cal_pbd.groupby("_date")["_ln"].sum().to_dict()

            _all_days_cal = [_cal_start + _dtm.timedelta(days=i) for i in range(365)]
            _start_dow   = _all_days_cal[0].weekday()          # 0=Mon
            _padded_cal  = [None] * _start_dow + _all_days_cal
            while len(_padded_cal) % 7 != 0:
                _padded_cal.append(None)
            _n_weeks_cal = len(_padded_cal) // 7

            _z_cal, _text_cal = [], []
            _dow_labels_cal = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            for _dow in range(7):
                _rz, _rt = [], []
                for _wk in range(_n_weeks_cal):
                    _d = _padded_cal[_wk * 7 + _dow]
                    if _d is None:
                        _rz.append(None); _rt.append("")
                    else:
                        _p = _day_map.get(_d, 0)
                        _rz.append(float(_p))
                        _rt.append(
                            f"{_d.strftime('%d/%m/%Y')}<br>{fmt_vnd(_p)}" if _p
                            else f"{_d.strftime('%d/%m/%Y')}<br>—"
                        )
                _z_cal.append(_rz); _text_cal.append(_rt)

            _week_x_labels = []
            for _wk in range(_n_weeks_cal):
                _fd = next((x for x in _padded_cal[_wk*7:_wk*7+7] if x is not None), None)
                _week_x_labels.append(_fd.strftime("%d/%m") if _fd else "")

            _zmax_cal = max((v for v in _day_map.values() if v > 0), default=1)
            fig_cal = go.Figure(go.Heatmap(
                z=_z_cal,
                x=list(range(_n_weeks_cal)),
                y=_dow_labels_cal,
                text=_text_cal,
                hovertemplate="%{text}<extra></extra>",
                colorscale=[
                    [0.0,  "#110f1a"],
                    [0.01, "#0e4429"],
                    [0.3,  "#006d32"],
                    [0.6,  "#26a641"],
                    [1.0,  "#39d353"],
                ],
                zmin=0,
                zmax=_zmax_cal,
                showscale=True,
                colorbar=dict(thickness=12, len=0.8, tickfont=dict(size=9, color="#a8a8b8")),
                xgap=3, ygap=3,
            ))
            fig_cal.update_layout(
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#a8a8b8", size=10),
                xaxis=dict(
                    tickmode="array",
                    tickvals=list(range(0, _n_weeks_cal, 4)),
                    ticktext=[_week_x_labels[i] for i in range(0, _n_weeks_cal, 4)],
                    tickfont=dict(size=9, color="#a8a8b8"),
                    showgrid=False, zeroline=False,
                ),
                yaxis=dict(
                    tickfont=dict(size=10, color="#a8a8b8"),
                    showgrid=False, zeroline=False,
                    autorange="reversed",
                ),
                margin=dict(l=45, r=25, t=18, b=45),
                height=250,
            )
            st.plotly_chart(fig_cal, use_container_width=True)

            _cal_active = sum(1 for v in _day_map.values() if v > 0)
            _cal_max_d  = max(_day_map, key=_day_map.get) if _day_map else None
            _calcc1, _calcc2 = st.columns(2)
            _calcc1.caption(f"Ngày có giao dịch: **{_cal_active}** / 365 ngày")
            if _cal_max_d:
                _calcc2.caption(f"Ngày đỉnh cao: **{_cal_max_d.strftime('%d/%m/%Y')}** · {fmt_vnd(_day_map[_cal_max_d])}")
        else:
            st.info("Chưa có dữ liệu.")

        # ── ⚡ Xu Hướng Bán Theo Tuần ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Xu Hướng Bán Theo Tuần</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            _wk_df = pbd.copy()
            # Floor to Monday of each week (timezone-safe)
            _wk_df["_week"] = _wk_df["Ngày DT"] - pd.to_timedelta(
                _wk_df["Ngày DT"].dt.dayofweek, unit="d"
            )
            _wk_df["_week"] = _wk_df["_week"].dt.normalize()

            # Merge single sold count
            _wk_count_df = pd.DataFrame(columns=["_week","Số con"])
            if not sold_df.empty:
                _sc = sold_df.copy()
                _sc["_dt"] = pd.to_datetime(_sc["Ngày Bán"], dayfirst=True, errors="coerce")
                _sc["_week"] = (_sc["_dt"] - pd.to_timedelta(_sc["_dt"].dt.dayofweek, unit="d")).dt.normalize()
                _wk_count_df = _sc.groupby("_week", as_index=False).agg(**{"Số con": ("_week","count")})
            # Merge bulk sold count
            if not bulk_history.empty:
                _bh = bulk_history.copy()
                _bh["_dt"] = pd.to_datetime(_bh["Ngày Bán"], dayfirst=True, errors="coerce")
                _bh["_week"] = (_bh["_dt"] - pd.to_timedelta(_bh["_dt"].dt.dayofweek, unit="d")).dt.normalize()
                _bh_qty = _bh.groupby("_week", as_index=False).agg(
                    _bqty=("Số Lượng Bán" if "Số Lượng Bán" in _bh.columns else "Ngày Bán", "sum"
                           if "Số Lượng Bán" in _bh.columns else "count")
                ).rename(columns={"_bqty": "Số con bulk"})
                if not _wk_count_df.empty:
                    _wk_count_df = _wk_count_df.merge(_bh_qty, on="_week", how="outer").fillna(0)
                    _wk_count_df["Số con"] = _wk_count_df.get("Số con", 0) + _wk_count_df.get("Số con bulk", 0)
                else:
                    _wk_count_df = _bh_qty.rename(columns={"Số con bulk": "Số con"})

            _wk_ln = _wk_df.groupby("_week", as_index=False)["Lợi Nhuận"].sum()
            if not _wk_count_df.empty:
                _wk_merged = _wk_ln.merge(
                    _wk_count_df[["_week","Số con"]] if "Số con" in _wk_count_df.columns else _wk_ln[["_week"]],
                    on="_week", how="left"
                ).fillna(0)
            else:
                _wk_merged = _wk_ln.copy()
                _wk_merged["Số con"] = 0
            _wk_merged = _wk_merged.sort_values("_week").tail(16)  # last 16 weeks
            _wk_merged["_label"] = _wk_merged["_week"].dt.strftime("%d/%m/%Y")

            if len(_wk_merged) >= 1:
                # Trend line via simple linear regression
                _x = np.arange(len(_wk_merged))
                _y = _wk_merged["Lợi Nhuận"].values.astype(float)
                try:
                    _m_coef, _b_coef = np.polyfit(_x, _y, 1)
                except (np.linalg.LinAlgError, ValueError):
                    _m_coef, _b_coef = 0.0, float(_y.mean()) if len(_y) else 0.0
                _trend_y = _m_coef * _x + _b_coef
                _trend_color = "#34d399" if _m_coef >= 0 else "#f87171"
                _trend_label = f"Xu hướng {'↑ tăng' if _m_coef >= 0 else '↓ giảm'} {abs(_m_coef / max(abs(_y.mean()), 1) * 100):.1f}%/tuần"

                _bar_colors = ["#34d399" if v >= 0 else "#f87171" for v in _wk_merged["Lợi Nhuận"]]
                _fig_wk = go.Figure()
                _fig_wk.add_trace(go.Bar(
                    x=_wk_merged["_label"], y=_wk_merged["Lợi Nhuận"],
                    name="LN/tuần", marker_color=_bar_colors, opacity=0.7,
                    text=_wk_merged["Lợi Nhuận"].apply(fmt_short),
                    textposition="outside", textfont=dict(color="#f0f0f5", size=11),
                    hovertemplate="<b>%{x}</b><br>Lợi nhuận: %{y:,.0f}₫<extra></extra>",
                    yaxis="y1",
                ))
                _fig_wk.add_trace(go.Scatter(
                    x=_wk_merged["_label"], y=_wk_merged["Số con"],
                    name="Số con bán", mode="lines+markers",
                    line=dict(color="#ff6a00", width=2.5),
                    marker=dict(size=7, color="#ff6a00"),
                    hovertemplate="<b>%{x}</b><br>Số con: %{y:,.0f}<extra></extra>",
                    yaxis="y2",
                ))
                _fig_wk.add_trace(go.Scatter(
                    x=_wk_merged["_label"], y=_trend_y.tolist(),
                    name=_trend_label, mode="lines",
                    line=dict(color=_trend_color, width=2.5, dash="dash"),
                    hoverinfo="skip", yaxis="y1",
                ))
                _fig_wk.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#a8a8b8", size=11),
                    xaxis=dict(tickfont=dict(color="#f0f0f5", size=10), gridcolor="#1a1a24"),
                    yaxis=dict(title="Lợi nhuận (₫)", gridcolor="#1a1a24",
                               tickfont=dict(color="#a8a8b8", size=10), tickformat=",.0f",
                               zeroline=True, zerolinecolor="#2d2040"),
                    yaxis2=dict(title="Số con", overlaying="y", side="right",
                                tickfont=dict(color="#ff6a00", size=10), zeroline=False, showgrid=False),
                    legend=dict(orientation="h", x=0, y=1.1, font=dict(color="#a8a8b8", size=10)),
                    margin=dict(l=10, r=55, t=45, b=10),
                    height=430, barmode="overlay",
                )
                st.plotly_chart(_fig_wk, use_container_width=True)

                # 4 KPI cho tuần này vs tuần trước
                _last2 = _wk_merged.tail(2)
                if len(_last2) == 2:
                    _this = _last2.iloc[-1]
                    _prev = _last2.iloc[-2]
                    _wkc1, _wkc2, _wkc3, _wkc4 = st.columns(4)
                    _wkc1.metric("Lợi nhuận tuần này", fmt_vnd(_this["Lợi Nhuận"]),
                                 delta=fmt_short(_this["Lợi Nhuận"] - _prev["Lợi Nhuận"]))
                    _wkc2.metric("Tuần trước", fmt_vnd(_prev["Lợi Nhuận"]))
                    _wkc3.metric("Số con tuần này", f"{int(_this['Số con']):,}")
                    _avg_wk = float(_wk_merged["Lợi Nhuận"].mean())
                    _wkc4.metric("Trung bình mỗi tuần", fmt_vnd(_avg_wk))
        else:
            st.info("Chưa có dữ liệu.")

        # ── 🧬 Phân Tích Trait ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Phân Tích Theo Trait</div>', unsafe_allow_html=True)

        if not sold_df.empty and "Số Trait" in sold_df.columns:
            _tr_df = sold_df.copy()
            _tr_df["_ln"]    = pd.to_numeric(_tr_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _tr_df["_dt"]    = pd.to_numeric(_tr_df["Doanh Thu"],  errors="coerce").fillna(0)
            _tr_df["_gn"]    = pd.to_numeric(_tr_df["Giá Nhập"],   errors="coerce").fillna(0)
            _tr_df["_trait"] = _tr_df["Số Trait"].astype(str).str.strip().replace({"": "None", "nan": "None", "0": "None"})

            _tr_grp = (
                _tr_df.groupby("_trait", as_index=False)
                .agg(LN_mean=("_ln","mean"), LN_total=("_ln","sum"),
                     DT_total=("_dt","sum"),  GN_mean=("_gn","mean"), Count=("_ln","count"))
            )
            _tr_grp["Margin"] = (_tr_grp["LN_total"] / _tr_grp["DT_total"].replace(0, float("nan")) * 100).fillna(0)
            _sort_order = {"None":0}
            _tr_grp["_s"] = _tr_grp["_trait"].map(lambda x: _sort_order.get(x, 99))
            _tr_grp = _tr_grp.sort_values(["_s","LN_mean"], ascending=[True, False]).drop(columns=["_s"])

            _trc1, _trc2 = st.columns(2)
            with _trc1:
                _tr_colors = ["#94a3b8" if t == "None" else
                              "#34d399" if i % 3 == 1 else
                              "#a78bfa" if i % 3 == 2 else "#f472b6"
                              for i, t in enumerate(_tr_grp["_trait"])]
                _fig_tr = go.Figure(go.Bar(
                    x=_tr_grp["_trait"], y=_tr_grp["LN_mean"],
                    marker_color=_tr_colors, opacity=0.85,
                    text=_tr_grp["LN_mean"].apply(fmt_short),
                    textposition="outside", textfont=dict(color="#f0f0f5", size=10),
                    customdata=_tr_grp[["LN_total","Count","Margin"]].values,
                    hovertemplate=(
                        "<b>Trait: %{x}</b><br>"
                        "LN TB/con: %{y:,.0f}₫<br>"
                        "Tổng LN: %{customdata[0]:,.0f}₫<br>"
                        "Số con: %{customdata[1]}<br>"
                        "Margin: %{customdata[2]:.1f}%"
                        "<extra></extra>"
                    ),
                ))
                _fig_tr.update_layout(
                    title=dict(text="Lợi Nhuận TB / Con theo Trait", font=dict(size=12, color="#f0f0f5")),
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#a8a8b8", size=11),
                    xaxis=dict(gridcolor="#1a1a24", tickfont=dict(color="#f0f0f5", size=10)),
                    yaxis=dict(gridcolor="#1a1a24", tickfont=dict(color="#a8a8b8", size=10),
                               tickformat=",.0f", zeroline=True, zerolinecolor="#2d2040"),
                    margin=dict(l=10, r=10, t=45, b=10), height=400, showlegend=False,
                )
                st.plotly_chart(_fig_tr, use_container_width=True)

            with _trc2:
                _tr_disp = _tr_grp.copy()
                _tr_disp["LN TB/con"]  = _tr_disp["LN_mean"].apply(fmt_vnd)
                _tr_disp["Tổng LN"]    = _tr_disp["LN_total"].apply(fmt_vnd)
                _tr_disp["Giá nhập TB"] = _tr_disp["GN_mean"].apply(fmt_vnd)
                _tr_disp["Margin %"]   = _tr_disp["Margin"].apply(lambda v: f"{v:.1f}%")
                _tr_disp = _tr_disp.rename(columns={"_trait":"Trait","Count":"Số con"})
                st.markdown("**Bảng chi tiết theo Trait**")
                st.dataframe(
                    _tr_disp[["Trait","Số con","LN TB/con","Tổng LN","Giá nhập TB","Margin %"]],
                    use_container_width=True, hide_index=True, height=300,
                )
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── 🏦 Hiệu Suất Vốn ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hiệu Suất Vốn</div>', unsafe_allow_html=True)

        # Capital inputs
        _cap_invested_single = float(pd.to_numeric(df["Giá Nhập"], errors="coerce").fillna(0).sum()) if not df.empty else 0.0
        _cap_invested_bulk   = float(pd.to_numeric(bulk_df["Giá Nhập Tổng"], errors="coerce").fillna(0).sum()) if not bulk_df.empty else 0.0
        _cap_invested_total  = _cap_invested_single + _cap_invested_bulk

        # Capital returned (cost of sold items)
        _cap_returned_single = float(pd.to_numeric(sold_df["Giá Nhập"], errors="coerce").fillna(0).sum()) if not sold_df.empty else 0.0
        _cap_returned_bulk   = 0.0
        if not bulk_df.empty and not bulk_history.empty:
            _bdf_cost_rate = bulk_df.copy()
            _bdf_cost_rate["_orig"] = pd.to_numeric(_bdf_cost_rate["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
            _bdf_cost_rate["_cost"] = pd.to_numeric(_bdf_cost_rate["Giá Nhập Tổng"], errors="coerce").fillna(0)
            _bdf_cost_rate["_unit_cost"] = _bdf_cost_rate["_cost"] / _bdf_cost_rate["_orig"]
            _bdf_map = dict(zip(_bdf_cost_rate["Tên Lô"].astype(str), _bdf_cost_rate["_unit_cost"]))
            if "Tên Lô" in bulk_history.columns and "Số Lượng Bán" in bulk_history.columns:
                _bh2 = bulk_history.copy()
                _bh2["_qty"]  = pd.to_numeric(_bh2["Số Lượng Bán"], errors="coerce").fillna(0)
                _bh2["_rate"] = _bh2["Tên Lô"].astype(str).map(_bdf_map).fillna(0)
                _cap_returned_bulk = float((_bh2["_qty"] * _bh2["_rate"]).sum())
        _cap_returned_total = _cap_returned_single + _cap_returned_bulk

        # Locked capital (still in stock)
        _cap_locked_single = float(pd.to_numeric(
            df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]["Giá Nhập"],
            errors="coerce"
        ).fillna(0).sum()) if not df.empty else 0.0
        _cap_locked_bulk = 0.0
        if not bulk_df.empty:
            _bdf3 = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"].copy()
            if not _bdf3.empty:
                _bdf3["_orig"] = pd.to_numeric(_bdf3["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
                _bdf3["_left"] = pd.to_numeric(_bdf3["Còn Lại"], errors="coerce").fillna(0)
                _bdf3["_cost"] = pd.to_numeric(_bdf3["Giá Nhập Tổng"], errors="coerce").fillna(0)
                _cap_locked_bulk = float((_bdf3["_cost"] / _bdf3["_orig"] * _bdf3["_left"]).sum())
        _cap_locked_total = _cap_locked_single + _cap_locked_bulk

        _recovery_pct = _cap_returned_total / _cap_invested_total * 100 if _cap_invested_total > 0 else 0.0
        _lock_pct     = _cap_locked_total   / _cap_invested_total * 100 if _cap_invested_total > 0 else 0.0

        # Ước tính thời gian hoàn vốn: dựa trên tốc độ thu hồi vốn hiện tại
        _days_active = max((now_vn().replace(tzinfo=None) - pd.to_datetime(
            df["Ngày Nhập"].dropna().replace("", float("nan")),
            dayfirst=True, errors="coerce"
        ).dropna().min().replace(tzinfo=None)).days, 1) if not df.empty else 1
        _daily_recovery = _cap_returned_total / _days_active if _days_active > 0 else 0
        _days_to_recover = int(_cap_locked_total / _daily_recovery) if _daily_recovery > 0 else 0

        # Gauge chart: Recovery %
        _fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=_recovery_pct,
            delta={"reference": 80, "suffix": "%", "increasing": {"color": "#34d399"}, "decreasing": {"color": "#f87171"}},
            number={"suffix": "%", "font": {"size": 42, "color": "#f0f0f5", "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#2d2040",
                         "tickfont": {"color": "#a8a8b8", "size": 12}},
                "bar":  {"color": "#ff6a00", "thickness": 0.25},
                "bgcolor": "#0a0a0f",
                "bordercolor": "#1a1a24",
                "steps": [
                    {"range": [0,  40], "color": "rgba(248,113,113,0.12)"},
                    {"range": [40, 70], "color": "rgba(251,191,36,0.10)"},
                    {"range": [70,100], "color": "rgba(52,211,153,0.10)"},
                ],
                "threshold": {
                    "line": {"color": "#fbbf24", "width": 2.5},
                    "thickness": 0.85, "value": 80,
                },
            },
            title={"text": "% Vốn Đã Thu Hồi", "font": {"size": 12, "color": "#a8a8b8", "family": "Inter"}},
        ))
        _fig_gauge.update_layout(
            paper_bgcolor="#0a0a0f",
            font=dict(family="Inter", color="#a8a8b8", size=11),
            margin=dict(l=20, r=20, t=35, b=10),
            height=310,
        )

        _gc1, _gc2 = st.columns([1.1, 1])
        with _gc1:
            st.plotly_chart(_fig_gauge, use_container_width=True)
        with _gc2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            _cv1, _cv2 = st.columns(2)
            _cv1.metric("Tổng vốn đã bỏ ra",    fmt_vnd(_cap_invested_total))
            _cv2.metric("Vốn đã thu về",         fmt_vnd(_cap_returned_total))
            _cv3, _cv4 = st.columns(2)
            _cv3.metric("Vốn đang kẹt trong kho", fmt_vnd(_cap_locked_total),
                        delta=f"-{_lock_pct:.1f}% vốn")
            _cv4.metric("Ước tính hoàn vốn còn lại",
                        f"~{_days_to_recover} ngày" if _days_to_recover > 0 and _days_to_recover < 3650 else "—",
                        help="Dựa trên tốc độ thu hồi vốn trung bình hiện tại")
