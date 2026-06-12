"""
Pure utility functions, formatting, parsing, and shared helpers.
"""
import json
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st

from _config import (
    COL_MAP, REVERSE_MAP, MAIN_SCHEMA, MUTATION_ICONS,
    OWNER_NS_FILE, BACKUP_DIR,
)
from _timezone import now_vn, now_str, now_iso

# ─── Search helpers ───────────────────────────────────────────────────────
_SEARCH_KEYS = ["sell_search_q", "inv_table_search", "copy_title_search",
                "bulk_sell_search", "bulk_table_search"]


def _clear_searches():
    st.session_state["_search_ver"] = st.session_state.get("_search_ver", 0) + 1


def _sv() -> str:
    return str(st.session_state.get("_search_ver", 0))


# ─── DataFrame utilities ──────────────────────────────────────────────────
def normalize_df(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=schema.keys())
    df = df.dropna(how="all").copy()
    for col, default in schema.items():
        if col not in df.columns:
            df[col] = default
    df = df[list(schema.keys())]
    for col, default in schema.items():
        if isinstance(default, (int, float)):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default)
        else:
            df[col] = df[col].fillna(default).astype(str)
    return df


def next_id(df: pd.DataFrame, col: str) -> int:
    if df.empty:
        return 1
    return int(pd.to_numeric(df[col], errors="coerce").fillna(0).max() + 1)


