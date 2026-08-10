"""
Supabase CRUD, data loading/sync, CSV I/O, settings persistence.
"""
import json
import os
import shutil

import pandas as pd
import streamlit as st
from supabase import create_client, Client

from _config import (
    COL_MAP, REVERSE_MAP, DB_FILE, BULK_FILE, BULK_HISTORY,
    BACKUP_DIR, MAIN_SCHEMA, BULK_SCHEMA, HISTORY_SCHEMA,
)
from _timezone import now_vn

# =============================================================================
# SUPABASE INIT
# =============================================================================
supabase_client: Client | None = None
USE_SUPABASE = False


@st.cache_resource(show_spinner=False)
def _get_supabase() -> tuple["Client | None", bool]:
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        elif "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
            return None, False
        return create_client(url, key), True
    except Exception as e:
        st.toast(f"⚠️ Không thể kết nối Supabase: {e}", icon="⚠️")
        return None, False


def _init_supabase():
    global supabase_client, USE_SUPABASE
    supabase_client, USE_SUPABASE = _get_supabase()


_init_supabase()

# =============================================================================
# COLUMN CONVERSION
# =============================================================================

def to_db(record: dict) -> dict:
    """Convert display-name dict → snake_case for Supabase."""
    out = {}
    for k, v in record.items():
        if k == "index":
            continue
        mapped = COL_MAP.get(k, k.lower().replace(" ", "_").replace("/", "_"))
        if isinstance(v, float) and pd.isna(v):
            v = None
        if mapped in ("time_nhap", "time_ban"):
            if not v or str(v).strip() in ("", "None", "nan", "NaT", "null", "-"):
                v = None
        if mapped in ("id", "ngay_ton") and v is not None:
            try:
                v = int(float(v))
            except (ValueError, TypeError):
                v = None
        out[mapped] = v
    return out


def from_db(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=REVERSE_MAP)

# =============================================================================
# CRUD OPERATIONS
# =============================================================================

def sb_insert(table: str, data: dict) -> bool:
    if not USE_SUPABASE:
        return False
    try:
        r = supabase_client.table(table).insert(data).execute()
        return bool(r.data)
    except Exception as e:
        st.toast(f"❌ Insert {table}: {e}", icon="❌")
        return False


def sb_insert_returning(table: str, data: dict) -> dict | None:
    if not USE_SUPABASE:
        return None
    try:
        r = supabase_client.table(table).insert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        st.toast(f"❌ Insert {table}: {e}", icon="❌")
        return None


def sb_insert_batch(table: str, records: list[dict]) -> bool:
    if not USE_SUPABASE or not records:
        return False
    try:
        r = supabase_client.table(table).insert(records).execute()
        return bool(r.data)
    except Exception as e:
        st.toast(f"❌ Batch insert {table}: {e}", icon="❌")
        return False


def sb_update(table: str, data: dict, col: str, val) -> bool:
    if not USE_SUPABASE:
        return False
    try:
        r = supabase_client.table(table).update(data).eq(col, val).execute()
        return bool(r.data)
    except Exception as e:
        st.toast(f"❌ Update {table}: {e}", icon="❌")
        return False


def sb_delete(table: str, col: str, val) -> bool:
    if not USE_SUPABASE:
        return False
    try:
        supabase_client.table(table).delete().eq(col, val).execute()
        return True
    except Exception as e:
        st.toast(f"❌ Delete {table}: {e}", icon="❌")
        return False


def sb_select(table: str, order: str = "stt") -> pd.DataFrame:
    if not USE_SUPABASE:
        return pd.DataFrame()
    try:
        r = supabase_client.table(table).select("*").order(order).limit(-1).execute()
        if r.data:
            return from_db(pd.DataFrame(r.data))
        return pd.DataFrame()
    except Exception as e:
        st.toast(f"❌ Select {table}: {e}", icon="❌")
        return pd.DataFrame()


def sb_upsert(table: str, records: list[dict], on_conflict: str = None) -> bool:
    if not USE_SUPABASE or not records:
        return False
    try:
        if on_conflict:
            supabase_client.table(table).upsert(records, on_conflict=on_conflict).execute()
        else:
            supabase_client.table(table).upsert(records).execute()
        return True
    except Exception as e:
        st.toast(f"❌ Upsert {table}: {e}", icon="❌")
        return False


def find_duplicates(table: str) -> pd.DataFrame:
    if not USE_SUPABASE:
        return pd.DataFrame()
    try:
        r = supabase_client.table(table).select("*").limit(-1).execute()
        if not r.data:
            return pd.DataFrame()
        df = pd.DataFrame(r.data)
        data_cols = [c for c in df.columns if c != "id"]
        if not data_cols:
            return pd.DataFrame()
        return df[df.duplicated(subset=data_cols, keep=False)].sort_values(data_cols)
    except Exception as e:
        st.toast(f"❌ find_duplicates {table}: {e}", icon="❌")
        return pd.DataFrame()

