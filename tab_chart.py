import pandas as pd
import streamlit as st

from _timezone import now_vn
from _config import EXCHANGE_RATE
from _helpers import fmt_vnd


def render_tab_chart(df, bulk_df, bulk_history):
    """Tab 2 (Thong Ke) orchestrator: badge, data aggregation, sub-chart calls."""

    # ── Ngay bat dau badge ──
    _all_dates = []
    if not df.empty and "Ngày Nhập" in df.columns:
        _all_dates.extend(pd.to_datetime(df["Ngày Nhập"], dayfirst=True, errors="coerce").dropna().tolist())
    if not bulk_history.empty and "Ngày Bán" in bulk_history.columns:
        _all_dates.extend(pd.to_datetime(bulk_history["Ngày Bán"], dayfirst=True, errors="coerce").dropna().tolist())
    _start_date_str = min(_all_dates).strftime("%d/%m/%Y") if _all_dates else "—"
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:8px;'
        'background:linear-gradient(135deg,rgba(139,92,246,0.22),rgba(0,200,255,0.08));'
        'border:1px solid rgba(139,92,246,0.35);border-radius:8px;'
        'padding:6px 14px;margin-bottom:12px;">'
        '<span style="font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;'
        'color:#777777;font-weight:500;">Ngày bắt đầu</span>'
        f'<span style="font-size:0.88rem;font-weight:600;color:#a78bfa;letter-spacing:0.02em;">{_start_date_str}</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Aggregate data ──
    sold_df = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)].copy()

    total_cost_single  = float(df["Giá Nhập"].sum()) if not df.empty else 0.0
    total_cost_bulk    = float(bulk_df["Giá Nhập Tổng"].sum()) if not bulk_df.empty else 0.0
    total_cost         = total_cost_single + total_cost_bulk

    if not sold_df.empty:
        _dt_col = pd.to_numeric(sold_df["Doanh Thu"], errors="coerce").fillna(0)
        _gb_col = pd.to_numeric(sold_df["Giá Bán"], errors="coerce").fillna(0) * EXCHANGE_RATE
        # Nếu Doanh Thu = 0 (null trong DB hoặc chưa được ghi), dùng Giá Bán * EXCHANGE_RATE làm fallback
        rev_single = float(_dt_col.where(_dt_col > 0, _gb_col).sum())
    else:
        rev_single = 0.0
    rev_bulk    = float(pd.to_numeric(bulk_history["Doanh Thu Giao Dịch"], errors="coerce").fillna(0).sum()) if not bulk_history.empty else 0.0
    total_rev   = rev_single + rev_bulk

    profit_single = float(sold_df["Lợi Nhuận"].sum()) if not sold_df.empty else 0.0
    # Chỉ tính lợi nhuận đã THỰC sự thu từ giao dịch pack (không cộng giá trị ám của pack chưa bán)
    profit_bulk   = float(bulk_history["Lợi Nhuận Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    net_profit    = profit_single + profit_bulk

    stock_count_single = int(df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)].shape[0])
    stock_count_bulk   = int(pd.to_numeric(
        bulk_df[bulk_df["Trạng Thái"]=="Available"]["Còn Lại"], errors="coerce"
    ).fillna(0).sum())
    total_stock = stock_count_single + stock_count_bulk

    # ── Build unified profit-by-date dataframe (needed by monthly stats + charts) ──
    frames = []
    if not sold_df.empty:
        tmp = sold_df[["Ngày Bán","Lợi Nhuận"]].copy()
        tmp.columns = ["Ngày","Lợi Nhuận"]
        frames.append(tmp)
    if not bulk_history.empty:
        tmp2 = bulk_history[["Ngày Bán","Lợi Nhuận Giao Dịch"]].copy()
        tmp2.columns = ["Ngày","Lợi Nhuận"]
        frames.append(tmp2)
    pbd = pd.DataFrame(columns=["Ngày","Lợi Nhuận"])
    if frames:
        pbd = pd.concat(frames, ignore_index=True)
    has_data = not pbd.empty
    if has_data:
        pbd["Ngày DT"] = pd.to_datetime(pbd["Ngày"], dayfirst=True, errors="coerce")
        pbd = pbd.dropna(subset=["Ngày DT"])
        pbd["Lợi Nhuận"] = pd.to_numeric(pbd["Lợi Nhuận"], errors="coerce").fillna(0)

    # ── Sub-chart modules ──
    from tab_chart_overview import render_overview
    from tab_chart_financial import render_financial
    from tab_chart_analysis import render_analysis
    from tab_chart_advanced import render_advanced
    from tab_chart_extra import render_extra

    render_overview(df, bulk_df, bulk_history, sold_df, pbd, has_data,
                    total_cost, total_rev, net_profit, total_stock)

    render_financial(df, bulk_df, bulk_history, sold_df, pbd, has_data,
                     total_cost, total_rev, net_profit)

    render_analysis(df, bulk_df, bulk_history, sold_df, pbd, has_data)

    render_advanced(sold_df, pbd, has_data)

    render_extra(df, bulk_df, bulk_history, sold_df, pbd, has_data)
