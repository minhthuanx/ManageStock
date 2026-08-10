# =============================================================================
# TAB KHO LE — NHẬP TAY NHIỀU PET QUA POPUP (giống dialog JSON / AI Vision)
#
# Trên trang chính chỉ có 1 nút ngang dài. Bấm → mở popup (st.dialog) chứa
# sẵn các dòng nhập (giống hệt bảng preview sau khi load JSON/AI Vision):
#   - Mỗi dòng: Tên Pet, Mutation, M/s, Số Trait, NameStock, Giá nhập,
#     Auto Title, ảnh listing + Giá bán ($) (để push Eldorado)
#   - Nút "＋ Thêm dòng" / "－ Bớt dòng" ngay trong popup
#   - Lưu → ghi DB + push Eldorado các dòng đủ điều kiện
# =============================================================================

import time as _time
import pandas as pd
import streamlit as st

from _timezone import now_str, now_iso
from _helpers import (
    parse_vnd, parse_usd, get_name_options, append_row,
    generate_auto_title, apply_ngay_ton, next_id,
)
from _config import MAIN_SCHEMA, LIST_SCHEMA, MUTATION_OPTIONS, PET_LIST_FILE
from _database import (
    USE_SUPABASE, sb_insert_batch,
    load_inventory, save_csv, to_db,
)
from _eldorado_helpers import _HAS_ELDORADO

try:
    from eldorado_client import DELIVERY_MAP, OTHER_TRADE_ENV_ID
except ImportError:
    DELIVERY_MAP = {}


class _FakeUploadedFile:
    """Lưu ảnh listing tạm trong session_state (mô phỏng file uploader)."""
    def __init__(self, data: bytes, name: str, mime: str):
        self._data = data
        self.name = name
        self.type = mime
        self._pos = 0

    def read(self, size=-1):
        if size == -1:
            result = self._data[self._pos:]
            self._pos = len(self._data)
        else:
            result = self._data[self._pos:self._pos + size]
            self._pos += len(result)
        return result

    def seek(self, pos):
        self._pos = pos

    def getvalue(self):
        return self._data


