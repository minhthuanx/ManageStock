"""
Tab Kho Le — Sell Single (search, select, 2-step confirm, undo).
"""
import re
import pandas as pd
import streamlit as st

from _timezone import now_str, now_iso
from _config import EXCHANGE_RATE, MAIN_SCHEMA
from _database import USE_SUPABASE, sb_update, load_inventory
from _helpers import (
    parse_usd, fmt_vnd, fmt_short, normalize_df, apply_ngay_ton,
    token_search, _clear_searches, _sv,
)


def render_sell_single(df):
    # ── UNDO banner ──
    if st.session_state.get("last_sale_undo", {}).get("type") == "single":
        _undo = st.session_state["last_sale_undo"]
        _ub1, _ub2 = st.columns([3, 1])
        _ub1.info(f"↩️ Vừa bán: **{_undo['label']}**  —  Bán nhầm? Hoàn tác ngay!")
        if _ub2.button("↩️ Hoàn tác", key="undo_single_btn", use_container_width=True):
            _ud = st.session_state.pop("last_sale_undo")
            _df2 = st.session_state.df.copy()
            _uid_col = "id" if _ud["sell_id"] > 0 else "stt"
            _uid_val = _ud["sell_id"] if _ud["sell_id"] > 0 else _ud["sel_stt"]
            _idx_list2 = _df2.index[_df2["STT"] == _ud["sel_stt"]].tolist()
            if _idx_list2:
                _recs2 = _df2.to_dict("records")
                _ip2 = _df2.index.get_loc(_idx_list2[0])
                _recs2[_ip2]["Giá Bán"]    = _ud["old_gia_ban"]
                _recs2[_ip2]["Doanh Thu"]  = _ud["old_doanh_thu"]
                _recs2[_ip2]["Lợi Nhuận"]  = _ud["old_loi_nhuan"]
                _recs2[_ip2]["Trạng Thái"] = _ud["old_trang_thai"]
                _recs2[_ip2]["Ngày Bán"]   = _ud["old_ngay_ban"]
                _recs2[_ip2]["time_ban"]   = _ud["old_time_ban"]
                _recs2[_ip2]["Place"]      = _ud["old_place"]
                _df2 = apply_ngay_ton(normalize_df(pd.DataFrame(_recs2), MAIN_SCHEMA))
                st.session_state.df = _df2
                if USE_SUPABASE:
                    sb_update("inventory", {
                        "gia_ban":    _ud["old_gia_ban"] if _ud["old_gia_ban"] else None,
                        "doanh_thu":  _ud["old_doanh_thu"] if _ud["old_doanh_thu"] else None,
                        "loi_nhuan":  _ud["old_loi_nhuan"] if _ud["old_loi_nhuan"] else None,
                        "ngay_ban":   _ud["old_ngay_ban"] if _ud["old_ngay_ban"] else None,
                        "trang_thai": _ud["old_trang_thai"],
                        "time_ban":   _ud["old_time_ban"] if _ud["old_time_ban"] else None,
                        "place":      _ud["old_place"] if _ud["old_place"] else None,
                        "ngay_ton":   _ud["old_ngay_ton"],
                    }, _uid_col, _uid_val)
                    st.cache_data.clear()
            st.toast("Đã hoàn tác giao dịch", icon="↩️")
            st.rerun()

    active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)]
    q = st.text_input("Tìm kiếm", placeholder="STT, tên, mutation, namestock...",
                      key=f"sell_search_q_{_sv()}")

    if not active.empty:
        if q.strip():
            _q_cols = ["STT", "Tên Pet", "Mutation", "NameStock", "Số Trait", "Auto Title", "Place"]
            mask = token_search(active, q, _q_cols)
            filt = active[mask]
        else:
            filt = active

        if not filt.empty:
            _stt_map = {int(r["STT"]): r for _, r in filt.iterrows()}

            def _pet_fmt(stt):
                r = _stt_map[stt]
                auto_t = str(r.get("Auto Title", "") or "")
                short = auto_t.split("🌸Cheapest")[0].lstrip("🌸").strip()
                if not short:
                    short = str(r.get("Tên Pet", ""))
                ns = str(r.get("NameStock", "") or "").strip()
                gia_nhap = float(r.get("Giá Nhập", 0) or 0)
                ngay_ton = int(float(r.get("Ngày Tồn", 0) or 0))
                ns_part  = f" · {ns}" if ns else ""
                ton_part = f" · tồn {ngay_ton}d" if ngay_ton > 0 else ""
                return f"#{stt}  {short}{ns_part}  ·  {fmt_short(gia_nhap)}{ton_part}"

            sel = st.selectbox(
                "Chọn Pet", list(_stt_map.keys()),
                format_func=_pet_fmt, label_visibility="collapsed",
            )
            sel_stt = sel
            sel_row = filt[filt["STT"] == sel_stt].iloc[0]
            _at_le = str(sel_row.get("Auto Title", "") or "")
            if _at_le:
                st.code(_at_le, language="text")
            st.caption(f"**{len(filt)}** kết quả phù hợp")

            with st.form(f"form_ban_le_{_sv()}", clear_on_submit=False):
                c1, c2 = st.columns([1.2, 1])
                s_price_raw = c1.text_input("Đơn giá ($)", placeholder="VD: 5.5")
                s_place     = c2.text_input("Kênh bán (tuỳ chọn)", placeholder="Note anything...")
                sell_btn    = st.form_submit_button("Xác Nhận Giao Dịch", type="primary", use_container_width=True)

            # Step 1: save pending
            if sell_btn:
                s_price = parse_usd(s_price_raw)
                if s_price <= 0:
                    st.error("Đơn giá phải lớn hơn 0")
                else:
                    st.session_state["pending_single_sale"] = {
                        "sel_stt":       sel_stt,
                        "auto_title":    str(sel_row.get("Auto Title", sel_row.get("Tên Pet", "?"))),
                        "gia_nhap":      float(sel_row.get("Giá Nhập", 0) or 0),
                        "s_price":       s_price,
                        "s_place":       s_place,
                        "sell_id":       int(float(sel_row.get("id", 0) or 0)),
                        "old_gia_ban":   float(sel_row.get("Giá Bán", 0) or 0),
                        "old_doanh_thu": float(sel_row.get("Doanh Thu", 0) or 0),
                        "old_loi_nhuan": float(sel_row.get("Lợi Nhuận", 0) or 0),
                        "old_trang_thai":str(sel_row.get("Trạng Thái", "Còn hàng")),
                        "old_ngay_ban":  str(sel_row.get("Ngày Bán", "") or ""),
                        "old_time_ban":  str(sel_row.get("time_ban", "") or ""),
                        "old_place":     str(sel_row.get("Place", "") or ""),
                        "old_ngay_ton":  int(float(sel_row.get("Ngày Tồn", 0) or 0)),
                    }
                    st.rerun()

            # Step 2: confirmation block
            _pnd_single = st.session_state.get("pending_single_sale")
            if _pnd_single and _pnd_single["sel_stt"] == sel_stt:
                _rev_prev = _pnd_single["s_price"] * EXCHANGE_RATE
                _ln_prev  = _rev_prev - _pnd_single["gia_nhap"]
                st.warning(
                    f"⚠️ **Xác nhận bán** · {_pnd_single['auto_title']}\n\n"
                    f"Giá: **${_pnd_single['s_price']}** → {fmt_vnd(_rev_prev)} · "
                    f"Lợi nhuận: **{fmt_vnd(_ln_prev)}**"
                )
                _cf1, _cf2 = st.columns(2)
                _do_confirm = _cf1.button("✅ Xác nhận bán", key="confirm_sell_single", type="primary", use_container_width=True)
                _do_cancel  = _cf2.button("❌ Hủy", key="cancel_sell_single", use_container_width=True)

                if _do_cancel:
                    st.session_state.pop("pending_single_sale", None)
                    st.rerun()

                if _do_confirm:
                    _pnd = st.session_state.pop("pending_single_sale")
                    _sel_stt2 = _pnd["sel_stt"]
                    _s_price2 = _pnd["s_price"]
                    _s_place2 = _pnd["s_place"]
                    _ts_ban   = now_iso()
                    _rev_vnd  = _s_price2 * EXCHANGE_RATE
                    _idx_list = df.index[df["STT"] == _sel_stt2].tolist()
                    if _idx_list:
                        _iloc_pos = df.index.get_loc(_idx_list[0])
                        _recs = df.to_dict("records")
                        _recs[_iloc_pos]["Giá Bán"]    = float(_s_price2)
                        _recs[_iloc_pos]["Doanh Thu"]  = float(_rev_vnd)
                        _recs[_iloc_pos]["Lợi Nhuận"]  = float(_rev_vnd - _pnd["gia_nhap"])
                        _recs[_iloc_pos]["Ngày Bán"]   = now_str()
                        _recs[_iloc_pos]["Trạng Thái"] = "Đã bán"
                        _recs[_iloc_pos]["time_ban"]   = _ts_ban
                        _recs[_iloc_pos]["Place"]      = _s_place2
                        df = apply_ngay_ton(normalize_df(pd.DataFrame(_recs), MAIN_SCHEMA))
                        st.session_state.df = df
                        if USE_SUPABASE:
                            _update_col = "id" if _pnd["sell_id"] > 0 else "stt"
                            _update_val = _pnd["sell_id"] if _pnd["sell_id"] > 0 else _sel_stt2
                            sb_update("inventory", {
                                "gia_ban":    float(_s_price2),
                                "doanh_thu":  float(_rev_vnd),
                                "loi_nhuan":  float(_rev_vnd - _pnd["gia_nhap"]),
                                "ngay_ban":   now_str(),
                                "trang_thai": "Đã bán",
                                "time_ban":   _ts_ban,
                                "place":      _s_place2,
                                "ngay_ton":   int(_recs[_iloc_pos]["Ngày Tồn"]),
                            }, _update_col, _update_val)
                            load_inventory.clear()
                        st.session_state["last_sale_undo"] = {
                            "type":          "single",
                            "label":         f"{_pnd['auto_title']} @ ${_pnd['s_price']}",
                            "sell_id":       _pnd["sell_id"],
                            "sel_stt":       _sel_stt2,
                            "old_gia_ban":   _pnd["old_gia_ban"],
                            "old_doanh_thu": _pnd["old_doanh_thu"],
                            "old_loi_nhuan": _pnd["old_loi_nhuan"],
                            "old_trang_thai":_pnd["old_trang_thai"],
                            "old_ngay_ban":  _pnd["old_ngay_ban"],
                            "old_time_ban":  _pnd["old_time_ban"],
                            "old_place":     _pnd["old_place"],
                            "old_ngay_ton":  _pnd["old_ngay_ton"],
                        }
                        st.toast("✅ Giao dịch hoàn tất · Nhấn Hoàn Tác nếu bán nhầm", icon="✅")
                        _clear_searches()
                        st.rerun()
        else:
            st.markdown('<div class="empty-state"><div class="es-icon">🔍</div><div class="es-title">Không tìm thấy kết quả</div><div class="es-sub">Thử điều chỉnh từ khoá tìm kiếm</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="es-icon">📦</div><div class="es-title">Kho trống</div><div class="es-sub">Nhấn "Nhập Kho" bên trái để thêm hàng</div></div>', unsafe_allow_html=True)
