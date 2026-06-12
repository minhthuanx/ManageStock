"""
Eldorado.gg client init, settings persistence, and cookie management.
"""
import json
import streamlit as st
from _database import USE_SUPABASE, supabase_client

# ─── Eldorado Client Init ────────────────────────────────────────────────
_HAS_ELDORADO = False
eldo_client = None

try:
    from eldorado_client import EldoradoClient, DELIVERY_MAP, DELIVERY_REV, COOKIE_FILE
    _HAS_ELDORADO = True
except Exception as _eldo_import_err:
    import sys
    print(f"[ELDO] Import failed: {_eldo_import_err}", file=sys.stderr)


def init_eldorado_client():
    global eld_client
    if _HAS_ELDORADO:
        _existing = st.session_state.get("eldorado_client")
        if _existing is None or getattr(_existing, "CLIENT_VERSION", 0) != EldoradoClient.CLIENT_VERSION:
            _eld_c = EldoradoClient(log_fn=lambda msg: None)
            st.session_state.eldorado_client = _eld_c
            if _eld_c._raw:
                try:
                    _auth = _eld_c.check_auth()
                    if not _auth.get("ok") and _eld_c.refresh_tokens():
                        _eld_c.check_auth()
                except Exception:
                    pass
        eld_client = st.session_state.eldorado_client
    else:
        eld_client = None
    return eld_client


# ─── Eldorado Settings ──────────────────────────────────────────────────

def _load_eld_settings() -> dict:
    if not USE_SUPABASE:
        return {}
    try:
        r = supabase_client.table("app_settings").select("value").eq("key", "eldorado_settings").execute()
        if r.data:
            return json.loads(r.data[0].get("value", "{}"))
    except Exception:
        pass
    return {}


def _save_eld_settings(settings: dict):
    if not USE_SUPABASE:
        return
    try:
        supabase_client.table("app_settings").upsert(
            {"key": "eldorado_settings", "value": json.dumps(settings, ensure_ascii=False)}
        ).execute()
    except Exception:
        pass


def _save_eld_cookie_to_sb(cookie_str: str):
    if not USE_SUPABASE or not cookie_str:
        return
    try:
        supabase_client.table("app_settings").upsert(
            {"key": "eldorado_cookie", "value": cookie_str}
        ).execute()
    except Exception:
        pass


def _load_eld_cookie_from_sb() -> str:
    if not USE_SUPABASE:
        return ""
    try:
        r = supabase_client.table("app_settings").select("value").eq("key", "eldorado_cookie").execute()
        if r.data:
            return r.data[0].get("value", "")
    except Exception:
        pass
    return ""


def _clear_eld_cookie_from_sb():
    if not USE_SUPABASE:
        return
    try:
        supabase_client.table("app_settings").delete().eq("key", "eldorado_cookie").execute()
    except Exception:
        pass
