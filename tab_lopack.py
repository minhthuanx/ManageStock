import re
import pandas as pd
import streamlit as st

from _timezone import now_vn, now_str
from _config import (
    BULK_SCHEMA, HISTORY_SCHEMA, MUTATION_OPTIONS, EXCHANGE_RATE,
)
from _database import (
    USE_SUPABASE, to_db, sb_insert, sb_insert_returning, sb_update, sb_delete,
    load_bulk, load_bulk_history, save_bulk_supabase,
)
from _helpers import (
    parse_vnd, parse_usd, fmt_vnd, fmt_short, get_name_options,
    append_row, generate_auto_title, next_id, normalize_df,
    _clear_searches, _sv,
)


def render_tab_lopack(df, bulk_df, bulk_history, pet_db, ns_db, trait_db):
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Quản Lý Lô (Pack)</div>', unsafe_allow_html=True)

        pack_in, pack_sell = st.columns([1.15, 1], gap="medium")

        with pack_in:
            with st.container(border=True):
                st.markdown("**Nhập Lô Mới**")
                with st.form("form_nhap_lo2", clear_on_submit=True):
                    b_pet2 = st.selectbox("Tên Pet", get_name_options(pet_db), key="bp1t2")
                    b1t, b2t, b3t = st.columns(3)
                    b_qty2    = b1t.number_input("Số lượng", min_value=1, max_value=999, value=10, key="bqt2")
                    b_ms_raw2 = b2t.text_input("M/s", placeholder="975", key="bp2t2")
                    b_mut2    = b3t.selectbox("Mutation", MUTATION_OPTIONS, key="bp3t2")
                    b_ns2     = st.selectbox("NameStock", [""]+get_name_options(ns_db,""), key="bp5t2")
                    b_cost_raw2 = st.text_input("Tổng vốn nhập (₫)", placeholder="2.000.000", key="bp4t2")
                    pack_ok2  = st.form_submit_button("Lưu Lô Hàng", type="primary", use_container_width=True)
                if pack_ok2:
                    b_cost2 = parse_vnd(b_cost_raw2)
                    b_ms2   = parse_usd(b_ms_raw2)
                    errs2 = []
                    if b_pet2 == "None":  errs2.append("Chọn tên Pet")
                    if b_ms2 <= 0:        errs2.append("M/s phải > 0")
                    if b_cost2 <= 0:      errs2.append("Giá nhập phải > 0")
                    if not b_ns2.strip(): errs2.append("Chọn NameStock")
                    if errs2:
                        for e in errs2: st.error(f"{e}")
                    else:
                        # Guard chống double-submit lô pack
                        lo_submit_key = f"nhap_lo_{b_pet2}_{b_qty2}_{b_cost2}_{b_ns2}"
                        if st.session_state.get("last_lo_key") == lo_submit_key:
                            st.warning("Lô này đã được lưu. Tải lại trang nếu cần.")
                            st.stop()
                        bid2 = next_id(bulk_df, "ID")
                        auto_title2 = generate_auto_title(b_pet2, b_mut2, "None", b_ms2, b_ns2)
                        row2 = {
                            "ID": bid2,
                            "Tên Lô": f"Pack {b_pet2} (x{int(b_qty2)})",
                            "Số Lượng Gốc": int(b_qty2),
                            "Còn Lại": int(b_qty2),
                            "Ngày Nhập": now_str(),
                            "Giá Nhập Tổng": b_cost2,
                            "Doanh Thu Tích Lũy": 0.0,
                            "Lợi Nhuận": -b_cost2,
                            "Trạng Thái": "Available",
                            "Auto Title": auto_title2,
                            "NameStock": b_ns2,
                        }
                        if USE_SUPABASE:
                            db_row2 = to_db(row2)
                            # Giữ nguyên id để Supabase dùng (không pop),
                            # nhất quán với save_bulk_supabase dùng explicit id
                            ok2 = sb_insert("bulk_inventory", db_row2)
                            if not ok2:
                                st.error("❌ Không thể lưu lô hàng. Vui lòng thử lại.")
                                st.stop()
                            st.cache_data.clear()
                        # Append vào session state ngay để hiển thị tức thì sau rerun
                        bulk_df = append_row(bulk_df, row2, BULK_SCHEMA)
                        st.session_state.bulk_df = bulk_df
                        # Guard key chỉ set sau khi lưu thành công
                        st.session_state.last_lo_key = lo_submit_key
                        st.toast("Lô hàng đã được lưu", icon="✅")
                        st.rerun()

        with pack_sell:
            with st.container(border=True):
                st.markdown("**Bán Từ Lô**")

                # ── UNDO banner ──
                if st.session_state.get("last_sale_undo", {}).get("type") == "bulk":
                    _undo_bk = st.session_state["last_sale_undo"]
                    _ub1, _ub2 = st.columns([3, 1])
                    _ub1.info(f"↩️ Vừa bán: **{_undo_bk['label']}**  —  Bán nhầm? Hoàn tác ngay!")
                    if _ub2.button("↩️ Hoàn tác", key="undo_bulk_btn", use_container_width=True):
                        _ud_bk = st.session_state.pop("last_sale_undo")
                        # Restore bulk_inventory row
                        if USE_SUPABASE:
                            sb_update("bulk_inventory", {
                                "con_lai":            _ud_bk["old_con_lai"],
                                "doanh_thu_tich_luy": _ud_bk["old_dt"],
                                "loi_nhuan":          _ud_bk["old_loi_nhuan"],
                                "trang_thai":         _ud_bk["old_trang_thai"],
                            }, "id", _ud_bk["bulk_id"])
                            # Delete the history record that was just inserted
                            if _ud_bk.get("hist_db_id"):
                                sb_delete("bulk_history", "id", _ud_bk["hist_db_id"])
                            st.cache_data.clear()
                            st.session_state.bulk_df      = load_bulk()
                            st.session_state.bulk_history = load_bulk_history()
                        else:
                            # Restore local state directly
                            _bdf3 = st.session_state.bulk_df.copy()
                            _idx3 = _bdf3.index[_bdf3["ID"] == _ud_bk["bulk_id"]]
                            if len(_idx3):
                                _bdf3.at[_idx3[0], "Còn Lại"]            = _ud_bk["old_con_lai"]
                                _bdf3.at[_idx3[0], "Doanh Thu Tích Lũy"] = _ud_bk["old_dt"]
                                _bdf3.at[_idx3[0], "Lợi Nhuận"]          = _ud_bk["old_loi_nhuan"]
                                _bdf3.at[_idx3[0], "Trạng Thái"]         = _ud_bk["old_trang_thai"]
                                st.session_state.bulk_df = _bdf3
                        st.toast("Đã hoàn tác giao dịch lô", icon="↩️")
                        st.rerun()

                avail2 = bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"]
                if not avail2.empty:
                    _bid_map = {int(r["ID"]): r for _, r in avail2.iterrows()}
                    def _bulk_fmt(bid):
                        r = _bid_map[bid]
                        auto_t = str(r.get("Auto Title", "") or "")
                        # Lấy phần trước boilerplate "🌸Cheapest..."
                        short = auto_t.split("🌸Cheapest")[0].lstrip("🌸").strip()
                        if not short:
                            short = str(r.get("Tên Lô", ""))
                        ns = str(r.get("NameStock", "") or "").strip()
                        con_lai = int(float(r["Còn Lại"]))
                        gia_tong = float(r["Giá Nhập Tổng"])
                        orig = max(float(r["Số Lượng Gốc"]), 1)
                        don_gia = gia_tong / orig
                        ns_part = f" · {ns}" if ns else ""
                        return f"#{bid}  {short}{ns_part}  ·  còn {con_lai}  ·  ~{fmt_short(don_gia)}/con"
                    sel_b2 = st.selectbox(
                        "Chọn lô", list(_bid_map.keys()),
                        format_func=_bulk_fmt,
                        label_visibility="collapsed", key="sel_b2",
                    )
                    target_id2 = sel_b2
                    target2 = avail2[avail2["ID"]==target_id2].iloc[0]
                    # ── Hiển thị đầy đủ Auto Title để copy ──
                    _at_full = str(target2.get("Auto Title", "") or "")
                    if _at_full:
                        st.code(_at_full, language="text")
                    _don_gia2 = float(target2["Giá Nhập Tổng"]) / max(float(target2["Số Lượng Gốc"]), 1)
                    _ngay_nhap2 = str(target2.get("Ngày Nhập", ""))[:10]
                    st.caption(
                        f"📦 Còn: **{int(target2['Còn Lại'])}** / {int(float(target2['Số Lượng Gốc']))} con"
                        f" · Vốn tổng: **{fmt_vnd(float(target2['Giá Nhập Tổng']))}**"
                        f" · Giá/con: **{fmt_vnd(_don_gia2)}**"
                        f" · Nhập: {_ngay_nhap2}"
                    )

                    with st.form(f"form_ban_lo2_{_sv()}", clear_on_submit=False):
                        s1t, s2t = st.columns(2)
                        s_qty2     = s1t.number_input("Số lượng", min_value=1, max_value=int(target2["Còn Lại"]), key=f"sqty2_{_sv()}")
                        s_prc_raw2 = s2t.text_input("Đơn giá ($/unit)", placeholder="3.5", key=f"sprc2_{_sv()}")
                        sell_ok2   = st.form_submit_button("Xác Nhận Giao Dịch", type="primary", use_container_width=True)

                    # ── Step 1: save pending on first click ──
                    if sell_ok2:
                        s_prc2 = parse_usd(s_prc_raw2)
                        if s_prc2 <= 0:
                            st.error("Đơn giá phải lớn hơn 0")
                        else:
                            _idx2_pre = bulk_df[bulk_df["ID"]==target2["ID"]].index[0]
                            st.session_state["pending_bulk_sale"] = {
                                "bulk_id":       int(target2["ID"]),
                                "ten_lo":        str(target2["Tên Lô"]),
                                "s_qty":         s_qty2,
                                "s_prc":         s_prc2,
                                "old_con_lai":   int(float(bulk_df.at[_idx2_pre, "Còn Lại"])),
                                "old_dt":        float(bulk_df.at[_idx2_pre, "Doanh Thu Tích Lũy"]),
                                "old_loi_nhuan": float(bulk_df.at[_idx2_pre, "Lợi Nhuận"]),
                                "old_trang_thai":str(bulk_df.at[_idx2_pre, "Trạng Thái"]),
                                "so_luong_goc":  float(target2["Số Lượng Gốc"]),
                                "gia_nhap_tong": float(target2["Giá Nhập Tổng"]),
                            }
                            st.rerun()

                    # ── Step 2: confirmation block ──
                    _pnd_bulk = st.session_state.get("pending_bulk_sale")
                    if _pnd_bulk and _pnd_bulk["bulk_id"] == int(target2["ID"]):
                        _rev_bk = _pnd_bulk["s_qty"] * _pnd_bulk["s_prc"] * EXCHANGE_RATE
                        _base_u = _pnd_bulk["gia_nhap_tong"] / max(_pnd_bulk["so_luong_goc"], 1)
                        _ln_bk  = _rev_bk - (_base_u * _pnd_bulk["s_qty"])
                        st.warning(
                            f"⚠️ **Xác nhận bán** · {_pnd_bulk['ten_lo']}\n\n"
                            f"Số lượng: **{_pnd_bulk['s_qty']}** @ **${_pnd_bulk['s_prc']}/unit** "
                            f"→ {fmt_vnd(_rev_bk)} · LN giao dịch: **{fmt_vnd(_ln_bk)}**"
                        )
                        _bf1, _bf2 = st.columns(2)
                        _do_confirm_bk = _bf1.button("✅ Xác nhận bán", key="confirm_sell_bulk", type="primary", use_container_width=True)
                        _do_cancel_bk  = _bf2.button("❌ Hủy", key="cancel_sell_bulk", use_container_width=True)

                        if _do_cancel_bk:
                            st.session_state.pop("pending_bulk_sale", None)
                            st.rerun()

                        if _do_confirm_bk:
                            _pnd_b = st.session_state.pop("pending_bulk_sale")
                            _idx2 = bulk_df[bulk_df["ID"]==_pnd_b["bulk_id"]].index[0]
                            _rev_vnd2 = _pnd_b["s_qty"] * _pnd_b["s_prc"] * EXCHANGE_RATE
                            _new_con_lai2   = max(0.0, float(bulk_df.at[_idx2,"Còn Lại"]) - float(_pnd_b["s_qty"]))
                            _new_dt2        = float(bulk_df.at[_idx2,"Doanh Thu Tích Lũy"]) + _rev_vnd2
                            _new_loi_nhuan2 = _new_dt2 - float(bulk_df.at[_idx2,"Giá Nhập Tổng"])
                            _new_status2    = "Sold Out" if _new_con_lai2 <= 0 else "Available"

                            bulk_df.at[_idx2,"Còn Lại"]            = _new_con_lai2
                            bulk_df.at[_idx2,"Doanh Thu Tích Lũy"] = _new_dt2
                            bulk_df.at[_idx2,"Lợi Nhuận"]          = _new_loi_nhuan2
                            bulk_df.at[_idx2,"Trạng Thái"]         = _new_status2

                            _base_unit2 = _pnd_b["gia_nhap_tong"] / max(_pnd_b["so_luong_goc"], 1)
                            _hist_row2 = {
                                "Ngày Bán":            now_str(),
                                "Tên Lô":              _pnd_b["ten_lo"],
                                "Số Lượng Bán":        _pnd_b["s_qty"],
                                "Lợi Nhuận Giao Dịch": _rev_vnd2 - (_base_unit2 * _pnd_b["s_qty"]),
                                "Doanh Thu Giao Dịch": _rev_vnd2,
                            }
                            bulk_history = append_row(bulk_history, _hist_row2, HISTORY_SCHEMA)
                            st.session_state.bulk_df      = bulk_df
                            st.session_state.bulk_history = bulk_history

                            _hist_db_id = None
                            _write_ok = True
                            if USE_SUPABASE:
                                _inserted = sb_insert_returning("bulk_history", to_db(_hist_row2))
                                _hist_db_id = _inserted.get("id") if _inserted else None
                                _write_ok2 = sb_update("bulk_inventory", {
                                    "con_lai":            int(_new_con_lai2),
                                    "doanh_thu_tich_luy": _new_dt2,
                                    "loi_nhuan":          _new_loi_nhuan2,
                                    "trang_thai":         _new_status2,
                                }, "id", _pnd_b["bulk_id"])
                                _write_ok = bool(_inserted) and _write_ok2
                                if _write_ok:
                                    load_bulk.clear()          # chỉ xóa 2 cache cần thiết
                                    load_bulk_history.clear()
                                    st.session_state.bulk_df      = load_bulk()
                                    st.session_state.bulk_history = load_bulk_history()
                                else:
                                    st.session_state.last_ban_lo_key = None

                            if _write_ok:
                                st.session_state["last_sale_undo"] = {
                                    "type":          "bulk",
                                    "label":         f"{_pnd_b['ten_lo']} x{_pnd_b['s_qty']} @ ${_pnd_b['s_prc']}",
                                    "bulk_id":       _pnd_b["bulk_id"],
                                    "hist_db_id":    _hist_db_id,
                                    "old_con_lai":   _pnd_b["old_con_lai"],
                                    "old_dt":        _pnd_b["old_dt"],
                                    "old_loi_nhuan": _pnd_b["old_loi_nhuan"],
                                    "old_trang_thai":_pnd_b["old_trang_thai"],
                                }
                                st.toast("✅ Giao dịch hoàn tất · Nhấn Hoàn Tác nếu bán nhầm", icon="✅")
                                _clear_searches()  # reset form key → xóa trắng giá bán
                                st.rerun()
                            else:
                                st.error("Ghi dữ liệu thất bại, vui lòng thử lại.")
                else:
                    st.info("Hiện không có lô hàng khả dụng.")

        st.markdown("---")
        st.markdown("**Danh Sách Lô Hàng**")
        bulk_cols_display2 = ["ID","Tên Lô","NameStock","Số Lượng Gốc","Còn Lại","Ngày Nhập",
                              "Giá Nhập Tổng","Doanh Thu Tích Lũy","Lợi Nhuận","Trạng Thái","Auto Title"]

        # ── THANH CÔNG CỤ LÔ PACK ──
        _bk1, _bk2, _bk3 = st.columns([2, 2, 1])
        bulk_status_filter = _bk1.radio(
            "Lọc lô",
            ["Available", "Sold Out", "Tất cả"],
            horizontal=True,
            label_visibility="collapsed",
            key="bulk_status_radio",
        )
        bulk_search = _bk2.text_input(
            "Tìm kiếm",
            placeholder="Tên lô, auto title...",
            label_visibility="collapsed",
            key=f"bulk_table_search_{_sv()}",
        )

        view_bulk_base = bulk_df[[c for c in bulk_cols_display2 if c in bulk_df.columns]].copy()
        if bulk_status_filter == "Available":
            view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Available"]
        elif bulk_status_filter == "Sold Out":
            view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Sold Out"]
        if bulk_search.strip():
            _tokens_bk = re.split(r'[\s\-]+', bulk_search.strip().lower())
            _tokens_bk = [t for t in _tokens_bk if t]
            _bk_cols = ["Tên Lô","NameStock","Auto Title"]
            _bk_haystack = view_bulk_base[[c for c in _bk_cols if c in view_bulk_base.columns]] \
                .astype(str).apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
            _bk_combined = _bk_haystack.apply(lambda row: ' '.join(row), axis=1)
            bk_mask = pd.Series([True] * len(view_bulk_base), index=view_bulk_base.index)
            for _tok in _tokens_bk:
                bk_mask &= _bk_combined.str.contains(_tok, regex=False, na=False)
            view_bulk_base = view_bulk_base[bk_mask]

        _bk3.metric("Tổng số", len(view_bulk_base))
        if not view_bulk_base.empty:
            csv_bulk = view_bulk_base.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "⬇️ Xuất CSV",
                data=csv_bulk,
                file_name=f"lo_pack_{now_vn().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_bulk_csv",
            )

        view_bulk2 = view_bulk_base
        _is_bulk_searching = bool(bulk_search.strip()) or bulk_status_filter != "Tất cả"
        if not view_bulk2.empty:
            before_bulk2x = view_bulk2.copy()
            edited_bulk2 = st.data_editor(
                before_bulk2x, key=f"editor_bulk2_{st.session_state.get('editor_bulk_ver', 0)}",
                use_container_width=True, hide_index=True,
                num_rows="fixed" if _is_bulk_searching else "dynamic",
                disabled=["ID"],
                column_config={
                    "NameStock": st.column_config.TextColumn("NameStock", width="small"),
                    "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                    "Giá Nhập Tổng": st.column_config.NumberColumn("Vốn nhập (VNĐ)", format="%d"),
                    "Doanh Thu Tích Lũy": st.column_config.NumberColumn("Doanh thu (VNĐ)", format="%d"),
                    "Lợi Nhuận": st.column_config.NumberColumn("Lợi nhuận (VNĐ)", format="%d"),
                },
            )

            # CẬP NHẬT: Không được reindex vào cột ID để không phá hỏng Primary Key của Supabase
            schema_bulk_view = {c: BULK_SCHEMA.get(c,"") for c in bulk_cols_display2 if c in bulk_df.columns}
            ab2  = normalize_df(edited_bulk2, schema_bulk_view)
            bb2  = normalize_df(before_bulk2x, schema_bulk_view)

            if not ab2.astype(str).equals(bb2.astype(str)):
                # Merge phần đã chỉnh sửa với phần bị ẩn (do filter/search) để không mất dữ liệu
                hidden_rows = bulk_df[[c for c in bulk_cols_display2 if c in bulk_df.columns]].copy()
                # Normalize to int trước khi so sánh tránh "1" vs "1.0" dtype mismatch (data_editor trả về float64)
                visible_ids = set(pd.to_numeric(ab2["ID"], errors="coerce").fillna(0).astype(int).astype(str).tolist()) if "ID" in ab2.columns else set()
                hidden_rows = hidden_rows[~pd.to_numeric(hidden_rows["ID"], errors="coerce").fillna(0).astype(int).astype(str).isin(visible_ids)]
                full_ab2 = normalize_df(pd.concat([ab2, hidden_rows], ignore_index=True), schema_bulk_view)

                save_bulk_supabase(full_ab2, st.session_state.bulk_df)
                # ── Luôn reload từ Supabase để lấy ID thật, tránh id=0 gây duplicate ──
                if USE_SUPABASE:
                    st.cache_data.clear()
                    st.session_state.bulk_df = load_bulk()
                else:
                    st.session_state.bulk_df = normalize_df(full_ab2, BULK_SCHEMA)
                # Bump version key để reset widget state
                st.session_state.editor_bulk_ver = st.session_state.get("editor_bulk_ver", 0) + 1
                st.toast("Đã lưu thay đổi", icon="✅")
                st.rerun()
        else:
            st.info("Chưa có lô hàng nào.")

        # ── XÓA DÒNG LÔ PACK ──
        if USE_SUPABASE and not bulk_df.empty:
            with st.expander("🗑️ Xóa dòng khỏi Lô Pack", expanded=False):
                def _safe_int_bk(v, default=0):
                    try: return int(float(v)) if v not in (None, "", "nan", "None") else default
                    except: return default
                _del_bk_rows = bulk_df[[c for c in ["ID","Tên Lô","NameStock"] if c in bulk_df.columns]].copy()
                _del_bk_labels = [
                    f"ID {_safe_int_bk(r.get('ID',0))} | {r.get('Tên Lô','')} – {r.get('NameStock','')}"
                    for _, r in _del_bk_rows.iterrows()
                ]
                _del_bk_id_map = {lbl: _safe_int_bk(r.get("ID", 0)) for lbl, (_, r) in zip(_del_bk_labels, _del_bk_rows.iterrows())}
                _sel_bk_del = st.multiselect(
                    "Chọn lô cần xóa",
                    options=_del_bk_labels,
                    placeholder="Tìm và chọn...",
                    key="bulk_del_multiselect",
                )
                if _sel_bk_del:
                    st.warning(f"⚠️ Sẽ xóa vĩnh viễn **{len(_sel_bk_del)} lô** khỏi Supabase. Không thể hoàn tác!")
                    if st.button("🗑️ Xác nhận Xóa", key="bulk_del_confirm", type="primary", use_container_width=True):
                        for _lbl in _sel_bk_del:
                            sb_delete("bulk_inventory", "id", _del_bk_id_map[_lbl])
                        st.cache_data.clear()
                        st.session_state.bulk_df = load_bulk()
                        st.session_state.editor_bulk_ver = st.session_state.get("editor_bulk_ver", 0) + 1
                        st.toast(f"Đã xóa {len(_sel_bk_del)} lô.", icon="🗑️")
                        st.rerun()
