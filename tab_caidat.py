"""
Tab 6: Cài Đặt — Category management, Eldorado connection, system monitor.
Extracted from app_backup.py lines 6151-6465.
"""
import gc
import os
import pickle
import re
import sys

import pandas as pd
import streamlit as st

from _config import PET_LIST_FILE, NS_LIST_FILE, TRAIT_LIST, LIST_SCHEMA
from _database import USE_SUPABASE, supabase_client, find_duplicates, save_csv
from _helpers import append_row, generate_auto_title, _save_owner_ns_map

try:
    from _eldorado_helpers import (
        _HAS_ELDORADO, _save_eld_settings,
    )
    from eldorado_client import DELIVERY_MAP
except ImportError:
    _HAS_ELDORADO = False
    DELIVERY_MAP = {}


def render_tab_caidat(pet_db, ns_db, trait_db, eld_client):
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Quản Lý Danh Mục</div>', unsafe_allow_html=True)

        cat_cols = st.columns(3)

        def manage_category(col, label: str, db: pd.DataFrame, file: str, icon: str):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{icon} {label}**")
                    with st.form(f"form_add_{file}", clear_on_submit=True):
                        c1, c2 = st.columns([3, 1])
                        new_val = c1.text_input("Thêm", placeholder=f"Tên {label}...", label_visibility="collapsed")
                        add_ok  = c2.form_submit_button("➕", use_container_width=True)
                    if add_ok:
                        v = new_val.strip()
                        if not v:
                            st.warning("Vui lòng nhập tên.")
                        elif v.lower() in [x.lower() for x in db["Name"].astype(str).tolist()]:
                            st.info("Mục này đã tồn tại.")
                        else:
                            db = append_row(db, {"Name": v}, LIST_SCHEMA)
                            save_csv(db, file)
                            st.toast(f"Đã thêm: {v}", icon="✅")
                            st.rerun()

                    st.dataframe(db, use_container_width=True, hide_index=True, height=140)

                    if not db.empty:
                        with st.form(f"form_del_{file}"):
                            d1, d2 = st.columns([2.5, 1.5])
                            sel_del = d1.selectbox("Xóa", db["Name"].astype(str).tolist(), label_visibility="collapsed")
                            del_ok  = d2.form_submit_button("🗑️", use_container_width=True)
                        if del_ok:
                            db = db[db["Name"].astype(str) != sel_del].reset_index(drop=True)
                            save_csv(db, file)
                            st.rerun()

        manage_category(cat_cols[0], "Pet",       pet_db,   PET_LIST_FILE, "🐾")
        manage_category(cat_cols[1], "NameStock", ns_db,    NS_LIST_FILE,  "🏷️")
        manage_category(cat_cols[2], "Trait",     trait_db, TRAIT_LIST,    "🧬")

        # ── Sua Auto Title sai dinh dang ──
        if USE_SUPABASE:
            st.markdown("---")
            st.markdown("### 🛠️ Sửa Auto Title (Trait)")
            st.caption("Tìm các dòng có auto_title dạng `[1]` thay vì `[1 Trait]` và cập nhật lại.")
            if st.button("Chạy Sửa Auto Title", use_container_width=True):
                try:
                    rows = supabase_client.table("inventory").select(
                        "id, auto_title, ten_pet, mutation, so_trait, ms, namestock"
                    ).limit(-1).execute().data or []
                    _broken_pat = re.compile(r"\[(\d+)\]")
                    fixed = 0
                    for row in rows:
                        at = row.get("auto_title") or ""
                        if _broken_pat.search(at):
                            new_at = generate_auto_title(
                                row.get("ten_pet", ""),
                                row.get("mutation", "Normal"),
                                row.get("so_trait", "None"),
                                row.get("ms", 0),
                                row.get("namestock", ""),
                            )
                            supabase_client.table("inventory").update(
                                {"auto_title": new_at}
                            ).eq("id", row["id"]).execute()
                            fixed += 1
                    if fixed:
                        st.success(f"Đã sửa **{fixed} dòng** — auto_title đã được cập nhật.")
                        st.cache_data.clear()
                    else:
                        st.info("Không tìm thấy dòng nào cần sửa.")
                except Exception as _e:
                    st.error(f"Lỗi: {_e}")

        # ── Kiem tra trung lap ──
        if USE_SUPABASE:
            st.markdown("---")
            st.markdown("### 🔍 Kiểm tra trùng lặp Database")
            st.caption("⚠️ Hệ thống chỉ phát hiện và báo cáo — việc xóa do bạn quyết định trực tiếp trong bảng.")
            c_m1, c_m2 = st.columns(2)
            run_inv  = c_m1.button("Kiểm Tra Hàng Lẻ",  use_container_width=True)
            run_bulk = c_m2.button("Kiểm Tra Lô Hàng", use_container_width=True)

            if run_inv:
                dup_inv = find_duplicates("inventory")
                if dup_inv.empty:
                    st.success("Hàng lẻ — không phát hiện trùng lặp.")
                else:
                    st.warning(f"Phát hiện **{len(dup_inv)} bản ghi** trùng lặp:")
                    st.dataframe(dup_inv[["id"] + [c for c in dup_inv.columns if c != "id"]], use_container_width=True, hide_index=True)
                    st.caption("Truy cập Supabase Dashboard → Table Editor → inventory → xoá thủ công theo ID.")

            if run_bulk:
                dup_bulk = find_duplicates("bulk_inventory")
                if dup_bulk.empty:
                    st.success("Lô hàng — không phát hiện trùng lặp.")
                else:
                    st.warning(f"Phát hiện **{len(dup_bulk)} bản ghi** trùng lặp:")
                    st.dataframe(dup_bulk[["id"] + [c for c in dup_bulk.columns if c != "id"]], use_container_width=True, hide_index=True)
                    st.caption("Truy cập Supabase Dashboard → Table Editor → bulk_inventory → xoá thủ công theo ID.")

        # ── ELDORADO CONNECTION ──
        if _HAS_ELDORADO:
            st.markdown("---")
            with st.container(border=True):
                st.markdown('<div class="sec-heading">🎮 Eldorado.gg Connection</div>', unsafe_allow_html=True)

                if eld_client and eld_client.logged_in:
                    st.success(f"Connected as **{eld_client.username}** (+{eld_client.pos}/-{eld_client.neg})")
                else:
                    st.warning("Chưa kết nối Eldorado.gg")

                with st.expander("🍪 Paste Cookie từ Browser DevTools", expanded=not (eld_client and eld_client.logged_in)):
                    st.caption("F12 → Application → Cookies → eldorado.gg → Copy all cookies as string")
                    cookie_input = st.text_area(
                        "Cookie String",
                        value="",
                        height=80,
                        placeholder="__Host-XSRF-TOKEN=...; __Host-EldoradoIdToken=...; ...",
                        key="eld_cookie_input",
                        label_visibility="collapsed",
                    )
                    c_conn, c_disc = st.columns(2)
                    with c_conn:
                        if st.button("🔗 Kết Nối", type="primary", use_container_width=True,
                                     disabled=not cookie_input.strip(),
                                     key="btn_eld_connect"):
                            with st.spinner("Đang xác thực..."):
                                eld_client.set_cookies(cookie_input.strip())
                                auth_result = eld_client.check_auth()
                            if auth_result["ok"]:
                                eld_client.save_cookies()
                                st.toast(f"Đăng nhập thành công: {eld_client.username}", icon="✅")
                                st.rerun()
                            else:
                                st.error(f"Lỗi xác thực: {auth_result.get('error', 'unknown')}")

                    with c_disc:
                        if st.button("🔌 Ngắt Kết Nối", use_container_width=True,
                                     disabled=not (eld_client and eld_client.logged_in),
                                     key="btn_eld_disconnect"):
                            eld_client.disconnect()
                            st.toast("Đã ngắt kết nối Eldorado", icon="🔌")
                            st.rerun()

                # Push defaults
                if eld_client and eld_client.logged_in:
                    st.markdown("---")
                    st.markdown("**⚙️ Push Defaults**")
                    _eld_s = st.session_state.get("eld_settings", {})

                    d1, d2, d3 = st.columns(3)
                    default_price = d1.number_input(
                        "Default Price (USD)", min_value=0.10, max_value=9999.0,
                        value=float(_eld_s.get("default_price", 0.50)),
                        step=0.05, format="%.2f", key="eld_default_price"
                    )
                    delivery_keys = list(DELIVERY_MAP.keys())
                    _def_del = _eld_s.get("default_delivery", "20 min")
                    _del_idx = delivery_keys.index(_def_del) if _def_del in delivery_keys else 2
                    default_delivery = d2.selectbox(
                        "Thời Gian Giao", delivery_keys, index=_del_idx,
                        key="eld_default_delivery"
                    )
                    default_desc = d3.text_input(
                        "Mô Tả Mặc Định",
                        value=_eld_s.get("default_desc", "Fast delivery! Contact me if any issues."),
                        key="eld_default_desc"
                    )

                    if st.button("💾 Lưu Eldorado Settings", use_container_width=True,
                                 key="btn_eld_save_settings"):
                        settings = {
                            "default_price": default_price,
                            "default_delivery": default_delivery,
                            "default_desc": default_desc,
                        }
                        _save_eld_settings(settings)
                        st.session_state.eld_settings = settings
                        st.toast("Đã lưu Eldorado settings", icon="✅")

                # ── Owner -> NameStock Mapping ──
                st.markdown("---")
                st.markdown("**🏷️ Owner → NameStock Mapping**")
                st.caption("JSON có `owner: bjn8th` → tự động map NameStock = `#B8`. Format txt: `username:NameStock` mỗi dòng.")

                _on_map = st.session_state.get("_owner_ns_map", {})
                if _on_map:
                    _on_df = pd.DataFrame([{"Owner": k, "NameStock": v} for k, v in sorted(_on_map.items())])
                    st.dataframe(_on_df, use_container_width=True, hide_index=True, height=min(200, 40 + len(_on_df) * 35))

                oc1, oc2 = st.columns([3, 1])
                _new_owner = oc1.text_input("Thêm owner", placeholder="username:NameStock (VD: bjn8th:#B8)",
                                             key="new_owner_ns_input", label_visibility="collapsed")
                if oc2.button("➕ Thêm", key="btn_add_owner_ns"):
                    if ":" in _new_owner.strip():
                        _k, _v = _new_owner.strip().split(":", 1)
                        _k, _v = _k.strip().lower(), _v.strip()
                        if _k and _v:
                            _on_map[_k] = _v
                            _save_owner_ns_map(_on_map)
                            st.session_state["_owner_ns_map"] = _on_map
                            st.toast(f"Đã thêm: {_k} → {_v}")
                            st.rerun()
                    elif _new_owner.strip():
                        st.warning("Sai format. Cần: `username:NameStock`")

                if _on_map:
                    _del_owner = st.selectbox("Xóa mapping", list(_on_map.keys()),
                                              key="del_owner_ns", label_visibility="collapsed")
                    if st.button("🗑️ Xóa", key="btn_del_owner_ns"):
                        _on_map.pop(_del_owner, None)
                        _save_owner_ns_map(_on_map)
                        st.session_state["_owner_ns_map"] = _on_map
                        st.toast(f"Đã xóa: {_del_owner}")
                        st.rerun()

        # ── Tai Nguyen He Thong ──
        st.markdown("---")
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🖥️ Tình Trạng Tài Nguyên</div>', unsafe_allow_html=True)

        # Process metrics via psutil
        try:
            import psutil
            _proc   = psutil.Process(os.getpid())
            _mem_mi = _proc.memory_info()
            _rss_mb = _mem_mi.rss / 1024 / 1024
            _vms_mb = _mem_mi.vms / 1024 / 1024
            _cpu_p  = _proc.cpu_percent(interval=0.1)
            _sys_mem   = psutil.virtual_memory()
            _sys_used  = _sys_mem.used  / 1024 / 1024 / 1024
            _sys_total = _sys_mem.total / 1024 / 1024 / 1024
            _sys_pct   = _sys_mem.percent
            _has_psutil = True
        except ImportError:
            _has_psutil = False

        def _est_size_bytes(obj):
            try:
                return sys.getsizeof(pickle.dumps(obj, protocol=2))
            except Exception:
                return sys.getsizeof(obj)

        _ss_keys     = list(st.session_state.keys())
        _ss_total_b  = sum(_est_size_bytes(st.session_state[k]) for k in _ss_keys)
        _ss_mb       = _ss_total_b / 1024 / 1024

        _df_inv  = st.session_state.get("df", pd.DataFrame())
        _df_bulk = st.session_state.get("bulk_df", pd.DataFrame())
        _df_hist = st.session_state.get("bulk_history", pd.DataFrame())

        _rc1, _rc2, _rc3, _rc4 = st.columns(4)

        if _has_psutil:
            _rc1.metric("💾 RAM Process (RSS)", f"{_rss_mb:.1f} MB", delta=f"VMS {_vms_mb:.0f} MB")
            _rc2.metric("⚙️ CPU Process", f"{_cpu_p:.1f}%")
            _rc3.metric("🖥️ RAM Hệ Thống", f"{_sys_used:.2f} / {_sys_total:.2f} GB", delta=f"{_sys_pct:.0f}% dùng")
        else:
            _rc1.metric("💾 RAM Process", "N/A", delta="Cài psutil để đo")
            _rc2.metric("⚙️ CPU Process", "N/A")
            _rc3.metric("🖥️ RAM Hệ Thống", "N/A")

        _rc4.metric("🗂️ Session State", f"{_ss_mb:.2f} MB", delta=f"{len(_ss_keys)} keys")

        _rd1, _rd2, _rd3, _rd4 = st.columns(4)
        _rd1.metric("📋 Tồn kho lẻ",    f"{len(_df_inv):,} hàng",  delta=f"~{_est_size_bytes(_df_inv)//1024} KB")
        _rd2.metric("📦 Lô hàng",        f"{len(_df_bulk):,} lô",   delta=f"~{_est_size_bytes(_df_bulk)//1024} KB")
        _rd3.metric("📜 Lịch sử lô",     f"{len(_df_hist):,} giao dịch", delta=f"~{_est_size_bytes(_df_hist)//1024} KB")
        _gc_objs = gc.get_count()
        _rd4.metric("♻️ GC Objects",     f"{sum(_gc_objs):,}", delta=f"gen {_gc_objs[0]}/{_gc_objs[1]}/{_gc_objs[2]}")

        with st.expander("🔍 Chi tiết Session State Keys"):
            _ss_rows = []
            for _k in sorted(_ss_keys):
                try:
                    _sz = _est_size_bytes(st.session_state[_k])
                    _tp = type(st.session_state[_k]).__name__
                    if isinstance(st.session_state[_k], pd.DataFrame):
                        _tp = f"DataFrame ({len(st.session_state[_k])} rows)"
                    _ss_rows.append({"Key": _k, "Type": _tp, "Size (bytes)": _sz})
                except Exception:
                    _ss_rows.append({"Key": _k, "Type": "?", "Size (bytes)": 0})
            _ss_detail_df = pd.DataFrame(_ss_rows).sort_values("Size (bytes)", ascending=False).reset_index(drop=True)
            st.dataframe(_ss_detail_df, use_container_width=True, hide_index=True,
                         column_config={"Size (bytes)": st.column_config.NumberColumn(format="%,d")})

        _rb1, _rb2 = st.columns(2)
        if _rb1.button("♻️ Chạy Garbage Collector", use_container_width=True):
            _before = sum(gc.get_count())
            _collected = gc.collect()
            st.success(f"GC: thu hồi {_collected} objects · còn {sum(gc.get_count())} (trước: {_before})")
        if _rb2.button("🧹 Xoá Cache Streamlit", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Đã xoá toàn bộ cache @st.cache_data và @st.cache_resource.")
