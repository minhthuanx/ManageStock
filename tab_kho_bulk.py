import re
import pandas as pd
import streamlit as st

from _timezone import now_vn, now_str, now_iso
from _config import MAIN_SCHEMA, EXCHANGE_RATE
from _database import (
    USE_SUPABASE, sb_insert, sb_insert_returning, sb_update,
    load_inventory, to_db,
)
from _helpers import (
    parse_usd, fmt_vnd, fmt_short, normalize_df, append_row,
    generate_auto_title, next_id, apply_ngay_ton,
    token_search, _clear_searches, _sv,
)
from _database import _load_pinned_resell_from_supabase, _save_pinned_resell_to_supabase


# ══════════════════════════════════════════════════════════════════════════════
# BULK SELL — Bán hàng loạt
# ══════════════════════════════════════════════════════════════════════════════

def render_bulk_sell(df):
    # ── BULK SELL ──
    _bulk_src = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
    if not _bulk_src.empty:
        with st.expander("Giao dịch hàng loạt", expanded=False):
            # Giỏ bán tích lũy — tồn tại qua nhiều lần tìm kiếm
            if "bulk_cart" not in st.session_state:
                st.session_state.bulk_cart = {}  # str(id_or_stt) → row dict

            # ── BƯỚC 1: Tìm & thêm vào giỏ ──
            st.caption("Tìm kiếm · Thêm vào giỏ · Nhập giá · Xác nhận")
            _bs_search = st.text_input(
                "Tìm pet cần bán", placeholder="Tên, mutation, STT...",
                key=f"bulk_sell_search_{_sv()}", label_visibility="collapsed",
            )
            _bs_df = _bulk_src.copy()
            if _bs_search.strip():
                _bs_toks = re.split(r'[\s\-]+', _bs_search.strip().lower())
                _bs_toks = [t for t in _bs_toks if t]
                _bs_hay = _bs_df[["Tên Pet","Mutation","Auto Title","NameStock","STT"]].astype(str) \
                    .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                _bs_combined = _bs_hay.apply(lambda r: ' '.join(r), axis=1)
                _bs_mask = pd.Series([True]*len(_bs_df), index=_bs_df.index)
                for _t in _bs_toks:
                    _bs_mask &= _bs_combined.str.contains(_t, regex=False, na=False)
                _bs_df = _bs_df[_bs_mask]

            if _bs_df.empty and _bs_search.strip():
                st.info("Không tìm thấy pet phù hợp.")
            else:
                _shown_bs = _bs_df.head(15)
                for _, _br in _shown_bs.iterrows():
                    _bid = str(int(float(_br.get("id", 0) or 0))) if int(float(_br.get("id", 0) or 0)) > 0 else f"stt_{int(_br['STT'])}"
                    _in_cart = _bid in st.session_state.bulk_cart
                    _rc1, _rc2 = st.columns([4, 1])
                    _br_ms     = _br.get("M/s", "")
                    _br_ns     = str(_br.get("NameStock", "") or "").strip()
                    _br_trait  = str(_br.get("Số Trait", "") or "").strip()
                    _br_ton    = int(float(_br.get("Ngày Tồn", 0) or 0))
                    _br_ms_str = f" · <b>{_br_ms}M/s</b>" if _br_ms else ""
                    _br_ns_str = f" · <span style='color:#7c6fa0'>{_br_ns}</span>" if _br_ns else ""
                    _br_trait_str = f" · Trait:{_br_trait}" if _br_trait and _br_trait.lower() != "none" else ""
                    _br_ton_str = f" · <span style='color:#f87171'>tồn {_br_ton}d</span>" if _br_ton > 0 else ""
                    _rc1.markdown(
                        f'<div style="font-size:0.82rem;padding:2px 0;">'
                        f'<b style="color:#c084fc">#{int(_br["STT"])}</b> · '
                        f'<b>{_br["Tên Pet"]}</b> · <span style="color:#a78bfa">{_br["Mutation"]}</span>'
                        f'{_br_ms_str}{_br_ns_str}{_br_trait_str}'
                        f' · <span style="color:#9d8fbf">{fmt_vnd(float(_br["Giá Nhập"]))}</span>'
                        f'{_br_ton_str}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if _in_cart:
                        if _rc2.button("✓ Bỏ", key=f"bs_rm_{_bid}", use_container_width=True):
                            del st.session_state.bulk_cart[_bid]
                            st.rerun()
                    else:
                        if _rc2.button("➕", key=f"bs_add_{_bid}", use_container_width=True, type="primary"):
                            st.session_state.bulk_cart[_bid] = _br.to_dict()
                            st.rerun()
                if len(_bs_df) > 15:
                    st.caption(f"Đang hiển thị 15 / {len(_bs_df)} kết quả — thu hẹp tìm kiếm để xem thêm.")

            # ── BƯỚC 2: Giỏ bán ──
            if st.session_state.bulk_cart:
                st.markdown("---")
                _ch1, _ch2 = st.columns([3, 1])
                _ch1.markdown(f"**🛒 Giỏ bán: {len(st.session_state.bulk_cart)} pet**")
                if _ch2.button("🗑️ Xóa giỏ", key="bs_clear_cart", use_container_width=True):
                    st.session_state.bulk_cart = {}
                    st.rerun()

                _cart_rows = []
                for _ck, _cv in st.session_state.bulk_cart.items():
                    _cart_rows.append({
                        "_cart_key":   _ck,
                        "id":          int(float(_cv.get("id", 0) or 0)),
                        "STT":         int(float(_cv.get("STT", 0) or 0)),
                        "Tên Pet":     str(_cv.get("Tên Pet", "")),
                        "Mutation":    str(_cv.get("Mutation", "")),
                        "M/s":         str(_cv.get("M/s", "") or ""),
                        "NameStock":   str(_cv.get("NameStock", "") or ""),
                        "Trait":       str(_cv.get("Số Trait", "") or ""),
                        "Tồn (ngày)":  int(float(_cv.get("Ngày Tồn", 0) or 0)),
                        "Giá Nhập":    float(pd.to_numeric(_cv.get("Giá Nhập", 0), errors="coerce") or 0),
                        "Giá bán ($)": 0.0,
                        "Place":       "",
                    })
                _cart_df = pd.DataFrame(_cart_rows)
                _cart_edited = st.data_editor(
                    _cart_df.drop(columns=["_cart_key", "id", "STT"]),
                    key=f"bulk_cart_editor_{st.session_state.get('editor_inv_ver', 0)}",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    disabled=["Tên Pet", "Mutation", "M/s", "NameStock", "Trait", "Tồn (ngày)", "Giá Nhập"],
                    column_config={
                        "Tên Pet":     st.column_config.TextColumn("Pet", width="medium"),
                        "Mutation":    st.column_config.TextColumn("Mut.", width="small"),
                        "M/s":         st.column_config.TextColumn("M/s", width="small"),
                        "NameStock":   st.column_config.TextColumn("NS", width="small"),
                        "Trait":       st.column_config.TextColumn("Trait", width="small"),
                        "Tồn (ngày)":  st.column_config.NumberColumn("Tồn", format="%d", width="small"),
                        "Giá Nhập":    st.column_config.NumberColumn("Vốn (₫)", format="%d", width="small"),
                        "Giá bán ($)": st.column_config.NumberColumn("Giá ($)", min_value=0.0, step=0.01, format="%.2f", width="small"),
                        "Place":       st.column_config.TextColumn("Place", width="small"),
                    },
                )
                # Gắn lại id/stt từ cart_df gốc (data_editor không trả về các cột bị drop)
                _cart_edited["_cart_key"] = _cart_df["_cart_key"].values
                _cart_edited["id"]        = _cart_df["id"].values
                _cart_edited["STT"]       = _cart_df["STT"].values

                _valid_sell   = _cart_edited[_cart_edited["Giá bán ($)"] > 0]
                _invalid_sell = _cart_edited[_cart_edited["Giá bán ($)"] <= 0]
                if not _invalid_sell.empty:
                    st.caption(f"{len(_invalid_sell)} mục chưa có giá — sẽ được bỏ qua.")
                if not _valid_sell.empty:
                    st.info(f"Sẵn sàng xử lý **{len(_valid_sell)}** giao dịch · Ước tính doanh thu: **{fmt_vnd(float((_valid_sell['Giá bán ($)'] * EXCHANGE_RATE).sum()))}**")
                    if st.button(f"Xác Nhận {len(_valid_sell)} Giao Dịch", type="primary", key="confirm_bulk_sell", use_container_width=True):
                        ts_ban_bulk = now_iso()
                        _full_df = st.session_state.df.copy()
                        _updated = 0
                        for _, _sell_row in _valid_sell.iterrows():
                            _s_price  = float(_sell_row["Giá bán ($)"])
                            _s_place  = str(_sell_row.get("Place", ""))
                            _s_id     = int(float(_sell_row.get("id", 0) or 0))
                            _s_stt    = int(float(_sell_row.get("STT", 0) or 0))
                            _rev_vnd  = _s_price * EXCHANGE_RATE
                            _cost_vnd = float(pd.to_numeric(_sell_row.get("Giá Nhập", 0), errors="coerce") or 0)
                            _profit   = _rev_vnd - _cost_vnd
                            if _s_id > 0:
                                _idx = _full_df.index[_full_df["id"] == _s_id].tolist()
                            else:
                                _idx = _full_df.index[_full_df["STT"] == _s_stt].tolist()
                            if _idx:
                                _row_idx = _idx[0]
                                # Ép cột numeric sang float trước khi gán tránh pandas TypeError
                                # khi cột bị cast sang int64 (vì tất cả giá trị đang là 0)
                                for _fc in ["Giá Bán", "Doanh Thu", "Lợi Nhuận"]:
                                    if _full_df[_fc].dtype != float:
                                        _full_df[_fc] = _full_df[_fc].astype(float)
                                _full_df.at[_row_idx, "Giá Bán"]    = float(_s_price)
                                _full_df.at[_row_idx, "Doanh Thu"]  = float(_rev_vnd)
                                _full_df.at[_row_idx, "Lợi Nhuận"]  = float(_profit)
                                _full_df.at[_row_idx, "Ngày Bán"]   = now_str()
                                _full_df.at[_row_idx, "Trạng Thái"] = "Đã bán"
                                _full_df.at[_row_idx, "time_ban"]   = ts_ban_bulk
                                _full_df.at[_row_idx, "Place"]      = _s_place
                            if USE_SUPABASE:
                                _uc = "id" if _s_id > 0 else "stt"
                                _uv = _s_id if _s_id > 0 else _s_stt
                                sb_update("inventory", {
                                    "gia_ban":    _s_price,
                                    "doanh_thu":  _rev_vnd,
                                    "loi_nhuan":  _profit,
                                    "ngay_ban":   now_str(),
                                    "trang_thai": "Đã bán",
                                    "time_ban":   ts_ban_bulk,
                                    "place":      _s_place,
                                }, _uc, _uv)
                            _updated += 1
                        _full_df = apply_ngay_ton(normalize_df(_full_df, MAIN_SCHEMA))
                        st.session_state.df = _full_df
                        if USE_SUPABASE:
                            st.cache_data.clear()
                            st.session_state.df = apply_ngay_ton(load_inventory())
                        st.session_state.bulk_cart = {}
                        st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                        st.toast(f"Hoàn tất {_updated} giao dịch", icon="✅")
                        _clear_searches()
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RE-SELL — Bán lại pet khách không lấy
# ══════════════════════════════════════════════════════════════════════════════

def render_resell(df):
    # ── RE-SELL (bán lại pet khách không lấy) ──
    _resell_src = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
    with st.expander("🔄 Bán lại (Re-sell)", expanded=False):
        # ── Init session states ──
        if "pinned_resell" not in st.session_state:
            st.session_state.pinned_resell = _load_pinned_resell_from_supabase()
        if "resell_cart" not in st.session_state:
            st.session_state.resell_cart = {}

        # ════════════════════════════════════════════════════
        # PHẦN 1: DANH SÁCH ĐÃ PIN — luôn hiển thị trên cùng
        # ════════════════════════════════════════════════════
        st.markdown(
            '<div style="display:inline-flex;align-items:center;gap:6px;'
            'background:rgba(168,85,247,0.1);border:1px solid rgba(168,85,247,0.3);'
            'border-radius:6px;padding:4px 10px;margin-bottom:8px;">'
            '<span style="font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;'
            'color:#a855f7;font-weight:600;">📌 Danh sách Pin</span>'
            '<span style="font-size:0.72rem;color:#9d8fbf;">— nhấn Re-sell khi chắc chắn khách không lấy</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.pinned_resell and not st.session_state.resell_cart:
            st.markdown(
                '<div style="text-align:center;padding:16px 8px;color:#4b3f6b;'
                'font-size:0.82rem;border:1px dashed rgba(168,85,247,0.2);border-radius:8px;">'
                '📌 Chưa có pet nào được pin<br>'
                '<span style="font-size:0.75rem;">Dùng ô tìm kiếm bên dưới để thêm</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            _rsp1, _rsp2 = st.columns([3, 1])
            _rsp1.caption(f"📌 {len(st.session_state.pinned_resell)} đang pin · ✅ {len(st.session_state.resell_cart)} sẵn sàng re-sell")
            if _rsp2.button("🗑️ Xóa tất cả", key="rs_clear_pin", use_container_width=True):
                st.session_state.pinned_resell = {}
                st.session_state.resell_cart = {}
                _save_pinned_resell_to_supabase({})
                st.rerun()

            for _pid in list(st.session_state.pinned_resell.keys()):
                _pv = st.session_state.pinned_resell[_pid]
                _already_in_rcart = _pid in st.session_state.resell_cart
                _pv_ms    = _pv.get("M/s", "")
                _pv_ns    = str(_pv.get("NameStock", "") or "").strip()
                _pv_mut   = str(_pv.get("Mutation", "") or "")
                _pv_ban   = str(_pv.get("Ngày Bán", "") or "").strip()
                _pv_ms_str  = f" · <b>{_pv_ms}M/s</b>" if _pv_ms else ""
                _pv_ns_str  = f" · <span style='color:#7c6fa0'>{_pv_ns}</span>" if _pv_ns else ""
                _pv_ban_str = f" · <span style='color:#f87171'>{_pv_ban}</span>" if _pv_ban and _pv_ban != "-" else ""
                _rs_badge   = " · <span style='color:#22c55e;font-weight:600;'>✅ Re-sell</span>" if _already_in_rcart else ""
                st.markdown(
                    f'<div style="font-size:0.82rem;padding:4px 0 2px 0;">'
                    f'<b style="color:#f97316">#{int(float(_pv.get("STT", 0) or 0))}</b> · '
                    f'<b>{_pv.get("Tên Pet", "")}</b> · <span style="color:#a78bfa">{_pv_mut}</span>'
                    f'{_pv_ms_str}{_pv_ns_str}{_pv_ban_str}{_rs_badge}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                _pc1, _pc2 = st.columns(2)
                if _already_in_rcart:
                    if _pc1.button("↩️ Hoàn tác", key=f"rs_undo_{_pid}", use_container_width=True):
                        st.session_state.resell_cart.pop(_pid, None)
                        st.rerun()
                else:
                    if _pc1.button("🔄 Re-sell", key=f"rs_move_{_pid}", use_container_width=True, type="primary"):
                        st.session_state.resell_cart[_pid] = _pv
                        st.rerun()
                if _pc2.button("❌ Bỏ pin", key=f"rs_del_{_pid}", use_container_width=True):
                    st.session_state.pinned_resell.pop(_pid, None)
                    st.session_state.resell_cart.pop(_pid, None)
                    _save_pinned_resell_to_supabase(st.session_state.pinned_resell)
                    st.rerun()
                st.markdown('<div style="border-top:1px solid rgba(45,37,64,0.5);margin:2px 0 4px 0;"></div>', unsafe_allow_html=True)

        # ════════════════════════════════════════════════════
        # PHẦN 2: TÌM & THÊM PIN (sub-expander, nằm dưới)
        # ════════════════════════════════════════════════════
        with st.expander("🔍 Tìm & thêm pin", expanded=False):
            if _resell_src.empty:
                st.info("Chưa có pet nào được đánh dấu 'Đã bán'.")
            else:
                _rs_search = st.text_input(
                    "Tìm pet đã bán", placeholder="Tên, mutation, STT, NameStock...",
                    key=f"resell_search_{_sv()}", label_visibility="collapsed",
                )
                _rs_df = _resell_src.copy()
                if _rs_search.strip():
                    _rs_toks = re.split(r'[\s\-]+', _rs_search.strip().lower())
                    _rs_toks = [t for t in _rs_toks if t]
                    _rs_hay = _rs_df[["Tên Pet","Mutation","Auto Title","NameStock","STT"]].astype(str) \
                        .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                    _rs_combined = _rs_hay.apply(lambda r: ' '.join(r), axis=1)
                    _rs_mask = pd.Series([True]*len(_rs_df), index=_rs_df.index)
                    for _rt in _rs_toks:
                        _rs_mask &= _rs_combined.str.contains(_rt, regex=False, na=False)
                    _rs_df = _rs_df[_rs_mask]

                if not _rs_search.strip():
                    st.caption("Nhập tên, mutation, STT... để tìm pet đã bán cần pin.")
                elif _rs_df.empty:
                    st.info("Không tìm thấy pet phù hợp.")
                else:
                    _shown_rs = _rs_df.head(15)
                    for _, _rr in _shown_rs.iterrows():
                        _rrid = str(int(float(_rr.get("id", 0) or 0))) if int(float(_rr.get("id", 0) or 0)) > 0 else f"stt_{int(_rr['STT'])}"
                        _is_pinned   = _rrid in st.session_state.pinned_resell
                        _is_in_rcart = _rrid in st.session_state.resell_cart
                        _rr_ms      = _rr.get("M/s", "")
                        _rr_ns      = str(_rr.get("NameStock", "") or "").strip()
                        _rr_ngayban = str(_rr.get("Ngày Bán", "") or "").strip()
                        _rr_ms_str  = f" · <b>{_rr_ms}M/s</b>" if _rr_ms else ""
                        _rr_ns_str  = f" · <span style='color:#7c6fa0'>{_rr_ns}</span>" if _rr_ns else ""
                        _rr_ban_str = f" · <span style='color:#f87171'>Bán: {_rr_ngayban}</span>" if _rr_ngayban and _rr_ngayban != "-" else ""
                        if _is_in_rcart:
                            _status_badge = " · <span style='color:#22c55e;font-weight:600;'>✅ Re-sell</span>"
                        elif _is_pinned:
                            _status_badge = " · <span style='color:#fb923c;font-weight:600;'>📌 Đã pin</span>"
                        else:
                            _status_badge = ""
                        st.markdown(
                            f'<div style="font-size:0.82rem;padding:4px 0 2px 0;">'
                            f'<b style="color:#f97316">#{int(_rr["STT"])}</b> · '
                            f'<b>{_rr["Tên Pet"]}</b> · <span style="color:#a78bfa">{_rr["Mutation"]}</span>'
                            f'{_rr_ms_str}{_rr_ns_str}{_rr_ban_str}{_status_badge}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if _is_pinned or _is_in_rcart:
                            if st.button("✓ Bỏ pin", key=f"rs_unpin_{_rrid}", use_container_width=True):
                                st.session_state.pinned_resell.pop(_rrid, None)
                                st.session_state.resell_cart.pop(_rrid, None)
                                _save_pinned_resell_to_supabase(st.session_state.pinned_resell)
                                st.rerun()
                        else:
                            if st.button("📌 Pin", key=f"rs_pin_{_rrid}", use_container_width=True, type="primary"):
                                st.session_state.pinned_resell[_rrid] = _rr.to_dict()
                                _save_pinned_resell_to_supabase(st.session_state.pinned_resell)
                                st.rerun()
                        st.markdown('<div style="border-top:1px solid rgba(45,37,64,0.5);margin:2px 0 4px 0;"></div>', unsafe_allow_html=True)
                    if len(_rs_df) > 15:
                        st.caption(f"Đang hiển thị 15 / {len(_rs_df)} kết quả — thu hẹp tìm kiếm để xem thêm.")

        # ── GIAI ĐOẠN 3: XÁC NHẬN RE-SELL ──
        if st.session_state.resell_cart:
            st.markdown("---")
            st.markdown(
                '<div style="display:inline-flex;align-items:center;gap:6px;'
                'background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);'
                'border-radius:6px;padding:4px 10px;margin-bottom:6px;">'
                '<span style="font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;'
                'color:#22c55e;font-weight:600;">③ Xác nhận Re-sell</span>'
                '<span style="font-size:0.72rem;color:#9d8fbf;">— tạo bản ghi kho mới, giá nhập 1₫</span>'
                '</div>',
                unsafe_allow_html=True,
            )

            # Bảng preview read-only
            _rs_preview = []
            for _rck, _rcv in st.session_state.resell_cart.items():
                _rs_preview.append({
                    "STT gốc":      int(float(_rcv.get("STT", 0) or 0)),
                    "Tên Pet":      str(_rcv.get("Tên Pet", "")),
                    "Mutation":     str(_rcv.get("Mutation", "")),
                    "M/s":          str(_rcv.get("M/s", "") or ""),
                    "NameStock":    str(_rcv.get("NameStock", "") or ""),
                    "Trait":        str(_rcv.get("Số Trait", "") or ""),
                    "Bán lần 1":    str(_rcv.get("Ngày Bán", "") or ""),
                    "Giá Nhập mới": 1,
                })
            st.dataframe(
                pd.DataFrame(_rs_preview),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "STT gốc":      st.column_config.NumberColumn("STT gốc", format="%d"),
                    "Giá Nhập mới": st.column_config.NumberColumn("Giá Nhập mới (₫)", format="%d"),
                },
            )

            st.warning(
                f"⚠️ Xác nhận sẽ tạo **{len(st.session_state.resell_cart)} bản ghi mới** "
                f"với giá nhập **1₫** và trạng thái **Còn hàng**. "
                f"Bản ghi gốc (lần bán 1) sẽ **không bị thay đổi**.",
                icon="🔄",
            )
            if st.button(
                f"✅ Xác Nhận Re-sell {len(st.session_state.resell_cart)} Pet",
                type="primary",
                key="confirm_resell",
                use_container_width=True,
            ):
                _rs_inserted  = 0
                _ts_nhap_rs   = now_iso()
                _ngay_nhap_rs = now_str()
                _rs_max_stt   = int(df["STT"].max()) if not df.empty else 0

                for _rck, _rcv in st.session_state.resell_cart.items():
                    _rs_max_stt += 1
                    _pet_name   = str(_rcv.get("Tên Pet", ""))
                    _mutation   = str(_rcv.get("Mutation", "Normal"))
                    _ms         = float(pd.to_numeric(_rcv.get("M/s", 0), errors="coerce") or 0)
                    _so_trait   = str(_rcv.get("Số Trait", "None") or "None")
                    _namestock  = str(_rcv.get("NameStock", "") or "")
                    _auto_title = generate_auto_title(_pet_name, _mutation, _so_trait, _ms, _namestock)

                    _new_payload = {
                        "stt":        _rs_max_stt,
                        "ten_pet":    _pet_name,
                        "ms":         _ms,
                        "mutation":   _mutation,
                        "so_trait":   _so_trait,
                        "namestock":  _namestock,
                        "gia_nhap":   1.0,
                        "gia_ban":    0.0,
                        "doanh_thu":  0.0,
                        "loi_nhuan":  0.0,
                        "ngay_nhap":  _ngay_nhap_rs,
                        "ngay_ban":   "-",
                        "auto_title": _auto_title,
                        "trang_thai": "Còn hàng",
                        "time_nhap":  _ts_nhap_rs,
                        "time_ban":   None,
                        "ngay_ton":   0,
                        "place":      "",
                    }

                    if USE_SUPABASE:
                        _inserted_row = sb_insert_returning("inventory", _new_payload)
                        if _inserted_row:
                            _rs_inserted += 1
                        else:
                            st.toast(f"❌ Lỗi khi tạo bản ghi cho {_pet_name}", icon="❌")
                    else:
                        _new_row = {
                            "id": 0, "STT": _rs_max_stt,
                            "Tên Pet": _pet_name, "M/s": _ms,
                            "Mutation": _mutation, "Số Trait": _so_trait,
                            "NameStock": _namestock, "Giá Nhập": 1.0,
                            "Giá Bán": 0.0, "Doanh Thu": 0.0, "Lợi Nhuận": 0.0,
                            "Ngày Nhập": _ngay_nhap_rs, "Ngày Bán": "-",
                            "Auto Title": _auto_title, "Trạng Thái": "Còn hàng",
                            "time_nhap": _ts_nhap_rs, "time_ban": "",
                            "Ngày Tồn": 0, "Place": "",
                        }
                        st.session_state.df = append_row(st.session_state.df, _new_row, MAIN_SCHEMA)
                        _rs_inserted += 1

                if USE_SUPABASE:
                    st.cache_data.clear()
                    st.session_state.df = apply_ngay_ton(load_inventory())
                df = st.session_state.df
                # Xóa cả pin lẫn cart sau khi insert xong
                _inserted_keys = set(st.session_state.resell_cart.keys())
                for _k in _inserted_keys:
                    st.session_state.pinned_resell.pop(_k, None)
                st.session_state.resell_cart = {}
                st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                st.toast(f"✅ Đã tạo {_rs_inserted} bản ghi re-sell mới trong kho!", icon="🔄")
                _clear_searches()
                st.rerun()
