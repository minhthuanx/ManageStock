import pandas as pd
import streamlit as st

from _timezone import now_vn, now_str, now_iso
from _helpers import (
    parse_vnd, parse_usd, get_name_options, append_row,
    generate_auto_title, next_id, apply_ngay_ton, _clear_searches,
)
from _config import MAIN_SCHEMA, LIST_SCHEMA, MUTATION_OPTIONS, PET_LIST_FILE
from _database import USE_SUPABASE, sb_insert, load_inventory, load_csv, save_csv, to_db


def render_manual_import(df, pet_db, ns_db, trait_db):
    # =========================================================
    # NHẬP THỦ CÔNG (Always visible)
    # =========================================================
    st.markdown("**Nhập Thủ Công**")
    pet_opts   = get_name_options(pet_db)
    trait_opts = ["None"] + get_name_options(trait_db)
    ns_opts    = [""] + get_name_options(ns_db, fallback="")

    # ── #12 Clone button ──
    _last_pet = st.session_state.get("last_saved_pet")
    if _last_pet:
        if st.button(f"Nhập tương tự: {_last_pet.get('p_name','')}", use_container_width=True, key="btn_clone_pet"):
            st.session_state.nhap_prefill = _last_pet.copy()
            st.rerun()
    _prefill = st.session_state.get("nhap_prefill", {})

    with st.form("form_nhap_le", clear_on_submit=True):
        _pi_pet = next((i for i, x in enumerate(pet_opts) if x == _prefill.get("p_name", "")), 0)
        p_name = st.selectbox("Tên Pet", pet_opts, index=_pi_pet)
        c1, c2, c3 = st.columns(3)
        ms_raw   = c1.text_input("M/s", placeholder="VD: 975", value=_prefill.get("ms_raw", ""))
        _pi_mut = next((i for i, m in enumerate(MUTATION_OPTIONS) if m == _prefill.get("p_mut", "")), 0)
        p_mut    = c2.selectbox("Mutation", MUTATION_OPTIONS, index=_pi_mut)
        _pi_trait = next((i for i, t in enumerate(trait_opts) if t == _prefill.get("p_trait", "")), 0)
        p_trait  = c3.selectbox("Số Trait", trait_opts, index=_pi_trait)
        c4, c5 = st.columns([1.5, 1])
        _pi_ns = next((i for i, n in enumerate(ns_opts) if n == _prefill.get("p_ns", "")), 0)
        p_ns       = c4.selectbox("NameStock", ns_opts, index=_pi_ns)
        p_cost_raw = c5.text_input("Giá nhập (VNĐ)", placeholder="150k / 1.5tr / 1.500.000")
        submitted = st.form_submit_button("Lưu Hàng", type="primary", use_container_width=True)

    if submitted:
        ms = parse_usd(ms_raw)
        cost = parse_vnd(p_cost_raw)
        errs = []
        if p_name == "None": errs.append("Chọn tên Pet")
        if ms <= 0:          errs.append("M/s phải > 0")
        if cost <= 0:        errs.append("Giá nhập phải > 0")
        if not p_ns.strip(): errs.append("Chọn NameStock")
        if errs:
            for e in errs: st.error(f"❌ {e}")
        else:
            # Guard chống double-submit: kiểm tra xem dữ liệu y hệt đã lưu chưa
            submit_key = f"nhap_le_{p_name}_{ms}_{cost}_{p_ns}"
            if st.session_state.get("last_nhap_key") == submit_key:
                st.warning("Mục này đã được lưu. Tải lại trang nếu cần.")
                st.stop()
            st.session_state.last_nhap_key = submit_key
            st.session_state.pop("nhap_prefill", None)  # Xóa prefill sau khi submit hợp lệ
            stt = next_id(df, "STT")
            ts  = now_iso()
            row = {
                "STT":        stt,
                "Tên Pet":    p_name,
                "M/s":        ms,
                "Mutation":   p_mut,
                "Số Trait":   p_trait,
                "NameStock":  p_ns,
                "Giá Nhập":   cost,
                "Giá Bán":    0.0,
                "Lợi Nhuận":  0.0,
                "Doanh Thu":  0.0,
                "Ngày Nhập":  now_str(),
                "Ngày Bán":   "-",
                "Auto Title": generate_auto_title(p_name, p_mut, p_trait, ms, p_ns),
                "Trạng Thái": "Còn hàng",
                "time_nhap":  ts,
                "time_ban":   "",
                "Ngày Tồn":   0,
                "Place":      "",
            }
            df = append_row(df, row, MAIN_SCHEMA)
            df = apply_ngay_ton(df)
            st.session_state.df = df
            if USE_SUPABASE:
                p_payload = to_db(row)
                p_payload.pop("id", None)
                sb_insert("inventory", p_payload)
                # Sync ID from DB
                st.cache_data.clear()
                st.session_state.df = apply_ngay_ton(load_inventory())

            st.session_state.last_saved_pet = {
                "p_name": p_name, "ms_raw": ms_raw,
                "p_mut": p_mut, "p_trait": p_trait, "p_ns": p_ns,
            }
            st.toast("Đã lưu thành công", icon="✅")
            st.caption("Sao chép tiêu đề:")
            st.code(row["Auto Title"], language="text")
            _clear_searches()
