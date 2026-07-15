"""
Tab 3: Hàng Tồn Lâu — filter by age threshold, display stuck inventory.
Extracted from app_backup.py lines 5389-5470.
"""
import pandas as pd
import streamlit as st

from _timezone import now_vn
from _helpers import fmt_vnd, fmt_ngay_ton, apply_ngay_ton
import _icons as IC


def render_tab_tonlau(df, bulk_df, bulk_history):
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hàng Tồn Lâu</div>', unsafe_allow_html=True)

        with st.form("form_ton_lau"):
            _fc1, _fc2, _fc3, _fc4 = st.columns([1, 1, 1.2, 1])
            age_thresh  = _fc1.number_input("Tồn từ (ngày)", min_value=0, max_value=365, value=0, step=1)
            age_max     = _fc2.number_input("Tối đa (ngày, 0=∞)", min_value=0, max_value=3650, value=0, step=1)
            loai_filter = _fc3.selectbox("Loại hàng", ["Tất cả", "Pet Lẻ", "Lô (Pack)"])
            sort_by     = _fc4.selectbox("Sắp xếp theo", ["Ngày Tồn (giảm)", "Giá trị vốn (giảm)", "Tên Pet"])
            st.form_submit_button("Lọc", use_container_width=False)

        # Pet le
        single_old = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)].copy()
        if "Ngày Tồn" not in single_old.columns or single_old["Ngày Tồn"].isna().all():
            single_old = apply_ngay_ton(single_old)
        single_old["Ngày Tồn"] = pd.to_numeric(single_old["Ngày Tồn"], errors="coerce").fillna(0)
        single_old = single_old[single_old["Ngày Tồn"] >= age_thresh]
        if age_max > 0:
            single_old = single_old[single_old["Ngày Tồn"] <= age_max]
        single_old["Loại"]               = "Pet Lẻ"
        single_old["Item"]               = single_old["Tên Pet"].astype(str)
        single_old["Số lượng còn"]       = 1
        single_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(single_old["Giá Nhập"], errors="coerce").fillna(0)
        sv = single_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]] if not single_old.empty else pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

        # Pack ton
        pack_old = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"].copy()
        if not pack_old.empty:
            pack_old["Ngày DT"]  = pd.to_datetime(pack_old["Ngày Nhập"], dayfirst=True, errors="coerce")
            pack_old["Ngày Tồn"] = (now_vn().replace(tzinfo=None) - pack_old["Ngày DT"].dt.tz_localize(None)).dt.days.fillna(0).astype(float)
            pack_old = pack_old[pack_old["Ngày Tồn"] >= age_thresh]
            if age_max > 0:
                pack_old = pack_old[pack_old["Ngày Tồn"] <= age_max]
            pack_old["Loại"]               = "Lô (Pack)"
            pack_old["Item"]               = pack_old["Tên Lô"].astype(str)
            pack_old["Số lượng còn"]       = pd.to_numeric(pack_old["Còn Lại"], errors="coerce").fillna(0).astype(int)
            pack_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(pack_old["Giá Nhập Tổng"], errors="coerce").fillna(0)
            pv = pack_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]]
        else:
            pv = pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

        old_items = pd.concat([sv, pv], ignore_index=True)

        if loai_filter != "Tất cả" and not old_items.empty:
            old_items = old_items[old_items["Loại"] == loai_filter]

        if old_items.empty:
            _age_label = f"{age_thresh}–{age_max} ngày" if age_max > 0 else (f"≥ {age_thresh} ngày" if age_thresh > 0 else "toàn bộ")
            st.info(f"Không có mục nào tồn {_age_label} — kho luân chuyển tốt.")
        else:
            if sort_by == "Ngày Tồn (giảm)":
                old_items = old_items.sort_values("Ngày Tồn", ascending=False)
            elif sort_by == "Giá trị vốn (giảm)":
                old_items = old_items.sort_values("Giá trị vốn (VNĐ)", ascending=False)
            else:
                old_items = old_items.sort_values("Item")

            total_stuck_val = old_items["Giá trị vốn (VNĐ)"].sum()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mục tồn", f"{len(old_items):,}")
            m2.metric("Vốn bị giữ", fmt_vnd(total_stuck_val))
            m3.metric("Tồn lâu nhất", fmt_ngay_ton(old_items['Ngày Tồn'].max()))
            m4.metric("Trung bình tồn", fmt_ngay_ton(old_items['Ngày Tồn'].mean()))

            old_items["Giá trị vốn"] = old_items["Giá trị vốn (VNĐ)"].apply(fmt_vnd)
            old_items["Tồn"]         = old_items["Ngày Tồn"].apply(fmt_ngay_ton)
            _ton_disp = old_items[["Loại","Item","Số lượng còn","Ngày Nhập","Tồn","Giá trị vốn","Auto Title"]].copy()

            st.dataframe(
                _ton_disp, use_container_width=True, hide_index=True, height=420,
                column_config={
                    "Auto Title":   st.column_config.TextColumn("Auto Title", width="large"),
                    "Tồn":          st.column_config.TextColumn("Tồn"),
                    "Item":         st.column_config.TextColumn("Item"),
                    "Loại":         st.column_config.TextColumn("Loại"),
                    "Số lượng còn": st.column_config.NumberColumn("Số lượng còn"),
                    "Giá trị vốn":  st.column_config.TextColumn("Giá trị vốn"),
                    "Ngày Nhập":    st.column_config.TextColumn("Ngày Nhập"),
                },
            )