# =============================================================================
# PAGINATION
# =============================================================================

def _fetch_all_with_pagination(table_name: str, order_col: str, batch_size: int = 1000) -> list:
    if not USE_SUPABASE or not supabase_client:
        return []
    all_data = []
    offset = 0
    while True:
        try:
            r = (supabase_client
                 .table(table_name)
                 .select("*")
                 .order(order_col)
                 .range(offset, offset + batch_size - 1)
                 .execute())
            if not r.data:
                break
            all_data.extend(r.data)
            if len(r.data) < batch_size:
                break
            offset += batch_size
        except Exception as e:
            st.toast(f"⚠️ Lỗi khi fetch {table_name} (offset {offset}): {e}", icon="⚠️")
            break
    return all_data

# =============================================================================
# CSV I/O
# =============================================================================

def load_csv(file: str, schema: dict) -> pd.DataFrame:
    if not os.path.exists(file):
        return pd.DataFrame(columns=schema.keys())
    try:
        return normalize_df(pd.read_csv(file), schema)
    except Exception:
        return pd.DataFrame(columns=schema.keys())


def save_csv(df: pd.DataFrame, file: str) -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = now_vn().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BACKUP_DIR, f"{os.path.basename(file)}_{ts}.bak")
    if os.path.exists(file):
        shutil.copy2(file, bak)
        existing = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.basename(file))])
        for old in existing[:-10]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except Exception:
                pass
    tmp = f"{file}.tmp"
    try:
        df.to_csv(tmp, index=False, encoding="utf-8-sig")
        os.replace(tmp, file)
    except Exception as e:
        st.toast(f"❌ Lưu CSV lỗi: {e}", icon="❌")
        if os.path.exists(tmp):
            os.remove(tmp)


# Avoid circular import: load_csv uses normalize_df from _helpers
# Import here after functions are defined
from _helpers import normalize_df

# =============================================================================
# DATA LOADING (cache_data TTL=300s)
# =============================================================================

