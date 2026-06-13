"""
JSON Import tab — Nhập dữ liệu pet từ JSON (Streamlit).
Extracted from app_backup.py lines 2355-2789.
"""

import json
import time as _time
import pandas as pd
import streamlit as st

from _timezone import now_vn, now_str, now_iso
from _helpers import (
    parse_vnd, parse_usd, fmt_vnd, get_name_options, append_row,
    generate_auto_title, parse_json_import, _clear_searches, _sv,
    apply_ngay_ton, next_id, _load_json_history, _save_json_history,
    _pet_key, _compare_json_batches,
)
from _config import (
    MAIN_SCHEMA, LIST_SCHEMA, MUTATION_OPTIONS, EXCHANGE_RATE, PET_LIST_FILE,
    DB_FILE,
)
from _database import (
    USE_SUPABASE, sb_insert, sb_insert_batch,
    load_inventory, load_csv, save_csv, supabase_client, to_db,
)
from _eldorado_helpers import _HAS_ELDORADO

try:
    from eldorado_client import DELIVERY_MAP, OTHER_TRADE_ENV_ID
except ImportError:
    DELIVERY_MAP = {}


def render_json_import(df, pet_db, ns_db, trait_db, eld_client=None):
    """Render the JSON Import section: text area, parse, dialog preview, save, Eldorado push."""

    # =========================================================
    # JSON IMPORT — Nhập từ JSON
    # =========================================================
    with st.expander("📋 JSON Import — Nhập từ JSON", expanded=st.session_state.get("json_import_expander", False)):
        st.caption("Dán JSON từ game vào đây để nhập dữ liệu pet nhanh chóng")

        if "json_import_key" not in st.session_state:
            st.session_state.json_import_key = 0

        json_input = st.text_area(
            "Dán JSON",
            value="",
            height=120,
            placeholder='[{"name":"Burguro And Fryuro","mutation":"Galaxy","gen_text":"2B/s","traits":["Galactic","Matteo Hat"],...}]',
            key=f"json_import_text_{st.session_state.json_import_key}",
            label_visibility="collapsed",
        )

        parse_btn = st.button(
            "Phân tích JSON",
            type="primary",
            use_container_width=True,
            key="btn_json_parse",
            disabled=not json_input.strip(),
        )

        if parse_btn and json_input.strip():
            json_results = parse_json_import(json_input)
            if not json_results:
                st.error("❌ Lỗi: Không thể phân tích JSON. Kiểm tra định dạng lại.")
            else:
                st.session_state.json_batch_results = json_results
                st.session_state.json_show_dialog = True

    # =========================================================
    # JSON DIALOG PREVIEW + EDIT
    # =========================================================
    if st.session_state.get("json_show_dialog") and st.session_state.get("json_batch_results"):
        json_results = st.session_state.json_batch_results

        @st.dialog("Kết Quả JSON — Xem trước & Chỉnh sửa", width="large")
        def json_preview_dialog():
            nonlocal pet_db
            # ── CACHE OPTIONS TRƯỚC ──
            pet_opts_dlg   = list(get_name_options(pet_db))
            pet_opts_lower_set = set(x.lower() for x in pet_opts_dlg)  # O(1) lookup
            trait_opts_dlg = ["None"] + [str(n) for n in range(1, 16)]
            ns_opts_dlg    = [""] + list(get_name_options(ns_db, fallback=""))

            st.caption(f"**{len(json_results)}** mục từ JSON · Tick 🗑️ Xoá ở từng dòng để bỏ qua khi lưu")

            # ── NameStock chung cho cả batch ──
            _gn1, _gn2 = st.columns([1, 3])
            use_global_ns = _gn1.checkbox("NameStock chung", key="dlg_json_global_ns_check",
                                           help="Áp dụng cùng 1 NameStock cho tất cả pet trong batch này")
            if use_global_ns:
                global_ns_val = _gn2.selectbox(
                    "NameStock áp dụng cho tất cả",
                    ns_opts_dlg,
                    key="dlg_json_global_ns_val",
                    label_visibility="collapsed",
                )
            else:
                global_ns_val = ""

            # ── PRE-PROCESS: Cache similar pets detection ──
            similar_cache = {}
            if not st.session_state.df.empty:
                # Build pet lookup map từ inventory: {(ns, mutation, ms_range): [(pet_name, ms, ns), ...]}
                for _, row in st.session_state.df.iterrows():
                    try:
                        ns = str(row.get("NameStock", "")).strip()
                        mut = str(row.get("Mutation", "Normal")).strip()
                        ms = float(row.get("M/s", 0))
                        pet_name = str(row.get("Tên Pet", ""))
                        if ns and mut and ms > 0 and pet_name:
                            key = (ns, mut, int(ms / 50) * 50)  # Group by 50M/s range
                            if key not in similar_cache:
                                similar_cache[key] = []
                            similar_cache[key].append((pet_name, ms, ns))  # ← STORE NameStock too
                    except (TypeError, ValueError):
                        pass

            st.markdown("---")
            edited_rows = []
            all_valid = True

            # ── Hiển thị thống kê diff ──
            _new_count = sum(1 for r in json_results if r.get("_is_new", True))
            _old_count = len(json_results) - _new_count
            if _old_count > 0:
                st.info(f"🔄 **{_old_count}** pet đã tồn tại (bị lược bỏ) · **{_new_count}** pet mới")

            for i, res in enumerate(json_results):
                if not res.get("_is_new", True):
                    continue  # bỏ qua pet đã có

                pet_name = res.get("Tên Pet", f"Item {i+1}")
                mutation = res.get("Mutation", "Normal")

                _expander_label = f"🆕 {pet_name} · {mutation}"

                with st.expander(_expander_label, expanded=True):
                    # Top row: Delete checkbox + basic info
                    _del_col, _info_col = st.columns([0.5, 5])
                    with _del_col:
                        r_delete = st.checkbox("🗑️ Xoá", key=f"dlg_json_delete_{i}", label_visibility="collapsed")

                    with _info_col:
                        ms_val = res.get('M/s')
                        st.caption(f"M/s: {f'{ms_val:g}' if ms_val else '?'} | Traits: {res.get('Số Trait')}")

                    # Main form columns
                    c1d, c2d, c3d = st.columns(3)

                    # Tên Pet
                    json_name = str(res.get("Tên Pet") or "")
                    # ──tối ưu: kiểm tra O(1) với set ──
                    if json_name and json_name.lower() not in pet_opts_lower_set:
                        pet_opts_dlg = [json_name] + pet_opts_dlg
                        pet_opts_lower_set.add(json_name.lower())
                    pi = next((j for j, x in enumerate(pet_opts_dlg) if x.lower() == json_name.lower()), 0)
                    r_name = c1d.selectbox(f"Tên Pet", pet_opts_dlg, index=pi, key=f"dlg_json_name_{i}", label_visibility="collapsed")

                    # Mutation
                    json_mut_v = str(res.get("Mutation") or "Normal")
                    mi = next((j for j, m in enumerate(MUTATION_OPTIONS) if m.lower() == json_mut_v.lower()), 0)
                    r_mut = c2d.selectbox(f"Mutation", MUTATION_OPTIONS, index=mi, key=f"dlg_json_mut_{i}", label_visibility="collapsed")

                    # M/s
                    val_ms = res.get("M/s")
                    str_ms = f"{val_ms:g}" if val_ms else ""
                    r_ms_raw = c3d.text_input(f"M/s", value=str_ms, key=f"dlg_json_ms_{i}", label_visibility="collapsed")

                    c4d, c5d, c6d = st.columns([1, 1, 1])

                    # Số Trait
                    json_trait = str(res.get("Số Trait") or "None").strip()
                    if json_trait not in trait_opts_dlg:
                        trait_opts_dlg = trait_opts_dlg + [json_trait]
                    ti = next((j for j, t in enumerate(trait_opts_dlg) if t.lower() == json_trait.lower()), 0)
                    r_trait = c4d.selectbox(f"Số Trait", trait_opts_dlg, index=ti, key=f"dlg_json_trait_{i}", label_visibility="collapsed")

                    # NameStock: dùng global nếu checkbox bật, ngược lại dùng per-row
                    _ns_raw = res.get("NameStock", "")
                    _ns_owner = res.get("_owner", "")
                    if use_global_ns:
                        r_ns = global_ns_val
                        _ns_display = global_ns_val if global_ns_val else "—"
                        c5d.markdown(
                            f'<div style="padding-top:1.8rem;font-size:0.82rem;color:#a78bfa;">'
                            f'NS: <b>{_ns_display}</b> <span style="color:#4b3f6b;">(chung)</span></div>',
                            unsafe_allow_html=True,
                        )
                        effective_ns = global_ns_val
                    elif _ns_raw:
                        r_ns = _ns_raw
                        _source = f"({_ns_owner})" if _ns_owner else ""
                        c5d.markdown(
                            f'<div style="padding-top:1.8rem;font-size:0.82rem;color:#a78bfa;">'
                            f'NS: <b>{_ns_raw}</b> <span style="color:#6b5b95;">{_source}</span></div>',
                            unsafe_allow_html=True,
                        )
                        effective_ns = _ns_raw
                    else:
                        nsi = next((j for j, x in enumerate(ns_opts_dlg) if x.lower() == _ns_raw.lower()), 0)
                        r_ns = c5d.selectbox(f"NameStock", ns_opts_dlg, index=nsi, key=f"dlg_json_ns_{i}", label_visibility="collapsed")
                        effective_ns = r_ns

                    # Giá Nhập
                    r_cost_raw = c6d.text_input(f"Giá nhập", value="", placeholder="VD: 150k", key=f"dlg_json_cost_{i}", label_visibility="collapsed")


                    # ── Auto Title (editable) ──
                    _temp_ms = parse_usd(r_ms_raw)
                    _gen_title = generate_auto_title(r_name, r_mut, r_trait, _temp_ms, effective_ns if effective_ns else "")
                    r_title = st.text_input(
                        "Auto Title", value=_gen_title,
                        key=f"dlg_json_title_{i}", label_visibility="collapsed",
                    )

                    # ── Giá bán $ + Upload hình ──
                    if _HAS_ELDORADO and eld_client and eld_client.logged_in:
                        _img_col, _price_col = st.columns([2, 1])
                        r_img = _img_col.file_uploader(
                            f"Ảnh listing cho {pet_name}",
                            type=["png", "jpg", "jpeg", "webp"],
                            key=f"dlg_json_img_{i}", label_visibility="collapsed",
                        )
                        if r_img:
                            _img_col.image(r_img, width=320)
                        r_price_raw = _price_col.text_input(
                            "Giá bán ($)", value="",
                            placeholder="$0.50",
                            key=f"dlg_json_price_{i}", label_visibility="collapsed",
                        )
                    else:
                        r_img = None
                        r_price_raw = ""

                    # ── Similar pet detection (dùng cache) ──
                    if effective_ns and effective_ns.strip():
                        try:
                            r_ms = parse_usd(r_ms_raw)
                            r_mut_str = str(r_mut).strip()

                            if r_ms > 0:
                                # Lookup từ cache
                                key = (effective_ns.strip(), r_mut_str, int(r_ms / 50) * 50)
                                similar_pets = similar_cache.get(key, [])

                                # Exact Match (100%) + EXPLICIT CHECK NameStock
                                similar_pets = [
                                    p for p in similar_pets
                                    if p[1] == r_ms and p[2] == effective_ns.strip()
                                ]

                                if similar_pets:
                                    similar_names = ", ".join([f"{p[0]} ({p[1]:.1f}M/s)" for p in similar_pets[:3]])
                                    if len(similar_pets) > 3:
                                        similar_names += f" +{len(similar_pets)-3} nữa"
                                    st.warning(f"⚠️ **Có vẻ trùng (cùng {effective_ns}):** {similar_names}")
                        except Exception as e:
                            pass

                    # ── Owner chưa map NameStock ──
                    _res_owner = res.get("_owner", "")
                    _res_unmapped = res.get("_owner_unmapped", False)
                    if _res_unmapped and _res_owner:
                        st.warning(f"⚠️ Owner `{_res_owner}` chưa có trong mapping Owner → NameStock. Hãy thêm ở tab Cài Đặt.")

                r_ms = parse_usd(r_ms_raw)
                r_cost = parse_vnd(r_cost_raw)
                r_price = 0.0
                if r_price_raw.strip():
                    try:
                        r_price = float(r_price_raw)
                    except (ValueError, TypeError):
                        r_price = 0.0
                err_row = []
                if not r_delete:  # Chỉ validate nếu không xoá
                    if not r_name or r_name == "None": err_row.append("Tên Pet")
                    if r_ms <= 0:  err_row.append("M/s")
                    if not r_ns.strip(): err_row.append("NameStock")
                    if r_cost <= 0: err_row.append("Giá nhập")
                    # Validate push fields (nếu Eldorado connected)
                    if _HAS_ELDORADO and eld_client and eld_client.logged_in:
                        if not r_img: err_row.append("ảnh listing")
                        if not r_price_raw.strip(): err_row.append("giá bán $")
                        elif r_price < 0.50: err_row.append("giá bán tối thiểu $0.50")

                if not r_delete and err_row:
                    st.info(f"⚠️ Thiếu thông tin: {', '.join(err_row)}")
                    all_valid = False

                edited_rows.append({
                    "Tên Pet":   r_name,
                    "Mutation":  r_mut,
                    "Rarity":    res.get("Rarity", ""),
                    "M/s":       r_ms,
                    "ms_range":  res.get("ms_range", ""),
                    "Số Trait":  r_trait,
                    "NameStock": r_ns,
                    "Giá Nhập":  r_cost,
                    "_delete":   r_delete,
                    "_valid":    r_delete or len(err_row) == 0,
                    "_title":    r_title,
                    "_price":    r_price,
                    "_image":    r_img,
                    "_index":    res.get("_original_json", {}).get("index", ""),
                    "_owner":    res.get("_owner", ""),
                })

            st.markdown("---")
            col_cancel, col_save = st.columns([1, 2])
            with col_cancel:
                if st.button("Huỷ bỏ", use_container_width=True):
                    st.session_state.json_show_dialog = False
                    st.session_state.json_batch_results = []
                    st.session_state.json_import_key = st.session_state.get("json_import_key", 0) + 1
                    st.rerun()

            with col_save:
                valid_count = sum(1 for r in edited_rows if r["_valid"])
                save_label = f"Lưu {valid_count} / {len(edited_rows)} mục hợp lệ"
                if st.button(save_label, type="primary", use_container_width=True, disabled=valid_count == 0):
                    saved = 0
                    current_df = st.session_state.df
                    sb_records_to_insert = []
                    _ts_batch   = now_iso()
                    _ngay_batch = now_str()
                    saved_original_json = []
                    unsaved_original_json = []

                    for i, r in enumerate(edited_rows):
                        if not r["_valid"]:
                            if "_original_json" in json_results[i]:
                                unsaved_original_json.append(json_results[i]["_original_json"])
                            continue

                        # ── BỎ QUA NẾU TICK XOÁ (Không thêm vào, không xoá DB) ──
                        if r["_delete"]:
                            if "_original_json" in json_results[i]:
                                unsaved_original_json.append(json_results[i]["_original_json"])
                            continue

                        if "_original_json" in json_results[i]:
                            saved_original_json.append(json_results[i]["_original_json"])

                        # ── THÊM MỚI ──
                        existing_lower = [x.lower() for x in get_name_options(pet_db)]
                        if r["Tên Pet"].lower() not in existing_lower:
                            pet_db = append_row(pet_db, {"Name": r["Tên Pet"]}, LIST_SCHEMA)
                            save_csv(pet_db, PET_LIST_FILE)

                        stt = next_id(current_df, "STT")
                        new_row = {
                            "STT":        stt,
                            "Tên Pet":    r["Tên Pet"],
                            "M/s":        float(r["M/s"]),
                            "Mutation":   r["Mutation"],
                            "Số Trait":   r["Số Trait"],
                            "NameStock":  r["NameStock"],
                            "Giá Nhập":   float(r.get("Giá Nhập", 0.0)),
                            "Giá Bán":    0.0,
                            "Lợi Nhuận":  0.0,
                            "Doanh Thu":  0.0,
                            "Ngày Nhập":  _ngay_batch,
                            "Ngày Bán":   "-",
                            "Auto Title": r.get("_title") or generate_auto_title(
                                r["Tên Pet"], r["Mutation"], r["Số Trait"], r["M/s"], r["NameStock"]
                            ),
                            "Trạng Thái": "Còn hàng",
                            "time_nhap":  _ts_batch,
                            "time_ban":   "",
                            "Ngày Tồn":   0,
                            "Place":      "",
                        }
                        current_df = append_row(current_df, new_row, MAIN_SCHEMA)
                        _db_row = to_db(new_row)
                        _db_row.pop("id", None)
                        sb_records_to_insert.append(_db_row)
                        saved += 1

                    # Toàn bộ I/O nằm trong spinner
                    _save_ok = False
                    with st.spinner(f"Đang lưu {saved} mục..."):
                        sb_ok = True

                        # Insert mới
                        if USE_SUPABASE:
                            if sb_records_to_insert:
                                sb_ok = sb_insert_batch("inventory", sb_records_to_insert)

                        if sb_ok:
                            if USE_SUPABASE:
                                st.cache_data.clear()
                                st.session_state.df = apply_ngay_ton(load_inventory())
                            else:
                                current_df = apply_ngay_ton(current_df)
                                st.session_state.df = current_df
                            save_csv(st.session_state.df, DB_FILE)
                            # ── Merge JSON history: old + new per owner ──
                            _merged_owners = {}
                            for _orig in saved_original_json:
                                _o = str(_orig.get("owner", "")).strip().lower()
                                if _o:
                                    if _o not in _merged_owners:
                                        _merged_owners[_o] = _load_json_history(_o)
                                    _merged_owners[_o].append(_orig)
                            for _o, _new_list in _merged_owners.items():
                                _save_json_history(_o, _new_list)
                            st.session_state.json_show_dialog = False
                            st.session_state.json_batch_results = []
                            st.session_state.json_import_expander = False
                            _save_ok = True

                    if _save_ok:
                        st.session_state.json_saved_output = json.dumps(saved_original_json, ensure_ascii=False, indent=2)
                        # ── PUSH LÊN ELDORADO SAU KHI LƯU DB ──
                        _push_items = [r for r in edited_rows if r.get("_valid") and not r.get("_delete")
                                       and r.get("_image") and r.get("_price", 0) >= 0.50]
                        _push_results = {"ok": [], "fail": []}
                        if _push_items and _HAS_ELDORADO and eld_client and eld_client.logged_in:
                            if not st.session_state.get("eld_game_loaded"):
                                st.session_state.eld_game_loaded = eld_client.ensure_game_cache()
                            if st.session_state.get("eld_game_loaded"):
                                _eld_set = st.session_state.get("eld_settings", {})
                                _def_desc = _eld_set.get("default_desc", "Fast delivery! Contact me if any issues.")
                                _def_del = _eld_set.get("default_delivery", "20 min")
                                _def_del_code = DELIVERY_MAP.get(_def_del, "Minute20")
                                for _pci, _pcfg in enumerate(_push_items):
                                    _pname = _pcfg.get("Tên Pet", "?")
                                    try:
                                        _img_data = None
                                        if _pcfg.get("_image"):
                                            _img_bytes = _pcfg["_image"].read()
                                            _img_data = eld_client.upload_image(
                                                _img_bytes, _pcfg["_image"].name or "image.png")
                                            if _img_data and _img_data.get("_rate_limit"):
                                                _img_data = None
                                        _pet_name = _pcfg.get("Tên Pet", "")
                                        _pet_idx = _pcfg.get("_index", "")
                                        _pet_rarity = _pcfg.get("Rarity", "")
                                        _pet_ms_range = _pcfg.get("ms_range", "")
                                        _env = eld_client.find_env(_pet_name, rarity=_pet_rarity, index=_pet_idx)
                                        _tid = _env["id"] if _env else OTHER_TRADE_ENV_ID
                                        _resp = eld_client.create_listing(
                                            title=_pcfg.get("_title", ""),
                                            description=_def_desc,
                                            price=_pcfg["_price"],
                                            ms=float(_pcfg.get("M/s", 0)),
                                            ms_range=_pet_ms_range,
                                            mutation=_pcfg.get("Mutation", "Normal"),
                                            trade_env_id=_tid,
                                            delivery_time=_def_del_code,
                                            image_data=_img_data,
                                        )
                                        if _resp and not _resp.get("error"):
                                            _push_results["ok"].append(_pcfg.get("_title", _pname))
                                        else:
                                            _err = _resp.get("error", "unknown") if isinstance(_resp, dict) else str(_resp)
                                            _push_results["fail"].append(f"{_pname}: {_err[:80]}")
                                    except Exception as _pe:
                                        _push_results["fail"].append(f"{_pname}: {str(_pe)[:80]}")
                                    if _pci < len(_push_items) - 1:
                                        _time.sleep(0.5)
                        st.session_state.json_push_results = _push_results
                        st.session_state.json_push_total = len(_push_items)
                        st.toast(f"✅ Đã lưu {saved} mục thành công", icon="✅")
                        st.rerun()

        json_preview_dialog()

    if st.session_state.get("json_saved_output"):
        st.success("🎉 Đã lưu thành công!")

        if st.session_state.json_saved_output != "[]":
            if st.button("📦 Trích xuất JSON các pet ĐÃ ĐƯỢC LƯU"):
                st.session_state.show_saved_json = True

            if st.session_state.get("show_saved_json"):
                st.code(st.session_state.json_saved_output, language="json")

            # ── Hiển thị kết quả push Eldorado sau rerun ──
            if "json_push_results" in st.session_state:
                _pr = st.session_state.json_push_results
                _pt = st.session_state.json_push_total
                if _pr:
                    if _pr["ok"]:
                        st.success(f"✅ Push Eldorado thành công: {len(_pr['ok'])}/{_pt}")
                        with st.expander("📋 Danh sách đã push", expanded=False):
                            for _t in _pr["ok"]:
                                st.caption(f"• {_t}")
                    if _pr["fail"]:
                        st.error(f"❌ Push Eldorado thất bại: {len(_pr['fail'])}/{_pt}")
                        with st.expander("❌ Chi tiết lỗi", expanded=True):
                            for _e in _pr["fail"]:
                                st.caption(f"• {_e}")
                else:
                    st.info("ℹ️ Không có mục nào đủ điều kiện push lên Eldorado (cần ảnh + giá $ ≥0.50).")
                if st.button("❌ Ẩn kết quả push", key="btn_hide_push"):
                    del st.session_state.json_push_results
                    del st.session_state.json_push_total
                    st.rerun()
        else:
            st.info("Không có pet nào được lưu.")

        if st.button("❌ Xóa toàn bộ kết quả này", key="btn_clear_json_results"):
            st.session_state.json_saved_output = ""
            st.session_state.json_unsaved_output = ""
            st.session_state.show_saved_json = False
            st.session_state.show_unsaved_json = False
            st.rerun()
