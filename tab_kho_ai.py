import json
import os
import re
import time
import base64
import threading
import requests
import pandas as pd
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from _timezone import now_vn, now_str, now_iso
import _icons as IC
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
from _eldorado_helpers import _HAS_ELDORADO
from _wiki import get_pet_list, normalize_pet_name

try:
    from eldorado_client import DELIVERY_MAP, OTHER_TRADE_ENV_ID
except ImportError:
    DELIVERY_MAP = {}


def _clean_groq_key(raw: str) -> str:
    """Loại bỏ ký tự ẩn (zero-width space ​, BOM...) — nguyên nhân 401 dù key nhìn đúng."""
    if not raw:
        return ""
    cleaned = re.sub(r"[​‌‍⁠﻿]", "", raw)
    return re.sub(r"[^A-Za-z0-9_\-]", "", cleaned)


def _verify_groq_key(key: str) -> tuple[bool, str]:
    """Gọi thử GET /models: 200 = key hoạt động; ngược lại trả thông báo lỗi cụ thể."""
    try:
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
        if r.status_code == 200:
            return True, ""
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, f"Không kết nối được: {e}"


class _FakeUploadedFile:
    """Dùng để lưu ảnh listing tạm trong session_state (giống tab_kho_json)."""
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


def render_ai_vision(df, pet_db, ns_db, trait_db, eld_client=None):
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
                _raw_key = ai_key_input.strip()
                _clean = _clean_groq_key(_raw_key)
                if _clean != _raw_key:
                    st.warning("Phát hiện ký tự ẩn trong key — đã tự động làm sạch (có thể do paste từ Zalo/Messenger).")
                if not _clean or not _clean.startswith("gsk_"):
                    st.error("Key Groq không hợp lệ: phải bắt đầu bằng 'gsk_' và chỉ gồm chữ/số. Vui lòng kiểm tra lại.")
                else:
                    _ok, _msg = _verify_groq_key(_clean)
                    if _ok:
                        st.session_state.groq_key = _clean
                        _save_groq_key_to_supabase(_clean)
                        st.toast("Đã xác minh & lưu Groq Key vĩnh viễn!", icon="🔑")
                        st.rerun()
                    else:
                        st.error(f"❌ Key bị từ chối bởi Groq ({_msg}). Kiểm tra lại key tại console.groq.com/keys — chú ý không dư/mất ký tự khi paste.")
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
                st.caption(f"Đã chọn **{len(batch_imgs)}** ảnh — {', '.join(f.name[:18] for f in batch_imgs[:3])}{'...' if len(batch_imgs) > 3 else ''}")

                # Danh sách tên pet chuẩn từ wiki (cache 7 ngày) — khóa prompt + chuẩn hóa kết quả
                wiki_pets = get_pet_list()
                if wiki_pets:
                    st.caption(f"📚 Wiki: **{len(wiki_pets)}** tên pet hợp lệ")

                scan_btn = st.button(
                    f"Phân tích {len(batch_imgs)} ảnh",
                    type="primary",
                    use_container_width=True,
                    key="btn_ai_scan_batch",
                )

                if scan_btn:
                    results = []
                    progress = st.progress(0, text="Đang khởi tạo...")

                    prompt = f"""Screenshot from Roblox game "Steal a Brainrot". Find the dark rounded INFO CARD near the pet.
The card has the pet NAME at the top and the large $M/s speed value is OUTSIDE the card.
The pet name MUST be chosen from this exact list (pick the closest match, do NOT invent names):
{', '.join(wiki_pets) if wiki_pets else '(no pet list available — read the name as-is)'}
Return ONLY valid JSON, no markdown:
{{
  "Tên Pet": "exact pet name from the card",
  "Mutation": "Gold|Diamond|Divine|Rainbow|Bloodrot|Candy|Lava|Galaxy|Yin-Yang|Radioactive|Cursed|Cyber|Phantom|Crystal|Normal",
  "Tốc độ": "speed in Millions as plain number: $700M/s→700  $1.2B/s→1200  $55M/s→55  $500K/s→0.5"
}}"""

                    headers = {
                        "Authorization": f"Bearer {ai_key}",
                        "Content-Type": "application/json"
                    }

                    # ── XÁC THỰC KEY + TÌM MODEL VISION ──
                    target_model = None
                    all_models = []
                    try:
                        m_resp = requests.get("https://api.groq.com/openai/v1/models",
                                              headers={"Authorization": f"Bearer {ai_key}"}, timeout=15)
                        if m_resp.status_code == 200:
                            m_data = m_resp.json()
                            all_models = [m["id"] for m in m_data.get("data", [])]
                        elif m_resp.status_code in (401, 403):
                            st.error(f"Groq API Key không hợp lệ hoặc đã hết hạn (HTTP {m_resp.status_code}). "
                                     f"Nhấn 'Thay đổi' để nhập key mới tại console.groq.com/keys")
                            st.stop()
                        else:
                            st.error(f"Groq API trả về lỗi HTTP {m_resp.status_code}: {m_resp.text[:200]}")
                            st.stop()
                    except Exception as _m_err:
                        st.error(f"Không thể kết nối Groq API: {_m_err}")
                        st.stop()

                    # Model vision đã biết (Groq gỡ llama-4 cũ, hiện dùng qwen3.6-27b; có thể thêm mới theo thời gian)
                    _KNOWN_VISION = [
                        "qwen/qwen3.6-27b",
                        "qwen3.6-27b",
                        "meta-llama/llama-4-scout-17b-16e-instruct",
                        "llama-4-scout-17b-16e-instruct",
                        "meta-llama/llama-4-maverick-17b-128e-instruct",
                    ]
                    vision_models = [
                        m for m in all_models
                        if any(k in m.lower() for k in ["qwen3", "qwen-3", "scout", "maverick", "pixtral", "vl", "vision"])
                    ]
                    target_model = (
                        next((m for m in vision_models if "qwen" in m.lower()), vision_models[0])
                        if vision_models
                        else next((m for m in _KNOWN_VISION if m in all_models), None)
                    )
                    if not target_model:
                        _model_hint = f"Danh sách model hiện tại ({len(all_models)}): {', '.join(all_models[:10])}{'...' if len(all_models) > 10 else ''}" if all_models else "Không lấy được danh sách model."
                        st.error(f"Không tìm thấy Model Đọc Ảnh nào khả dụng! {_model_hint}")
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
                                # Chuẩn hóa tên pet theo danh sách wiki (sửa lỗi đọc lệch của model)
                                _ai_name = normalize_pet_name(str(parsed.get("Tên Pet", "")), wiki_pets)
                                return {
                                    "_filename": item["name"],
                                    "_ok": True,
                                    "Tên Pet":   _ai_name,
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
                                text=f"Đã xong {_n}/{len(_img_data)} ảnh..."
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
                    f"× {fname} — Lỗi nhận dạng" if not is_ok
                    else f"✓ {fname} — {str(res.get('Tên Pet','?'))} · {str(res.get('Mutation','Normal'))} · {str(res.get('M/s','?'))}M/s"
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
                                f'<div style="padding-top:1.8rem;font-size:0.82rem;color:#d4d4d8;">'
                                f'NS: <b>{_ns_display}</b> <span style="color:#777777;">(chung)</span></div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            r_ns = c5d.selectbox(f"NameStock", ns_opts_dlg, key=f"dlg_ns_{i}")

                        r_cost = c6d.text_input(f"Giá nhập", placeholder="150k / 1.5tr / 1500000", key=f"dlg_cost_{i}")

                        # ── Giá bán $ + tái sử dụng ảnh đã upload (Eldorado) ──
                        if _HAS_ELDORADO and eld_client and eld_client.logged_in:
                            _price_col = st.empty()
                            r_price_raw = _price_col.text_input(
                                "Giá bán ($)", value="",
                                placeholder="$0.50 (bỏ trống = không push Eldorado)",
                                key=f"dlg_ai_price_{i}", label_visibility="collapsed",
                            )
                            # Ảnh đã upload để AI phân tích được tái dùng làm ảnh listing
                            u_key = st.session_state.get("ai_uploader_key", 0)
                            current_files = st.session_state.get(f"ai_batch_upload_{u_key}", [])
                            matched_img = next((f for f in current_files if f.name == fname), None)
                            if matched_img:
                                _img_bytes = matched_img.getvalue()
                                r_img = _FakeUploadedFile(_img_bytes, fname, matched_img.type or "image/png")
                            else:
                                r_img = None
                        else:
                            r_img = None
                            r_price_raw = ""

                    r_ms = parse_usd(r_ms_raw)
                    r_price = 0.0
                    if r_price_raw.strip():
                        try:
                            r_price = float(r_price_raw)
                        except (ValueError, TypeError):
                            r_price = 0.0
                    err_row = []
                    if not r_name or r_name == "None": err_row.append("Tên Pet")
                    if r_ms <= 0:  err_row.append("M/s")
                    if not r_ns.strip(): err_row.append("NameStock")
                    if parse_vnd(r_cost) <= 0: err_row.append("Giá nhập")
                    # Validate push fields (nếu Eldorado connected)
                    if _HAS_ELDORADO and eld_client and eld_client.logged_in:
                        if r_price_raw.strip():
                            if r_price < 0.50: err_row.append("giá bán tối thiểu $0.50")
                            if not r_img: err_row.append("thiếu ảnh pet (không push được)")
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
                        "_title":    generate_auto_title(r_name, r_mut, r_trait, r_ms, r_ns),
                        "_price":    r_price,
                        "_image":    r_img,
                        "_filename": fname,
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
                        # ── PUSH LÊN ELDORADO SAU KHI LƯU DB ──
                        # Những pet có nhập giá bán $ mới push (ảnh dùng lại ảnh upload lúc scan)
                        _push_items = [r for r in edited_rows if r.get("_valid")
                                       and r.get("_price", 0) >= 0.50]
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
                                        _pet_name = _pcfg.get("Tên Pet", "")
                                        _img_data = None
                                        # Ảnh đã upload để AI phân tích → dùng luôn làm ảnh listing
                                        if _pcfg.get("_image"):
                                            _pcfg["_image"].seek(0)
                                            _img_bytes = _pcfg["_image"].read()
                                            _img_data = eld_client.upload_image(
                                                _img_bytes, _pcfg["_image"].name or "image.png")
                                            if _img_data and _img_data.get("_rate_limit"):
                                                _img_data = None
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
                                        time.sleep(0.5)
                        st.session_state.ai_push_results = _push_results
                        st.session_state.ai_push_total = len(_push_items)
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

        ai_preview_dialog()

    # =========================================================
    # KẾT QUẢ PUSH ELDORADO (sau rerun)
    # =========================================================
    if st.session_state.get("ai_push_results"):
        _pr = st.session_state.ai_push_results
        _pt = st.session_state.ai_push_total
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
        if st.button("× Ẩn kết quả push", key="btn_hide_ai_push"):
            del st.session_state.ai_push_results
            del st.session_state.ai_push_total
            st.rerun()