@st.cache_data(show_spinner=False, ttl=300)
def load_inventory() -> pd.DataFrame:
    if USE_SUPABASE:
        try:
            all_data = _fetch_all_with_pagination("inventory", "stt")
            if all_data:
                df = pd.DataFrame(all_data)
                st.session_state["_inv_sb_cols"] = set(df.columns)
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "id"
                df = df.rename(columns=rename_map)
                for _tc in ["time_nhap", "time_ban"]:
                    if _tc in df.columns:
                        df[_tc] = df[_tc].apply(_to_vn_iso)
                return normalize_df(df, MAIN_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load inventory: {e}", icon="❌")
    return load_csv(DB_FILE, MAIN_SCHEMA)


@st.cache_data(show_spinner=False, ttl=300)
def load_bulk() -> pd.DataFrame:
    if USE_SUPABASE:
        try:
            all_data = _fetch_all_with_pagination("bulk_inventory", "id")
            if all_data:
                df = pd.DataFrame(all_data)
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "ID"
                df = df.rename(columns=rename_map)
                return normalize_df(df, BULK_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load bulk_inventory: {e}", icon="❌")
    return load_csv(BULK_FILE, BULK_SCHEMA)


@st.cache_data(show_spinner=False, ttl=300)
def load_bulk_history() -> pd.DataFrame:
    if USE_SUPABASE:
        try:
            all_data = _fetch_all_with_pagination("bulk_history", "id")
            if all_data:
                df = pd.DataFrame(all_data)
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "id"
                df = df.rename(columns=rename_map)
                return normalize_df(df, HISTORY_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load bulk_history: {e}", icon="❌")
    return load_csv(BULK_HISTORY, HISTORY_SCHEMA)

# =============================================================================
# TIME CONVERSION
# =============================================================================

def _to_vn_iso(ts_str) -> str:
    if not ts_str or str(ts_str).strip() in ("", "nan", "None", "null", "-"):
        return ""
    try:
        dt = datetime.fromisoformat(str(ts_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(VN_TZ).isoformat()
    except Exception:
        return str(ts_str)

# =============================================================================
# DATA SYNC (inventory & bulk)
# =============================================================================

def save_inventory_supabase(df_after: pd.DataFrame, df_before: pd.DataFrame):
    if not USE_SUPABASE:
        return
    try:
        _sb_cols = st.session_state.get("_inv_sb_cols")
        if not _sb_cols:
            try:
                _probe = supabase_client.table("inventory").select("*").limit(1).execute()
                if _probe.data:
                    _sb_cols = set(_probe.data[0].keys())
                    st.session_state["_inv_sb_cols"] = _sb_cols
            except Exception:
                pass

        def _filter_record(rec: dict) -> dict:
            if _sb_cols:
                return {k: v for k, v in rec.items() if k in _sb_cols}
            return rec

        # 1. Delete removed rows
        if not df_before.empty and not df_after.empty:
            before_ids = set(df_before[df_before["id"] > 0]["id"].dropna().astype(int))
            after_ids  = set(df_after[df_after["id"] > 0]["id"].dropna().astype(int))
            for d_id in (before_ids - after_ids):
                sb_delete("inventory", "id", d_id)

        records = [_filter_record(to_db(r)) for r in df_after.to_dict("records")]

        # 2. Split update vs insert
        update_records = [r for r in records if int(float(r.get("id") or 0)) > 0]
        insert_records = [r for r in records if int(float(r.get("id") or 0)) <= 0]
        for r in insert_records:
            r.pop("id", None)

        if update_records:
            sb_upsert("inventory", update_records, on_conflict="id")

        if insert_records:
            try:
                existing_resp = supabase_client.table("inventory") \
                    .select("auto_title, time_nhap").limit(-1).execute()
                existing_keys = {
                    (r.get("auto_title", ""), str(r.get("time_nhap", "")))
                    for r in (existing_resp.data or [])
                }
            except Exception:
                existing_keys = set()

            truly_new = [
                r for r in insert_records
                if (r.get("auto_title", ""), str(r.get("time_nhap", ""))) not in existing_keys
            ]
            for r in truly_new:
                sb_insert("inventory", r)
    except Exception as e:
        st.toast(f"❌ Sync inventory: {e}", icon="❌")


def save_bulk_supabase(df_after: pd.DataFrame, df_before: pd.DataFrame):
    if not USE_SUPABASE:
        return
    try:
        if not df_before.empty and not df_after.empty:
            before_ids = set(df_before[df_before["ID"] > 0]["ID"].dropna().astype(int))
            after_ids  = set(df_after[df_after["ID"] > 0]["ID"].dropna().astype(int))
            for d_id in (before_ids - after_ids):
                sb_delete("bulk_inventory", "id", d_id)

        records = [to_db(r) for r in df_after.to_dict("records")]

        update_records = [r for r in records if int(float(r.get("id") or 0)) > 0]
        insert_records = [r for r in records if int(float(r.get("id") or 0)) <= 0]
        for r in insert_records:
            r.pop("id", None)

        if update_records:
            sb_upsert("bulk_inventory", update_records, on_conflict="id")

        if insert_records:
            try:
                existing_resp = supabase_client.table("bulk_inventory") \
                    .select("ten_lo, ngay_nhap").limit(-1).execute()
                existing_keys = {
                    (r.get("ten_lo", ""), str(r.get("ngay_nhap", "")))
                    for r in (existing_resp.data or [])
                }
            except Exception:
                existing_keys = set()

            truly_new = [
                r for r in insert_records
                if (r.get("ten_lo", ""), str(r.get("ngay_nhap", ""))) not in existing_keys
            ]
            for r in truly_new:
                sb_insert("bulk_inventory", r)
    except Exception as e:
        st.toast(f"❌ Sync bulk: {e}", icon="❌")

# =============================================================================
# SETTINGS PERSISTENCE (app_settings table)
# =============================================================================

def _load_groq_key_from_supabase() -> str:
    if not USE_SUPABASE:
        return ""
    try:
        r = supabase_client.table("app_settings").select("value").eq("key", "groq_key").execute()
        if r.data:
            return r.data[0].get("value", "")
    except Exception:
        pass
    return ""


def _save_groq_key_to_supabase(api_key: str):
    if not USE_SUPABASE:
        return
    try:
        supabase_client.table("app_settings").upsert(
            {"key": "groq_key", "value": api_key}, on_conflict="key"
        ).execute()
    except Exception as e:
        st.toast(f"⚠️ Không thể lưu Groq key: {e}", icon="⚠️")


def _load_pinned_resell_from_supabase() -> dict:
    if not USE_SUPABASE:
        return {}
    try:
        r = supabase_client.table("app_settings").select("value").eq("key", "pinned_resell").execute()
        if r.data:
            return json.loads(r.data[0].get("value", "{}"))
    except Exception:
        pass
    return {}


def _save_pinned_resell_to_supabase(pinned: dict):
    if not USE_SUPABASE:
        return
    try:
        supabase_client.table("app_settings").upsert(
            {"key": "pinned_resell", "value": json.dumps(pinned, ensure_ascii=False, default=str)},
            on_conflict="key",
        ).execute()
    except Exception as e:
        st.toast(f"⚠️ Không thể lưu pin re-sell: {e}", icon="⚠️")


# lazy imports needed for _to_vn_iso
from datetime import datetime, timezone
from _timezone import VN_TZ
