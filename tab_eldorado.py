import base64
import time as _time
import pandas as pd
import streamlit as st

from _timezone import now_vn
from _helpers import _sv

try:
    from _eldorado_helpers import (
        _HAS_ELDORADO, _save_eld_cookie_to_sb, _clear_eld_cookie_from_sb,
    )
except ImportError:
    _HAS_ELDORADO = False


def render_tab_eldorado(eld_client):
    # ─────────────────────────────────────────────────────────────────────────────
    # TAB ELDORADO: Quản lý listing trên sàn
    # ─────────────────────────────────────────────────────────────────────────────
    if not _HAS_ELDORADO:
        st.warning("Module Eldorado không khả dụng. Kiểm tra eldorado_client.py.")
    else:
        # ── SECTION 1: LOGIN / PROFILE CARD ──
        with st.container(border=True):
            st.markdown('<div class="sec-heading">🎮 Eldorado.gg</div>', unsafe_allow_html=True)

            if eld_client and eld_client.logged_in:
                # Profile card — download avatar + hiển thị
                if not st.session_state.get("_eldo_avatar_b64"):
                    _av_url = eld_client.avatar or ""
                    if _av_url:
                        try:
                            # Thử nhiều URL patterns
                            _patterns = [
                                f"https://eldorado.gg{_av_url}" if _av_url.startswith("/") else _av_url,
                                f"https://eldorado.gg{_av_url}" if not _av_url.startswith("http") else _av_url,
                            ]
                            for _av_full in _patterns:
                                try:
                                    _av_resp = eld_client._session.get(_av_full, timeout=8,
                                        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://eldorado.gg/"})
                                    if _av_resp.ok and _av_resp.headers.get("content-type", "").startswith("image/"):
                                        import base64 as _b64
                                        st.session_state["_eldo_avatar_b64"] = _b64.b64encode(_av_resp.content).decode()
                                        st.session_state["_eldo_avatar_ct"] = _av_resp.headers["content-type"]
                                        break
                                except Exception:
                                    continue
                        except Exception:
                            pass

                _av_b64 = st.session_state.get("_eldo_avatar_b64", "")
                _av_ct = st.session_state.get("_eldo_avatar_ct", "image/png")

                # Centered profile card
                st.markdown('<div style="display:flex;justify-content:center;">', unsafe_allow_html=True)
                _pf_col1, _pf_col2, _pf_col3 = st.columns([1, 3, 1])
                with _pf_col2:
                    if _av_b64:
                        st.markdown(
                            f'<div style="text-align:center;">'
                            f'<img src="data:{_av_ct};base64,{_av_b64}" width="96" height="96" '
                            f'style="border-radius:50%;object-fit:cover;border:3px solid #c084fc;">'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        _initial = (eld_client.username or "?")[0].upper()
                        st.markdown(
                            f'<div style="text-align:center;">'
                            f'<div style="width:96px;height:96px;border-radius:50%;background:linear-gradient(135deg,#c084fc,#e879f9);'
                            f'display:inline-flex;align-items:center;justify-content:center;font-size:36px;font-weight:700;'
                            f'color:#fff;border:3px solid #c084fc;">{_initial}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown(
                        f'<div style="text-align:center;margin-top:8px;">'
                        f'<div style="font-size:1.3rem;font-weight:700;color:#f0e6ff;">{eld_client.username}</div>'
                        f'<div style="font-size:0.85rem;color:#9d8fbf;margin-top:4px;">'
                        f'ID: <code>{eld_client.userId[:12]}...</code> &nbsp;|&nbsp; '
                        f'👍 {eld_client.pos} &nbsp; 👎 {eld_client.neg}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("🔌 Logout", key="eldo_logout_top", use_container_width=True):
                        eld_client.disconnect()
                        _clear_eld_cookie_from_sb()
                        st.toast("Đã đăng xuất Eldorado")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                with st.form("form_eldo_login", clear_on_submit=False):
                    st.caption("F12 → Application → Cookies → eldorado.gg → Copy all as string")
                    cookie_str = st.text_area("Cookie", height=80, label_visibility="collapsed",
                                               placeholder="__Host-XSRF-TOKEN=...; __Host-EldoradoIdToken=...")
                    login_ok = st.form_submit_button("🔗 Đăng Nhập Eldorado", type="primary", use_container_width=True)
                if login_ok and cookie_str.strip():
                    with st.spinner("Đang xác thực..."):
                        eld_client.set_cookies(cookie_str.strip())
                        auth_r = eld_client.check_auth()
                    if auth_r.get("ok"):
                        eld_client.save_cookies()
                        _save_eld_cookie_to_sb(cookie_str.strip())
                        st.toast(f"Đăng nhập thành công: {eld_client.username}")
                        st.rerun()
                    else:
                        st.error(f"Lỗi: {auth_r.get('error', 'unknown')}")

        if eld_client and eld_client.logged_in:
            # ── SECTION 2: LISTINGS ──
            with st.container(border=True):
                st.markdown('<div class="sec-heading">📦 Listing Của Tôi</div>', unsafe_allow_html=True)

                # ── Load ALL listings ──
                _eldo_reload = st.button("🔄 Tải lại", key="eldo_refresh_listings")
                if _eldo_reload:
                    st.session_state._eldo_all = []
                    st.session_state["_eldo_states_loaded"] = False

                _all_data = st.session_state.get("_eldo_all", [])

                if not _all_data or _eldo_reload:
                    with st.spinner("Đang tải toàn bộ listings..."):
                        _raw = eld_client.get_all_listings()
                        if isinstance(_raw, dict) and "results" in _raw:
                            _all_data = _raw["results"]
                            st.session_state._eldo_all = _all_data

                # ── State counts (lấy từ API) ──
                if not st.session_state.get("_eldo_states_loaded") or _eldo_reload:
                    try:
                        _raw_states = eld_client.get_states()
                        _states = _raw_states if isinstance(_raw_states, dict) else {}
                    except Exception:
                        _states = {}
                    st.session_state["_eldo_states"] = _states
                    st.session_state["_eldo_states_loaded"] = True
                _states = st.session_state.get("_eldo_states", {})
                _cnt_a = int(_states.get("activeOffers") or _states.get("active_offers") or 0)
                _cnt_p = int(_states.get("pausedOffers") or _states.get("paused_offers") or 0)
                _cnt_c = int(_states.get("closedOffers") or _states.get("closed_offers") or 0)
                _cnt_all = _cnt_a + _cnt_p + _cnt_c
                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Tổng", _cnt_all)
                sc2.metric("Active", _cnt_a)
                sc3.metric("Paused", _cnt_p)
                sc4.metric("Closed", _cnt_c)

                _listings = _all_data
                if not _listings:
                    st.info("Không có listing nào. Nhấn 🔄 Tải lại.")
                else:
                    # ── Filters ──
                    fl1, fl2, fl3 = st.columns([2, 1.5, 1])
                    _eldo_search = fl1.text_input("🔍 Tìm kiếm", placeholder="Tên listing...",
                                                   key="eldo_search_q", label_visibility="collapsed")
                    _eldo_sort = fl2.selectbox("Sắp xếp", ["Mới nhất", "Giá thấp→cao", "Giá cao→thấp",
                                                "Tên A→Z"], key="eldo_sort", label_visibility="collapsed")
                    _eldo_state_flt = fl3.selectbox("State", ["Tất cả", "Active", "Paused", "Closed"],
                                                    key="eldo_state_flt", label_visibility="collapsed")

                    _flt = list(_listings)
                    if _eldo_search.strip():
                        _sq = _eldo_search.strip().lower()
                        _flt = [x for x in _flt if _sq in (x.get("offerTitle") or "").lower()
                                or _sq in str(x.get("id", ""))]
                    if _eldo_state_flt != "Tất cả":
                        _flt = [x for x in _flt if x.get("offerState") == _eldo_state_flt]
                    if _eldo_sort == "Giá thấp→cao":
                        _flt.sort(key=lambda x: float(x.get("pricePerUnit", {}).get("amount", 0)))
                    elif _eldo_sort == "Giá cao→thấp":
                        _flt.sort(key=lambda x: float(x.get("pricePerUnit", {}).get("amount", 0)), reverse=True)
                    elif _eldo_sort == "Tên A→Z":
                        _flt.sort(key=lambda x: (x.get("offerTitle") or "").lower())

                    # ── Bulk actions ──
                    with st.expander("⚡ Thao Tác Hàng Loạt", expanded=False):
                        _bulk_state = st.selectbox("Chọn state", ["Active", "Paused", "Closed"],
                                                    key="eldo_bulk_state")
                        _bulk_items = [x for x in _listings if x.get("offerState") == _bulk_state]
                        st.caption(f"**{len(_bulk_items)}** listing {_bulk_state} trong toàn bộ kho")

                        if _bulk_items:
                            ba1, ba2 = st.columns(2)
                            if ba2.button(f"🗑️ Xoá tất cả {len(_bulk_items)} {_bulk_state}",
                                          type="primary", use_container_width=True, key="btn_bulk_delete"):
                                _dprog = st.progress(0)
                                _dok = 0
                                for _bi, _br in enumerate(_bulk_items):
                                    _dprog.progress(_bi / len(_bulk_items))
                                    _r = eld_client.delete_listing(_br.get("id", ""))
                                    if _r and not _r.get("error"):
                                        _dok += 1
                                    _time.sleep(0.3)
                                _dprog.progress(1.0)
                                st.success(f"✅ Đã xoá: {_dok}/{len(_bulk_items)}")
                                st.session_state._eldo_all = []
                                st.rerun()

                            if _bulk_state in ("Active", "Closed"):
                                _pause_label = "⏸️ Pause" if _bulk_state == "Active" else "⏸️ Pause (nếu có thể)"
                                if ba1.button(_pause_label, use_container_width=True, key="btn_bulk_pause"):
                                    _pok = 0
                                    for _br in _bulk_items:
                                        if _br.get("offerState") == "Active":
                                            _r = eld_client.change_state(_br.get("id", ""), "Paused")
                                            if _r and not _r.get("error"):
                                                _pok += 1
                                            _time.sleep(0.3)
                                    st.toast(f"Paused: {_pok}/{len(_bulk_items)}")
                                    st.session_state._eldo_all = []
                                    st.rerun()
                            elif _bulk_state == "Paused":
                                if ba1.button("▶️ Resume tất cả", use_container_width=True, key="btn_bulk_resume"):
                                    _rok = 0
                                    for _br in _bulk_items:
                                        _r = eld_client.change_state(_br.get("id", ""), "Active")
                                        if _r and not _r.get("error"):
                                            _rok += 1
                                        _time.sleep(0.3)
                                    st.toast(f"Resumed: {_rok}/{len(_bulk_items)}")
                                    st.session_state._eldo_all = []
                                    st.rerun()

                    # ── Giảm giá toàn bộ ──
                    with st.expander("📉 Giảm giá toàn bộ (Active)", expanded=False):
                        _act = [x for x in _listings if x.get("offerState") == "Active"]
                        if not _act:
                            st.info("Không có listing Active.")
                        else:
                            st.caption(f"**{len(_act)}** listings Active trong toàn bộ kho")
                            _dm, _dv = st.columns(2)
                            _disc_mode = _dm.radio("Chế độ", ["%", "$"], horizontal=True, key="eldo_dm")
                            if _disc_mode == "%":
                                _disc_val = _dv.number_input("Giảm %", 0.1, 90.0, 5.0, 0.5,
                                                             format="%.1f", key="eldo_dv")
                            else:
                                _disc_val = _dv.number_input("Giảm $", 0.01, 100.0, 0.05, 0.01,
                                                             format="%.2f", key="eldo_dv")

                            _prev = []
                            for _l in _act:
                                _op = float(_l.get("pricePerUnit", {}).get("amount", 0))
                                _np = max(0.01, round(_op * (1 - _disc_val / 100), 2)) if _disc_mode == "%" \
                                    else max(0.01, round(_op - _disc_val, 2))
                                if _np != _op:
                                    _prev.append({"Title": (_l.get("offerTitle", "") or "")[:50],
                                                  "Cũ": _op, "Mới": _np, "ID": _l.get("id", "")})

                            if _prev:
                                st.dataframe(pd.DataFrame(_prev)[["Title", "Cũ", "Mới"]],
                                             use_container_width=True, hide_index=True, height=200)
                                if st.button(f"📉 Xác nhận giảm {len(_prev)} listings",
                                             type="primary", use_container_width=True, key="btn_eldo_disc"):
                                    _dprog = st.progress(0)
                                    _dok = 0
                                    for _di, _dr in enumerate(_prev):
                                        _dprog.progress(_di / len(_prev))
                                        _r = eld_client.change_price(_dr["ID"], _dr["Mới"])
                                        if _r and not _r.get("error"):
                                            _dok += 1
                                        _time.sleep(0.3)
                                    _dprog.progress(1.0)
                                    st.success(f"✅ Đã giảm: {_dok}/{len(_prev)}")
                                    st.session_state._eldo_all = []
                                    st.rerun()
                            else:
                                st.info("Đã ở giá tối thiểu.")

                    # ── Danh sách listings ──
                    st.caption(f"**{len(_flt)}** / {len(_listings)} listings")

                    # Tạo HTML scroll container + listing cards
                    _cards_html = ""
                    for _o in _flt:
                        _oid = _o.get("id", "")
                        _otitle = (_o.get("offerTitle", "") or "")[:65]
                        _oprice = float(_o.get("pricePerUnit", {}).get("amount", 0))
                        _ostate = _o.get("offerState", "?")
                        _oimg = (_o.get("mainOfferImage") or {}).get("smallImage", "")
                        _state_colors = {"Active": ("#22c55e", "Active"), "Paused": ("#f59e0b", "Paused"), "Closed": ("#ef4444", "Closed")}
                        _sc, _sl = _state_colors.get(_ostate, ("#6b7280", _ostate))

                        if _oimg:
                            if not _oimg.startswith("http"):
                                _oimg = f"https://assetsdelivery.eldorado.gg/v7/_offers-v2_/{_oimg}"
                            _img_tag = f'<img src="{_oimg}" width="52" height="52" style="border-radius:8px;object-fit:cover;">'
                        else:
                            _img_tag = '<div style="width:52px;height:52px;border-radius:8px;background:#1a1528;display:flex;align-items:center;justify-content:center;font-size:22px;">📦</div>'

                        _cards_html += f'''
                        <div style="display:flex;align-items:center;gap:12px;padding:10px 12px;margin-bottom:6px;border:1px solid rgba(192,132,252,0.2);border-radius:10px;background:rgba(17,15,26,0.6);">
                            {_img_tag}
                            <div style="flex:1;min-width:0;">
                                <div style="font-size:0.92rem;font-weight:600;color:#f0e6ff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{_otitle}</div>
                                <div style="font-size:0.82rem;color:#9d8fbf;margin-top:2px;">${_oprice:.2f} · <span style="color:{_sc};font-weight:600;">{_sl}</span> · ID: {_oid}</div>
                            </div>
                        </div>'''

                    st.markdown(
                        f'<div style="max-height:700px;overflow-y:auto;border:1px solid rgba(192,132,252,0.15);border-radius:10px;padding:8px;">'
                        f'{_cards_html}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # ── Action buttons cho mỗi listing (bên ngoài scroll) ──
                    _sel_oid = st.selectbox(
                        "Chọn listing để thao tác",
                        [f"{x.get('id', '')} — {(x.get('offerTitle', '') or '')[:40]} — ${float(x.get('pricePerUnit', {}).get('amount', 0)):.2f} — {x.get('offerState', '?')}" for x in _flt],
                        key="eldo_select_listing",
                    )
                    _sel_idx = next((i for i, x in enumerate(_flt) if f"{x.get('id', '')} —" in _sel_oid), 0)
                    _sel_o = _flt[_sel_idx] if _flt else None

                    if _sel_o:
                        _oid = _sel_o.get("id", "")
                        _oprice = float(_sel_o.get("pricePerUnit", {}).get("amount", 0))
                        _ostate = _sel_o.get("offerState", "?")

                        ac1, ac2, ac3, ac4 = st.columns(4)
                        _np_val = ac1.number_input("Giá mới ($)", 0.01, 9999.0, _oprice, 0.05, format="%.2f", key="eldo_new_price")
                        if ac2.button("💰 Đổi giá", type="primary", use_container_width=True, key="btn_change_price"):
                            _r = eld_client.change_price(_oid, _np_val)
                            if _r and not _r.get("error"):
                                st.toast("Đã đổi giá")
                                st.session_state._eldo_all = []
                                st.rerun()
                        if _ostate == "Active":
                            if ac3.button("⏸️ Pause", use_container_width=True, key="btn_pause"):
                                eld_client.change_state(_oid, "Paused")
                                st.session_state._eldo_all = []
                                st.rerun()
                        elif _ostate == "Paused":
                            if ac3.button("▶️ Resume", use_container_width=True, key="btn_resume"):
                                eld_client.change_state(_oid, "Active")
                                st.session_state._eldo_all = []
                                st.rerun()
                        else:
                            ac3.button("⏸️", disabled=True, key="btn_pause_disabled")
                        if ac4.button("🗑️ Xoá", type="primary", use_container_width=True, key="btn_delete_sel"):
                            eld_client.delete_listing(_oid)
                            st.session_state._eldo_all = []
                            st.rerun()
