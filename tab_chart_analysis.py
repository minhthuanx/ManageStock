import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from _helpers import fmt_vnd, fmt_short


def render_analysis(df, bulk_df, bulk_history, sold_df, pbd, has_data):
    # ── Compute inventory capital from df / bulk_df ──
    _con_hang = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
    _von_le   = float(pd.to_numeric(_con_hang["Giá Nhập"], errors="coerce").fillna(0).sum())
    _von_lo   = float(pd.to_numeric(
        bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"]["Giá Nhập Tổng"], errors="coerce"
    ).fillna(0).sum())

        # ── Revenue channel split ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Phân Tích Kênh & Sản Phẩm</div>', unsafe_allow_html=True)
        c_left, c_right = st.columns(2)

        with c_left:
            # So sánh Doanh thu đã thu vs Tổng vốn tồn kho
            _dt_sold_total = float(pd.to_numeric(sold_df["Doanh Thu"], errors="coerce").fillna(0).sum()) if not sold_df.empty else 0.0
            _von_ton_total = _von_le + _von_lo
            _compare_df = pd.DataFrame({
                "Hạng mục": ["Doanh thu", "Vốn tồn"],
                "Giá trị":   [_dt_sold_total, _von_ton_total],
            })
            fig_cmp = go.Figure(go.Bar(
                x=_compare_df["Hạng mục"],
                y=_compare_df["Giá trị"],
                marker_color=["#8b5cf6", "#8b5cf6"],
                text=_compare_df["Giá trị"].apply(fmt_short),
                textposition="outside",
                textfont=dict(color="#f0f0f0", size=11),
            ))
            fig_cmp.update_layout(
                paper_bgcolor="#000000",
                plot_bgcolor="#000000",
                font=dict(family="Inter", color="#999999", size=11),
                title=dict(text="Doanh thu - Vốn tồn", font=dict(size=12, color="#f0f0f0")),
                margin=dict(l=10, r=10, t=55, b=10),
                height=400,
                yaxis_title="VNĐ",
                xaxis=dict(tickfont=dict(color="#f0f0f0", size=10)),
                yaxis=dict(tickfont=dict(color="#999999", size=10), gridcolor="#141414"),
            )
            if _dt_sold_total > 0 or _von_ton_total > 0:
                st.plotly_chart(fig_cmp, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

        with c_right:
            # Top 10 pets by profit
            if not sold_df.empty:
                top_pets = (
                    sold_df.groupby("Tên Pet", as_index=False)["Lợi Nhuận"]
                    .sum()
                    .sort_values("Lợi Nhuận", ascending=True)
                    .tail(10)
                )
                fig_bar = go.Figure(go.Bar(
                    x=top_pets["Lợi Nhuận"],
                    y=top_pets["Tên Pet"],
                    orientation="h",
                    marker=dict(color="#8b5cf6"),
                    text=top_pets["Lợi Nhuận"].apply(fmt_short),
                    textposition="outside",
                    textfont=dict(color="#f0f0f0", size=11),
                ))
                fig_bar.update_layout(
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    font=dict(family="Inter", color="#999999", size=11),
                    title=dict(text="Top 10 Pet Lợi nhuận cao", font=dict(size=12, color="#f0f0f0")),
                    xaxis=dict(gridcolor="#141414", tickformat=",.0f", tickfont=dict(color="#999999", size=10)),
                    yaxis=dict(gridcolor="#141414", tickfont=dict(color="#f0f0f0", size=10)),
                    margin=dict(l=10, r=10, t=55, b=10),
                    height=400,
                    showlegend=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

        # ── Bubble Scatter: Volume vs Margin per Mutation ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hiệu Quả Theo Mutation — Volume vs Margin</div>', unsafe_allow_html=True)

        if not sold_df.empty and "Mutation" in sold_df.columns:
            _tm_df = sold_df.copy()
            _tm_df["_mut"] = _tm_df["Mutation"].astype(str).str.strip().replace("", "Không rõ")
            _tm_df["_dt"]  = pd.to_numeric(_tm_df["Doanh Thu"], errors="coerce").fillna(0)
            _tm_df["_ln"]  = pd.to_numeric(_tm_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _tm_grp = (
                _tm_df.groupby("_mut", as_index=False)
                .agg(DT=("_dt","sum"), LN_total=("_ln","sum"), Count=("_ln","count"))
                .query("Count > 0")
            )
            _tm_grp["LN_per_unit"] = _tm_grp["LN_total"] / _tm_grp["Count"]
            _tm_grp["Margin_pct"]  = (_tm_grp["LN_total"] / _tm_grp["DT"].replace(0, float("nan")) * 100).fillna(0)

            if not _tm_grp.empty:
                # Quadrant reference lines at medians
                _med_x = float(_tm_grp["Count"].median())
                _med_y = float(_tm_grp["LN_per_unit"].median())

                # Color palette per mutation (distinct vivid colors)
                _MUT_PALETTE = {
                    "Normal":"#888888","Gold":"#fbbf24","Diamond":"#a78bfa",
                    "Bloodrot":"#f87171","Candy":"#f9a8d4","Divine":"#a78bfa",
                    "Lava":"#ff6b35","Galaxy":"#8b5cf6","Yin-Yang":"#e2e8f0",
                    "Radioactive":"#86efac","Cursed":"#4ade80","Rainbow":"#f472b6",
                    "Không rõ":"#6b7280",
                }
                _dot_colors = [_MUT_PALETTE.get(m, "#a78bfa") for m in _tm_grp["_mut"]]

                _fig_bub = go.Figure()

                # Quadrant shading
                _fig_bub.add_hrect(y0=_med_y, y1=_tm_grp["LN_per_unit"].max()*1.2,
                                   fillcolor="rgba(139,92,246,0.04)", line_width=0)
                _fig_bub.add_hrect(y0=_tm_grp["LN_per_unit"].min()*1.2, y1=_med_y,
                                   fillcolor="rgba(248,113,113,0.04)", line_width=0)

                # Quadrant lines
                _fig_bub.add_hline(y=_med_y, line=dict(color="#1f1f1f", width=1, dash="dot"))
                _fig_bub.add_vline(x=_med_x, line=dict(color="#1f1f1f", width=1, dash="dot"))

                # Quadrant labels
                for _ql_x, _ql_y, _ql_txt in [
                    (_tm_grp["Count"].max()*0.92, _tm_grp["LN_per_unit"].max()*1.1, "⭐ Ngôi sao"),
                    (_tm_grp["Count"].max()*0.03, _tm_grp["LN_per_unit"].max()*1.1, "💎 Hiếm & lời"),
                    (_tm_grp["Count"].max()*0.92, _med_y*0.02, "📦 Bán nhiều, ít lời"),
                    (_tm_grp["Count"].max()*0.03, _med_y*0.02, "⚠️ Cần xem xét"),
                ]:
                    _fig_bub.add_annotation(
                        x=_ql_x, y=_ql_y, text=_ql_txt,
                        showarrow=False, font=dict(color="#555555", size=11),
                        xanchor="left",
                    )

                # Bubbles
                for _, _row in _tm_grp.iterrows():
                    _col = _MUT_PALETTE.get(str(_row["_mut"]), "#a78bfa")
                    _sz  = max(24, min(90, _row["DT"] / (_tm_grp["DT"].max() or 1) * 80 + 14))
                    _fig_bub.add_trace(go.Scatter(
                        x=[_row["Count"]],
                        y=[_row["LN_per_unit"]],
                        mode="markers+text",
                        name=str(_row["_mut"]),
                        marker=dict(
                            size=_sz,
                            color=_col,
                            opacity=0.85,
                            line=dict(color="#000000", width=1.5),
                        ),
                        text=[str(_row["_mut"])],
                        textposition="top center",
                        textfont=dict(color="#f0f0f0", size=10),
                        hovertemplate=(
                            f"<b>{_row['_mut']}</b><br>"
                            f"Số con: {int(_row['Count'])}<br>"
                            f"LN TB/con: {_row['LN_per_unit']:,.0f}₫<br>"
                            f"Tổng LN: {_row['LN_total']:,.0f}₫<br>"
                            f"Doanh thu: {_row['DT']:,.0f}₫<br>"
                            f"Margin: {_row['Margin_pct']:.1f}%"
                            "<extra></extra>"
                        ),
                        showlegend=False,
                    ))

                _fig_bub.update_layout(
                    paper_bgcolor="#000000", plot_bgcolor="#000000",
                    font=dict(family="Inter", color="#999999", size=11),
                    xaxis=dict(
                        title="Số con đã bán (volume)",
                        gridcolor="#141414", tickfont=dict(color="#999999", size=10),
                        zeroline=False,
                    ),
                    yaxis=dict(
                        title="LN trung bình / con (₫)",
                        gridcolor="#141414", tickfont=dict(color="#999999", size=10),
                        tickformat=",.0f", zeroline=True, zerolinecolor="#1f1f1f",
                    ),
                    margin=dict(l=10, r=10, t=25, b=10),
                    height=480,
                    hovermode="closest",
                )
                st.plotly_chart(_fig_bub, use_container_width=True)
                st.caption("Kích thước bubble = tổng doanh thu · Kẻ đứt = median")
            else:
                st.info("Chưa có dữ liệu.")
        else:
            st.info("Chưa có dữ liệu.")

        # ── Pet Performance Scatter ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hiệu Quả Theo Tên Pet — Giá vs Lợi Nhuận</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            _pp_df = sold_df.copy()
            _pp_df["_gn"]  = pd.to_numeric(_pp_df["Giá Nhập"],  errors="coerce").fillna(0)
            _pp_df["_ln"]  = pd.to_numeric(_pp_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _pp_df["_pet"] = _pp_df["Tên Pet"].astype(str).str.strip()
            _pp_grp = (
                _pp_df.groupby("_pet", as_index=False)
                .agg(AvgCost=("_gn","mean"), AvgLN=("_ln","mean"),
                     TotalDT=("_gn","sum"),  Count=("_ln","count"))
            )
            _pp_grp["Margin"] = _pp_grp["AvgLN"] / (_pp_grp["AvgCost"].replace(0, float("nan"))) * 100
            _pp_grp = _pp_grp[_pp_grp["AvgCost"] > 0].dropna(subset=["Margin"])

            if not _pp_grp.empty:
                _med_px = float(_pp_grp["AvgCost"].median())
                _med_py = float(_pp_grp["AvgLN"].median())

                _fig_pp = go.Figure()
                _fig_pp.add_hline(y=_med_py, line=dict(color="#1f1f1f", width=1, dash="dot"))
                _fig_pp.add_vline(x=_med_px, line=dict(color="#1f1f1f", width=1, dash="dot"))

                _pp_xmax = float(_pp_grp["AvgCost"].max())
                _pp_ymax = float(_pp_grp["AvgLN"].max())
                for _qx2, _qy2, _qt2 in [
                    (_pp_xmax * 0.65, _pp_ymax * 1.05, "💰 Đắt & lời nhiều"),
                    (_pp_xmax * 0.01, _pp_ymax * 1.05, "💎 Rẻ & lời nhiều"),
                    (_pp_xmax * 0.65, _med_py * 0.05,  "📦 Đắt, lời ít"),
                    (_pp_xmax * 0.01, _med_py * 0.05,  "⚠️ Rẻ, lời ít"),
                ]:
                    _fig_pp.add_annotation(
                        x=_qx2, y=_qy2, text=_qt2,
                        showarrow=False, font=dict(color="#555555", size=11), xanchor="left"
                    )

                _PP_PALETTE = [
                    "#8b5cf6","#8b5cf6","#f472b6","#fbbf24","#38bdf8",
                    "#a78bfa","#4ade80","#ff6b35","#a78bfa","#f87171",
                    "#39d353","#86efac","#fdba74","#8b5cf6","#f9a8d4",
                    "#a78bfa","#fde68a","#bae6fd","#fecdd3","#bbf7d0",
                ]
                for _pi, (_, _pr) in enumerate(_pp_grp.iterrows()):
                    _sz2 = max(16, min(68, _pr["Count"] / max(float(_pp_grp["Count"].max()), 1) * 52 + 16))
                    _m2  = float(_pr["Margin"])
                    _c2  = _PP_PALETTE[_pi % len(_PP_PALETTE)]
                    _fig_pp.add_trace(go.Scatter(
                        x=[_pr["AvgCost"]], y=[_pr["AvgLN"]],
                        mode="markers",
                        name=str(_pr["_pet"]),
                        marker=dict(size=_sz2, color=_c2, opacity=0.88,
                                    line=dict(color="#000000", width=1.5)),
                        hovertemplate=(
                            f"<b>{_pr['_pet']}</b><br>"
                            f"Giá nhập TB: {_pr['AvgCost']:,.0f}₫<br>"
                            f"LN TB/con: {_pr['AvgLN']:,.0f}₫<br>"
                            f"Margin: {_m2:.1f}%<br>"
                            f"Số lần bán: {int(_pr['Count'])}"
                            "<extra></extra>"
                        ),
                        showlegend=True,
                    ))

                _fig_pp.update_layout(
                    paper_bgcolor="#000000", plot_bgcolor="#000000",
                    font=dict(family="Inter", color="#999999", size=11),
                    xaxis=dict(title="Giá nhập TB (₫)", gridcolor="#141414",
                               tickfont=dict(color="#999999", size=10), tickformat=",.0f", zeroline=False),
                    yaxis=dict(title="LN TB / con (₫)", gridcolor="#141414",
                               tickfont=dict(color="#999999", size=10), tickformat=",.0f",
                               zeroline=True, zerolinecolor="#1f1f1f"),
                    legend=dict(
                        orientation="v", x=1.01, y=1,
                        font=dict(color="#999999", size=9),
                        bgcolor="rgba(10,10,15,0.9)",
                        bordercolor="#141414", borderwidth=1,
                    ),
                    margin=dict(l=10, r=180, t=25, b=10),
                    height=490,
                    hovermode="closest",
                )
                st.plotly_chart(_fig_pp, use_container_width=True)
                st.caption("Kích thước = số lần bán · Mỗi màu = 1 loại pet · Hover để xem chi tiết · Kẻ đứt = median")
            else:
                st.info("Chưa có dữ liệu.")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── Avg days to sell + Top mutation ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hiệu Suất Bán Hàng</div>', unsafe_allow_html=True)
        _perf_c1, _perf_c2 = st.columns(2)

        with _perf_c1:
            st.markdown("**Vòng Quay Hàng — Thời gian tồn kho TB trước khi bán**")
            if not sold_df.empty:
                _sold_speed = sold_df.copy()
                _sold_speed["Ngày Tồn"] = pd.to_numeric(_sold_speed["Ngày Tồn"], errors="coerce").fillna(0)
                _avg_days = _sold_speed["Ngày Tồn"].mean()
                _med_days = _sold_speed["Ngày Tồn"].median()
                _sp1, _sp2 = st.columns(2)
                _sp1.metric("Trung bình", f"{int(round(_avg_days))} ngày")
                _sp2.metric("Trung vị", f"{int(round(_med_days))} ngày")

                # Biểu đồ theo tên pet (top 10 bán chậm nhất)
                _spd_by_pet = (
                    _sold_speed.groupby("Tên Pet", as_index=False)["Ngày Tồn"]
                    .mean()
                    .sort_values("Ngày Tồn", ascending=False)
                    .head(10)
                )
                fig_spd = go.Figure(go.Bar(
                    x=_spd_by_pet["Ngày Tồn"],
                    y=_spd_by_pet["Tên Pet"],
                    orientation="h",
                    marker=dict(color="#f472b6"),
                    text=_spd_by_pet["Ngày Tồn"].apply(lambda v: f"{int(round(v))}d"),
                    textposition="outside",
                    textfont=dict(color="#f0f0f0", size=10),
                ))
                fig_spd.update_layout(
                    paper_bgcolor="#000000", plot_bgcolor="#000000",
                    font=dict(family="Inter", color="#999999", size=11),
                    title=dict(text="Top 10 Pet bán chậm nhất (ngày TB)", font=dict(size=12, color="#f0f0f0")),
                    xaxis=dict(gridcolor="#141414", tickfont=dict(color="#999999", size=10)),
                    yaxis=dict(gridcolor="#141414", tickfont=dict(color="#f0f0f0", size=10)),
                    margin=dict(l=10, r=25, t=50, b=10),
                    height=400, showlegend=False,
                )
                st.plotly_chart(fig_spd, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu bán.")

        with _perf_c2:
            st.markdown("**Hiệu Suất Theo Mutation**")
            if not sold_df.empty:
                _mut_perf = (
                    sold_df.copy()
                    .assign(LN=lambda d: pd.to_numeric(d["Lợi Nhuận"], errors="coerce").fillna(0))
                    .groupby("Mutation", as_index=False)
                    .agg(LN_mean=("LN","mean"), LN_total=("LN","sum"), Count=("LN","count"))
                    .sort_values("LN_mean", ascending=True)
                )
                fig_mut = go.Figure(go.Bar(
                    x=_mut_perf["LN_mean"],
                    y=_mut_perf["Mutation"],
                    orientation="h",
                    marker=dict(color="#8b5cf6"),
                    text=_mut_perf["LN_mean"].apply(fmt_short),
                    textposition="outside",
                    textfont=dict(color="#f0f0f0", size=10),
                    customdata=_mut_perf[["LN_total","Count"]].values,
                    hovertemplate="<b>%{y}</b><br>TB/con: %{x:,.0f}₫<br>Tổng: %{customdata[0]:,.0f}₫<br>Số con: %{customdata[1]}<extra></extra>",
                ))
                fig_mut.update_layout(
                    paper_bgcolor="#000000", plot_bgcolor="#000000",
                    font=dict(family="Inter", color="#999999", size=11),
                    title=dict(text="Lợi nhuận TB theo Mutation", font=dict(size=12, color="#f0f0f0")),
                    xaxis=dict(gridcolor="#141414", tickformat=",.0f", tickfont=dict(color="#999999", size=10)),
                    yaxis=dict(gridcolor="#141414", tickfont=dict(color="#f0f0f0", size=10)),
                    margin=dict(l=10, r=25, t=50, b=10),
                    height=400, showlegend=False,
                )
                st.plotly_chart(fig_mut, use_container_width=True)

                # Bảng tóm tắt
                _mut_disp = _mut_perf.sort_values("LN_mean", ascending=False).copy()
                _mut_disp["LN TB/con"] = _mut_disp["LN_mean"].apply(fmt_vnd)
                _mut_disp["Tổng LN"]   = _mut_disp["LN_total"].apply(fmt_vnd)
                _mut_disp = _mut_disp.rename(columns={"Count":"Số con"})
                st.dataframe(_mut_disp[["Mutation","Số con","LN TB/con","Tổng LN"]], use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có dữ liệu bán.")
