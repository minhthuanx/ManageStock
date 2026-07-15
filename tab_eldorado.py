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
            st.markdown('<div class="sec-heading">Eldorado.gg</div>', unsafe_allow_html=True)

            if eld_client and eld_client.logged_in:
                # Profile card — centered, no avatar
                _initial = (eld_client.username or "?")[0].upper()
                st.markdown(f'''
                <div style="text-align:center;padding:1.2rem 0 0.8rem;">
                    <div style="width:80px;height:80px;border-radius:50%;background:hsl(217.2 32.6% 17.5%);
                    display:inline-flex;align-items:center;justify-content:center;font-size:32px;font-weight:700;
                    color:hsl(210 40% 98%);border:2px solid hsl(217.2 32.6% 22%);">{_initial}</div>
                    <div style="font-size:1.5rem;font-weight:700;color:hsl(210 40% 98%);margin-top:10px;">{eld_client.username}</div>
                    <div style="font-size:0.875rem;color:hsl(217.2 20% 45%);margin-top:6px;">
                        👍 {eld_client.pos} &nbsp;&nbsp; 👎 {eld_client.neg} &nbsp;&nbsp; | &nbsp;&nbsp; {eld_client.pos + eld_client.neg} giao dịch
                    </div>
                </div>
                ''', unsafe_allow_html=True)

                if st.button("🔌 Logout", key="eldo_logout_top", use_container_width=True):
                    eld_client.disconnect()
                    _clear_eld_cookie_from_sb()
                    st.toast("Đã đăng xuất Eldorado")
                    st.rerun()
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
                st.markdown('<div class="sec-heading">Listing Của Tôi</div>', unsafe_allow_html=True)

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

                    # ── Danh sách listings (Active only) ──
                    _active_listings = [x for x in _flt if x.get("offerState") == "Active"]
                    st.caption(f"**{len(_active_listings)}** Active / {len(_flt)} tổng")

                    if not _active_listings:
                        st.info("Không có listing Active nào.")
                    else:
                        for _o in _active_listings:
                            _oid = _o.get("id", "")
                            _otitle = (_o.get("offerTitle", "") or "")[:55]
                            _oprice = float(_o.get("pricePerUnit", {}).get("amount", 0))
                            _oimg = (_o.get("mainOfferImage") or {}).get("smallImage", "")
                            _is_expanded = st.session_state.get("_eldo_expanded_id") == _oid

                            # Compact card row
                            rc1, rc2, rc3 = st.columns([0.5, 4, 1.5])
                            with rc1:
                                if _oimg:
                                    if not _oimg.startswith("http"):
                                        _oimg = f"https://assetsdelivery.eldorado.gg/v7/_offers-v2_/{_oimg}"
                                    st.markdown(f'<img src="{_oimg}" width="42" height="42" style="border-radius:8px;object-fit:cover;">', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div style="width:42px;height:42px;border-radius:8px;background:#222b45;display:flex;align-items:center;justify-content:center;font-size:18px;">📦</div>', unsafe_allow_html=True)
                            with rc2:
                                st.markdown(f"**{_otitle}**")
                                st.caption(f"**${_oprice:.2f}**")
                            with rc3:
                                if st.button("▼" if not _is_expanded else "▲", key=f"ed_{_oid}", use_container_width=True):
                                    st.session_state["_eldo_expanded_id"] = _oid if not _is_expanded else None
                                    st.rerun()

                            # Inline action panel
                            if _is_expanded:
                                with st.container():
                                    ac1, ac2, ac3, ac4 = st.columns([2, 1, 1, 1])
                                    _np_val = ac1.number_input("Giá mới ($)", 0.01, 9999.0, _oprice, 0.05, format="%.2f", key="eldo_price_edit")
                                    if ac2.button("💰", key="btn_upd_price", use_container_width=True, help="Đổi giá"):
                                        _r = eld_client.change_price(_oid, _np_val)
                                        if _r and not _r.get("error"):
                                            st.toast("Đã đổi giá")
                                            st.session_state._eldo_all = []
                                            st.session_state.pop("_eldo_expanded_id", None)
                                            st.rerun()
                                        else:
                                            st.error(_r.get("error", "Lỗi"))
                                    if ac3.button("⏸️", key="btn_pause_one", use_container_width=True, help="Tạm dừng"):
                                        eld_client.change_state(_oid, "Paused")
                                        st.session_state._eldo_all = []
                                        st.session_state.pop("_eldo_expanded_id", None)
                                        st.rerun()
                                    if ac4.button("🗑️", key="btn_del_one", use_container_width=True, help="Xoá"):
                                        eld_client.delete_listing(_oid)
                                        st.session_state._eldo_all = []
                                        st.session_state.pop("_eldo_expanded_id", None)
                                        st.rerun()

            # ══════════════════════════════════════════════════════════════
            # SECTION 3: ORDERS
            # ══════════════════════════════════════════════════════════════
        if eld_client and eld_client.logged_in:
            with st.container(border=True):
                st.markdown('<div class="sec-heading">Đơn Hàng</div>', unsafe_allow_html=True)

                _eldo_reload_orders = st.button("🔄 Tải đơn hàng", key="eldo_refresh_orders")
                if _eldo_reload_orders:
                    st.session_state._eldo_orders = None
                    st.session_state._eldo_notifications = None

                # ── Orders ──
                if st.session_state.get("_eldo_orders") is None or _eldo_reload_orders:
                    with st.spinner("Đang tải đơn hàng..."):
                        _orders_raw = eld_client.get_orders(page_size=50)
                        st.session_state["_eldo_orders"] = _orders_raw if isinstance(_orders_raw, dict) else {"orders": []}
                _orders = st.session_state.get("_eldo_orders", {})
                _order_list = _orders.get("orders", [])

                # ── Notifications ──
                if st.session_state.get("_eldo_notifications") is None or _eldo_reload_orders:
                    with st.spinner("Đang tải thông báo..."):
                        _notifs_raw = eld_client.get_notifications(page_size=20)
                        st.session_state["_eldo_notifications"] = _notifs_raw if isinstance(_notifs_raw, dict) else {"notifications": []}
                _notifs = st.session_state.get("_eldo_notifications", {})
                _notif_list = _notifs.get("notifications", [])

                # Stats
                _pending_count = sum(1 for o in _order_list if o.get("orderState") == "Pending")
                _active_count = sum(1 for o in _order_list if o.get("orderState") == "Active")
                _delivered_count = sum(1 for o in _order_list if o.get("orderState") == "Delivered")
                _unread_count = sum(1 for n in _notif_list if not n.get("isRead", True))

                oc1, oc2, oc3, oc4 = st.columns(4)
                oc1.metric("⏳ Pending", _pending_count)
                oc2.metric("🔄 Active", _active_count)
                oc3.metric("✅ Delivered", _delivered_count)
                oc4.metric("🔔 Thông báo mới", _unread_count)

                # ── Notifications feed ──
                if _notif_list:
                    with st.expander(f"🔔 Thông báo ({len(_notif_list)})", expanded=False):
                        for _n in _notif_list[:10]:
                            _nread = _n.get("isRead", True)
                            _ntitle = _n.get("title", "") or _n.get("message", "") or str(_n.get("type", ""))
                            _ncard = f"{'🔵' if not _nread else '⚪'} {_ntitle}"
                            st.caption(_ncard)
                        if _unread_count > 0:
                            if st.button("✅ Đánh dấu tất cả đã đọc", key="btn_mark_read"):
                                eld_client.mark_notifications_read()
                                st.session_state._eldo_notifications = None
                                st.rerun()

                # ── Orders list ──
                if not _order_list:
                    st.info("Không có đơn hàng nào.")
                else:
                    for _o in _order_list:
                        _oid = _o.get("id", "")
                        _ostate = _o.get("orderState", "?")
                        _oprice = float((_o.get("pricePerUnit") or {}).get("amount", 0))
                        _otitle = (_o.get("offerTitle") or _o.get("augmentedGame", {}).get("offerTitle", "") or "")[:60]
                        _buyer = _o.get("buyerUsername", "") or _o.get("buyer", "") or ""
                        _created = (_o.get("createdDate") or _o.get("createdAt", ""))[:16]
                        _deliver = _o.get("guaranteedDeliveryTime", "")
                        _game = _o.get("augmentedGame", {})
                        _pet = (_game.get("offerAttributes") or [{}])[0].get("value", "") if _game.get("offerAttributes") else ""

                        _state_colors = {"Pending": ("#f59e0b", "⏳ Pending"), "Active": ("hsl(142, 76%, 56%)", "🔄 Active"), "Delivered": ("#3b82f6", "✅ Delivered"), "Cancelled": ("#ef4444", "❌ Cancelled")}
                        _sc, _sl = _state_colors.get(_ostate, ("#6b7280", _ostate))

                        with st.container():
                            _o1, _o2, _o3, _o4 = st.columns([3, 1.5, 1.5, 1])
                            with _o1:
                                st.markdown(f"**{_otitle}**")
                                if _buyer:
                                    st.caption(f"👤 {_buyer} · 📅 {_created}")
                            with _o2:
                                st.markdown(f"**${_oprice:.2f}**")
                                st.caption(f"{_sl}")
                            with _o3:
                                st.caption(f"⏱ {_deliver}" if _deliver else "")
                                if _pet:
                                    st.caption(f"🎮 {str(_pet)[:20]}")
                            with _o4:
                                if _ostate == "Pending":
                                    if st.button("✅ Xác nhận", key=f"od_{_oid}", use_container_width=True, type="primary"):
                                        eld_client.mark_delivered(_oid)
                                        st.session_state._eldo_orders = None
                                        st.rerun()
                                elif _ostate == "Active":
                                    if st.button("📦 Đã giao", key=f"od_{_oid}", use_container_width=True):
                                        eld_client.mark_delivered(_oid)
                                        st.session_state._eldo_orders = None
                                        st.rerun()
                                else:
                                    st.caption("")