def reindex(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.reset_index(drop=True).copy()
    if col in df.columns:
        df[col] = range(1, len(df) + 1)
    return df


def append_row(df: pd.DataFrame, row: dict, schema: dict) -> pd.DataFrame:
    return normalize_df(pd.concat([df, pd.DataFrame([row])], ignore_index=True), schema)


def get_name_options(db: pd.DataFrame, fallback: str = "None") -> list:
    if db.empty:
        return [fallback]
    vals = db["Name"].astype(str).str.strip()
    vals = vals[vals != ""]
    return vals.drop_duplicates().tolist() or [fallback]


# ─── Price parsing ────────────────────────────────────────────────────────
def parse_vnd(s: str) -> float:
    """Parse gia VNĐ — shorthand: 150k, 1.5tr, 2ty."""
    raw = str(s).strip().lower().replace(" ", "")
    if not raw:
        return 0.0
    multiplier = 1
    for suffix, mult in [("tỷ", 1_000_000_000), ("b", 1_000_000_000),
                         ("tr", 1_000_000), ("m", 1_000_000),
                         ("k", 1_000)]:
        if raw.endswith(suffix):
            raw = raw[:-len(suffix)]
            multiplier = mult
            break
    dot_count   = raw.count(".")
    comma_count = raw.count(",")
    if dot_count + comma_count > 1:
        raw = raw.replace(".", "").replace(",", "")
    elif comma_count == 1 and dot_count == 0:
        parts = raw.split(",")
        if len(parts[1]) == 3 and parts[1].isdigit():
            raw = raw.replace(",", "")
        else:
            raw = raw.replace(",", ".")
    elif dot_count == 1 and comma_count == 0:
        pass
    else:
        raw = re.sub(r"[^0-9]", "", raw)
    try:
        return float(raw) * multiplier if raw else 0.0
    except ValueError:
        return 0.0


def parse_usd(s: str) -> float:
    s_str = str(s).upper()
    cleaned = re.sub(r"[^0-9.]", "", s_str)
    try:
        val = float(cleaned) if cleaned else 0.0
        if "B" in s_str:
            val *= 1000
        return val
    except ValueError:
        return 0.0


# ─── Formatting ───────────────────────────────────────────────────────────
def fmt_vnd(v: float) -> str:
    return f"₫{v:,.0f}"


def fmt_short(v: float) -> str:
    """Format for chart labels: ₫1.5M style."""
    v = float(v)
    sign = "-" if v < 0 else ""
    abs_v = abs(v)
    if abs_v >= 1_000_000:
        return f"{sign}₫{abs_v/1_000_000:.3f}M"
    if abs_v >= 1_000:
        return f"{sign}₫{abs_v/1_000:.1f}K"
    return f"{sign}₫{int(abs_v):,}"


def fmt_ngay_ton(v) -> str:
    """Hiển thị thoi gian ton: phut / gio / ngay."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "-"
    total_sec = v * 86400
    if total_sec < 60:
        return "vừa nhập"
    total_min = int(total_sec // 60)
    if total_min < 60:
        return f"{total_min}p"
    total_h = total_min // 60
    rem_min = total_min % 60
    if total_h < 24:
        return f"{total_h}g{rem_min}p" if rem_min else f"{total_h}g"
    days = int(v)
    rem_h = int((v - days) * 24)
    return f"{days} ngày {rem_h}g" if rem_h else f"{days} ngày"


# ─── Auto Title ───────────────────────────────────────────────────────────
def generate_auto_title(pet_name, mutation, trait_str, ms_value, namestock) -> str:
    icon = MUTATION_ICONS.get(str(mutation).lower(), "🌟")
    _t = str(trait_str).strip() if trait_str else ""
    _t = re.sub(r'\s*[Tt]raits?\s*$', '', _t).strip()
    if _t and _t.lower() != "none" and _t != "0":
        _label = "Trait" if _t == "1" else "Traits"
        t_str = f" [{_t} {_label}]"
    else:
        t_str = ""
    display_ms = f"{ms_value / 1000:g}B/s" if ms_value >= 1000 else f"{ms_value:g}M/s"
    ns_str = f" {namestock}" if namestock else ""
    if str(mutation).lower() == "normal" or not mutation:
        return f"🌸{pet_name} {display_ms}{t_str}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"
    return f"🌸{icon}{mutation} {pet_name} {display_ms}{t_str}{icon}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"


# ─── Ngay Ton calculation ────────────────────────────────────────────────
def calc_ngay_ton(row) -> float:
    def _parse_ts(ts_str):
        if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
            return None
        try:
            dt = datetime.fromisoformat(str(ts_str))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN_TZ)
            return dt
        except Exception:
            return None

    def _parse_text_date(d_str):
        if not d_str or str(d_str).strip() in ("", "nan", "None", "-"):
            return None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(str(d_str).strip(), fmt)
                return dt.replace(tzinfo=VN_TZ)
            except Exception:
                pass
        return None

    from _timezone import VN_TZ

    status = str(row.get("Trạng Thái", ""))
    t_nhap = _parse_ts(row.get("time_nhap", "")) or _parse_text_date(row.get("Ngày Nhập", ""))
    if t_nhap is None:
        return 0.0
    if "Đã bán" in status:
        t_ban = _parse_ts(row.get("time_ban", "")) or _parse_text_date(row.get("Ngày Bán", ""))
        if t_ban:
            return max(0.0, (t_ban - t_nhap).total_seconds() / 86400)
    return max(0.0, (now_vn() - t_nhap).total_seconds() / 86400)


def apply_ngay_ton(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["Ngày Tồn"] = df.apply(calc_ngay_ton, axis=1)
    return df


# ─── Shared token-based search (replaces 5x copy-paste) ──────────────────
def token_search(df: pd.DataFrame, query: str, search_cols: list) -> pd.Series:
    """Token-based search: each token must appear in at least one column.
    Returns boolean mask Series."""
    if not query.strip():
        return pd.Series([True] * len(df), index=df.index)
    tokens = [t for t in re.split(r'[\s\-]+', query.strip().lower()) if t]
    haystack = df[[c for c in search_cols if c in df.columns]].astype(str).apply(
        lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True)
    )
    combined = haystack.apply(lambda row: ' '.join(row), axis=1)
    mask = pd.Series([True] * len(df), index=df.index)
    for tok in tokens:
        mask &= combined.str.contains(tok, regex=False, na=False)
    return mask


# ─── Shared is-today checks (replaces 3x duplication) ────────────────────
def is_today_timestamp(ts_str, target_date=None) -> bool:
    """Check if an ISO timestamp belongs to target_date (default: today VN)."""
    from _timezone import VN_TZ
    if target_date is None:
        target_date = now_vn().date()
    if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
        return False
    try:
        dt = datetime.fromisoformat(str(ts_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=VN_TZ)
        return dt.astimezone(VN_TZ).date() == target_date
    except Exception:
        return False


def is_today_bulk_date(d_str, target_date=None) -> bool:
    """Check if dd/mm/yyyy HH:MM string belongs to target_date."""
    if target_date is None:
        target_date = now_vn().date()
    if not d_str or str(d_str).strip() in ("", "nan", "None", "-"):
        return False
    try:
        return datetime.strptime(str(d_str).strip(), "%d/%m/%Y %H:%M").date() == target_date
    except Exception:
        return False


# ─── JSON Import ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_gen_text(gen_text: str) -> float:
    if not gen_text:
        return 0.0
    try:
        gen_str = str(gen_text).strip().upper()
        gen_str = gen_str.replace(" ", "").replace("/S", "")
        multiplier = 1
        if "B" in gen_str:
            gen_str = gen_str.replace("B", "")
            multiplier = 1000
        elif "M" in gen_str:
            gen_str = gen_str.replace("M", "")
            multiplier = 1
        elif "K" in gen_str:
            gen_str = gen_str.replace("K", "")
            multiplier = 0.001
        value = float(gen_str) if gen_str else 0.0
        return value * multiplier
    except (ValueError, TypeError):
        return 0.0


def parse_json_import(json_str: str) -> list:
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return []
        _on_map = st.session_state.get("_owner_ns_map", {})
        _pet_ns_map = build_pet_namestock_map()
        _pet_ns_lower = {k.lower(): v for k, v in _pet_ns_map.items()}
        results = []
        for item in data:
            if not isinstance(item, dict):
                continue
            pet_name = str(item.get("name", ""))
            if not pet_name.strip():
                continue
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
            _owner = str(item.get("owner", "")).strip()
            _ns_from_owner = _on_map.get(_owner.lower(), "") if _owner else ""
            _ns_from_pet = (_pet_ns_lower.get(pet_name.strip().lower()) or [""])[0] if pet_name.strip() else ""
            _ns = _ns_from_owner or _ns_from_pet
            _owner_unmapped = bool(_owner and not _ns_from_owner)
            results.append({
                "Tên Pet": pet_name,
                "Mutation": str(item.get("mutation", "Normal")).strip() or "Normal",
                "M/s": ms_val,
                "Số Trait": str(len(item.get("traits", []))) if item.get("traits") else "None",
                "NameStock": _ns,
                "_ok": True,
                "_owner": _owner,
                "_owner_unmapped": _owner_unmapped,
                "_original_json": item,
            })
        return results
    except (json.JSONDecodeError, ValueError):
        return []


def build_pet_namestock_map() -> dict:
    pet_ns_map = {}
    if hasattr(st.session_state, 'df') and not st.session_state.df.empty:
        try:
            for _, row in st.session_state.df.iterrows():
                pet = str(row.get("Tên Pet", "")).strip()
                ns = str(row.get("NameStock", "")).strip()
                if pet and ns:
                    if pet not in pet_ns_map:
                        pet_ns_map[pet] = set()
                    pet_ns_map[pet].add(ns)
            pet_ns_map = {k: sorted(list(v)) for k, v in pet_ns_map.items()}
        except Exception:
            pass
    return pet_ns_map


# ─── Owner NameStock mapping ─────────────────────────────────────────────
def _load_owner_ns_map() -> dict:
    _m = {}
    if os.path.exists(OWNER_NS_FILE):
        try:
            for line in open(OWNER_NS_FILE, "r", encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    _k, _v = line.split(":", 1)
                    _k, _v = _k.strip().lower(), _v.strip()
                    if _k and _v:
                        _m[_k] = _v
        except Exception:
            pass
    return _m


def _save_owner_ns_map(m: dict):
    try:
        with open(OWNER_NS_FILE, "w", encoding="utf-8") as f:
            for k, v in sorted(m.items()):
                f.write(f"{k}:{v}\n")
    except Exception:
        pass
