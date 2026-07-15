import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from _timezone import now_vn, VN_TZ
from _helpers import fmt_vnd, fmt_short
from _config import EXCHANGE_RATE


def render_overview(df, bulk_df, bulk_history, sold_df, pbd, has_data, total_cost, total_rev, net_profit, total_stock):
    # ── KPI Row ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Tổng Quan</div>', unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Lợi nhuận ròng",   fmt_vnd(net_profit))
        k2.metric("📈 Tổng doanh thu",   fmt_vnd(total_rev))
        k3.metric("📥 Tổng vốn nhập",    fmt_vnd(total_cost))
        k4.metric("📦 Pet đang tồn",     f"{total_stock:,}")

    # ── Thống kê theo tháng — biểu đồ ──
    if has_data and not pbd.empty:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">Thống Kê Theo Tháng</div>', unsafe_allow_html=True)
            _mo_df = (
                pbd.assign(
                    _mo=pbd["Ngày DT"].dt.strftime("%m/%Y"),
                    _sk=pbd["Ngày DT"].dt.strftime("%Y-%m"),
                )
                .groupby(["_mo","_sk"], as_index=False)
                .agg(_ln=("Lợi Nhuận","sum"), _cnt=("Lợi Nhuận","count"))
                .sort_values("_sk")
            )
            _mo_colors = [
                "#00ff88" if v >= 0 else "#f87171"
                for v in _mo_df["_ln"]
            ]
            _fig_mo = go.Figure(go.Bar(
                x=_mo_df["_mo"],
                y=_mo_df["_ln"],
                marker_color=_mo_colors,
                marker_line_width=0,
                text=[
                    f"{fmt_short(v)}<br><span style='font-size:11px;color:#8b93a7'>{c} GD</span>"
                    for v, c in zip(_mo_df["_ln"], _mo_df["_cnt"])
                ],
                textposition="outside",
                textfont=dict(color="#e8eaf0", size=11),
                hovertemplate="<b>%{x}</b><br>Lợi nhuận: %{y:,.0f}₫<extra></extra>",
            ))
            _fig_mo.update_layout(
                paper_bgcolor="#0b0e17",
                plot_bgcolor="#0b0e17",
                font=dict(family="Inter", color="#8b93a7", size=11),
                xaxis=dict(
                    gridcolor="#1a2035",
                    tickfont=dict(color="#e8eaf0", size=10),
                    tickangle=0,
                ),
                yaxis=dict(
                    gridcolor="#1a2035",
                    tickfont=dict(color="#8b93a7", size=10),
                    tickformat=",.0f",
                    zeroline=True,
                    zerolinecolor="#222230",
                ),
                margin=dict(l=10, r=10, t=45, b=10),
                height=260,
                showlegend=False,
                bargap=0.35,
            )
            st.plotly_chart(_fig_mo, use_container_width=True)
            # KPI tóm tắt
            if _mo_df.empty:
                st.info("Không đủ dữ liệu để hiển thị thống kê theo tháng.")
            else:
                _mo_best_idx = _mo_df["_ln"].idxmax()
                _mo_best_mo  = _mo_df.loc[_mo_best_idx, "_mo"]
                _mo_best_ln  = float(_mo_df.loc[_mo_best_idx, "_ln"])
                _mo_best_cnt = int(_mo_df.loc[_mo_best_idx, "_cnt"])
                # Lọc đúng tháng hiện tại (không dùng iloc[-1] để tránh hiển thị tháng cũ)
                _cur_mo_sk   = now_vn().strftime("%Y-%m")
                _mo_cur_rows = _mo_df[_mo_df["_sk"] == _cur_mo_sk]
                _mo_last_ln  = float(_mo_cur_rows["_ln"].iloc[0]) if not _mo_cur_rows.empty else 0.0
                _mo_last_cnt = int(_mo_cur_rows["_cnt"].iloc[0]) if not _mo_cur_rows.empty else 0
                _mc1, _mc2, _mc3 = st.columns(3)
                _mc1.metric("📅 Tháng hiện tại",
                            fmt_vnd(_mo_last_ln),
                            delta=f"{_mo_last_cnt} giao dịch", delta_color="off")
                _mc2.metric("🏆 Tháng tốt nhất",
                            f"{_mo_best_mo}",
                            delta=fmt_vnd(_mo_best_ln), delta_color="off")
                _mc3.metric("📊 TB / tháng",
                            fmt_vnd(float(_mo_df["_ln"].mean())),
                            delta=f"{int(_mo_df['_cnt'].mean())} GD/tháng", delta_color="off")

    # ── Thống kê theo ngày — hôm nay ──
    with st.container(border=True):
        _dn_today = now_vn().date()
        _dn_label = _dn_today.strftime("%d/%m/%Y")
        st.markdown(f'<div class="sec-heading">Thống Kê Hôm Nay — {_dn_label}</div>', unsafe_allow_html=True)

        _dn_sel = pd.Timestamp(_dn_today)

        # Lọc lẻ hôm nay
        _dn_le_mask = (
            pd.to_datetime(sold_df["Ngày Bán"], dayfirst=True, errors="coerce").dt.normalize() == _dn_sel
            if not sold_df.empty else pd.Series([], dtype=bool)
        )
        _dn_sold_le = sold_df[_dn_le_mask].copy() if not sold_df.empty and len(_dn_le_mask) else pd.DataFrame()

        # Lọc lô hôm nay
        _dn_bk_mask = (
            pd.to_datetime(bulk_history["Ngày Bán"], dayfirst=True, errors="coerce").dt.normalize() == _dn_sel
            if not bulk_history.empty else pd.Series([], dtype=bool)
        )
        _dn_sold_bk = bulk_history[_dn_bk_mask].copy() if not bulk_history.empty and len(_dn_bk_mask) else pd.DataFrame()

        # KPI
        _dn_ln  = (float(pd.to_numeric(_dn_sold_le["Lợi Nhuận"], errors="coerce").fillna(0).sum()) if not _dn_sold_le.empty else 0.0) + \
                  (float(pd.to_numeric(_dn_sold_bk["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if not _dn_sold_bk.empty else 0.0)
        _dn_rev = (float(pd.to_numeric(_dn_sold_le["Doanh Thu"], errors="coerce").fillna(0).sum()) if not _dn_sold_le.empty else 0.0) + \
                  (float(pd.to_numeric(_dn_sold_bk["Doanh Thu Giao Dịch"], errors="coerce").fillna(0).sum()) if not _dn_sold_bk.empty else 0.0)
        _dn_cnt = len(_dn_sold_le) + len(_dn_sold_bk)
        _dn_cost = float(pd.to_numeric(_dn_sold_le["Giá Nhập"], errors="coerce").fillna(0).sum()) if not _dn_sold_le.empty else 0.0
        _dn_roi  = (_dn_ln / _dn_cost * 100) if _dn_cost > 0 else 0.0

        # So sánh với TB ngày có giao dịch
        if has_data and not pbd.empty:
            _dn_agg_all = pbd.groupby(pbd["Ngày DT"].dt.normalize())["Lợi Nhuận"].sum()
            _dn_avg = float(_dn_agg_all.mean()) if len(_dn_agg_all) > 0 else 0.0
        else:
            _dn_avg = 0.0
        _dn_delta = _dn_ln - _dn_avg
        # Delta string: sign phải đứng đầu để Streamlit nhận màu đúng
        _dn_delta_str = f"{_dn_delta:+,.0f} ₫ vs TB"

        _dm1, _dm2, _dm3, _dm4 = st.columns(4)
        _dm1.metric("🛒 Giao dịch",   f"{_dn_cnt}")
        _dm2.metric("💰 Lợi nhuận",   fmt_vnd(_dn_ln),
                    delta=_dn_delta_str, delta_color="normal")
        _dm3.metric("📈 Doanh thu",   fmt_vnd(_dn_rev))
        _dm4.metric("📊 ROI ngày",    f"{_dn_roi:.1f}%")

        # Bảng chi tiết — title · giờ bán · tồn · giá nhập · giá bán · lợi nhuận
        _dn_rows = []
        if not _dn_sold_le.empty:
            for _, _r in _dn_sold_le.iterrows():
                _ts = pd.to_datetime(_r.get("time_ban"), errors="coerce", utc=True)
                _gio = _ts.tz_convert(VN_TZ).strftime("%H:%M:%S") if pd.notna(_ts) else "—"
                _dn_rows.append({
                    "_sort": _ts if pd.notna(_ts) else pd.Timestamp.min.tz_localize("UTC"),
                    "Title":       str(_r.get("Auto Title") or _r.get("Tên Pet") or "—"),
                    "Giờ Bán":     _gio,
                    "Tồn (ngày)":  int(float(_r.get("Ngày Tồn", 0) or 0)),
                    "Giá Nhập ₫":  float(pd.to_numeric(_r.get("Giá Nhập"),  errors="coerce") or 0),
                    "Giá Bán $":   float(pd.to_numeric(_r.get("Giá Bán"),   errors="coerce") or 0),
                    "Lợi Nhuận ₫": float(pd.to_numeric(_r.get("Lợi Nhuận"), errors="coerce") or 0),
                })
        if not _dn_sold_bk.empty:
            for _, _r in _dn_sold_bk.iterrows():
                _dn_rows.append({
                    "_sort": pd.Timestamp.min.tz_localize("UTC"),
                    "Title":       str(_r.get("Tên Lô") or "—"),
                    "Giờ Bán":     str(_r.get("Ngày Bán", "—")),
                    "Tồn (ngày)":  "—",
                    "Giá Nhập ₫":  0.0,
                    "Giá Bán $":   float(pd.to_numeric(_r.get("Doanh Thu Giao Dịch"), errors="coerce") or 0) / max(EXCHANGE_RATE, 1),
                    "Lợi Nhuận ₫": float(pd.to_numeric(_r.get("Lợi Nhuận Giao Dịch"), errors="coerce") or 0),
                })

        if _dn_rows:
            _dn_tbl = (
                pd.DataFrame(_dn_rows)
                .sort_values("_sort", ascending=False)
                .drop(columns=["_sort"])
                .reset_index(drop=True)
            )
            _dn_tbl.index += 1
            st.dataframe(
                _dn_tbl,
                use_container_width=True,
                column_config={
                    "Title":       st.column_config.TextColumn("Title",        width="large"),
                    "Giờ Bán":     st.column_config.TextColumn("Giờ Bán",     width="small"),
                    "Tồn (ngày)":  st.column_config.Column("Tồn",             width="small"),
                    "Giá Nhập ₫":  st.column_config.NumberColumn("Giá Nhập",  format="%,.0f", width="medium"),
                    "Giá Bán $":   st.column_config.NumberColumn("Giá Bán $", format="%.2f",  width="small"),
                    "Lợi Nhuận ₫": st.column_config.NumberColumn("Lợi Nhuận", format="%,.0f", width="medium"),
                },
            )
            # Best / worst
            _dn_le_only = _dn_tbl[_dn_tbl["Tồn (ngày)"] != "—"]
            if not _dn_le_only.empty:
                _dn_ln_col = pd.to_numeric(_dn_le_only["Lợi Nhuận ₫"], errors="coerce")
                _dn_best  = _dn_le_only.loc[_dn_ln_col.idxmax()]
                _dn_worst = _dn_le_only.loc[_dn_ln_col.idxmin()]
                _gb, _gw = st.columns(2)
                _gb.success(f"🏆 **Tốt nhất:** {_dn_best['Title']} → {fmt_vnd(float(_dn_best['Lợi Nhuận ₫']))}")
                _gw.warning(f"📉 **Thấp nhất:** {_dn_worst['Title']} → {fmt_vnd(float(_dn_worst['Lợi Nhuận ₫']))}")
        else:
            st.caption("Chưa có giao dịch nào hôm nay.")