def render_manual_multi(df, pet_db, ns_db, trait_db, eld_client=None):
    """1 nút ngang dài → popup nhập tay nhiều dòng (giống dialog JSON/AI Vision)."""

    # ── State ──
    if "manual_n_rows" not in st.session_state:
        st.session_state.manual_n_rows = 1
    if "manual_show_dialog" not in st.session_state:
        st.session_state.manual_show_dialog = False
    if "manual_img_bytes" not in st.session_state:
        st.session_state.manual_img_bytes = {}

    # ══════════════════════════════════════════════════════════════════
    # NÚT NGANG DÀI DUY NHẤT (dưới phần nhập thủ công)
    # ══════════════════════════════════════════════════════════════════
    if st.button(
        "＋ Nhập Tay Nhiều Pet — mở bảng nhập nhanh",
        type="primary", use_container_width=True, key="btn_manual_open_popup",
    ):
        st.session_state.manual_n_rows = 1
        st.session_state.manual_img_bytes = {}
        st.session_state.manual_show_dialog = True

    # ══════════════════════════════════════════════════════════════════
    # POPUP — xổ ra giống hệt dialog sau khi load JSON / AI Vision
    # ══════════════════════════════════════════════════════════════════
    if st.session_state.get("manual_show_dialog"):

        @st.dialog("Nhập Tay Nhiều Pet — Điền từng dòng", width="large")
        def manual_entry_dialog():
            # pet_db là biến local để tránh UnboundLocalError khi append
            pet_db_local = pet_db
            pet_opts_dlg = get_name_options(pet_db_local)
            pet_opts_lower = set(x.lower() for x in pet_opts_dlg)
            trait_opts_dlg = ["None"] + [str(n) for n in range(1, 16)]
            ns_opts_dlg = [""] + get_name_options(ns_db, fallback="")
            _show_push = _HAS_ELDORADO and eld_client and eld_client.logged_in

            st.caption("Điền từng dòng · bấm **＋ Thêm dòng** để thêm nhiều pet · "
                       "Dòng có ảnh + giá bán $ ≥ 0.50 sẽ tự push lên Eldorado")

            # ── NameStock chung cho toàn bộ dòng ──
            _gn1, _gn2 = st.columns([1, 3])
            use_global_ns = _gn1.checkbox("NameStock chung", key="mmp_global_ns",
                                           help="Áp dụng cùng 1 NameStock cho tất cả dòng")
            if use_global_ns:
                global_ns_val = _gn2.selectbox(
                    "NameStock áp dụng cho tất cả", ns_opts_dlg,
                    key="mmp_global_ns_val", label_visibility="collapsed",
                )
            else:
                global_ns_val = ""

            st.markdown("---")
            n_rows = st.session_state.manual_n_rows
            edited_rows = []

            # ── Các dòng nhập ──
            for row_i in range(n_rows):
                # Label expander hiện tên pet đã chọn (từ lần render trước)
                _sel_name = st.session_state.get(f"mmp_name_{row_i}", None)
                _label = f"Dòng {row_i + 1}"
                if _sel_name and str(_sel_name) not in ("", "None"):
                    _label += f" — {_sel_name}"
                with st.expander(_label, expanded=True):
                    col1, col2, col3 = st.columns(3)

                    # Tên Pet
                    pet_sel = col1.selectbox(
                        "Tên Pet", pet_opts_dlg, key=f"mmp_name_{row_i}",
                        label_visibility="collapsed",
                    )
                    # Mutation
                    _norm_i = next((j for j, m in enumerate(MUTATION_OPTIONS) if m == "Normal"), 0)
                    mut_sel = col2.selectbox(
                        "Mutation", MUTATION_OPTIONS, index=_norm_i,
                        key=f"mmp_mut_{row_i}", label_visibility="collapsed",
                    )
                    # M/s
                    ms_raw = col3.text_input(
                        "M/s", placeholder="VD: 975", key=f"mmp_ms_{row_i}",
                        label_visibility="collapsed",
                    )

                    col4, col5, col6 = st.columns(3)
                    # Số Trait
                    trait_sel = col4.selectbox(
                        "Số Trait", trait_opts_dlg, key=f"mmp_trait_{row_i}",
                        label_visibility="collapsed",
                    )
                    # NameStock (global hoặc per-row)
                    if use_global_ns:
                        ns_val = global_ns_val
                        _ns_display = global_ns_val if global_ns_val else "—"
                        col5.markdown(
                            f'<div style="padding-top:1.8rem;font-size:0.82rem;color:#d4d4d8;">'
                            f'NS: <b>{_ns_display}</b> <span style="color:#777777;">(chung)</span></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        ns_val = col5.selectbox(
                            "NameStock", ns_opts_dlg, key=f"mmp_ns_{row_i}",
                            label_visibility="collapsed",
                        )
                    # Giá nhập
                    cost_raw = col6.text_input(
                        "Giá nhập", placeholder="150k / 1.5tr / 1500000",
                        key=f"mmp_cost_{row_i}", label_visibility="collapsed",
                    )

                    # ── Auto Title (editable) ──
                    _temp_ms = parse_usd(ms_raw)
                    _gen_title = generate_auto_title(pet_sel, mut_sel, trait_sel, _temp_ms, ns_val or "")
                    r_title = st.text_input(
                        "Auto Title", value=_gen_title,
                        key=f"mmp_title_{row_i}", label_visibility="collapsed",
                    )

                    # ── Giá bán $ + Ảnh listing (Eldorado) ──
                    if _show_push:
                        _saved_key = f"mmp_img_{row_i}"
                        _saved = st.session_state.manual_img_bytes.get(_saved_key)

                        _img_col, _price_col = st.columns([2, 1])
                        if _saved:
                            _img_col.image(_saved["bytes"], width=240)
                            _img_col.caption(f"Ảnh đã lưu: {_saved['name']}")
                            if _img_col.button("Xóa ảnh", key=f"mmp_rm_img_{row_i}",
                                               use_container_width=True):
                                del st.session_state.manual_img_bytes[_saved_key]
                                st.rerun()
                            r_img = _FakeUploadedFile(_saved["bytes"], _saved["name"], _saved["mime"])
                        else:
                            up_img = _img_col.file_uploader(
                                "Ảnh listing (để push Eldorado)",
                                type=["png", "jpg", "jpeg", "webp"],
                                key=f"mmp_img_{row_i}", label_visibility="collapsed",
                            )
                            if up_img:
                                _b = up_img.read()
                                up_img.seek(0)
                                st.session_state.manual_img_bytes[_saved_key] = {
                                    "bytes": _b,
                                    "name": up_img.name or "image.png",
                                    "mime": up_img.type or "image/png",
                                }
                                _img_col.image(_b, width=240)
                            r_img = up_img

                        price_raw = _price_col.text_input(
                            "Giá bán ($)", placeholder="$0.50",
                            key=f"mmp_price_{row_i}", label_visibility="collapsed",
                        )
                    else:
                        r_img = None
                        price_raw = ""

                # ── Validate + thu thập dòng ──
                r_ms = parse_usd(ms_raw)
                r_cost = parse_vnd(cost_raw)
                r_price = 0.0
                if price_raw.strip():
                    try:
                        r_price = float(price_raw)
                    except (ValueError, TypeError):
                        r_price = 0.0

                err_row = []
                if not pet_sel or pet_sel == "None": err_row.append("Tên Pet")
                if r_ms <= 0: err_row.append("M/s")
                if not ns_val.strip(): err_row.append("NameStock")
                if r_cost <= 0: err_row.append("Giá nhập")
                if _show_push:
                    if not r_img: err_row.append("ảnh listing")
                    if not price_raw.strip(): err_row.append("giá bán $")
                    elif r_price < 0.50: err_row.append("giá bán tối thiểu $0.50")

                if err_row:
                    st.info(f"! Thiếu thông tin Dòng {row_i + 1}: {', '.join(err_row)}")

                edited_rows.append({
                    "Tên Pet":   pet_sel,
                    "Mutation":  mut_sel,
                    "M/s":       r_ms,
                    "Số Trait":  trait_sel,
                    "NameStock": ns_val,
                    "Giá Nhập":  r_cost,
                    "_valid":    len(err_row) == 0,
                    "_title":    r_title,
                    "_price":    r_price,
                    "_image":    r_img,
                })

            # ── Thêm / Bớt dòng (ngay trong popup) ──
            _b1, _b2, _b3 = st.columns([1, 1, 2])
            if _b1.button("＋ Thêm dòng", use_container_width=True, key="btn_mmp_add"):
                st.session_state.manual_n_rows += 1
                st.rerun()
            if n_rows > 1:
                if _b2.button("－ Bớt dòng", use_container_width=True, key="btn_mmp_remove"):
                    st.session_state.manual_n_rows -= 1
                    st.session_state.manual_img_bytes.pop(f"mmp_img_{n_rows - 1}", None)
                    st.rerun()

            # ── Huỷ / Lưu ──
            st.markdown("---")
            valid_count = sum(1 for r in edited_rows if r["_valid"])
            col_cancel, col_save = st.columns([1, 2])
            with col_cancel:
                if st.button("Huỷ bỏ", use_container_width=True, key="btn_mmp_cancel"):
                    st.session_state.manual_show_dialog = False
                    st.session_state.manual_img_bytes = {}
                    st.session_state.manual_n_rows = 1
                    st.rerun()

            with col_save:
                if st.button(
                    f"Lưu {valid_count} / {len(edited_rows)} dòng hợp lệ",
                    type="primary", use_container_width=True, disabled=valid_count == 0,
                    key="btn_mmp_save",
                ):
                    saved = 0
                    current_df = st.session_state.df
                    sb_records_to_insert = []
                    _ts_batch   = now_iso()
                    _ngay_batch = now_str()

                    for r in edited_rows:
                        if not r["_valid"]:
                            continue
                        existing_lower = [x.lower() for x in get_name_options(pet_db_local)]
                        if r["Tên Pet"].lower() not in existing_lower:
                            pet_db_local = append_row(pet_db_local, {"Name": r["Tên Pet"]}, LIST_SCHEMA)
                            save_csv(pet_db_local, PET_LIST_FILE)

                        stt = next_id(current_df, "STT")
                        new_row = {
                            "STT":        stt,
                            "Tên Pet":    r["Tên Pet"],
                            "M/s":        float(r["M/s"]),
                            "Mutation":   r["Mutation"],
                            "Số Trait":   r["Số Trait"],
                            "NameStock":  r["NameStock"],
                            "Giá Nhập":   float(r["Giá Nhập"]),
                            "Giá Bán":    0.0,
                            "Lợi Nhuận":  0.0,
                            "Doanh Thu":  0.0,
                            "Ngày Nhập":  _ngay_batch,
                            "Ngày Bán":   "-",
                            "Auto Title": r["_title"] or generate_auto_title(
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

                    _save_ok = False
                    with st.spinner(f"Đang lưu {saved} dòng..."):
                        sb_ok = True
                        if USE_SUPABASE and sb_records_to_insert:
                            sb_ok = sb_insert_batch("inventory", sb_records_to_insert)

                        if sb_ok:
                            if USE_SUPABASE:
                                st.cache_data.clear()
                                st.session_state.df = apply_ngay_ton(load_inventory())
                            else:
                                current_df = apply_ngay_ton(current_df)
                                st.session_state.df = current_df
                            save_csv(st.session_state.df, DB_FILE)
                            st.session_state.manual_show_dialog = False
                            st.session_state.manual_img_bytes = {}
                            st.session_state.manual_n_rows = 1
                            _save_ok = True

                    if _save_ok:
                        # ── PUSH LÊN ELDORADO SAU KHI LƯU DB ──
                        _push_items = [r for r in edited_rows if r.get("_valid")
                                       and r.get("_image") and r.get("_price", 0) >= 0.50]
                        _push_results = {"ok": [], "fail": []}
                        if _push_items and _HAS_ELDORADO and eld_client and eld_client.logged_in:
                            if not st.session_state.get("eld_game_loaded"):
                                st.toast("Đang kết nối game Eldorado...", icon="🔗")
                                st.session_state.eld_game_loaded = eld_client.ensure_game_cache()
                            if st.session_state.get("eld_game_loaded"):
                                _eld_set = st.session_state.get("eld_settings", {})
                                _def_desc = _eld_set.get("default_desc", "Fast delivery! Contact me if any issues.")
                                _def_del = _eld_set.get("default_delivery", "20 min")
                                _def_del_code = DELIVERY_MAP.get(_def_del, "Minute20")
                                _push_total = len(_push_items)
                                st.toast(f"Bắt đầu push {_push_total} listing lên Eldorado...", icon="🚀")
                                for _pci, _pcfg in enumerate(_push_items):
                                    _pname = _pcfg.get("Tên Pet", "?")
                                    st.toast(f"[{_pci+1}/{_push_total}] Đang upload ảnh {_pname}...", icon="📤")
                                    try:
                                        _img_data = None
                                        if _pcfg.get("_image"):
                                            _pcfg["_image"].seek(0)
                                            _img_bytes = _pcfg["_image"].read()
                                            _img_data = eld_client.upload_image(
                                                _img_bytes, _pcfg["_image"].name or "image.png")
                                            if _img_data and _img_data.get("_rate_limit"):
                                                _img_data = None
                                        _pet_name = _pcfg.get("Tên Pet", "")
                                        _env = eld_client.find_env(_pet_name)
                                        _tid = _env["id"] if _env else OTHER_TRADE_ENV_ID
                                        st.toast(f"[{_pci+1}/{_push_total}] Đang tạo listing {_pname}...", icon="📋")
                                        _resp = eld_client.create_listing(
                                            title=_pcfg.get("_title", ""),
                                            description=_def_desc,
                                            price=_pcfg["_price"],
                                            ms=float(_pcfg.get("M/s", 0)),
                                            ms_range="",
                                            mutation=_pcfg.get("Mutation", "Normal"),
                                            trade_env_id=_tid,
                                            delivery_time=_def_del_code,
                                            image_data=_img_data,
                                        )
                                        if _resp and not _resp.get("error"):
                                            _push_results["ok"].append(_pcfg.get("_title", _pname))
                                            st.toast(f"{_pname} — push thành công", icon="✅")
                                        else:
                                            _err = _resp.get("error", "unknown") if isinstance(_resp, dict) else str(_resp)
                                            _push_results["fail"].append(f"{_pname}: {_err[:80]}")
                                            st.toast(f"{_pname} — {_err[:50]}", icon="❌")
                                    except Exception as _pe:
                                        _push_results["fail"].append(f"{_pname}: {str(_pe)[:80]}")
                                        st.toast(f"{_pname} — lỗi: {str(_pe)[:50]}", icon="❌")
                                    if _pci < _push_total - 1:
                                        _time.sleep(0.5)
                        st.session_state.manual_push_results = _push_results
                        st.session_state.manual_push_total = len(_push_items)
                        _ok_n = len(_push_results.get("ok", []))
                        _fail_n = len(_push_results.get("fail", []))
                        if _push_items:
                            if _fail_n == 0:
                                st.toast(f"Push thành công {_ok_n}/{len(_push_items)} listing", icon="✅")
                            else:
                                st.toast(f"Push xong: {_ok_n} thành công, {_fail_n} thất bại", icon="⚠️")
                        else:
                            st.toast(f"Đã lưu {saved} dòng thành công", icon="✅")
                        st.rerun()

        manual_entry_dialog()

    # ── Kết quả push Eldorado (sau rerun) ──
    if st.session_state.get("manual_push_results"):
        _pr = st.session_state.manual_push_results
        _pt = st.session_state.manual_push_total
        if _pr:
            if _pr["ok"]:
                st.success(f"✓ Push Eldorado thành công: {len(_pr['ok'])}/{_pt}")
                with st.expander("Danh sách đã push", expanded=False):
                    for _t in _pr["ok"]:
                        st.caption(f"• {_t}")
            if _pr["fail"]:
                st.error(f"× Push Eldorado thất bại: {len(_pr['fail'])}/{_pt}")
                with st.expander("Chi tiết lỗi", expanded=True):
                    for _e in _pr["fail"]:
                        st.caption(f"• {_e}")
        else:
            st.info("i Không có mục nào đủ điều kiện push lên Eldorado (cần ảnh + giá $ >=0.50).")
        if st.button("× Ẩn kết quả push", key="btn_hide_manual_push"):
            del st.session_state.manual_push_results
            del st.session_state.manual_push_total
            st.rerun()