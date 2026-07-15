import json
import re
import time
import base64
import threading
import requests
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from _timezone import now_vn, now_str, now_iso
from _helpers import (
    parse_vnd, parse_usd, fmt_vnd, get_name_options, append_row,
    generate_auto_title, _clear_searches, _sv,
    next_id, apply_ngay_ton,
)
from _config import MAIN_SCHEMA, LIST_SCHEMA, MUTATION_OPTIONS, PET_LIST_FILE, DB_FILE
from _database import (
    USE_SUPABASE, sb_insert, sb_insert_batch,
    load_inventory, load_csv, save_csv, supabase_client,
    to_db, _save_groq_key_to_supabase,
)


def render_ai_vision(df, pet_db, ns_db, trait_db):
    """Render the AI Vision expander section for auto-scanning pet images via Groq API."""

    # =========================================================
    # AI VISION – Key setup + multi-image + dialog preview
    # =========================================================
    # Giữ expander mở khi có file đã upload hoặc có kết quả đang hiển thị
    _ai_ukey = st.session_state.get("ai_uploader_key", 0)
    _ai_has_files   = bool(st.session_state.get(f"ai_batch_upload_{_ai_ukey}", []))
    _ai_has_results = bool(st.session_state.get("ai_batch_results", []) or st.session_state.get("ai_show_dialog", False))
    if _ai_has_files or _ai_has_results:
        st.session_state.ai_expander = True

    with st.expander("AI Vision — Nhập tự động", expanded=st.session_state.get("ai_expander", False)):

        # ── STEP 1: API KEY ──
        ai_key = st.session_state.get("groq_key", "")
        if ai_key:
            # Key đã được cấu hình — hiển thị masked + nút cập nhật
            _masked = ai_key[:6] + "*" * (len(ai_key) - 10) + ai_key[-4:] if len(ai_key) > 10 else "****"
            _kc1, _kc2 = st.columns([3, 1])
            _kc1.success(f"API đã kết nối · {_masked}")
            if _kc2.button("Thay đổi", use_container_width=True, key="btn_change_groq"):
                st.session_state.groq_key = ""
                st.rerun()
        else:
            ai_key_input = st.text_input(
                "🔑 Groq API Key",
                type="password",
                value="",
                placeholder="gsk_...",
                help="Lấy miễn phí tại console.groq.com/keys",
            )
            if ai_key_input and ai_key_input.strip():
                st.session_state.groq_key = ai_key_input.strip()
                _save_groq_key_to_supabase(ai_key_input.strip())
                st.toast("✅ Đã lưu Groq Key vĩnh viễn!", icon="🔑")
                st.rerun()
            st.info("Nhập Groq API Key để bật nhận dạng hình ảnh AI (Llama 3.2 90B Vision · miễn phí).")
            ai_key = ""

        # ── STEP 2: MULTI-IMAGE UPLOAD ── (hiện khi đã có Groq key)
        if ai_key:
            st.markdown("**Tải lên ảnh sản phẩm**")
            if "ai_uploader_key" not in st.session_state:
                st.session_state.ai_uploader_key = 0

            batch_imgs = st.file_uploader(
                "Chọn ảnh",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key=f"ai_batch_upload_{st.session_state.ai_uploader_key}",
            )

            if batch_imgs:
                st.caption(f"🖼️ Đã chọn **{len(batch_imgs)}** ảnh — {', '.join(f.name[:18] for f in batch_imgs[:3])}{'...' if len(batch_imgs) > 3 else ''}")

                scan_btn = st.button(
                    f"Phân tích {len(batch_imgs)} ảnh",
                    type="primary",
                    use_container_width=True,
                    key="btn_ai_scan_batch",
                )

                if scan_btn:
                    results = []
                    progress = st.progress(0, text="Đang khởi tạo...")

                    prompt = """Screenshot from Roblox game "Steal a Brainrot". Find the dark rounded INFO CARD near the pet.
The card has the pet NAME at the top and the large $M/s speed value is OUTSIDE the card.
Return ONLY valid JSON, no markdown:
{
  "Tên Pet": "exact pet name from the card",
  "Mutation": "Gold|Diamond|Divine|Rainbow|Bloodrot|Candy|Lava|Galaxy|Yin-Yang|Radioactive|Cursed|Celestial|Normal",
  "Tốc độ": "speed in Millions as plain number: $700M/s→700  $1.2B/s→1200  $55M/s→55  $500K/s→0.5"
}"""

                    headers = {
                        "Authorization": f"Bearer {ai_key}",
                        "Content-Type": "application/json"
                    }

                    # Tự động lấy danh sách Model (tránh vụ model cũ bị xoá/decommissioned)
                    target_model = None
                    all_models = []
                    try:
                        m_resp = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {ai_key}"})
                        if m_resp.status_code == 200:
                            m_data = m_resp.json()
                            all_models = [m["id"] for m in m_data.get("data", [])]
                            vision_models = [m for m in all_models if any(k in m.lower() for k in ["vision", "scout", "pixtral", "vl"])]
                            if vision_models:
                                target_model = next((m for m in vision_models if "90b" in m.lower() or "scout" in m.lower()), vision_models[0])
                        else:
                            st.error(f"❌ Groq API trả về lỗi HTTP {m_resp.status_code}: {m_resp.text[:200]}")
                            st.stop()
                    except Exception as _m_err:
                        st.error(f"❌ Không thể kết nối Groq API: {_m_err}")
                        st.stop()

                    if not target_model:
                        _model_hint = f"Danh sách model hiện tại ({len(all_models)}): {', '.join(all_models[:10])}{'...' if len(all_models) > 10 else ''}" if all_models else "Không lấy được danh sách model."
                        st.error(f"❌ Không tìm thấy Model Đọc Ảnh nào khả dụng! {_model_hint}")
                        st.stop()

                    st.toast(f"Model: {target_model}", icon="🦙")

                    # Đọc và encode tất cả ảnh trước (I/O)
                    _img_data = []
                    for img_f in batch_imgs:
                        img_f.seek(0)
                        _img_data.append({
                            "name": img_f.name,
                            "b64": base64.b64encode(img_f.read()).decode("utf-8"),
                            "mime": img_f.type or "image/jpeg",
                        })

                    _lock = threading.Lock()
                    _done_count = [0]

                    def _analyze_one(item):
                        _payload = {
                            "model": target_model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a game data extractor. Output ONLY valid JSON, no markdown, no extra text."
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {"type": "image_url", "image_url": {"url": f"data:{item['mime']};base64,{item['b64']}"}}
                                    ]
                                }
                            ],
                            "temperature": 0.0,
                            "max_tokens": 128
                        }
                        MAX_RETRY = 3
                        last_err = ""
                        for _attempt in range(MAX_RETRY):
                            try:
                                resp = requests.post(
                                    "https://api.groq.com/openai/v1/chat/completions",
                                    json=_payload, headers=headers, timeout=30
                                )
                                if resp.status_code == 429:
                                    time.sleep(15 + _attempt * 5)
                                    continue
                                if resp.status_code != 200:
                                    last_err = f"API {resp.status_code}: {resp.text[:150]}"
                                    break
                                txt = resp.json()["choices"][0]["message"]["content"].strip()
                                json_str = txt
                                if "```json" in txt:
                                    json_str = txt.split("```json")[-1].split("```")[0].strip()
                                elif "{" in txt:
                                    json_str = txt[txt.find("{"):txt.rfind("}")+1]
                                parsed = json.loads(json_str)
                                with _lock:
                                    _done_count[0] += 1
                                return {
                                    "_filename": item["name"],
                                    "_ok": True,
                                    "Tên Pet":   parsed.get("Tên Pet", ""),
                                    "Mutation":  parsed.get("Mutation", "Normal"),
                                    "M/s":       parsed.get("Tốc độ", ""),
                                    "Số Trait":  "None",
                                    "NameStock": "",
                                    "Giá Nhập":  "",
                                }
                            except (json.JSONDecodeError, KeyError) as _je:
                                last_err = f"Parse error: {_je}"
                                if _attempt < MAX_RETRY - 1:
                                    time.sleep(2)
                                continue
                            except Exception as _e:
                                last_err = str(_e)
                                break
                        with _lock:
                            _done_count[0] += 1
                        return {
                            "_filename": item["name"], "_ok": False, "_error": last_err,
                            "Tên Pet": "", "Mutation": "Normal", "M/s": "",
                            "Số Trait": "None", "NameStock": "", "Giá Nhập": "",
                        }

                    # Chạy song song, tối đa 4 luồng
                    _futures_map = {}
                    with ThreadPoolExecutor(max_workers=4) as _pool:
                        for _item in _img_data:
                            _futures_map[_pool.submit(_analyze_one, _item)] = _item["name"]
                        for _fut in as_completed(_futures_map):
                            results.append(_fut.result())
                            _n = _done_count[0]
                            progress.progress(
                                int(_n / len(_img_data) * 100),
                                text=f"⚡ Đã xong {_n}/{len(_img_data)} ảnh..."
                            )
                    # Sắp xếp lại theo thứ tự ảnh gốc
                    _order = {d["name"]: i for i, d in enumerate(_img_data)}
                    results.sort(key=lambda r: _order.get(r["_filename"], 999))

                    progress.progress(100, text="Hoàn thành phân tích!")
                    st.session_state.ai_batch_results = results
                    st.session_state.ai_show_dialog = True
                    st.rerun()

    # =========================================================
    # DIALOG PREVIEW + EDIT (hiện khi có kết quả AI)
    # =========================================================
    if st.session_state.get("ai_show_dialog") and st.session_state.get("ai_batch_results"):
        results = st.session_state.ai_batch_results

        @st.dialog("Kết Quả AI — Xem trước & Chỉnh sửa", width="large")
        def ai_preview_dialog():
            pet_opts_dlg   = get_name_options(pet_db)
            # Số Trait là con số đếm (1-15), không phụ thuộc vào file CSV
            trait_opts_dlg = ["None"] + [str(n) for n in range(1, 16)]
            ns_opts_dlg    = [""] + get_name_options(ns_db, fallback="")

            st.caption(f"**{len(results)}** ảnh đã phân tích · Xem lại và xác nhận trước khi lưu")

            # ── NameStock chung cho cả batch ──
            _gn1, _gn2 = st.columns([1, 3])
            use_global_ns = _gn1.checkbox("NameStock chung", key="dlg_global_ns_check",
                                           help="Áp dụng cùng 1 NameStock cho tất cả pet trong batch này")
            if use_global_ns:
                global_ns_val = _gn2.selectbox(
                    "NameStock áp dụng cho tất cả",
                    ns_opts_dlg,
                    key="dlg_global_ns_val",
                    label_visibility="collapsed",
                )
            else:
                global_ns_val = ""

            st.markdown("---")
            edited_rows = []
            all_valid = True

            for i, res in enumerate(results):
                fname = res.get("_filename", f"Image {i+1}")
                is_ok = res.get("_ok", False)

                _expander_label = (
                    f"❌ {fname} — Lỗi nhận dạng" if not is_ok
                    else f"✅ {fname} — {str(res.get('Tên Pet','?'))} · {str(res.get('Mutation','Normal'))} · {str(res.get('M/s','?'))}M/s"
                )
                with st.expander(_expander_label, expanded=True):
                    if not is_ok:
                        st.warning(f"Không thể đọc ảnh này · {res.get('_error','')} · Có thể nhập thủ công.")

                    img_col, form_col = st.columns([1, 3.5])

                    with img_col:
                        u_key = st.session_state.get("ai_uploader_key", 0)
                        current_files = st.session_state.get(f"ai_batch_upload_{u_key}", [])
                        matched_img = next((f for f in current_files if f.name == fname), None)
                        if matched_img:
                            st.image(matched_img, use_container_width=True)
                        else:
                            st.caption("Không thể tải ảnh")

                    with form_col:
                        c1d, c2d, c3d = st.columns(3)

                        ai_name = str(res.get("Tên Pet") or "")
                        if ai_name and ai_name.lower() not in [x.lower() for x in pet_opts_dlg]:
                            pet_opts_dlg = [ai_name] + pet_opts_dlg
                        pi = next((j for j, x in enumerate(pet_opts_dlg) if x.lower() == ai_name.lower()), 0)
                        r_name = c1d.selectbox(f"Tên Pet", pet_opts_dlg, index=pi, key=f"dlg_name_{i}")

                        ai_mut_v = str(res.get("Mutation") or "Normal")
                        mi = next((j for j, m in enumerate(MUTATION_OPTIONS) if m.lower() == ai_mut_v.lower()), 0)
                        r_mut = c2d.selectbox(f"Mutation", MUTATION_OPTIONS, index=mi, key=f"dlg_mut_{i}")

                        r_ms_raw = c3d.text_input(f"M/s", value=str(res.get("M/s") or ""), key=f"dlg_ms_{i}")

                        c4d, c5d, c6d = st.columns(3)
                        ai_trait = str(res.get("Số Trait") or "None").strip()
                        # Tự thêm vào list nếu model trả giá trị ngoài 1-15
                        if ai_trait not in trait_opts_dlg:
                            trait_opts_dlg = trait_opts_dlg + [ai_trait]
                        ti = next((j for j, t in enumerate(trait_opts_dlg) if t.lower() == ai_trait.lower()), 0)
                        r_trait = c4d.selectbox(f"Số Trait", trait_opts_dlg, index=ti, key=f"dlg_trait_{i}")

                        # NameStock: dùng global nếu checkbox bật, ngược lại dùng per-row
                        if use_global_ns:
                            r_ns = global_ns_val
                            _ns_display = global_ns_val if global_ns_val else "—"
                            c5d.markdown(
                                f'<div style="padding-top:1.8rem;font-size:0.82rem;color:hsl(217, 91%, 70%);">'
                                f'NS: <b>{_ns_display}</b> <span style="color:hsl(217.2, 20%, 40%);">(chung)</span></div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            r_ns = c5d.selectbox(f"NameStock", ns_opts_dlg, key=f"dlg_ns_{i}")

                        r_cost = c6d.text_input(f"Giá nhập", placeholder="150k / 1.5tr / 1500000", key=f"dlg_cost_{i}")

                    r_ms = parse_usd(r_ms_raw)
                    err_row = []
                    if not r_name or r_name == "None": err_row.append("Tên Pet")
                    if r_ms <= 0:  err_row.append("M/s")
                    if not r_ns.strip(): err_row.append("NameStock")
                    if parse_vnd(r_cost) <= 0: err_row.append("Giá nhập")
                    if err_row:
                        st.info(f"Thiếu thông tin: {', '.join(err_row)}")
                        all_valid = False

                    edited_rows.append({
                        "Tên Pet":   r_name,
                        "Mutation":  r_mut,
                        "M/s":       r_ms,
                        "Số Trait":  r_trait,
                        "NameStock": r_ns,
                        "Giá Nhập":  parse_vnd(r_cost),
                        "_valid":    len(err_row) == 0,
                    })

            st.markdown("---")
            col_cancel, col_save = st.columns([1, 2])
            with col_cancel:
                if st.button("Huỷ bỏ", use_container_width=True):
                    st.session_state.ai_show_dialog = False
                    st.session_state.ai_batch_results = []
                    st.session_state.ai_uploader_key = st.session_state.get("ai_uploader_key", 0) + 1
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

                    for r in edited_rows:
                        if not r["_valid"]:
                            continue
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
                            "Giá Nhập":   float(r["Giá Nhập"]),
                            "Giá Bán":    0.0,
                            "Lợi Nhuận":  0.0,
                            "Doanh Thu":  0.0,
                            "Ngày Nhập":  _ngay_batch,
                            "Ngày Bán":   "-",
                            "Auto Title": generate_auto_title(
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

                    # Toàn bộ I/O nằm trong spinner — không có khoảng freeze nào bên ngoài
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
                            st.session_state.ai_show_dialog = False
                            st.session_state.ai_batch_results = []
                            st.session_state.ai_uploader_key = st.session_state.get("ai_uploader_key", 0) + 1
                            st.session_state.ai_expander = False
                            _save_ok = True

                    if _save_ok:
                        st.toast(f"✅ Đã lưu {saved} mục thành công", icon="✅")
                        st.rerun()

        ai_preview_dialog()
