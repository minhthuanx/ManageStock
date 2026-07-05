# CHANGELOG — Sửa autofill M/s khi import JSON

**Ngày:** 2026-06-29

---

## Mục tiêu

Khi import JSON từ game, trường **M/s** tự động hiển thị chính xác hơn:
- **≥ 1 tỷ raw units** → hiển thị dạng `X.XB/s` (1 số thập phân), ví dụ `2.2B/s`
- **< 1 tỷ raw units** → giữ nguyên hiển thị `XXXM/s` từ `gen_text`, ví dụ `760M/s`

Trước đó code chỉ lấy `gen_text` nên luôn hiển thị `2B/s` thay vì `2.2B/s`.

---

## Các thay đổi

### 1. `_helpers.py` — `parse_json_import()` (dòng ~307–316)

**Trước:**
```python
gen_val = item.get("gen_value")
if gen_val is not None:
    try:
        ms_val = float(gen_val) / 1000000.0
        if ms_val >= 1000:
            ms_val = parse_gen_text(item.get("gen_text", ""))
    except Exception:
        ms_val = parse_gen_text(item.get("gen_text", ""))
else:
    ms_val = parse_gen_text(item.get("gen_text", ""))
```

**Sau:**
```python
gen_val = item.get("gen_value")
if gen_val is not None:
    try:
        _gen_f = float(gen_val)
        if _gen_f >= 1_000_000_000:
            ms_val = _gen_f / 1_000_000
        else:
            ms_val = parse_gen_text(item.get("gen_text", ""))
    except Exception:
        ms_val = parse_gen_text(item.get("gen_text", ""))
else:
    ms_val = parse_gen_text(item.get("gen_text", ""))
```

**Giải thích:** `gen_value` ≥ 1 tỷ → lấy raw value chia 1 triệu → float M/s (1200.0). < 1 tỷ → fallback `gen_text` giữ nguyên.

---

### 2. `tab_kho_json.py` — Caption hiển thị trong dialog (dòng ~146–147)

**Trước:**
```python
ms_val = res.get('M/s')
st.caption(f"M/s: {f'{ms_val:g}' if ms_val else '?'} | Traits: {res.get('Số Trait')}")
```

**Sau:**
```python
ms_val = res.get('M/s')
if ms_val and ms_val >= 1000:
    ms_str = f"{ms_val / 1000:.1f}B/s"
else:
    ms_str = f"{ms_val:g}M/s" if ms_val else "?"
st.caption(f"M/s: {ms_str} | Traits: {res.get('Số Trait')}")
```

---

### 3. `tab_kho_json.py` — Autofill text_input M/s (dòng ~167–168)

**Trước:**
```python
val_ms = res.get("M/s")
str_ms = f"{val_ms:g}" if val_ms else ""
```

**Sau:**
```python
val_ms = res.get("M/s")
if val_ms and val_ms >= 1000:
    str_ms = f"{val_ms / 1000:.1f}B/s"
else:
    str_ms = f"{val_ms:g}" if val_ms else ""
```

---

## Ví dụ kết quả

| `gen_value` | `gen_text` | Kết quả autofill | Giải thích |
|---|---|---|---|
| 2,240,000,000 | 2B/s | `2.2B/s` | ≥ 1 tỷ → dùng gen_value |
| 1,500,000,000 | 1B/s | `1.5B/s` | ≥ 1 tỷ → dùng gen_value |
| 760,000,000 | 760M/s | `760M/s` | < 1 tỷ → fallback gen_text |
| (thiếu) | 700M/s | `700M/s` | gen_value None → fallback gen_text |

---

## Phạm vi ảnh hưởng

- **Chỉ** thay đổi logic parse JSON import trong `parse_json_import()`.
- **Chỉ** thay đổi hiển thị và autofill trong dialog JSON import.
- **Không** ảnh hưởng: AI Vision (`tab_kho_ai.py`), form nhập thủ công (`tab_kho_form.py`), bulk sell (`tab_kho_bulk.py`), Eldorado, database, title generation.
- `parse_usd()` downstream vẫn hoạt động vì nhận string `"2.2B/s"` → `2200.0`.
- `generate_auto_title()` nhận float M/s → không bị ảnh hưởng.
