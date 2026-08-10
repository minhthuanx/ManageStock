# =============================================================================
# TAB KHO LE — NHẬP TAY NHIỀU DÒNG (manual multi-row via popup preview)
#
# Cách dùng:
#   1. Form đơn ở trang chính (giống "Nhập Thủ Công") — điền & bấm "Thêm vào danh sách"
#   2. Mỗi lần submit → thêm 1 mục vào session_state["manual_pending"]
#   3. Bấm "Mở Xem Trước (N mục)" → popup dialog hiện BẢNG tổng tất cả mục
#      (giống hệt preview của JSON Import / AI Vision), cho sửa/xoá/thêm dòng,
#      upload ảnh + giá bán $ từng dòng, rồi Lưu → push Eldorado nếu đủ điều kiện
# =============================================================================

import time as _time
import pandas as pd
import streamlit as st

from _timezone import now_vn, now_str, now_iso
from _helpers import (
    parse_vnd, parse_usd, fmt_vnd, get_name_options, append_row,
    generate_auto_title, _clear_searches, _sv, apply_ngay_ton, next_id,
)
from _config import MAIN_SCHEMA, LIST_SCHEMA, MUTATION_OPTIONS, PET_LIST_FILE
from _database import (
    USE_SUPABASE, sb_insert, sb_insert_batch,
    load_inventory, load_csv, save_csv, supabase_client, to_db,
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


def _ns_opts(ns_db):
    return [""] + get_name_options(ns_db, fallback="")


def render_manual_multi(df, pet_db, ns_db, trait_db, eld_client=None):
    """Form nhập tay nhiều dòng — nhập đơn trên trang, tổng hợp + preview trong popup."""

    # ── State ──
    if "manual_pending" not in st.session_state:
        st.session_state.manual_pending = []       # list các dict đã thêm
    if "manual_img_bytes" not in st.session_state:
        st.session_state.manual_img_bytes = {}     # ảnh đã upload trong popup (key per row)

    with st.container(border=True):
        st.markdown("**Nhập Tay Nhiều Dòng**")
        st.caption("Điền thông tin từng con pet, bấm **Thêm vào danh sách** — "
                   "sau đó mở **Xem Trước** để soát lại cả batch (giống JSON Import)")

        pet_opts = get_name_options(pet_db)
        trait_opts = ["None"] + [str(n) for n in range(1, 16)]
        ns_opts = _ns_opts(ns_db)

        # ── Form đơn (giống "Nhập Thủ Công" nhưng thêm Mutation/Trait/NameStock) ──
        with st.form("form_manual_multi_add", clear_on_submit=True):
            pet_sel = st.selectbox("Tên Pet", pet_opts)
            _norm_i = next((j for j, m in enumerate(MUTATION_OPTIONS) if m == "Normal"), 0)
            c1, c2, c3 = st.columns(3)
            ms_raw   = c1.text_input("M/s", placeholder="VD: 975")
            mut_sel  = c2.selectbox("Mutation", MUTATION_OPTIONS, index=_norm_i)
            trait_sel= c3.selectbox("Số Trait", trait_opts)
            c4, c5 = st.columns([1.5, 1])
            ns_sel   = c4.selectbox("NameStock", ns_opts)
            cost_raw = c5.text_input("Giá nhập (VNĐ)", placeholder="150k / 1.5tr / 1.500.000")

            _add_col, _preview_col = st.columns([1, 1])
            submitted = _add_col.form_submit_button("＋ Thêm vào danh sách", use_container_width=True)

        # ── Sau khi submit: validate rồi thêm vào list ──
        if submitted:
            ms = parse_usd(ms_raw)
            cost = parse_vnd(cost_raw)
            errs = []
            if pet_sel == "None": errs.append("Tên Pet")
            if ms <= 0:           errs.append("M/s phải > 0")
            if cost <= 0:         errs.append("Giá nhập phải > 0")
            if not ns_sel.strip(): errs.append("NameStock")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                st.session_state.manual_pending.append({
                    "Tên Pet":   pet_sel,
                    "Mutation":  mut_sel,
                    "M/s":       ms,
                    "Số Trait":  trait_sel,
                    "NameStock": ns_sel,
                    "Giá Nhập":  cost,
                    "_valid":    True,
                })
                st.toast(f"Đã thêm {pet_sel} — tổng {len(st.session_state.manual_pending)} mục", icon="➕")

        # ── Nút mở popup preview ──
        _n = len(st.session_state.manual_pending)
        _btn_label = f"Xem Trước & Lưu {_n} mục" if _n else "Xem Trước & Lưu (trống)"
        if st.button(_btn_label, type="primary", use_container_width=True,
                     key="btn_manual_open_preview", disabled=_n == 0):
            st.session_state.manual_show_dialog = True

        if st.session_state.manual_pending and st.button("✕ Xoá toàn bộ danh sách",
                                                         use_container_width=True,
                                                         key="btn_manual_clear"):
            st.session_state.manual_pending = []
            st.session_state.manual_img_bytes = {}
            st.rerun()

        with st.expander(f"Danh sách đang chờ ({_n} mục)", expanded=False):
            for _i, _p in enumerate(st.session_state.manual_pending):
                _ms_p = _p.get("M/s", 0)
                _ms_s = f"{_ms_p:g}M/s" if _ms_p else "?"
                st.caption(f"{_i+1}. {_p.get('Tên Pet','?')} · {_p.get('Mutation','Normal')} · {_ms_s} · "
                           f"NS: {_p.get('NameStock','') or '—'} · {fmt_vnd(_p.get('Giá Nhập', 0))}")

    # =========================================================
    # DIALOG PREVIEW (giống JSON / AI Vision)
    # =========================================================
    if st.session_state.get("manual_show_dialog") and st.session_state.get("manual_pending"):
        pending = st.session_state.manual_pending
        pending_list = list(pending)  # snapshot

        @st.dialog("Nhập Tay — Xem Trước & Chỉnh Sửa", width="large")
        def manual_preview_dialog():
            # pet_db là biến local để tránh UnboundLocalError khi append
            pet_db_local = pet_db
            pet_opts_dlg = get_name_options(pet_db_local)
            pet_opts_lower = set(x.lower() for x in pet_opts_dlg)
            trait_opts_dlg = ["None"] + [str(n) for n in range(1, 16)]
            ns_opts_dlg = _ns_opts(ns_db)

            st.caption(f"**{len(pending_list)}** mục · Tick ✓ để chọn lưu (bỏ tick = bỏ qua mục đó) · "
                       "Có thể thêm dòng mới ngay tại đây")

            # ── Thêm dòng mới ngay trong popup ──
            with st.expander("＋ Thêm dòng mới tại đây", expanded=False):
                _c1, _c2, _c3 = st.columns(3)
                _npet = _c1.selectbox("Tên Pet (mới)", pet_opts_dlg, key="dlg_mp_name")
                _nms  = _c2.text_input("M/s", placeholder="VD: 975", key="dlg_mp_ms")
                _nmut = _c3.selectbox("Mutation", MUTATION_OPTIONS, key="dlg_mp_mut")
                _c4, _c5, _c6 = st.columns(3)
                _ntr  = _c4.selectbox("Số Trait", trait_opts_dlg, key="dlg_mp_trait")
                _nns  = _c5.selectbox("NameStock", ns_opts_dlg, key="dlg_mp_ns")
                _ncost = _c6.text_input("Giá nhập", placeholder="150k", key="dlg_mp_cost")
                if st.button("Thêm mục này", key="btn_dlg_mp_add", use_container_width=True):
                    _ms_v = parse_usd(_nms)
                    _cost_v = parse_vnd(_ncost)
                    _errs = []
                    if _npet == "None": _errs.append("Tên Pet")
                    if _ms_v <= 0: _errs.append("M/s")
                    if _cost_v <= 0: _errs.append("Giá nhập")
                    if not _nns.strip(): _errs.append("NameStock")
                    if _errs:
                        st.error(f"Thiếu: {', '.join(_errs)}")
                    else:
                        st.session_state.manual_pending.append({
                            "Tên Pet": _npet, "Mutation": _nmut, "M/s": _ms_v,
                            "Số Trait": _ntr, "NameStock": _nns, "Giá Nhập": _cost_v,
                            "_valid": True,
                        })
                        st.rerun()

            # ── NameStock chung ──
            _gn1, _gn2 = st.columns([1, 3])
            use_global_ns = _gn1.checkbox("NameStock chung", key="dlg_mp_global_ns_check",
                                           help="Áp dụng cùng 1 NameStock cho tất cả mục")
            if use_global_ns:
                global_ns_val = _gn2.selectbox(
                    "NameStock áp dụng cho tất cả", ns_opts_dlg,
                    key="dlg_mp_global_ns_val", label_visibility="collapsed",
                )
            else:
                global_ns_val = ""

            st.markdown("---")
            edited_rows = []
            all_valid = True

            for i, res in enumerate(pending_list):
                pet_name = res.get("Tên Pet", f"Item {i+1}")
                mutation = res.get("Mutation", "Normal")
                _expander_label = f"✓ {pet_name} · {mutation}"

                with st.expander(_expander_label, expanded=True):
                    _del_col, _info_col = st.columns([0.5, 5])
                    with _del_col:
                        r_keep = st.checkbox("✓", value=True, key=f"dlg_mp_keep_{i}",
                                             label="Giữ", help="Bỏ tick để bỏ qua mục này khi lưu")
                    with _info_col:
                        ms_val = res.get('M/s')
                        if ms_val and ms_val >= 1000:
                            ms_str = f"{int(ms_val / 100) / 10:.1f}B/s"
                        else:
                            ms_str = f"{ms_val:g}M/s" if ms_val else "?"
                        st.caption(f"M/s: {ms_str} | Traits: {res.get('Số Trait')}")

                    c1d, c2d, c3d = st.columns(3)
                    # Tên Pet
                    d_name = str(res.get("Tên Pet") or "")
                    if d_name and d_name.lower() not in pet_opts_lower:
                        pet_opts_dlg = [d_name] + pet_opts_dlg
                        pet_opts_lower.add(d_name.lower())
                    pi = next((j for j, x in enumerate(pet_opts_dlg) if x.lower() == d_name.lower()), 0)
                    r_name = c1d.selectbox("Tên Pet", pet_opts_dlg, index=pi,
                                           key=f"dlg_mp_name_{i}", label_visibility="collapsed")
                    # Mutation
                    d_mut = str(res.get("Mutation") or "Normal")
                    mi = next((j for j, m in enumerate(MUTATION_OPTIONS) if m.lower() == d_mut.lower()), 0)
                    r_mut = c2d.selectbox("Mutation", MUTATION_OPTIONS, index=mi,
                                          key=f"dlg_mp_mut_{i}", label_visibility="collapsed")
                    # M/s
                    val_ms = res.get("M/s")
                    if val_ms and val_ms >= 1000:
                        str_ms = f"{int(val_ms / 100) / 10:.1f}B/s"
                    else:
                        str_ms = f"{val_ms:g}" if val_ms else ""
                    r_ms_raw = c3d.text_input("M/s", value=str_ms, key=f"dlg_mp_ms_{i}",
                                              label_visibility="collapsed")

                    c4d, c5d, c6d = st.columns([1, 1, 1])
                    # Số Trait
                    d_trait = str(res.get("Số Trait") or "None").strip()
                    if d_trait not in trait_opts_dlg:
                        trait_opts_dlg = trait_opts_dlg + [d_trait]
                    ti = next((j for j, t in enumerate(trait_opts_dlg) if t.lower() == d_trait.lower()), 0)
                    r_trait = c4d.selectbox("Số Trait", trait_opts_dlg, index=ti,
                                            key=f"dlg_mp_trait_{i}", label_visibility="collapsed")
                    # NameStock (global hoặc per-row)
                    d_ns = res.get("NameStock", "")
                    if use_global_ns:
                        r_ns = global_ns_val
                        _ns_display = global_ns_val if global_ns_val else "—"
                        c5d.markdown(
                            f'<div style="padding-top:1.8rem;font-size:0.82rem;color:#d4d4d8;">'
                            f'NS: <b>{_ns_display}</b> <span style="color:#777777;">(chung)</span></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        nsi = next((j for j, x in enumerate(ns_opts_dlg) if x.lower() == d_ns.lower()), 0)
                        r_ns = c5d.selectbox("NameStock", ns_opts_dlg, index=nsi,
                                             key=f"dlg_mp_ns_{i}", label_visibility="collapsed")
                    # Giá Nhập
                    _cost_v = res.get("Giá Nhập", 0)
                    _cost_s = f"{_cost_v:g}" if _cost_v else ""
                    r_cost_raw = c6d.text_input("Giá nhập", value=_cost_s,
                                                key=f"dlg_mp_cost_{i}", label_visibility="collapsed")

                    # ── Auto Title (editable) ──
                    _temp_ms = parse_usd(r_ms_raw)
                    _gen_title = generate_auto_title(r_name, r_mut, r_trait, _temp_ms, r_ns or "")
                    r_title = st.text_input("Auto Title", value=_gen_title,
                                            key=f"dlg_mp_title_{i}", label_visibility="collapsed")

                    # ── Giá bán $ + Ảnh listing (Eldorado) ──
                    _show_push = _HAS_ELDORADO and eld_client and eld_client.logged_in
                    if _show_push:
                        if "manual_img_bytes" not in st.session_state:
                            st.session_state.manual_img_bytes = {}
                        _saved_key = f"dlg_mp_img_{i}"
                        _saved = st.session_state.manual_img_bytes.get(_saved_key)

                        _img_col, _price_col = st.columns([2, 1])
                        if _saved:
                            _img_col.image(_saved["bytes"], width=240)
                            _img_col.caption(f"Ảnh đã lưu: {_saved['name']}")
                            if _img_col.button("Xóa ảnh", key=f"dlg_mp_rm_img_{i}",
                                               use_container_width=True):
                                del st.session_state.manual_img_bytes[_saved_key]
                                st.rerun()
                            r_img = _FakeUploadedFile(_saved["bytes"], _saved["name"], _saved["mime"])
                        else:
                            up_img = _img_col.file_uploader(
                                f"Ảnh listing cho {pet_name}",
                                type=["png", "jpg", "jpeg", "webp"],
                                key=f"dlg_mp_img_{i}", label_visibility="collapsed",
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

                        r_price_raw = _price_col.text_input(
                            "Giá bán ($)", value="", placeholder="$0.50",
                            key=f"dlg_mp_price_{i}", label_visibility="collapsed",
                        )
                    else:
                        r_img = None
                        r_price_raw = ""

                # ── Validate từng dòng ──
                r_ms = parse_usd(r_ms_raw)
                r_cost = parse_vnd(r_cost_raw)
                r_price = 0.0
                if r_price_raw.strip():
                    try:
                        r_price = float(r_price_raw)
                    except (ValueError, TypeError):
                        r_price = 0.0
                err_row = []
                if r_keep:
                    if not r_name or r_name == "None": err_row.append("Tên Pet")
                    if r_ms <= 0: err_row.append("M/s")
                    if not r_ns.strip(): err_row.append("NameStock")
                    if r_cost <= 0: err_row.append("Giá nhập")
                    if _show_push:
                        if not r_img: err_row.append("ảnh listing")
                        if not r_price_raw.strip(): err_row.append("giá bán $")
                        elif r_price < 0.50: err_row.append("giá bán tối thiểu $0.50")
                if r_keep and err_row:
                    st.info(f"! Thiếu thông tin: {', '.join(err_row)}")
                    all_valid = False

                edited_rows.append({
                    "Tên Pet":   r_name,
                    "Mutation":  r_mut,
                    "M/s":       r_ms,
                    "Số Trait":  r_trait,
                    "NameStock": r_ns,
                    "Giá Nhập":  r_cost,
                    "_keep":     r_keep,
                    "_valid":    r_keep and len(err_row) == 0,
                    "_title":    r_title,
                    "_price":    r_price,
                    "_image":    r_img,
                })

            # ── Huỷ / Lưu ──
            st.markdown("---")
            col_cancel, col_save = st.columns([1, 2])
            with col_cancel:
                if st.button("Huỷ bỏ", use_container_width=True):
                    st.session_state.manual_show_dialog = False
                    st.session_state.manual_img_bytes = {}
                    st.rerun()

            with col_save:
                valid_count = sum(1 for r in edited_rows if r["_valid"])
                save_label = f"Lưu {valid_count} / {len(edited_rows)} mục hợp lệ"
                if st.button(save_label, type="primary", use_container_width=True,
                             disabled=valid_count == 0):
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
                    with st.spinner(f"Đang lưu {saved} mục..."):
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
                            st.session_state.manual_pending = []
                            st.session_state.manual_img_bytes = {}
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
                            st.toast(f"Đã lưu {saved} mục thành công", icon="✅")
                        st.rerun()

        manual_preview_dialog()

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