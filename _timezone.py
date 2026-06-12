"""
Vietnam timezone helpers.
"""
from datetime import datetime, timezone, timedelta

VN_TZ = timezone(timedelta(hours=7))


def now_vn() -> datetime:
    return datetime.now(VN_TZ)


def now_str() -> str:
    return now_vn().strftime("%d/%m/%Y %H:%M")


def now_iso() -> str:
    return now_vn().isoformat()
