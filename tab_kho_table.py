import re
import base64
import pandas as pd
import streamlit as st
import streamlit.components.v1 as _cmp

from datetime import datetime, timedelta
from _timezone import now_vn, VN_TZ
from _config import MAIN_SCHEMA
from _database import (
    USE_SUPABASE, sb_delete, load_inventory,
    save_inventory_supabase, supabase_client,
)
from _helpers import (
    fmt_ngay_ton, normalize_df, reindex, generate_auto_title,
    apply_ngay_ton, token_search, _clear_searches, _sv,
)


def render_inventory_table(df):
    # ── BẢNG TỒN KHO ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Tồn Kho Lẻ</div>', unsafe_allow_html=True)

        with st.expander("Xem bảng tồn kho", expanded=True):
            # ── THANH CÔNG CỤ ──
            _tb1, _tb2, _tb3 = st.columns([2, 2.5, 1])
            view_mode = _tb1.radio(
                "Lọc trạng thái",
                ["Đang bán", "Đã bán", "Tất cả"],
                horizontal=True,
                label_visibility="collapsed",
            )
            inv_search = _tb2.text_input(
                "🔍 Tìm kiếm",
                placeholder="STT, tên pet, mutation, title...",
                label_visibility="collapsed",
                key=f"inv_table_search_{_sv()}",
            )

            # ── Quick filter Mutation chips ──
            _all_mutations = sorted(df["Mutation"].astype(str).str.strip().unique().tolist())
            _all_mutations = [m for m in _all_mutations if m not in ("", "nan")]
            _mut_options = ["Tất cả"] + _all_mutations
            _mut_sel = st.radio(
                "Lọc Mutation",
                _mut_options,
                horizontal=True,
                label_visibility="collapsed",
                key="inv_mut_filter",
            )

            if view_mode == "Đang bán":
                view_df = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
                show_all = False
            elif view_mode == "Đã bán":
                view_df = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
                show_all = True
            else:
                view_df = df.copy()
                show_all = True

            # Áp dụng quick filter mutation
            if _mut_sel != "Tất cả":
                view_df = view_df[view_df["Mutation"].astype(str).str.strip() == _mut_sel]

            # Áp dụng tìm kiếm text – token-based: mỗi từ phải xuất hiện ở ít nhất 1 cột
            if inv_search.strip():
                # Chuẩn hoá: bỏ dấu '-', tách thành tokens
                _tokens = re.split(r'[\s\-]+', inv_search.strip().lower())
                _tokens = [t for t in _tokens if t]
                _search_cols = ["STT","Tên Pet","Mutation","NameStock","Số Trait","Auto Title","Place"]
                _haystack = view_df[[c for c in _search_cols if c in view_df.columns]] \
                    .astype(str).apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                _combined = _haystack.apply(lambda row: ' '.join(row), axis=1)
                mask = pd.Series([True] * len(view_df), index=view_df.index)
                for _tok in _tokens:
                    mask &= _combined.str.contains(_tok, regex=False, na=False)
                view_df = view_df[mask]

            # Thêm cột hiển thị "Tồn" (text) từ Ngày Tồn (float ngày)
            view_df = view_df.copy()
            view_df["Tồn"] = view_df["Ngày Tồn"].apply(fmt_ngay_ton)

            display_cols = ["id","STT","Tên Pet","M/s","Mutation","Số Trait","NameStock",
                            "Giá Nhập","Giá Bán","Lợi Nhuận","Ngày Nhập","Ngày Bán",
                            "Tồn","Trạng Thái","Auto Title","Place"]
            view_cols = [c for c in display_cols if c in view_df.columns]

            # Nút xuất CSV + đếm kết quả
            _tb3.metric("Tổng sổ", len(view_df))
            if not view_df.empty:
                csv_inv = view_df[view_cols].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    "⬇️ Xuất CSV",
                    data=csv_inv,
                    file_name=f"kho_le_{now_vn().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_inv_csv",
                )

            if not view_df.empty:
                # Khi search hoặc khi lọc mutation: coi như đang filter → dùng safe merge-back
                _is_searching = bool(inv_search.strip()) or (_mut_sel != "Tất cả")
                # Show editable table
                before_edit = view_df[view_cols].copy()
                edited = st.data_editor(
                    before_edit,
                    key=f"editor_inventory_{st.session_state.get('editor_inv_ver', 0)}",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed" if _is_searching else "dynamic",
                    disabled=["id"],
                    column_config={
                        "id": st.column_config.NumberColumn("Database ID", help="Mã định danh gốc từ Supabase (Read-only)", format="%d"),
                        "Tồn": st.column_config.TextColumn("Tồn", disabled=True),
                        "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                        "Giá Nhập": st.column_config.NumberColumn("Giá Nhập (VNĐ)", format="%d"),
                        "Giá Bán": st.column_config.NumberColumn("Giá Bán ($)"),
                        "Lợi Nhuận": st.column_config.NumberColumn("Lợi Nhuận (VNĐ)", format="%d"),
                    },
                )

                # Chỉ reindex STT khi xem "Tất cả" + không tìm kiếm → tránh STT conflict khi merge-back
                _can_reindex = (view_mode == "Tất cả") and not _is_searching
                after_reindexed  = reindex(normalize_df(edited.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols}), "STT") if _can_reindex \
                    else normalize_df(edited.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols})
                before_reindexed = reindex(normalize_df(before_edit.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols}), "STT") if _can_reindex \
                    else normalize_df(before_edit.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols})

                # So sánh TRƯỚC khi regen auto title — tránh vòng lặp lưu vô hạn
                # do format cũ "[1]" vs mới "[1 Trait]" khiến always-dirty
                _compare_cols = [c for c in after_reindexed.columns if c != "Auto Title"]
                _user_changed = not after_reindexed[_compare_cols].astype(str).equals(
                    before_reindexed[[c for c in _compare_cols if c in before_reindexed.columns]].astype(str)
                )

                # Regenerate auto titles (chỉ để ghi, không dùng để so sánh)
                has_title_col = "Auto Title" in after_reindexed.columns
                if has_title_col:
                    def _regen_title(r):
                        return generate_auto_title(
                            r.get("Tên Pet",""), r.get("Mutation","Normal"),
                            r.get("Số Trait","None"),
                            float(pd.to_numeric(r.get("M/s", 0), errors="coerce") or 0),
                            r.get("NameStock",""),
                        )
                    after_reindexed["Auto Title"] = after_reindexed.apply(_regen_title, axis=1)

                if _user_changed:
                    # Merge changes back into full df
                    full_df = st.session_state.df.copy()

                    # Khôi phục time_nhap / time_ban bị mất do view_cols không hiển thị chúng
                    if "id" in after_reindexed.columns and not full_df.empty:
                        _ts_src = full_df[["id", "time_nhap", "time_ban"]].copy()
                        _ts_src["_id_int"] = pd.to_numeric(_ts_src["id"], errors="coerce").fillna(0).astype(int)
                        _ar = after_reindexed.copy()
                        _ar["_id_int"] = pd.to_numeric(_ar["id"], errors="coerce").fillna(0).astype(int)
                        _ar = _ar.merge(_ts_src[["_id_int", "time_nhap", "time_ban"]], on="_id_int", how="left").drop(columns=["_id_int"])
                        after_reindexed = _ar

                    if _is_searching:
                        # Khi search: chỉ cập nhật các dòng hiển thị, giữ nguyên dòng ẩn
                        # Normalize to int trước khi so sánh tránh "1" vs "1.0" dtype mismatch (data_editor trả về float64)
                        visible_ids = set(pd.to_numeric(after_reindexed["id"], errors="coerce").fillna(0).astype(int).astype(str).tolist()) if "id" in after_reindexed.columns else set()
                        hidden_rows = full_df[~pd.to_numeric(full_df["id"], errors="coerce").fillna(0).astype(int).astype(str).isin(visible_ids)]
                        merged = pd.concat([after_reindexed, hidden_rows], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))
                    elif view_mode == "Tất cả":
                        full_updated = apply_ngay_ton(normalize_df(after_reindexed, MAIN_SCHEMA))
                    elif view_mode == "Đã bán":
                        # Chỉ cập nhật hàng đã bán, giữ nguyên hàng còn hàng
                        con_hang_df = full_df[full_df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
                        merged = pd.concat([con_hang_df, after_reindexed], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))
                    else:
                        # Chỉ cập nhật hàng còn hàng, giữ nguyên hàng đã bán
                        sold_df = full_df[full_df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
                        merged = pd.concat([after_reindexed, sold_df], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))

                    save_inventory_supabase(full_updated, st.session_state.df)
                    # ── Luôn reload từ Supabase để lấy ID thật, tránh id=0 gây duplicate ──
                    if USE_SUPABASE:
                        st.cache_data.clear()
                        st.session_state.df = apply_ngay_ton(load_inventory())
                    else:
                        st.session_state.df = full_updated
                    df = st.session_state.df
                    # Bump version key để reset widget state, tránh vòng lặp lưu vô hạn
                    st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                    _clear_searches()
            else:
                st.info("Không có dữ liệu để hiển thị.")

        # ── XÓA DÒNG KHO LẺ ──
        if USE_SUPABASE and not df.empty:
            with st.expander("🗑️ Xóa dòng khỏi Kho Lẻ", expanded=False):
                def _safe_int(v, default=0):
                    try: return int(float(v)) if v not in (None, "", "nan", "None") else default
                    except: return default
                _del_rows = df[["id","STT","Tên Pet","Mutation","NameStock"]].copy()
                _del_labels = [
                    f"ID {_safe_int(r['id'])} | STT {_safe_int(r['STT'])} | {r['Tên Pet']} {r['Mutation']} – {r['NameStock']}"
                    for _, r in _del_rows.iterrows()
                ]
                _del_id_map = {lbl: _safe_int(r["id"]) for lbl, (_, r) in zip(_del_labels, _del_rows.iterrows())}
                _sel_del = st.multiselect(
                    "Chọn dòng cần xóa",
                    options=_del_labels,
                    placeholder="Tìm và chọn...",
                    key="inv_del_multiselect",
                )
                if _sel_del:
                    st.warning(f"⚠️ Sẽ xóa vĩnh viễn **{len(_sel_del)} dòng** khỏi Supabase. Không thể hoàn tác!")
                    if st.button("🗑️ Xác nhận Xóa", key="inv_del_confirm", type="primary", use_container_width=True):
                        for _lbl in _sel_del:
                            sb_delete("inventory", "id", _del_id_map[_lbl])
                        st.cache_data.clear()
                        st.session_state.df = apply_ngay_ton(load_inventory())
                        st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                        st.toast(f"Đã xóa {len(_sel_del)} dòng.", icon="🗑️")
                        st.rerun()

        # ── COPY AUTO TITLE NHANH ──
        _shop_desc = st.session_state.get("_shop_desc", "")
        _b64_desc = base64.b64encode(_shop_desc.encode("utf-8")).decode("ascii") if _shop_desc else ""

        _copy_src = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        if not _copy_src.empty:
            with st.expander("Sao chép Auto Title", expanded=False):
                _cp_q = st.text_input("🔍 Tìm pet", placeholder="Tên, STT, mutation...", key=f"copy_title_search_{_sv()}", label_visibility="collapsed")

                _cp_base = _copy_src.copy()

                if _cp_q.strip():
                    # Khi search: tìm trong toàn bộ còn hàng
                    _cp_toks = re.split(r'[\s\-]+', _cp_q.strip().lower())
                    _cp_toks = [t for t in _cp_toks if t]
                    _cp_hay = _cp_base[["Tên Pet","Mutation","Auto Title","NameStock","STT"]].astype(str) \
                        .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                    _cp_combined = _cp_hay.apply(lambda r: ' '.join(r), axis=1)
                    _cp_mask = pd.Series([True] * len(_cp_base), index=_cp_base.index)
                    for _t in _cp_toks:
                        _cp_mask &= _cp_combined.str.contains(_t, regex=False, na=False)
                    _cp_filtered = _cp_base[_cp_mask]
                    _cp_mode_label = f"{len(_cp_filtered)} kết quả tìm kiếm"
                else:
                    # Mặc định: chỉ pet nhập trong 1 giờ qua
                    _now_vn = now_vn()
                    _cutoff = _now_vn - timedelta(hours=1)

                    def _is_recent(ts_str):
                        if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                            return False
                        try:
                            dt = datetime.fromisoformat(str(ts_str))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=VN_TZ)
                            return dt >= _cutoff
                        except Exception:
                            return False

                    _recent_mask = _cp_base["time_nhap"].apply(_is_recent)
                    _cp_filtered = _cp_base[_recent_mask].sort_values("STT", ascending=False)
                    _cp_mode_label = f"{len(_cp_filtered)} pet nhập trong 1 giờ qua"

                if _cp_filtered.empty:
                    if _cp_q.strip():
                        st.info("Không tìm thấy pet phù hợp.")
                    else:
                        st.caption("Chưa có pet nào được nhập trong 1 giờ qua. Dùng ô tìm kiếm để tìm bất kỳ pet nào.")
                else:
                    st.caption(f"📌 {_cp_mode_label}")
                    for _ci, (_, _crow) in enumerate(_cp_filtered.iterrows()):
                        # Luôn regen để đảm bảo định dạng mới (Trait/Traits) dù DB chưa cập nhật
                        _display_title = generate_auto_title(
                            _crow.get("Tên Pet", ""), _crow.get("Mutation", "Normal"),
                            _crow.get("Số Trait", "None"),
                            float(pd.to_numeric(_crow.get("M/s", 0), errors="coerce") or 0),
                            _crow.get("NameStock", ""),
                        )
                        st.markdown(
                            f'<div style="font-size:0.78rem;color:#737373;margin-top:0.5rem;">'
                            f'STT <b style="color:#fb923c">{int(_crow["STT"])}</b> · '
                            f'{_crow["Tên Pet"]} · <span style="color:#fb923c">{_crow["Mutation"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        _ct1, _ct2 = st.columns([4, 1])
                        with _ct1:
                            st.code(_display_title, language=None)
                        with _ct2:
                            if _b64_desc:
                                _bid = "cpShop" + str(_ci)
                                _cmp.html(
                                    '<button id="' + _bid + '" style="width:100%;padding:8px 4px;border:none;'
                                    'border-radius:8px;cursor:pointer;background:linear-gradient(135deg,#f97316,#fb923c);'
                                    'color:#0a0a0f;font-weight:600;font-size:11px;">&#x1F47B; M&#xF4; t&#x1EA3;</button>'
                                    '<script>(function(){'
                                    'var btn=document.getElementById("' + _bid + '");'
                                    'var b64="' + _b64_desc + '";'
                                    'btn.addEventListener("click",function(){'
                                    'var b=this;var bytes=Uint8Array.from(atob(b64),function(c){return c.charCodeAt(0)});'
                                    'var txt=new TextDecoder("utf-8").decode(bytes);'
                                    'navigator.clipboard.writeText(txt)'
                                    '.then(function(){b.innerHTML="&#x2705;";'
                                    'setTimeout(function(){b.innerHTML="&#x1F47B; M&#xF4; t&#x1EA3;";},1500);})'
                                    '.catch(function(){b.innerHTML="&#x274C;";});'
                                    '});})();</script>',
                                    height=45,
                                )
