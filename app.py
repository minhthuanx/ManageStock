import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode, JsCode
    _HAS_AGGRID = True
except ImportError:
    _HAS_AGGRID = False

# --- SUPABASE ---
from supabase import create_client, Client

# =============================================================================
# PAGE CONFIG (must be first Streamlit call)
# =============================================================================
st.set_page_config(
    page_title="Management Dashboard",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# TIMEZONE VN
# =============================================================================
VN_TZ = timezone(timedelta(hours=7))

def now_vn() -> datetime:
    return datetime.now(VN_TZ)

def now_str() -> str:
    return now_vn().strftime("%d/%m/%Y %H:%M")

def now_iso() -> str:
    return now_vn().isoformat()

# =============================================================================
# SUPABASE INIT
# =============================================================================
supabase_client: Client | None = None
USE_SUPABASE = False

@st.cache_resource(show_spinner=False)
def _get_supabase() -> tuple["Client | None", bool]:
    """Tạo và cache Supabase client – tránh kết nối lại mỗi lần rerun."""
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
# COLUMN MAPPING (Python display name → Supabase snake_case)
# =============================================================================
COL_MAP = {
    "STT":           "stt",
    "Tên Pet":       "ten_pet",
    "M/s":           "ms",
    "Mutation":      "mutation",
    "Số Trait":      "so_trait",
    "NameStock":     "namestock",
    "Giá Nhập":      "gia_nhap",
    "Giá Bán":       "gia_ban",
    "Lợi Nhuận":     "loi_nhuan",
    "Doanh Thu":     "doanh_thu",
    "Ngày Nhập":     "ngay_nhap",
    "Ngày Bán":      "ngay_ban",
    "Auto Title":    "auto_title",
    "Trạng Thái":    "trang_thai",
    "time_nhap":     "time_nhap",
    "time_ban":      "time_ban",
    "Ngày Tồn":      "ngay_ton",
    "Place":         "place",
    # bulk
    "ID":                   "id",
    "Tên Lô":               "ten_lo",
    "Số Lượng Gốc":         "so_luong_goc",
    "Còn Lại":              "con_lai",
    "Giá Nhập Tổng":        "gia_nhap_tong",
    "Doanh Thu Tích Lũy":   "doanh_thu_tich_luy",
    "Số Lượng Bán":         "so_luong_ban",
    "Lợi Nhuận Giao Dịch":  "loi_nhuan_giao_dich",
    "Doanh Thu Giao Dịch":  "doanh_thu_giao_dich",
    # NOTE: Không thêm "id": "id" ở đây vì sẽ gây collision với "ID": "id"
    # và làm hỏng REVERSE_MAP cho bulk_inventory (ID=0 toàn bộ)
}
REVERSE_MAP = {v: k for k, v in COL_MAP.items()}

def to_db(record: dict) -> dict:
    """Convert display-name dict → snake_case for Supabase."""
    out = {}
    for k, v in record.items():
        if k == "index":
            continue
        mapped = COL_MAP.get(k, k.lower().replace(" ", "_").replace("/", "_"))
        # convert NaN / None safely
        if isinstance(v, float) and pd.isna(v):
            v = None
        # Xử lý lỗi Supabase khi truyền chuỗi rỗng vào cột Timestamp
        if v == "" and mapped in ["time_nhap", "time_ban"]:
            v = None
        out[mapped] = v
    return out

def from_db(df: pd.DataFrame) -> pd.DataFrame:
    """Rename snake_case columns → display names."""
    return df.rename(columns=REVERSE_MAP)

# =============================================================================
# SUPABASE CRUD
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
    """Insert and return the inserted row (with auto-generated id). Returns None on failure."""
    if not USE_SUPABASE:
        return None
    try:
        r = supabase_client.table(table).insert(data).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        st.toast(f"❌ Insert {table}: {e}", icon="❌")
        return None

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
        r = supabase_client.table(table).select("*").order(order).execute()
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
    """Trả về DataFrame các row bị dup hoàn toàn (trừ id) để user xem trước.”"""
    if not USE_SUPABASE:
        return pd.DataFrame()
    try:
        r = supabase_client.table(table).select("*").execute()
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
# CONFIGURATION
# =============================================================================
DB_FILE       = "inventory.csv"
BULK_FILE     = "bulk_inventory.csv"
BULK_HISTORY  = "bulk_history.csv"
PET_LIST_FILE = "pet_list.csv"
NS_LIST_FILE  = "namestock_list.csv"
TRAIT_LIST    = "traits_list.csv"
BACKUP_DIR    = "backups"
EXCHANGE_RATE = 20400

MAIN_SCHEMA = {
    "STT":         0,
    "id":          0,
    "Tên Pet":     "",
    "M/s":         0.0,
    "Mutation":    "Normal",
    "Số Trait":    "None",
    "NameStock":   "",
    "Giá Nhập":    0.0,
    "Giá Bán":     0.0,
    "Lợi Nhuận":   0.0,
    "Doanh Thu":   0.0,
    "Ngày Nhập":   "",
    "Ngày Bán":    "-",
    "Auto Title":  "",
    "Trạng Thái":  "Còn hàng",
    "time_nhap":   "",
    "time_ban":    "",
    "Ngày Tồn":    0,
    "Place":       "",
}

BULK_SCHEMA = {
    "ID":                  0,
    "Tên Lô":              "",
    "Số Lượng Gốc":        0,
    "Còn Lại":             0,
    "Ngày Nhập":           "",
    "Giá Nhập Tổng":       0.0,
    "Doanh Thu Tích Lũy":  0.0,
    "Lợi Nhuận":           0.0,
    "Trạng Thái":          "Available",
    "Auto Title":          "",
    "NameStock":           "",
}

HISTORY_SCHEMA = {
    "Ngày Bán":             "",
    "Tên Lô":               "",
    "Số Lượng Bán":         0,
    "Lợi Nhuận Giao Dịch":  0.0,
    "Doanh Thu Giao Dịch":  0.0,
}

LIST_SCHEMA = {"Name": ""}

MUTATION_OPTIONS = [
    "Normal", "Gold", "Diamond", "Bloodrot", "Candy",
    "Divine", "Lava", "Galaxy", "Yin-Yang", "Radioactive",
    "Cursed", "Rainbow",
]

# =============================================================================
# HELPERS
# =============================================================================
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
        # keep only 10 most recent backups per file
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


def next_id(df: pd.DataFrame, col: str) -> int:
    if df.empty:
        return 1
    return int(pd.to_numeric(df[col], errors="coerce").fillna(0).max() + 1)


def reindex(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.reset_index(drop=True).copy()
    if col in df.columns:
        df[col] = range(1, len(df) + 1)
    return df


def parse_vnd(s: str) -> float:
    cleaned = re.sub(r"[^0-9]", "", str(s))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def parse_usd(s: str) -> float:
    s_str = str(s).upper()
    cleaned = re.sub(r"[^0-9.]", "", s_str)
    try:
        val = float(cleaned) if cleaned else 0.0
        if "B" in s_str: # Nếu là Billion thì nhân 1000 để đưa về đơn vị Millions
            val *= 1000
        return val
    except ValueError:
        return 0.0


def fmt_vnd(v: float) -> str:
    return f"₫{v:,.0f}"


_SEARCH_KEYS = ["sell_search_q", "inv_table_search", "copy_title_search", "bulk_sell_search", "bulk_table_search"]

def _clear_searches():
    """Bump search version counter → widgets recreate with empty values on next rerun."""
    st.session_state["_search_ver"] = st.session_state.get("_search_ver", 0) + 1

def _sv() -> str:
    """Return current search version suffix for widget keys."""
    return str(st.session_state.get("_search_ver", 0))

def fmt_short(v: float) -> str:
    """Format ₫1.5M style for chart labels."""
    v = float(v)
    if abs(v) >= 1_000_000:
        return f"₫{v/1_000_000:.3f}M"
    if abs(v) >= 1_000:
        return f"₫{v/1_000:.1f}K"
    return f"₫{int(v):,}"


def get_name_options(db: pd.DataFrame, fallback: str = "None") -> list:
    if db.empty:
        return [fallback]
    vals = db["Name"].astype(str).str.strip()
    vals = vals[vals != ""]
    return vals.drop_duplicates().tolist() or [fallback]


def append_row(df: pd.DataFrame, row: dict, schema: dict) -> pd.DataFrame:
    return normalize_df(pd.concat([df, pd.DataFrame([row])], ignore_index=True), schema)


# =============================================================================
# AUTO TITLE
# =============================================================================
MUTATION_ICONS = {
    "gold": "👑", "diamond": "💎", "bloodrot": "🩸", "candy": "🍬",
    "divine": "✨", "lava": "🌋", "galaxy": "🌌", "yin-yang": "☯️",
    "radioactive": "☢️", "cursed": "😈", "rainbow": "🌈",
}

def _to_vn_iso(ts_str) -> str:
    """Chuyển timestamp UTC từ Supabase → ISO string giờ VN (+07:00).
    Supabase timestamptz lưu UTC nội bộ, trả về UTC khi query.
    Hàm này đảm bảo hiển thị và tính toán luôn dùng giờ VN.
    """
    if not ts_str or str(ts_str).strip() in ("", "nan", "None", "null", "-"):
        return ""
    try:
        dt = datetime.fromisoformat(str(ts_str))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(VN_TZ).isoformat()
    except Exception:
        return str(ts_str)


def generate_auto_title(pet_name, mutation, trait_str, ms_value, namestock) -> str:
    icon = MUTATION_ICONS.get(str(mutation).lower(), "🌟")
    t_str = f" [{trait_str}]" if (trait_str and str(trait_str).lower() != "none") else ""
    display_ms = f"{ms_value / 1000:g}B/s" if ms_value >= 1000 else f"{ms_value:g}M/s"
    ns_str = f" {namestock}" if namestock else ""
    if str(mutation).lower() == "normal" or not mutation:
        return f"🌸{pet_name} {display_ms}{t_str}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"
    return f"🌸{icon}{mutation} {pet_name} {display_ms}{t_str}{icon}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"


# =============================================================================
# NGÀY TỒN CALCULATION
# =============================================================================
def calc_ngay_ton(row) -> float:
    """
    - Nếu status = 'Đã bán' và có time_ban + time_nhap: chốt = time_ban - time_nhap
    - Ngược lại: now_vn() - time_nhap
    - Fallback: dùng Ngày Nhập (text) nếu time_nhap rỗng
    - Trả về float (ngày thập phân) để hiển thị giờ/phút chính xác
    """
    def _parse_ts(ts_str) -> datetime | None:
        if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
            return None
        try:
            # ISO format from Supabase
            dt = datetime.fromisoformat(str(ts_str))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN_TZ)
            return dt
        except Exception:
            return None

    def _parse_text_date(d_str) -> datetime | None:
        if not d_str or str(d_str).strip() in ("", "nan", "None", "-"):
            return None
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(str(d_str).strip(), fmt)
                return dt.replace(tzinfo=VN_TZ)
            except Exception:
                pass
        return None

    status = str(row.get("Trạng Thái", ""))
    t_nhap = _parse_ts(row.get("time_nhap", "")) or _parse_text_date(row.get("Ngày Nhập", ""))
    if t_nhap is None:
        return 0.0

    if "Đã bán" in status:
        t_ban = _parse_ts(row.get("time_ban", "")) or _parse_text_date(row.get("Ngày Bán", ""))
        if t_ban:
            return max(0.0, (t_ban - t_nhap).total_seconds() / 86400)

    return max(0.0, (now_vn() - t_nhap).total_seconds() / 86400)


def fmt_ngay_ton(v) -> str:
    """Hiển thị thời gian tồn: phút / giờ / ngày."""
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


def apply_ngay_ton(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ngay_ton calculation to all rows."""
    if df.empty:
        return df
    df = df.copy()
    df["Ngày Tồn"] = df.apply(calc_ngay_ton, axis=1)
    return df


# =============================================================================
# LOAD DATA
# =============================================================================
@st.cache_data(show_spinner=False, ttl=300)
def load_inventory() -> pd.DataFrame:
    """Load inventory. Bypass sb_select/from_db để tránh REVERSE_MAP["id"]="ID"
    đổi cột 'id' thành 'ID' → normalize_df tạo id=0 → mọi lần save đều INSERT mới.
    """
    if USE_SUPABASE:
        try:
            r = supabase_client.table("inventory").select("*").order("stt").execute()
            if r.data:
                df = pd.DataFrame(r.data)
                # Rename snake_case → display name, nhưng KHÔNG đổi "id" → "ID"
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "id"   # FORCE giữ "id" lowercase cho inventory PK
                df = df.rename(columns=rename_map)
                # Supabase trả time_nhap/time_ban dạng UTC → chuyển về giờ VN
                for _tc in ["time_nhap", "time_ban"]:
                    if _tc in df.columns:
                        df[_tc] = df[_tc].apply(_to_vn_iso)
                return normalize_df(df, MAIN_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load inventory: {e}", icon="❌")
    return load_csv(DB_FILE, MAIN_SCHEMA)

@st.cache_data(show_spinner=False, ttl=300)
def load_bulk() -> pd.DataFrame:
    """Load bulk_inventory. Bypass sb_select/from_db để xử lý đúng 'id'→'ID'.
    REVERSE_MAP["id"]="ID" (từ COL_MAP "ID":"id"), nhưng inventory cũng dùng
    cột "id" nên từng bảng phải load riêng để rename đúng.
    """
    if USE_SUPABASE:
        try:
            r = supabase_client.table("bulk_inventory").select("*").order("id").execute()
            if r.data:
                df = pd.DataFrame(r.data)
                # Rename snake_case → display name, nhưng map "id" → "ID" rõ ràng
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "ID"   # force uppercase cho bulk primary key
                df = df.rename(columns=rename_map)
                return normalize_df(df, BULK_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load bulk_inventory: {e}", icon="❌")
    return load_csv(BULK_FILE, BULK_SCHEMA)

@st.cache_data(show_spinner=False, ttl=300)
def load_bulk_history() -> pd.DataFrame:
    """Load bulk_history. Bypass sb_select/from_db để tránh id→ID rename."""
    if USE_SUPABASE:
        try:
            r = supabase_client.table("bulk_history").select("*").order("id").execute()
            if r.data:
                df = pd.DataFrame(r.data)
                rename_map = {c: REVERSE_MAP.get(c, c) for c in df.columns}
                rename_map["id"] = "id"   # giữ lowercase
                df = df.rename(columns=rename_map)
                return normalize_df(df, HISTORY_SCHEMA)
        except Exception as e:
            st.toast(f"❌ Load bulk_history: {e}", icon="❌")
    return load_csv(BULK_HISTORY, HISTORY_SCHEMA)


def save_inventory_supabase(df_after: pd.DataFrame, df_before: pd.DataFrame):
    """Sync inventory to Supabase using native 'id' as primary key.
    Tách riêng UPDATE (id>0) và INSERT (id=0) để tuyệt đối tránh duplicate.
    """
    if not USE_SUPABASE: return
    try:
        # ── 1. Xoá các dòng đã bị xoá khỏi editor ──
        if not df_before.empty and not df_after.empty:
            before_ids = set(df_before[df_before["id"] > 0]["id"].dropna().astype(int))
            after_ids  = set(df_after[df_after["id"] > 0]["id"].dropna().astype(int))
            for d_id in (before_ids - after_ids):
                sb_delete("inventory", "id", d_id)

        records = [to_db(r) for r in df_after.to_dict("records")]

        # ── 2. Phân loại: có ID thì UPDATE, không ID thì INSERT mới ──
        update_records = [r for r in records if int(float(r.get("id") or 0)) > 0]
        insert_records = [r for r in records if int(float(r.get("id") or 0)) <= 0]
        for r in insert_records:
            r.pop("id", None)

        # UPDATE existing rows (safe – chỉ cập nhật, không tạo bản ghi mới)
        if update_records:
            sb_upsert("inventory", update_records, on_conflict="id")

        # INSERT new rows – kiểm tra trùng bằng auto_title + time_nhap trước khi insert
        if insert_records:
            try:
                existing_resp = supabase_client.table("inventory") \
                    .select("auto_title, time_nhap").execute()
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
    """Sync bulk inventory to Supabase using 'id'.
    Tách riêng UPDATE (ID>0) và INSERT (ID=0) để tuyệt đối tránh duplicate.
    bulk_df dùng cột 'ID' (uppercase) – khác với inventory dùng 'id' (lowercase).
    """
    if not USE_SUPABASE: return
    try:
        # ── 1. Xoá các dòng đã bị xoá khỏi editor ──
        if not df_before.empty and not df_after.empty:
            before_ids = set(df_before[df_before["ID"] > 0]["ID"].dropna().astype(int))
            after_ids  = set(df_after[df_after["ID"] > 0]["ID"].dropna().astype(int))
            for d_id in (before_ids - after_ids):
                sb_delete("bulk_inventory", "id", d_id)

        records = [to_db(r) for r in df_after.to_dict("records")]

        # ── 2. Phân loại: có ID thì UPDATE, không có thì INSERT mới ──
        update_records = [r for r in records if int(float(r.get("id") or 0)) > 0]
        insert_records = [r for r in records if int(float(r.get("id") or 0)) <= 0]
        for r in insert_records:
            r.pop("id", None)

        if update_records:
            sb_upsert("bulk_inventory", update_records, on_conflict="id")

        if insert_records:
            try:
                existing_resp = supabase_client.table("bulk_inventory") \
                    .select("ten_lo, ngay_nhap").execute()
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
# SESSION STATE INIT
# =============================================================================
def _load_groq_key_from_supabase() -> str:
    """Đọc Groq API key từ bảng app_settings trên Supabase."""
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
    """Lưu Groq API key vào bảng app_settings (upsert theo primary key 'groq_key')."""
    if not USE_SUPABASE:
        return
    try:
        supabase_client.table("app_settings").upsert(
            {"key": "groq_key", "value": api_key}, on_conflict="key"
        ).execute()
    except Exception as e:
        st.toast(f"⚠️ Không thể lưu Groq key: {e}", icon="⚠️")

def init_session():
    if "initialized" not in st.session_state:
        _sk_ph = st.empty()
        _sk_ph.markdown(
            '<style>@keyframes _sk{0%{background-position:200% 0}100%{background-position:-200% 0}}</style>'
            '<div style="padding:1.2rem 0;display:flex;flex-direction:column;gap:0.65rem;">'
            '<div style="height:22px;width:38%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1528 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.55rem;margin:0.3rem 0;">'
            + ('<div style="height:68px;border-radius:10px;background:linear-gradient(90deg,#110f1a 25%,#1a1528 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>' * 4) +
            '</div>'
            '<div style="height:130px;border-radius:10px;background:linear-gradient(90deg,#110f1a 25%,#1a1528 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="height:13px;width:55%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1528 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '<div style="height:13px;width:75%;border-radius:6px;background:linear-gradient(90deg,#110f1a 25%,#1a1528 50%,#110f1a 75%);background-size:200% 100%;animation:_sk 1.4s infinite;"></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        # Tải song song 4 nguồn dữ liệu để giảm thời gian chờ
        with ThreadPoolExecutor(max_workers=4) as _ex:
            _f_inv  = _ex.submit(load_inventory)
            _f_bulk = _ex.submit(load_bulk)
            _f_hist = _ex.submit(load_bulk_history)
            _f_groq = _ex.submit(_load_groq_key_from_supabase)
            _inv_df = _f_inv.result()
            _bulk_r = _f_bulk.result()
            _hist_r = _f_hist.result()
            _groq_r = _f_groq.result()
        st.session_state.df           = apply_ngay_ton(_inv_df)
        st.session_state.bulk_df      = _bulk_r
        st.session_state.bulk_history = _hist_r
        # Tải Groq key đã lưu (nếu có)
        if not st.session_state.get("groq_key") and _groq_r:
            st.session_state.groq_key = _groq_r
        _sk_ph.empty()
        st.session_state.initialized = True
    else:
        # Migrate: đảm bảo bulk_df luôn có đủ cột từ BULK_SCHEMA (sau khi thêm cột mới)
        _bdf = st.session_state.get("bulk_df", pd.DataFrame())
        for _col, _default in BULK_SCHEMA.items():
            if _col not in _bdf.columns:
                _bdf[_col] = _default
                st.session_state.bulk_df = _bdf

init_session()

df           = st.session_state.df
bulk_df      = st.session_state.bulk_df
bulk_history = st.session_state.bulk_history

pet_db   = load_csv(PET_LIST_FILE, LIST_SCHEMA)
ns_db    = load_csv(NS_LIST_FILE,  LIST_SCHEMA)
trait_db = load_csv(TRAIT_LIST,    LIST_SCHEMA)

# =============================================================================
# GLOBAL CSS - Mobile-first, dark premium
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─── Root variables ─── */
:root {
  --bg:        #0a0a0f;
  --surface:   #110f1a;
  --surface2:  #1a1528;
  --border:    #2d2540;
  --accent:    #c084fc;
  --accent2:   #e879f9;
  --green:     #86efac;
  --red:       #f472b6;
  --text:      #f0e6ff;
  --muted:     #9d8fbf;
  --radius:    12px;
}

/* ─── Base ─── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
  font-feature-settings: "tnum" 1, "cv01" 1, "ss01" 1;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
/* Giữ gutter cho scrollbar – tránh layout shift khi tab cao/thấp khác nhau */
/* Scroll ở cấp html/body để window.scrollY luôn đúng → Plotly tooltip không bị lệch */
html { scrollbar-gutter: stable !important; overflow-y: auto !important; }
body { overflow: visible !important; }
section.main { overflow: visible !important; }
[data-testid="stAppViewContainer"] { overflow: visible !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
.block-container { padding: 1rem 1rem 3rem !important; max-width: 1400px; }

/* ─── Main content area — nền tím trung tâm ─── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  background: var(--surface2) !important;
  border-radius: 16px !important;
  border: 1px solid rgba(192,132,252,0.15) !important;
  box-shadow: 0 0 60px rgba(192,132,252,0.07) inset !important;
}

div[data-testid="stMetricValue"] { font-size: clamp(1rem, 2.5vw, 1.4rem) !important; font-weight: 700 !important; color: var(--text) !important; }
div[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: var(--muted) !important; letter-spacing: 0.03em; text-transform: uppercase; }

/* ─── Buttons ─── */
.stButton > button {
  border-radius: 8px !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.01em !important;
  transition: all 0.15s ease !important;
  width: 100%;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #0a0a0f !important;
  border: none !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 24px rgba(192,132,252,0.5) !important;
  filter: brightness(1.1) !important;
}

/* ─── Tabs ─── */
[data-testid="stTabs"] > div:first-child {
  gap: 0 !important;
  border-bottom: 2px solid var(--border) !important;
  background: transparent !important;
  padding: 0 !important;
}
/* ẩn thanh gạch mặc định của Streamlit (đỏ/hồng) */
[data-testid="stTabs"] [role="tablist"] > div[data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTab"] {
  border-radius: 0 !important;
  padding: 0.65rem 1.2rem !important;
  /* LOCK font-weight – không đổi khi active → tab bên cạnh không bị đẩy dịch */
  font-weight: 600 !important;
  font-size: 0.78rem !important;
  letter-spacing: 0.07em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  border: none !important;
  background: transparent !important;
  transition: color 0.15s ease !important;
  position: relative !important;
  outline: none !important;
  white-space: nowrap !important;
}
/* đường kẻ gradient indicator bằng pseudo-element */
[data-testid="stTab"]::after {
  content: '' !important;
  display: block !important;
  position: absolute !important;
  bottom: -2px !important;
  left: 10% !important;
  width: 80% !important;
  height: 3px !important;
  border-radius: 999px !important;
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  opacity: 0 !important;
  transform: scaleX(0.4) !important;
  transition: opacity 0.2s ease, transform 0.2s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--text) !important;
  /* font-weight giữ nguyên 600 – chỉ đổi màu, không đổi weight */
  background: transparent !important;
}
[data-testid="stTab"][aria-selected="true"]::after {
  opacity: 1 !important;
  transform: scaleX(1) !important;
}
[data-testid="stTab"]:hover:not([aria-selected="true"]) {
  color: var(--text) !important;
  background: transparent !important;
}
[data-testid="stTab"]:hover::after {
  opacity: 0.35 !important;
  transform: scaleX(0.7) !important;
}

/* ─── Inputs ─── */
.stTextInput input, .stNumberInput input, .stSelectbox select {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
}

/* ─── Containers — purple tint frames ─── */
[data-testid="stVerticalBlockBorderWrapper"] {
  /* Override CSS variable Streamlit uses to draw the border */
  --border-color-default: rgba(192,132,252,0.55) !important;
  border-color: rgba(192,132,252,0.55) !important;
  background: linear-gradient(160deg, rgba(192,132,252,0.07) 0%, rgba(17,15,26,0.97) 55%) !important;
  border-radius: var(--radius) !important;
  box-shadow:
    inset 0 1px 0 rgba(192,132,252,0.15),
    0 6px 32px rgba(0,0,0,0.35) !important;
}
/* Target the intermediate div Streamlit sometimes inserts */
[data-testid="stVerticalBlockBorderWrapper"] > div {
  --border-color-default: rgba(192,132,252,0.55) !important;
  border-color: rgba(192,132,252,0.55) !important;
}
/* Force inner block transparent so wrapper purple shows through */
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
  background: transparent !important;
  box-shadow: none !important;
}

/* ─── Tab content — clean panel ─── */
[data-testid="stTabContent"] {
  background: rgba(17,15,26,0.6) !important;
  /* Dùng box-shadow thay border – không ảnh hưởng layout, không cần bù margin */
  box-shadow: inset 0 0 0 1px rgba(192,132,252,0.12) !important;
  border-top: none !important;
  border-radius: 0 0 var(--radius) var(--radius) !important;
  padding: 1rem !important;
  width: 100% !important;
  box-sizing: border-box !important;
}

/* ─── DataFrames — material glass ─── */
.stDataFrame {
  border-radius: var(--radius) !important;
  overflow: hidden !important;
  border: 1px solid var(--border) !important;
  border-top: 2px solid rgba(192,132,252,0.5) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
  background: var(--surface) !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stDataFrame:hover {
  border-color: rgba(192,132,252,0.3) !important;
  border-top-color: var(--accent) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 0 transparent !important;
}
/* toolbar icons */
[data-testid="stElementToolbar"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
[data-testid="stElementToolbarButton"] svg { color: var(--muted) !important; }
[data-testid="stElementToolbarButton"]:hover svg { color: var(--accent) !important; }

/* ─── Status badges ─── */
.badge-sold   { color: var(--green); font-weight: 600; }
.badge-stock  { color: var(--accent); font-weight: 600; }

/* ─── Hero banner — glassmorphism ─── */
.hero-banner {
  background: linear-gradient(135deg, rgba(192,132,252,0.08) 0%, rgba(232,121,249,0.05) 50%, rgba(192,132,252,0.08) 100%);
  border: 1px solid rgba(192,132,252,0.2);
  backdrop-filter: blur(12px);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.hero-banner .logo { font-size: 2rem; }
.hero-banner h1 { margin: 0; font-size: clamp(1.1rem, 3vw, 1.5rem); font-weight: 700; letter-spacing: -0.01em; }
.hero-banner p  { margin: 0; color: var(--muted); font-size: 0.82rem; }

/* ─── Stats row ─── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.6rem;
  margin-bottom: 0.8rem;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 0.9rem;
  text-align: center;
  transition: all 0.2s;
}
.stat-card:hover { border-color: var(--accent); box-shadow: 0 8px 24px rgba(192,132,252,0.2); }
.stat-card .val  { font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.stat-card .lbl  { font-size: 0.7rem; color: var(--muted); margin-top: 0.1rem; letter-spacing: 0.04em; }

/* ─── Section headings ─── */
.sec-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 2rem 0 1rem !important;
  padding: 0;
  width: 100%;
  position: relative;
}
.sec-heading::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  border-radius: 2px;
  background: linear-gradient(180deg, var(--accent), var(--accent2));
  flex-shrink: 0;
}
.sec-heading::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(192,132,252,0.3) 0%, transparent 100%);
  margin-left: 0.4rem;
}

/* ─── Section card panels — wrap stat content ─── */
.stat-panel {
  background: linear-gradient(145deg, rgba(192,132,252,0.07) 0%, rgba(17,15,26,0.95) 100%);
  border: 1px solid rgba(192,132,252,0.2);
  border-radius: var(--radius);
  padding: 1.2rem 1.2rem 0.8rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25), inset 0 1px 0 rgba(192,132,252,0.08);
}

/* ─── Metric cards — left stripe style ─── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  padding: 0.7rem 0.9rem !important;
  transition: all 0.2s;
  box-shadow: 0 2px 12px rgba(192,132,252,0.05) !important;
}
div[data-testid="stMetric"]:hover {
  border-color: var(--accent) !important;
  border-left-color: var(--accent2) !important;
  box-shadow: 0 6px 24px rgba(192,132,252,0.22) !important;
}

/* ─── Expanders — purple tinted border ─── */
[data-testid="stExpander"] {
  border: 1px solid rgba(192,132,252,0.28) !important;
  border-radius: var(--radius) !important;
  background: linear-gradient(135deg, rgba(192,132,252,0.06) 0%, var(--surface) 55%) !important;
  overflow: hidden !important;
  box-shadow: 0 2px 16px rgba(192,132,252,0.07) !important;
}
[data-testid="stExpander"] summary {
  padding: 0.6rem 0.9rem !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.01em !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }

/* ─── Progress bar ─── */
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  border-radius: 999px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--surface2) !important;
  border-radius: 999px !important;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ─── Mobile responsive ─── */
@media (max-width: 768px) {
  .block-container { padding: 0.4rem 0.4rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 0.95rem !important; }
  div[data-testid="stMetricLabel"] { font-size: 0.68rem !important; }
  .stat-card .val { font-size: 0.95rem; }
  [data-testid="stTab"] { padding: 0.3rem 0.5rem !important; font-size: 0.7rem !important; letter-spacing: 0.02em !important; }
  .hero-banner { padding: 0.6rem 0.8rem; gap: 0.5rem; }
  .hero-banner .logo { font-size: 1.5rem; }
  .hero-banner h1 { font-size: 1rem !important; }
  .hero-banner p { font-size: 0.72rem; }
  .sec-heading { font-size: 0.88rem; margin: 0.7rem 0 0.4rem; }

  /* Columns stack vertically on mobile */
  [data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.3rem !important;
  }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: 100% !important;
    flex: 1 1 100% !important;
  }

  /* Forms compact */
  .stForm { padding: 0.5rem !important; }
  .stButton > button { padding: 0.5rem 0.8rem !important; font-size: 0.82rem !important; }

  /* DataEditor scroll hint */
  .stDataFrame { max-height: 350px !important; }
  [data-testid="stDataFrameResizable"] { font-size: 0.75rem !important; }

  /* Expanders compact */
  [data-testid="stExpander"] summary { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }

  /* Selectbox / inputs */
  .stTextInput input, .stNumberInput input { font-size: 0.85rem !important; padding: 0.4rem 0.6rem !important; }
  .stSelectbox [data-baseweb="select"] { font-size: 0.85rem !important; }

  /* Radio buttons (filters) wrap better */
  [data-testid="stRadio"] > div { flex-wrap: wrap !important; gap: 0.2rem !important; }
  [data-testid="stRadio"] label { font-size: 0.75rem !important; padding: 0.25rem 0.5rem !important; }

  /* Sidebar overlay */
  [data-testid="stSidebar"] { min-width: 260px !important; }

  /* Plotly charts */
  .js-plotly-plot { min-height: 250px !important; }
}

/* ─── Copy description button ─── */
.copy-desc-btn {
  background: linear-gradient(135deg, #c084fc, #e879f9) !important;
  color: #0a0a0f !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
.copy-desc-btn:hover {
  box-shadow: 0 4px 24px rgba(192,132,252,0.5) !important;
}

/* ─── Toast override ─── */
[data-testid="stToast"] { font-size: 0.85rem !important; border-radius: 10px !important; }

/* ─── Alert / Notification boxes ─── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-width: 1px !important;
  font-size: 0.84rem !important;
  padding: 0.65rem 0.9rem !important;
}
/* info */
[data-testid="stAlert"][kind="info"],
div[data-testid="stInfo"] > div {
  background: rgba(192,132,252,0.07) !important;
  border-color: rgba(192,132,252,0.3) !important;
  color: var(--text) !important;
}
/* success */
[data-testid="stAlert"][kind="success"],
div[data-testid="stSuccess"] > div {
  background: rgba(134,239,172,0.07) !important;
  border-color: rgba(134,239,172,0.3) !important;
  color: var(--text) !important;
}
/* warning */
[data-testid="stAlert"][kind="warning"],
div[data-testid="stWarning"] > div {
  background: rgba(251,191,36,0.07) !important;
  border-color: rgba(251,191,36,0.25) !important;
  color: var(--text) !important;
}
/* error */
[data-testid="stAlert"][kind="error"],
div[data-testid="stError"] > div {
  background: rgba(244,114,182,0.07) !important;
  border-color: rgba(244,114,182,0.3) !important;
  color: var(--text) !important;
}

/* ─── Secondary / default buttons ─── */
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: rgba(192,132,252,0.07) !important;
  border-color: rgba(192,132,252,0.45) !important;
  color: var(--text) !important;
  transform: none !important;
  box-shadow: none !important;
}
.stButton > button[kind="tertiary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: none !important;
}
.stButton > button[kind="tertiary"]:hover {
  color: var(--accent) !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ─── Form container ─── */
[data-testid="stForm"] {
  background: rgba(192,132,252,0.08) !important;
  border: 1px solid rgba(192,132,252,0.28) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
  box-shadow: 0 2px 16px rgba(192,132,252,0.08) !important;
}

/* ─── Selectbox / multiselect styled ─── */
[data-baseweb="select"] > div:first-child {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}
[data-baseweb="select"] > div:first-child:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
[data-baseweb="popover"] [role="option"]:hover {
  background: rgba(192,132,252,0.1) !important;
}
[data-baseweb="tag"] {
  background: rgba(192,132,252,0.15) !important;
  color: var(--accent) !important;
  border: none !important;
  border-radius: 6px !important;
}

/* ─── Caption / small text ─── */
[data-testid="stCaptionContainer"] p {
  color: var(--muted) !important;
  font-size: 0.76rem !important;
}

/* ─── Divider ─── */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 0.8rem 0 !important;
}

/* ─── Sidebar section headings ─── */
[data-testid="stSidebar"] .sidebar-heading {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  padding: 0.5rem 0 0.3rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.4rem;
  display: block;
}

/* ─── Radio → pill chip style ─── */
[data-testid="stRadio"] > div {
  gap: 0.3rem !important;
  flex-wrap: wrap !important;
}
[data-testid="stRadio"] label {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 999px !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--muted) !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
  white-space: nowrap !important;
}
[data-testid="stRadio"] label:has(input:checked) {
  background: rgba(192,132,252,0.15) !important;
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  font-weight: 600 !important;
}
[data-testid="stRadio"] label:hover {
  border-color: var(--accent) !important;
  color: var(--text) !important;
}
/* hide the actual radio circle */
[data-testid="stRadio"] label input[type="radio"] {
  display: none !important;
}
[data-testid="stRadio"] label > div:first-child {
  display: none !important;
}

/* ─── Tồn lâu badge ─── */
.badge-warn {
  background: rgba(147,51,234,0.25);
  color: var(--accent2);
  border: 1px solid rgba(147,51,234,0.4);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.72rem;
  font-weight: 700;
  margin-left: 8px;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

/* ─── Hide Streamlit branding ─── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

/* ─── Ambient background orbs ─── */
/* Orbs dùng position:fixed, không cần overflow-x:hidden để kiểm soát chúng */
body::before {
  content: '';
  position: fixed;
  top: -200px; left: -200px;
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(192,132,252,0.07) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}
body::after {
  content: '';
  position: fixed;
  bottom: -180px; right: -180px;
  width: 650px; height: 650px;
  background: radial-gradient(circle, rgba(232,121,249,0.05) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}

/* ─── Skeleton shimmer ─── */
.sk-line {
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface2) 50%, var(--surface) 75%);
  background-size: 200% 100%;
  animation: sk-shimmer 1.4s infinite;
}
@keyframes sk-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ─── Toast enhanced ─── */
[data-testid="stToast"] {
  background: var(--surface2) !important;
  border: 1px solid rgba(192,132,252,0.22) !important;
  border-radius: 12px !important;
  font-size: 0.85rem !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(192,132,252,0.08) !important;
  backdrop-filter: blur(16px) !important;
  color: var(--text) !important;
}
[data-testid="stToastContainer"] {
  bottom: 2rem !important;
  right: 1.5rem !important;
}

/* ─── Empty state ─── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1rem;
  gap: 0.45rem;
  text-align: center;
}
.empty-state .es-icon { font-size: 2.4rem; opacity: 0.45; }
.empty-state .es-title { font-size: 0.95rem; font-weight: 600; color: var(--muted); }
.empty-state .es-sub { font-size: 0.78rem; color: var(--muted); opacity: 0.65; }

/* ─── Button loading spinner ─── */
@keyframes btn-spin {
  to { transform: rotate(360deg); }
}
.btn-busy {
  opacity: 0.65 !important;
  pointer-events: none !important;
  cursor: wait !important;
}

/* ═══════════════════════════════════════════════
   SMOOTH ANIMATIONS  
   ═══════════════════════════════════════════════ */

/* ── Keyframes ── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0);    }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.97); }
  to   { opacity: 1; transform: scale(1);    }
}

/* ── Tab content: fade khi chuyển tab (dùng fadeIn, không có transform để tránh stacking context làm lệch Plotly tooltip) ── */
[data-testid="stTabContent"] {
  animation: fadeIn 0.22s ease forwards !important;
}

/* ── Toàn bộ nội dung block-container: fade khi rerun ── */
[data-testid="stAppViewContainer"] > section.main > div.block-container {
  animation: fadeIn 0.25s ease forwards !important;
}

/* ── Expander khi mở: fade content ── */
[data-testid="stExpander"] > div:last-child {
  animation: fadeIn 0.18s ease both !important;
}

/* ── Alert/warning/success box ── */
[data-testid="stAlert"],
div[data-testid="stInfo"] > div,
div[data-testid="stSuccess"] > div,
div[data-testid="stWarning"] > div,
div[data-testid="stError"] > div {
  animation: scaleIn 0.18s ease both !important;
}

/* ── Button: nhấn xuống nhẹ ── */
.stButton > button:active {
  transform: scale(0.97) !important;
  transition: transform 0.08s ease !important;
}
.stButton > button[kind="primary"]:active {
  filter: brightness(0.93) !important;
  box-shadow: 0 2px 8px rgba(192,132,252,0.3) !important;
}

/* ── Input focus: glow transition mượt hơn ── */
.stTextInput input,
.stNumberInput input,
[data-baseweb="select"] > div:first-child {
  transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}

/* ── Toast: slide từ phải vào ── */
@keyframes toastIn {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0);    }
}
[data-testid="stToast"] {
  animation: toastIn 0.22s cubic-bezier(0.22,1,0.36,1) both !important;
}

/* ── Giảm animation khi user prefer-reduced-motion ── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
""", unsafe_allow_html=True)

# ─── Loading overlay — phủ FOUC cho đến khi CSS+data sẵn sàng ────────────────
import streamlit.components.v1 as _cmp_gsov
_cmp_gsov.html("""
<script>
(function(){
  var pd=window.parent.document;
  if(pd.getElementById('gs-overlay'))return;
  /* CSS cho overlay */
  var sty=pd.createElement('style');
  sty.id='gs-overlay-style';
  sty.textContent=[
    '#gs-overlay{position:fixed;inset:0;z-index:2147483647;background:#0a0a0f;',
      'display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.2rem;',
      'transition:opacity 0.65s cubic-bezier(.4,0,.2,1),visibility 0.65s;}',
    '#gs-overlay.gs-out{opacity:0;visibility:hidden;pointer-events:none;}',
    '#gs-overlay .gs-g{font-size:2.8rem;animation:gsb 1.1s ease-in-out infinite;}',
    '#gs-overlay .gs-rail{width:190px;height:3px;border-radius:999px;background:rgba(192,132,252,0.13);overflow:hidden;}',
    '#gs-overlay .gs-bar{height:100%;width:45%;border-radius:999px;',
      'background:linear-gradient(90deg,#c084fc,#e879f9);animation:gsbr 1.5s ease-in-out infinite alternate;}',
    '#gs-overlay .gs-t{font-family:Inter,ui-sans-serif,sans-serif;font-size:0.74rem;',
      'font-weight:500;letter-spacing:0.12em;text-transform:uppercase;color:#9d8fbf;}',
    '@keyframes gsb{0%,100%{transform:translateY(0)}50%{transform:translateY(-9px)}}',
    '@keyframes gsbr{0%{width:25%;margin-left:15%}100%{width:65%;margin-left:0}}'
  ].join('');
  pd.head.appendChild(sty);
  /* Tạo div overlay */
  var ov=pd.createElement('div');
  ov.id='gs-overlay';
  ov.innerHTML='<div class="gs-g">\U0001F47B</div>'
    +'<div class="gs-rail"><div class="gs-bar"></div></div>'
    +'<div class="gs-t">\u0110ang T\u1EA3i...</div>';
  pd.body.appendChild(ov);
  /* Dismiss overlay */
  function bye(){
    ov.classList.add('gs-out');
    setTimeout(function(){
      if(ov.parentNode)ov.remove();
      var s=pd.getElementById('gs-overlay-style');
      if(s)s.remove();
    },750);
  }
  /* Kiểm tra app đã ready: CSS var --bg tồn tại + block-container có nội dung */
  function ok(){
    var bg=getComputedStyle(pd.documentElement).getPropertyValue('--bg').trim();
    if(!bg)return false;
    var bc=pd.querySelector('[data-testid="stAppViewContainer"] .block-container');
    return !!(bc&&bc.children&&bc.children.length>1);
  }
  var n=0;
  (function poll(){
    n++;
    if(ok()){setTimeout(bye,150);}
    else if(n<200){setTimeout(poll,60);}
    else{bye();} /* failsafe 12s */
  })();
})();
</script>
""", height=0)

# Hero banner – tính stats nhanh
_hb_con_hang = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
_badge_count  = int(_hb_con_hang[pd.to_numeric(_hb_con_hang["Ngày Tồn"], errors="coerce").fillna(0) >= 7].shape[0])
_hb_con_hang_count = len(_hb_con_hang)
_hb_da_ban = int(df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False).sum())
_hb_today  = now_vn().date()
def _hb_is_today(ts):
    if not ts or str(ts).strip() in ("","nan","None","-"): return False
    try:
        dt = datetime.fromisoformat(str(ts))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=VN_TZ)
        return dt.astimezone(VN_TZ).date() == _hb_today
    except: return False
_hb_sold_today  = df[df["time_ban"].apply(_hb_is_today)]
_hb_profit_le   = float(pd.to_numeric(_hb_sold_today["Lợi Nhuận"], errors="coerce").fillna(0).sum())
# Cộng lợi nhuận lô pack hôm nay (Ngày Bán dạng dd/mm/yyyy HH:MM)
def _hb_bulk_is_today(d_str):
    if not d_str or str(d_str).strip() in ("","nan","None","-"): return False
    try:
        dt = datetime.strptime(str(d_str).strip(), "%d/%m/%Y %H:%M")
        return dt.date() == _hb_today
    except: return False
_hb_bulk_today  = bulk_history[bulk_history["Ngày Bán"].apply(_hb_bulk_is_today)] if not bulk_history.empty else pd.DataFrame()
_hb_profit_bulk = float(pd.to_numeric(_hb_bulk_today["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if not _hb_bulk_today.empty else 0.0
_hb_profit_today = _hb_profit_le + _hb_profit_bulk
_badge_html = f'<span class="badge-warn">&#9888; {_badge_count} tồn lâu</span>' if _badge_count > 0 else ""
st.markdown(f"""
<div class="hero-banner" style="flex-wrap:wrap;gap:0.9rem;">
  <div style="display:flex;align-items:center;gap:0.75rem;flex:1;min-width:180px;">
    <div class="logo">👻</div>
    <div>
      <h1 style="margin:0;">Management Dashboard{_badge_html}</h1>
      <p style="margin:0;">Copyright &copy; 2026 MINHTHUAN. All rights reserved.</p>
    </div>
  </div>
  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;">
    <div style="background:rgba(134,239,172,0.08);border:1px solid rgba(134,239,172,0.2);border-radius:9px;padding:0.3rem 0.8rem;text-align:center;min-width:64px;">
      <div style="font-size:1.15rem;font-weight:700;color:#86efac;line-height:1.2;">{_hb_con_hang_count}</div>
      <div style="font-size:0.62rem;color:#9d8fbf;letter-spacing:0.05em;text-transform:uppercase;">Còn hàng</div>
    </div>
    <div style="background:rgba(192,132,252,0.08);border:1px solid rgba(192,132,252,0.2);border-radius:9px;padding:0.3rem 0.8rem;text-align:center;min-width:64px;">
      <div style="font-size:1.15rem;font-weight:700;color:#c084fc;line-height:1.2;">{_hb_da_ban}</div>
      <div style="font-size:0.62rem;color:#9d8fbf;letter-spacing:0.05em;text-transform:uppercase;">Đã bán</div>
    </div>
    <div style="background:rgba(232,121,249,0.08);border:1px solid rgba(232,121,249,0.2);border-radius:9px;padding:0.3rem 0.8rem;text-align:center;min-width:64px;">
      <div style="font-size:1.1rem;font-weight:700;color:#e879f9;line-height:1.2;">{fmt_vnd(_hb_profit_today)}</div>
      <div style="font-size:0.62rem;color:#9d8fbf;letter-spacing:0.05em;text-transform:uppercase;">Hôm nay</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("---")
    st.caption(f"🕐 {now_vn().strftime('%d/%m/%Y %H:%M')} (VN)")
    if USE_SUPABASE:
        st.success("Kết nối · Supabase Cloud", icon="✅")
    else:
        st.warning("Offline · Chế độ CSV cục bộ")

    # ── Tồn kho real-time ──
    _con_hang = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
    _von_le   = float(pd.to_numeric(_con_hang["Giá Nhập"], errors="coerce").fillna(0).sum())
    _von_lo   = float(pd.to_numeric(
        bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"]["Giá Nhập Tổng"], errors="coerce"
    ).fillna(0).sum())
    st.markdown('<span class="sidebar-heading">Tồn kho hiện tại</span>', unsafe_allow_html=True)
    st.metric("Có thể bán", f"{len(_con_hang):,} đơn vị", delta=None)
    st.metric("Vốn tồn — lẻ", fmt_vnd(_von_le))
    st.metric("Vốn tồn — lô", fmt_vnd(_von_lo))
    st.caption(f"Tổng vốn lưu động: **{fmt_vnd(_von_le+_von_lo)}**")
    st.markdown("---")

    # ── Dashboard hôm nay ──
    _today_date = now_vn().date()
    def _is_today_ban(ts_str):
        if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
            return False
        try:
            dt = datetime.fromisoformat(str(ts_str))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=VN_TZ)
            return dt.astimezone(VN_TZ).date() == _today_date
        except Exception:
            return False
    _sold_today   = df[df["time_ban"].apply(_is_today_ban)]
    _today_count  = len(_sold_today)
    _profit_le    = float(pd.to_numeric(_sold_today["Lợi Nhuận"], errors="coerce").fillna(0).sum())
    # Cộng lợi nhuận lô pack hôm nay
    def _is_today_bulk(d_str):
        if not d_str or str(d_str).strip() in ("", "nan", "None", "-"): return False
        try: return datetime.strptime(str(d_str).strip(), "%d/%m/%Y %H:%M").date() == _today_date
        except: return False
    _bulk_today   = bulk_history[bulk_history["Ngày Bán"].apply(_is_today_bulk)] if not bulk_history.empty else pd.DataFrame()
    _profit_bulk  = float(pd.to_numeric(_bulk_today["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if not _bulk_today.empty else 0.0
    _today_profit = _profit_le + _profit_bulk
    st.markdown('<span class="sidebar-heading">Hôm nay</span>', unsafe_allow_html=True)
    _td1, _td2 = st.columns(2)
    _td1.metric("Giao dịch", f"{_today_count}")
    _td2.metric("Lợi nhuận", fmt_vnd(_today_profit))

    # ── #22 Mục tiêu lãi ngày ──
    if "daily_profit_target" not in st.session_state:
        st.session_state["daily_profit_target"] = 5_000_000
    st.number_input("Mục tiêu lợi nhuận (₫)", min_value=0, step=500_000,
                    key="daily_profit_target", format="%d")
    _daily_target_val = st.session_state["daily_profit_target"]
    if _daily_target_val > 0:
        _goal_pct = min(_today_profit / _daily_target_val, 1.0)
        st.progress(_goal_pct, text=f"{fmt_vnd(_today_profit)} / {fmt_vnd(_daily_target_val)} ({_goal_pct*100:.0f}%)")
    st.markdown("---")

    # ── Copy Shop Description ──
    _SHOP_DESC = """👻Welcome to Management Dashboard - The Safest Way to Trade! 👻

Don't risk your items with "base-stealing" transfers. While others make you "steal" items from base to base, we use the "Trade Machine" for every order! 🚀

✅ Best Prices 💸

✅ Zero Risk (Trade Machine) 🔒

✅ Instant Delivery 🚚⚡

How to get your Brainrot 📦:

1️⃣ Send Username: Please provide your username after payment.

2️⃣ Stay Online: Stay active in-game to receive your trade invite.

3️⃣ Accept Invite: Our team will send you a request via the Trade Machine.

4️⃣ Confirm Trade: We transfer your Brainrot directly through the secure trade interface.

5️⃣ Secure the Loot: Once accepted, your Brainrot is 100% secured in your base—no risk of being intercepted!

Why Management Dashboard is Different?

In Steal a Brainrot, manual transfers are slow and dangerous. We skip the "stealing" hassle entirely! By utilizing the in-game Trade function, we guarantee your pets are protected during the entire process. No shared servers required, no risks taken.

Secure. Professional. Ghostly. 👻⚡"""
    st.session_state["_shop_desc"] = _SHOP_DESC
    st.markdown("---")

    if st.button("Đồng Bộ Dữ Liệu", use_container_width=True):
        st.cache_data.clear()
        del st.session_state["initialized"]
        st.rerun()

    # ── Auto-refresh cố định 5 phút ──
    import streamlit.components.v1 as _cmp_ar
    _cmp_ar.html(
        '<script>'
        '(function(){'
        '  setTimeout(function(){'
        '    var btns = window.parent.document.querySelectorAll("button[kind=\'secondary\']");'
        '    var found = Array.from(btns).find(function(b){return b.innerText.includes("D\u1eef Li\u1ec7u");});'
        '    if(found){found.click();} else {window.parent.location.reload();}'
        '  }, 300000);'
        '})();'
        '</script>',
        height=0,
    )
    st.caption("Tự động đồng bộ · mỗi 5 phút")

# =============================================================================
# MAIN TABS
# =============================================================================
tab_kho, tab_pack, tab_chart, tab_ton, tab_settings = st.tabs([
    "📦 Kho Lẻ", "🗃️ Lô Pack", "📊 Thống Kê", "⏳ Tồn Lâu", "⚙️ Cài Đặt",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: KHO (Nhập + Bán + Bảng tồn kho)
# ─────────────────────────────────────────────────────────────────────────────
with tab_kho:
    col_in, col_sell = st.columns([1.15, 1], gap="medium")

    # ── NHẬP KHO ──
    with col_in:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">Nhập Kho</div>', unsafe_allow_html=True)

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
                            import requests
                            import base64
                            import time
                            
                            results = []
                            progress = st.progress(0, text="Đang khởi tạo...")
                            
                            prompt = """This is a screenshot from the Roblox game "Steal a Brainrot". Each brainrot (pet) has an info panel above it showing: its name, speed ($/s), optional mutation indicator, and optional trait icons.

Extract and return VALID JSON only (no markdown, no extra text):
{
  "Tên Pet": "The brainrot's name as shown in the info panel (e.g. 'Tralalero Tralala', 'Bombardiro Crocodilo')",
  "Mutation": "Detect the mutation from visual cues or text labels. Mutations change the pet's color/glow: Gold=golden/yellow tint, Diamond=blue/crystal shimmer, Divine=white heavenly glow, Rainbow=multicolor sparkles, Bloodrot=dark red tint, Candy=pastel candy swirl, Lava=orange molten glow, Galaxy=purple starfield aura, Yin-Yang=black+white balanced glow, Radioactive=green radioactive glow, Cursed=dark purple aura, Celestial=stars/celestial shimmer. If no special color/glow is visible, return 'Normal'.",
  "Tốc độ": "The speed/income value shown near the pet. Normalize to Millions (M number only). Examples: '1.2B/s' → '1200', '975M/s' → '975', '500K/s' → '0.5'. Always return a plain number string.",
  "Số Trait": "Count the small trait ICONS/SYMBOLS displayed in the pet's info panel (NOT the pet model decorations). In Steal a Brainrot, traits appear as small distinct icons in a row within the info card. Known trait symbols include: asteroid, shark fin, hat, Bombardiro Crocodilo face, spider/web, graffiti spray, taco, glitch pixel, crab claw, fire/flame, three sparkles, nyan cat, white flash, strawberry, raindrop, snowflake, star. Count how many of these distinct icon symbols you see in the info panel. Return 'None' if 0 traits, else return the count as a string like '1', '2', '3'."
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
                            except Exception:
                                pass
                            
                            if not target_model:
                                st.error(f"❌ Không tìm thấy Model Đọc Ảnh nào khả dụng cho Key của bạn! Danh sách model Groq trả về hiện tại: {', '.join(all_models)}")
                                st.stop()
                                
                            st.toast(f"Model: {target_model}", icon="🦙")

                            for idx, img_f in enumerate(batch_imgs):
                                progress.progress(
                                    int((idx / len(batch_imgs)) * 100),
                                    text=f"Quét ảnh {idx+1}/{len(batch_imgs)}: {img_f.name[:20]}..."
                                )
                                success = False
                                last_err = ""
                                
                                try:
                                    img_f.seek(0)
                                    b64_img = base64.b64encode(img_f.read()).decode("utf-8")
                                    mime_type = img_f.type if img_f.type else "image/jpeg"
                                    
                                    payload = {
                                        "model": target_model,
                                        "messages": [
                                            {
                                                "role": "user",
                                                "content": [
                                                    {"type": "text", "text": prompt},
                                                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}}
                                                ]
                                            }
                                        ],
                                        "temperature": 0.1
                                    }
                                    
                                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        txt = data["choices"][0]["message"]["content"].strip()
                                        
                                        json_str = txt
                                        if "```json" in txt:
                                            json_str = txt.split("```json")[-1].split("```")[0].strip()
                                        elif txt.find("{") != -1:
                                            json_str = txt[txt.find("{"):txt.rfind("}")+1]
                                            
                                        parsed_data  = json.loads(json_str)
                                        results.append({
                                            "_filename": img_f.name,
                                            "_ok": True,
                                            "Tên Pet":  parsed_data.get("Tên Pet", ""),
                                            "Mutation": parsed_data.get("Mutation", "Normal"),
                                            "M/s":      parsed_data.get("Tốc độ", ""),
                                            "Số Trait": str(parsed_data.get("Số Trait", "None")),
                                            "NameStock": "",
                                            "Giá Nhập": "",
                                        })
                                        success = True
                                    else:
                                        last_err = f"API Error {resp.status_code}: {resp.text}"
                                except Exception as e_img:
                                    last_err = str(e_img)
                                
                                if not success:
                                    if "429" in last_err or "rate" in last_err.lower():
                                        last_err = "❌ Rate Limit! (Groq giới hạn 15 ảnh/phút). Vui lòng đợi xíu."
                                    results.append({
                                        "_filename": img_f.name,
                                        "_ok": False,
                                        "_error": last_err,
                                        "Tên Pet": "", "Mutation": "Normal",
                                        "M/s": "", "Số Trait": "None",
                                        "NameStock": "", "Giá Nhập": "",
                                    })
                                
                                if idx < len(batch_imgs) - 1:
                                    _pct_done = int(((idx + 1) / len(batch_imgs)) * 100)
                                    for _cd in range(4, 0, -1):
                                        progress.progress(
                                            _pct_done,
                                            text=f"✅ Xong ảnh {idx+1}/{len(batch_imgs)} · Chờ {_cd}s (Groq giới hạn 15 ảnh/phút)..."
                                        )
                                        time.sleep(1)
                            
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
                    global pet_db
                    pet_opts_dlg   = get_name_options(pet_db)
                    trait_opts_dlg = ["None"] + get_name_options(trait_db)
                    ns_opts_dlg    = [""] + get_name_options(ns_db, fallback="")

                    st.caption(f"**{len(results)}** ảnh đã phân tích · Xem lại và xác nhận trước khi lưu")

                    edited_rows = []
                    all_valid = True

                    for i, res in enumerate(results):
                        fname = res.get("_filename", f"Image {i+1}")
                        is_ok = res.get("_ok", False)

                        # Chỉ auto-expand ảnh bị lỗi; ảnh OK thu gọn mặc định
                        _expander_label = (
                            f"❌ {fname} — Lỗi nhận dạng" if not is_ok
                            else f"✅ {fname} — {str(res.get('Tên Pet','?'))} · {str(res.get('Mutation','Normal'))} · {str(res.get('M/s','?'))}M/s"
                        )
                        with st.expander(_expander_label, expanded=True):
                            if not is_ok:
                                st.warning(f"Không thể đọc ảnh này · {res.get('_error','')} · Có thể nhập thủ công.")

                            # Chia layout: 1 cột nhỏ hiển thị ảnh, 1 cột lớn nhập liệu
                            img_col, form_col = st.columns([1, 3.5])
                            
                            with img_col:
                                # Lấy ảnh từ session_state để preview
                                u_key = st.session_state.get("ai_uploader_key", 0)
                                current_files = st.session_state.get(f"ai_batch_upload_{u_key}", [])
                                matched_img = next((f for f in current_files if f.name == fname), None)
                                if matched_img:
                                    st.image(matched_img, use_container_width=True)
                                else:
                                    st.caption("Không thể tải ảnh")

                            with form_col:
                                c1d, c2d, c3d = st.columns(3)

                                # Tên Pet
                                ai_name = str(res.get("Tên Pet") or "")
                                if ai_name and ai_name.lower() not in [x.lower() for x in pet_opts_dlg]:
                                    # Tự thêm vào list nếu chưa có
                                    pet_opts_dlg = [ai_name] + pet_opts_dlg
                                pi = next((j for j, x in enumerate(pet_opts_dlg) if x.lower() == ai_name.lower()), 0)
                                r_name = c1d.selectbox(f"Tên Pet", pet_opts_dlg, index=pi, key=f"dlg_name_{i}")

                                # Mutation
                                ai_mut_v = str(res.get("Mutation") or "Normal")
                                mi = next((j for j, m in enumerate(MUTATION_OPTIONS) if m.lower() == ai_mut_v.lower()), 0)
                                r_mut = c2d.selectbox(f"Mutation", MUTATION_OPTIONS, index=mi, key=f"dlg_mut_{i}")

                                # M/s
                                r_ms_raw = c3d.text_input(f"M/s", value=str(res.get("M/s") or ""), key=f"dlg_ms_{i}")

                                c4d, c5d, c6d = st.columns(3)
                                ai_trait = str(res.get("Số Trait") or "None").strip()
                                ti = next((j for j, t in enumerate(trait_opts_dlg) if t.lower() == ai_trait.lower()), 0)
                                r_trait = c4d.selectbox(f"Số Trait", trait_opts_dlg, index=ti, key=f"dlg_trait_{i}")
                                r_ns    = c5d.selectbox(f"NameStock", ns_opts_dlg, key=f"dlg_ns_{i}")
                                r_cost  = c6d.text_input(f"Giá nhập", placeholder="150", key=f"dlg_cost_{i}")

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
                                "Tên Pet":  r_name,
                                "Mutation": r_mut,
                                "M/s":      r_ms,
                                "Số Trait": r_trait,
                                "NameStock": r_ns,
                                "Giá Nhập": parse_vnd(r_cost),
                                "_valid":   len(err_row) == 0,
                            })

                    st.markdown("---")
                    col_cancel, col_save = st.columns([1, 2])
                    with col_cancel:
                        if st.button("Huỷ bỏ", use_container_width=True):
                            st.session_state.ai_show_dialog = False
                            st.session_state.ai_batch_results = []
                            st.rerun()

                    with col_save:
                        valid_count = sum(1 for r in edited_rows if r["_valid"])
                        save_label = f"Lưu {valid_count} / {len(edited_rows)} mục hợp lệ"
                        if st.button(save_label, type="primary", use_container_width=True, disabled=valid_count == 0):
                            saved = 0
                            current_df = st.session_state.df
                            sb_records_to_insert = []
                            
                            for r in edited_rows:
                                if not r["_valid"]:
                                    continue
                                # Auto-add new pet name to DB
                                existing_lower = [x.lower() for x in get_name_options(pet_db)]
                                if r["Tên Pet"].lower() not in existing_lower:
                                    pet_db = append_row(pet_db, {"Name": r["Tên Pet"]}, LIST_SCHEMA)
                                    save_csv(pet_db, PET_LIST_FILE)

                                stt = next_id(current_df, "STT")
                                ts  = now_iso()
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
                                    "Ngày Nhập":  now_str(),
                                    "Ngày Bán":   "-",
                                    "Auto Title": generate_auto_title(
                                        r["Tên Pet"], r["Mutation"], r["Số Trait"], r["M/s"], r["NameStock"]
                                    ),
                                    "Trạng Thái": "Còn hàng",
                                    "time_nhap":  ts,
                                    "time_ban":   "",
                                    "Ngày Tồn":   0,
                                    "Place":      "",
                                }
                                current_df = append_row(current_df, new_row, MAIN_SCHEMA)
                                sb_records_to_insert.append(to_db(new_row))
                                saved += 1

                            # Đẩy từng record lên Supabase bằng sb_insert (an toàn hơn upsert)
                            sb_ok = True
                            if USE_SUPABASE and sb_records_to_insert:
                                for r in sb_records_to_insert:
                                    r.pop("id", None)  # Để DB tự cấp ID – tuyệt đối không upsert
                                    if not sb_insert("inventory", r):
                                        sb_ok = False
                                        break
                            
                            if sb_ok:
                                if USE_SUPABASE:
                                    # Refresh Cache để lấy ID thật từ DB về tránh dup khi reindex
                                    load_inventory.clear()
                                    st.session_state.df = apply_ngay_ton(load_inventory())
                                else:
                                    current_df = apply_ngay_ton(current_df)
                                    st.session_state.df = current_df
                                    
                                save_csv(st.session_state.df, DB_FILE)
                                st.session_state.ai_show_dialog = False
                                st.session_state.ai_batch_results = []
                                st.session_state.ai_uploader_key = st.session_state.get("ai_uploader_key", 0) + 1
                                st.session_state.ai_expander = False
                                st.toast(f"Đã lưu {saved} mục thành công", icon="✅")
                                st.rerun()

                ai_preview_dialog()

            # =========================================================
            # NHẬP THỦ CÔNG (Always visible)
            # =========================================================
            st.markdown("**Nhập Thủ Công**")
            pet_opts   = get_name_options(pet_db)
            trait_opts = ["None"] + get_name_options(trait_db)
            ns_opts    = [""] + get_name_options(ns_db, fallback="")

            # ── #12 Clone button ──
            _last_pet = st.session_state.get("last_saved_pet")
            if _last_pet:
                if st.button(f"Nhập tương tự: {_last_pet.get('p_name','')}", use_container_width=True, key="btn_clone_pet"):
                    st.session_state.nhap_prefill = _last_pet.copy()
                    st.rerun()
            _prefill = st.session_state.get("nhap_prefill", {})

            with st.form("form_nhap_le", clear_on_submit=True):
                _pi_pet = next((i for i, x in enumerate(pet_opts) if x == _prefill.get("p_name", "")), 0)
                p_name = st.selectbox("Tên Pet", pet_opts, index=_pi_pet)
                c1, c2, c3 = st.columns(3)
                ms_raw   = c1.text_input("M/s", placeholder="VD: 975", value=_prefill.get("ms_raw", ""))
                _pi_mut = next((i for i, m in enumerate(MUTATION_OPTIONS) if m == _prefill.get("p_mut", "")), 0)
                p_mut    = c2.selectbox("Mutation", MUTATION_OPTIONS, index=_pi_mut)
                _pi_trait = next((i for i, t in enumerate(trait_opts) if t == _prefill.get("p_trait", "")), 0)
                p_trait  = c3.selectbox("Số Trait", trait_opts, index=_pi_trait)
                c4, c5 = st.columns([1.5, 1])
                _pi_ns = next((i for i, n in enumerate(ns_opts) if n == _prefill.get("p_ns", "")), 0)
                p_ns       = c4.selectbox("NameStock", ns_opts, index=_pi_ns)
                p_cost_raw = c5.text_input("Giá nhập (VNĐ)", placeholder="150000")
                submitted = st.form_submit_button("Lưu Hàng", type="primary", use_container_width=True)

            if submitted:
                ms = parse_usd(ms_raw)
                cost = parse_vnd(p_cost_raw)
                errs = []
                if p_name == "None": errs.append("Chọn tên Pet")
                if ms <= 0:          errs.append("M/s phải > 0")
                if cost <= 0:        errs.append("Giá nhập phải > 0")
                if not p_ns.strip(): errs.append("Chọn NameStock")
                if errs:
                    for e in errs: st.error(f"❌ {e}")
                else:
                    # Guard chống double-submit: kiểm tra xem dữ liệu y hệt đã lưu chưa
                    submit_key = f"nhap_le_{p_name}_{ms}_{cost}_{p_ns}"
                    if st.session_state.get("last_nhap_key") == submit_key:
                        st.warning("Mục này đã được lưu. Tải lại trang nếu cần.")
                        st.stop()
                    st.session_state.last_nhap_key = submit_key
                    st.session_state.pop("nhap_prefill", None)  # Xóa prefill sau khi submit hợp lệ
                    stt = next_id(df, "STT")
                    ts  = now_iso()
                    row = {
                        "STT":        stt,
                        "Tên Pet":    p_name,
                        "M/s":        ms,
                        "Mutation":   p_mut,
                        "Số Trait":   p_trait,
                        "NameStock":  p_ns,
                        "Giá Nhập":   cost,
                        "Giá Bán":    0.0,
                        "Lợi Nhuận":  0.0,
                        "Doanh Thu":  0.0,
                        "Ngày Nhập":  now_str(),
                        "Ngày Bán":   "-",
                        "Auto Title": generate_auto_title(p_name, p_mut, p_trait, ms, p_ns),
                        "Trạng Thái": "Còn hàng",
                        "time_nhap":  ts,
                        "time_ban":   "",
                        "Ngày Tồn":   0,
                        "Place":      "",
                    }
                    df = append_row(df, row, MAIN_SCHEMA)
                    df = apply_ngay_ton(df)
                    st.session_state.df = df
                    if USE_SUPABASE:
                        p_payload = to_db(row)
                        p_payload.pop("id", None)
                        sb_insert("inventory", p_payload)
                        # Sync ID from DB
                        load_inventory.clear()
                        st.session_state.df = apply_ngay_ton(load_inventory())
                        
                    st.session_state.last_saved_pet = {
                        "p_name": p_name, "ms_raw": ms_raw,
                        "p_mut": p_mut, "p_trait": p_trait, "p_ns": p_ns,
                    }
                    st.toast("Đã lưu thành công", icon="✅")
                    st.caption("Sao chép tiêu đề:")
                    st.code(row["Auto Title"], language="text")
                    _clear_searches()
                    st.rerun()

    # ── BÁN LẺ ──
    with col_sell:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">Bán Pet Lẻ</div>', unsafe_allow_html=True)

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
                            load_inventory.clear()
                    st.toast("Đã hoàn tác giao dịch", icon="↩️")
                    st.rerun()

            active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)]
            q = st.text_input("Tìm kiếm", placeholder="STT, tên, mutation, namestock...", key=f"sell_search_q_{_sv()}")

            if not active.empty:
                if q.strip():
                    _q_toks = re.split(r'[\s\-]+', q.strip().lower())
                    _q_toks = [t for t in _q_toks if t]
                    _q_cols = ["STT", "Tên Pet", "Mutation", "NameStock", "Số Trait", "Auto Title", "Place"]
                    _q_hay = active[[c for c in _q_cols if c in active.columns]].astype(str) \
                        .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                    _q_combined = _q_hay.apply(lambda row: ' '.join(row), axis=1)
                    _q_mask = pd.Series([True] * len(active), index=active.index)
                    for _qt in _q_toks:
                        _q_mask &= _q_combined.str.contains(_qt, regex=False, na=False)
                    filt = active[_q_mask]
                else:
                    filt = active
                if not filt.empty:
                    _stt_map = {int(r["STT"]): r for _, r in filt.iterrows()}
                    def _pet_fmt(stt):
                        r = _stt_map[stt]
                        auto_t = str(r.get("Auto Title", "") or "")
                        # Lấy phần trước boilerplate
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
                        "Chọn Pet",
                        list(_stt_map.keys()),
                        format_func=_pet_fmt,
                        label_visibility="collapsed",
                    )
                    sel_stt = sel
                    sel_row = filt[filt["STT"] == sel_stt].iloc[0]
                    # Hiển thị Auto Title đầy đủ để copy
                    _at_le = str(sel_row.get("Auto Title", "") or "")
                    if _at_le:
                        st.code(_at_le, language="text")

                    st.caption(f"**{len(filt)}** kết quả phù hợp")

                    with st.form("form_ban_le", clear_on_submit=True):
                        c1, c2 = st.columns([1.2, 1])
                        s_price_raw = c1.text_input("Đơn giá ($)", placeholder="VD: 5.5")
                        s_place     = c2.text_input("Kênh bán (tuỳ chọn)", placeholder="Note anything...")
                        sell_btn    = st.form_submit_button("Xác Nhận Giao Dịch", type="primary", use_container_width=True)

                    # ── Step 1: save pending on first click ──
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

                    # ── Step 2: confirmation block ──
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
                                    st.cache_data.clear()
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
                                load_inventory.clear()
                                st.toast("✅ Giao dịch hoàn tất · Nhấn Hoàn Tác nếu bán nhầm", icon="✅")
                                _clear_searches()
                                st.rerun()
                else:
                    st.markdown('<div class="empty-state"><div class="es-icon">🔍</div><div class="es-title">Không tìm thấy kết quả</div><div class="es-sub">Thử điều chỉnh từ khoá tìm kiếm</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state"><div class="es-icon">📦</div><div class="es-title">Kho trống</div><div class="es-sub">Nhấn "Nhập Kho" bên trái để thêm hàng</div></div>', unsafe_allow_html=True)

    # ── BẢNG TỒN KHO ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Tồn Kho Lẻ</div>', unsafe_allow_html=True)

        with st.expander("Xem bảng tồn kho", expanded=True):
            # ── THANH CÔNG CỤ ──
            _tb1, _tb2, _tb3 = st.columns([2, 2.5, 1])
            view_mode = _tb1.radio(
                "Lọc trạng thái",
                ["Đang bán", "Đã bán", "Tất cả"],
                horizontal=True,
                label_visibility="collapsed",
            )
            inv_search = _tb2.text_input(
                "🔍 Tìm kiếm",
                placeholder="STT, tên pet, mutation, title...",
                label_visibility="collapsed",
                key=f"inv_table_search_{_sv()}",
            )

            # ── Quick filter Mutation chips ──
            _all_mutations = sorted(df["Mutation"].astype(str).str.strip().unique().tolist())
            _all_mutations = [m for m in _all_mutations if m not in ("", "nan")]
            _mut_options = ["Tất cả"] + _all_mutations
            _mut_sel = st.radio(
                "Lọc Mutation",
                _mut_options,
                horizontal=True,
                label_visibility="collapsed",
                key="inv_mut_filter",
            )

            if view_mode == "Đang bán":
                view_df = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
                show_all = False
            elif view_mode == "Đã bán":
                view_df = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
                show_all = True
            else:
                view_df = df.copy()
                show_all = True

            # Áp dụng quick filter mutation
            if _mut_sel != "Tất cả":
                view_df = view_df[view_df["Mutation"].astype(str).str.strip() == _mut_sel]

            # Áp dụng tìm kiếm text – token-based: mỗi từ phải xuất hiện ở ít nhất 1 cột
            if inv_search.strip():
                # Chuẩn hoá: bỏ dấu '-', tách thành tokens
                _tokens = re.split(r'[\s\-]+', inv_search.strip().lower())
                _tokens = [t for t in _tokens if t]
                _search_cols = ["STT","Tên Pet","Mutation","NameStock","Số Trait","Auto Title","Place"]
                _haystack = view_df[[c for c in _search_cols if c in view_df.columns]] \
                    .astype(str).apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                _combined = _haystack.apply(lambda row: ' '.join(row), axis=1)
                mask = pd.Series([True] * len(view_df), index=view_df.index)
                for _tok in _tokens:
                    mask &= _combined.str.contains(_tok, regex=False, na=False)
                view_df = view_df[mask]

            # Thêm cột hiển thị "Tồn" (text) từ Ngày Tồn (float ngày)
            view_df = view_df.copy()
            view_df["Tồn"] = view_df["Ngày Tồn"].apply(fmt_ngay_ton)

            display_cols = ["id","STT","Tên Pet","M/s","Mutation","Số Trait","NameStock",
                            "Giá Nhập","Giá Bán","Lợi Nhuận","Ngày Nhập","Ngày Bán",
                            "Tồn","Trạng Thái","Auto Title","Place"]
            view_cols = [c for c in display_cols if c in view_df.columns]

            # Nút xuất CSV + đếm kết quả
            _tb3.metric("Tổng sổ", len(view_df))
            if not view_df.empty:
                csv_inv = view_df[view_cols].to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    "⬇️ Xuất CSV",
                    data=csv_inv,
                    file_name=f"kho_le_{now_vn().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_inv_csv",
                )

            if not view_df.empty:
                # Khi search hoặc khi lọc mutation: coi như đang filter → dùng safe merge-back
                _is_searching = bool(inv_search.strip()) or (_mut_sel != "Tất cả")
                # Show editable table
                before_edit = view_df[view_cols].copy()
                edited = st.data_editor(
                    before_edit,
                    key=f"editor_inventory_{st.session_state.get('editor_inv_ver', 0)}",
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed" if _is_searching else "dynamic",
                    disabled=["id"],
                    column_config={
                        "id": st.column_config.NumberColumn("Database ID", help="Mã định danh gốc từ Supabase (Read-only)", format="%d"),
                        "Tồn": st.column_config.TextColumn("Tồn", disabled=True),
                        "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                        "Giá Nhập": st.column_config.NumberColumn("Giá Nhập (VNĐ)", format="%d"),
                        "Giá Bán": st.column_config.NumberColumn("Giá Bán ($)"),
                        "Lợi Nhuận": st.column_config.NumberColumn("Lợi Nhuận (VNĐ)", format="%d"),
                    },
                )

                # Chỉ reindex STT khi xem "Tất cả" + không tìm kiếm → tránh STT conflict khi merge-back
                _can_reindex = (view_mode == "Tất cả") and not _is_searching
                after_reindexed  = reindex(normalize_df(edited.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols}), "STT") if _can_reindex \
                    else normalize_df(edited.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols})
                before_reindexed = reindex(normalize_df(before_edit.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols}), "STT") if _can_reindex \
                    else normalize_df(before_edit.copy(), {c: MAIN_SCHEMA.get(c, "") for c in view_cols})

                # Regenerate auto titles
                has_title_col = "Auto Title" in after_reindexed.columns
                if has_title_col:
                    def _regen_title(r):
                        return generate_auto_title(
                            r.get("Tên Pet",""), r.get("Mutation","Normal"),
                            r.get("Số Trait","None"),
                            float(pd.to_numeric(r.get("M/s", 0), errors="coerce") or 0),
                            r.get("NameStock",""),
                        )
                    after_reindexed["Auto Title"] = after_reindexed.apply(_regen_title, axis=1)

                if not after_reindexed.astype(str).equals(before_reindexed.astype(str)):
                    # Merge changes back into full df
                    full_df = st.session_state.df.copy()

                    if _is_searching:
                        # Khi search: chỉ cập nhật các dòng hiển thị, giữ nguyên dòng ẩn
                        # Normalize to int trước khi so sánh tránh "1" vs "1.0" dtype mismatch (data_editor trả về float64)
                        visible_ids = set(pd.to_numeric(after_reindexed["id"], errors="coerce").fillna(0).astype(int).astype(str).tolist()) if "id" in after_reindexed.columns else set()
                        hidden_rows = full_df[~pd.to_numeric(full_df["id"], errors="coerce").fillna(0).astype(int).astype(str).isin(visible_ids)]
                        merged = pd.concat([after_reindexed, hidden_rows], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))
                    elif view_mode == "Tất cả":
                        full_updated = apply_ngay_ton(normalize_df(after_reindexed, MAIN_SCHEMA))
                    elif view_mode == "Đã bán":
                        # Chỉ cập nhật hàng đã bán, giữ nguyên hàng còn hàng
                        con_hang_df = full_df[full_df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
                        merged = pd.concat([con_hang_df, after_reindexed], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))
                    else:
                        # Chỉ cập nhật hàng còn hàng, giữ nguyên hàng đã bán
                        sold_df = full_df[full_df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
                        merged = pd.concat([after_reindexed, sold_df], ignore_index=True)
                        full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))

                    save_inventory_supabase(full_updated, st.session_state.df)
                    # ── Luôn reload từ Supabase để lấy ID thật, tránh id=0 gây duplicate ──
                    if USE_SUPABASE:
                        load_inventory.clear()
                        st.session_state.df = apply_ngay_ton(load_inventory())
                    else:
                        st.session_state.df = full_updated
                    df = st.session_state.df
                    # Bump version key để reset widget state, tránh vòng lặp lưu vô hạn
                    st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                    st.toast("✅ Đã lưu thay đổi.", icon="💾")
                    _clear_searches()
                    st.rerun()
            else:
                st.info("Không có dữ liệu để hiển thị.")

        # ── COPY AUTO TITLE NHANH ──
        _shop_desc = st.session_state.get("_shop_desc", "")
        import base64 as _b64
        import streamlit.components.v1 as _cmp
        _b64_desc = _b64.b64encode(_shop_desc.encode("utf-8")).decode("ascii") if _shop_desc else ""

        _copy_src = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        if not _copy_src.empty:
            with st.expander("Sao chép Auto Title", expanded=False):
                _cp_q = st.text_input("🔍 Tìm pet", placeholder="Tên, STT, mutation...", key=f"copy_title_search_{_sv()}", label_visibility="collapsed")

                _cp_base = _copy_src.copy()

                if _cp_q.strip():
                    # Khi search: tìm trong toàn bộ còn hàng
                    _cp_toks = re.split(r'[\s\-]+', _cp_q.strip().lower())
                    _cp_toks = [t for t in _cp_toks if t]
                    _cp_hay = _cp_base[["Tên Pet","Mutation","Auto Title","NameStock","STT"]].astype(str) \
                        .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                    _cp_combined = _cp_hay.apply(lambda r: ' '.join(r), axis=1)
                    _cp_mask = pd.Series([True] * len(_cp_base), index=_cp_base.index)
                    for _t in _cp_toks:
                        _cp_mask &= _cp_combined.str.contains(_t, regex=False, na=False)
                    _cp_filtered = _cp_base[_cp_mask]
                    _cp_mode_label = f"{len(_cp_filtered)} kết quả tìm kiếm"
                else:
                    # Mặc định: chỉ pet nhập trong 1 giờ qua
                    _now_vn = now_vn()
                    _cutoff = _now_vn - timedelta(hours=1)

                    def _is_recent(ts_str):
                        if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                            return False
                        try:
                            dt = datetime.fromisoformat(str(ts_str))
                            if dt.tzinfo is None:
                                dt = dt.replace(tzinfo=VN_TZ)
                            return dt >= _cutoff
                        except Exception:
                            return False

                    _recent_mask = _cp_base["time_nhap"].apply(_is_recent)
                    _cp_filtered = _cp_base[_recent_mask].sort_values("STT", ascending=False)
                    _cp_mode_label = f"{len(_cp_filtered)} pet nhập trong 1 giờ qua"

                if _cp_filtered.empty:
                    if _cp_q.strip():
                        st.info("Không tìm thấy pet phù hợp.")
                    else:
                        st.caption("Chưa có pet nào được nhập trong 1 giờ qua. Dùng ô tìm kiếm để tìm bất kỳ pet nào.")
                else:
                    st.caption(f"📌 {_cp_mode_label}")
                    for _ci, (_, _crow) in enumerate(_cp_filtered.iterrows()):
                        st.markdown(
                            f'<div style="font-size:0.78rem;color:#9d8fbf;margin-top:0.5rem;">'
                            f'STT <b style="color:#c084fc">{int(_crow["STT"])}</b> · '
                            f'{_crow["Tên Pet"]} · <span style="color:#c084fc">{_crow["Mutation"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        _ct1, _ct2 = st.columns([4, 1])
                        with _ct1:
                            st.code(_crow["Auto Title"], language=None)
                        with _ct2:
                            if _b64_desc:
                                _bid = "cpShop" + str(_ci)
                                _cmp.html(
                                    '<button id="' + _bid + '" style="width:100%;padding:8px 4px;border:none;'
                                    'border-radius:8px;cursor:pointer;background:linear-gradient(135deg,#c084fc,#e879f9);'
                                    'color:#0a0a0f;font-weight:600;font-size:11px;">&#x1F47B; M&#xF4; t&#x1EA3;</button>'
                                    '<script>(function(){'
                                    'var btn=document.getElementById("' + _bid + '");'
                                    'var b64="' + _b64_desc + '";'
                                    'btn.addEventListener("click",function(){'
                                    'var b=this;var bytes=Uint8Array.from(atob(b64),function(c){return c.charCodeAt(0)});'
                                    'var txt=new TextDecoder("utf-8").decode(bytes);'
                                    'navigator.clipboard.writeText(txt)'
                                    '.then(function(){b.innerHTML="&#x2705;";'
                                    'setTimeout(function(){b.innerHTML="&#x1F47B; M&#xF4; t&#x1EA3;";},1500);})'
                                    '.catch(function(){b.innerHTML="&#x274C;";});'
                                    '});})();</script>',
                                    height=45,
                                )

        # ── BULK SELL ──
        _bulk_src = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        if not _bulk_src.empty:
            with st.expander("Giao dịch hàng loạt", expanded=False):
                # Giỏ bán tích lũy — tồn tại qua nhiều lần tìm kiếm
                if "bulk_cart" not in st.session_state:
                    st.session_state.bulk_cart = {}  # str(id_or_stt) → row dict

                # ── BƯỚC 1: Tìm & thêm vào giỏ ──
                st.caption("Tìm kiếm · Thêm vào giỏ · Nhập giá · Xác nhận")
                _bs_search = st.text_input(
                    "Tìm pet cần bán", placeholder="Tên, mutation, STT...",
                    key=f"bulk_sell_search_{_sv()}", label_visibility="collapsed",
                )
                _bs_df = _bulk_src.copy()
                if _bs_search.strip():
                    _bs_toks = re.split(r'[\s\-]+', _bs_search.strip().lower())
                    _bs_toks = [t for t in _bs_toks if t]
                    _bs_hay = _bs_df[["Tên Pet","Mutation","Auto Title","NameStock","STT"]].astype(str) \
                        .apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
                    _bs_combined = _bs_hay.apply(lambda r: ' '.join(r), axis=1)
                    _bs_mask = pd.Series([True]*len(_bs_df), index=_bs_df.index)
                    for _t in _bs_toks:
                        _bs_mask &= _bs_combined.str.contains(_t, regex=False, na=False)
                    _bs_df = _bs_df[_bs_mask]

                if _bs_df.empty and _bs_search.strip():
                    st.info("Không tìm thấy pet phù hợp.")
                else:
                    _shown_bs = _bs_df.head(15)
                    for _, _br in _shown_bs.iterrows():
                        _bid = str(int(float(_br.get("id", 0) or 0))) if int(float(_br.get("id", 0) or 0)) > 0 else f"stt_{int(_br['STT'])}"
                        _in_cart = _bid in st.session_state.bulk_cart
                        _rc1, _rc2 = st.columns([4, 1])
                        _br_ms     = _br.get("M/s", "")
                        _br_ns     = str(_br.get("NameStock", "") or "").strip()
                        _br_trait  = str(_br.get("Số Trait", "") or "").strip()
                        _br_ton    = int(float(_br.get("Ngày Tồn", 0) or 0))
                        _br_ms_str = f" · <b>{_br_ms}M/s</b>" if _br_ms else ""
                        _br_ns_str = f" · <span style='color:#7c6fa0'>{_br_ns}</span>" if _br_ns else ""
                        _br_trait_str = f" · Trait:{_br_trait}" if _br_trait and _br_trait.lower() != "none" else ""
                        _br_ton_str = f" · <span style='color:#f87171'>tồn {_br_ton}d</span>" if _br_ton > 0 else ""
                        _rc1.markdown(
                            f'<div style="font-size:0.82rem;padding:2px 0;">'
                            f'<b style="color:#c084fc">#{int(_br["STT"])}</b> · '
                            f'<b>{_br["Tên Pet"]}</b> · <span style="color:#a78bfa">{_br["Mutation"]}</span>'
                            f'{_br_ms_str}{_br_ns_str}{_br_trait_str}'
                            f' · <span style="color:#9d8fbf">{fmt_vnd(float(_br["Giá Nhập"]))}</span>'
                            f'{_br_ton_str}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if _in_cart:
                            if _rc2.button("✓ Bỏ", key=f"bs_rm_{_bid}", use_container_width=True):
                                del st.session_state.bulk_cart[_bid]
                                st.rerun()
                        else:
                            if _rc2.button("➕", key=f"bs_add_{_bid}", use_container_width=True, type="primary"):
                                st.session_state.bulk_cart[_bid] = _br.to_dict()
                                st.rerun()
                    if len(_bs_df) > 15:
                        st.caption(f"Đang hiển thị 15 / {len(_bs_df)} kết quả — thu hẹp tìm kiếm để xem thêm.")

                # ── BƯỚC 2: Giỏ bán ──
                if st.session_state.bulk_cart:
                    st.markdown("---")
                    _ch1, _ch2 = st.columns([3, 1])
                    _ch1.markdown(f"**🛒 Giỏ bán: {len(st.session_state.bulk_cart)} pet**")
                    if _ch2.button("🗑️ Xóa giỏ", key="bs_clear_cart", use_container_width=True):
                        st.session_state.bulk_cart = {}
                        st.rerun()

                    _cart_rows = []
                    for _ck, _cv in st.session_state.bulk_cart.items():
                        _cart_rows.append({
                            "_cart_key":   _ck,
                            "id":          int(float(_cv.get("id", 0) or 0)),
                            "STT":         int(float(_cv.get("STT", 0) or 0)),
                            "Tên Pet":     str(_cv.get("Tên Pet", "")),
                            "Mutation":    str(_cv.get("Mutation", "")),
                            "M/s":         str(_cv.get("M/s", "") or ""),
                            "NameStock":   str(_cv.get("NameStock", "") or ""),
                            "Trait":       str(_cv.get("Số Trait", "") or ""),
                            "Tồn (ngày)":  int(float(_cv.get("Ngày Tồn", 0) or 0)),
                            "Giá Nhập":    float(pd.to_numeric(_cv.get("Giá Nhập", 0), errors="coerce") or 0),
                            "Giá bán ($)": 0.0,
                            "Place":       "",
                        })
                    _cart_df = pd.DataFrame(_cart_rows)
                    _cart_edited = st.data_editor(
                        _cart_df.drop(columns=["_cart_key", "id", "STT"]),
                        key=f"bulk_cart_editor_{st.session_state.get('editor_inv_ver', 0)}",
                        use_container_width=True,
                        hide_index=True,
                        num_rows="fixed",
                        disabled=["Tên Pet", "Mutation", "M/s", "NameStock", "Trait", "Tồn (ngày)", "Giá Nhập"],
                        column_config={
                            "Tên Pet":     st.column_config.TextColumn("Pet", width="medium"),
                            "Mutation":    st.column_config.TextColumn("Mut.", width="small"),
                            "M/s":         st.column_config.TextColumn("M/s", width="small"),
                            "NameStock":   st.column_config.TextColumn("NS", width="small"),
                            "Trait":       st.column_config.TextColumn("Trait", width="small"),
                            "Tồn (ngày)":  st.column_config.NumberColumn("Tồn", format="%d", width="small"),
                            "Giá Nhập":    st.column_config.NumberColumn("Vốn (₫)", format="%d", width="small"),
                            "Giá bán ($)": st.column_config.NumberColumn("Giá ($)", min_value=0.0, step=0.01, format="%.2f", width="small"),
                            "Place":       st.column_config.TextColumn("Place", width="small"),
                        },
                    )
                    # Gắn lại id/stt từ cart_df gốc (data_editor không trả về các cột bị drop)
                    _cart_edited["_cart_key"] = _cart_df["_cart_key"].values
                    _cart_edited["id"]        = _cart_df["id"].values
                    _cart_edited["STT"]       = _cart_df["STT"].values

                    _valid_sell   = _cart_edited[_cart_edited["Giá bán ($)"] > 0]
                    _invalid_sell = _cart_edited[_cart_edited["Giá bán ($)"] <= 0]
                    if not _invalid_sell.empty:
                        st.caption(f"{len(_invalid_sell)} mục chưa có giá — sẽ được bỏ qua.")
                    if not _valid_sell.empty:
                        st.info(f"Sẵn sàng xử lý **{len(_valid_sell)}** giao dịch · Ước tính doanh thu: **{fmt_vnd(float((_valid_sell['Giá bán ($)'] * EXCHANGE_RATE).sum()))}**")
                        if st.button(f"Xác Nhận {len(_valid_sell)} Giao Dịch", type="primary", key="confirm_bulk_sell", use_container_width=True):
                            ts_ban_bulk = now_iso()
                            _full_df = st.session_state.df.copy()
                            _updated = 0
                            for _, _sell_row in _valid_sell.iterrows():
                                _s_price  = float(_sell_row["Giá bán ($)"])
                                _s_place  = str(_sell_row.get("Place", ""))
                                _s_id     = int(float(_sell_row.get("id", 0) or 0))
                                _s_stt    = int(float(_sell_row.get("STT", 0) or 0))
                                _rev_vnd  = _s_price * EXCHANGE_RATE
                                _cost_vnd = float(pd.to_numeric(_sell_row.get("Giá Nhập", 0), errors="coerce") or 0)
                                _profit   = _rev_vnd - _cost_vnd
                                if _s_id > 0:
                                    _idx = _full_df.index[_full_df["id"] == _s_id].tolist()
                                else:
                                    _idx = _full_df.index[_full_df["STT"] == _s_stt].tolist()
                                if _idx:
                                    _row_idx = _idx[0]
                                    # Ép cột numeric sang float trước khi gán tránh pandas TypeError
                                    # khi cột bị cast sang int64 (vì tất cả giá trị đang là 0)
                                    for _fc in ["Giá Bán", "Doanh Thu", "Lợi Nhuận"]:
                                        if _full_df[_fc].dtype != float:
                                            _full_df[_fc] = _full_df[_fc].astype(float)
                                    _full_df.at[_row_idx, "Giá Bán"]    = float(_s_price)
                                    _full_df.at[_row_idx, "Doanh Thu"]  = float(_rev_vnd)
                                    _full_df.at[_row_idx, "Lợi Nhuận"]  = float(_profit)
                                    _full_df.at[_row_idx, "Ngày Bán"]   = now_str()
                                    _full_df.at[_row_idx, "Trạng Thái"] = "Đã bán"
                                    _full_df.at[_row_idx, "time_ban"]   = ts_ban_bulk
                                    _full_df.at[_row_idx, "Place"]      = _s_place
                                if USE_SUPABASE:
                                    _uc = "id" if _s_id > 0 else "stt"
                                    _uv = _s_id if _s_id > 0 else _s_stt
                                    sb_update("inventory", {
                                        "gia_ban":    _s_price,
                                        "doanh_thu":  _rev_vnd,
                                        "loi_nhuan":  _profit,
                                        "ngay_ban":   now_str(),
                                        "trang_thai": "Đã bán",
                                        "time_ban":   ts_ban_bulk,
                                        "place":      _s_place,
                                    }, _uc, _uv)
                                _updated += 1
                            _full_df = apply_ngay_ton(normalize_df(_full_df, MAIN_SCHEMA))
                            st.session_state.df = _full_df
                            if USE_SUPABASE:
                                load_inventory.clear()
                                st.session_state.df = apply_ngay_ton(load_inventory())
                            st.session_state.bulk_cart = {}
                            st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
                            st.toast(f"Hoàn tất {_updated} giao dịch", icon="✅")
                            _clear_searches()
                            st.rerun()

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 2: CHART & THỐNG KÊ
    # ─────────────────────────────────────────────────────────────────────────────
with tab_chart:
    st.markdown(
        '<div style="display:inline-flex;align-items:center;gap:8px;'
        'background:linear-gradient(135deg,rgba(192,132,252,0.12),rgba(232,121,249,0.08));'
        'border:1px solid rgba(192,132,252,0.35);border-radius:8px;'
        'padding:6px 14px;margin-bottom:12px;">'
        '<span style="font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;'
        'color:#9d8fbf;font-weight:500;">Ngày bắt đầu</span>'
        '<span style="font-size:0.88rem;font-weight:600;color:#c084fc;letter-spacing:0.02em;">13/04/2026</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    # ── Aggregate data ──
    sold_df = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)].copy()

    total_cost_single  = float(df["Giá Nhập"].sum()) if not df.empty else 0.0
    total_cost_bulk    = float(bulk_df["Giá Nhập Tổng"].sum()) if not bulk_df.empty else 0.0
    total_cost         = total_cost_single + total_cost_bulk

    rev_single  = float(sold_df["Doanh Thu"].sum()) if not sold_df.empty else 0.0
    rev_bulk    = float(bulk_history["Doanh Thu Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    total_rev   = rev_single + rev_bulk

    profit_single = float(sold_df["Lợi Nhuận"].sum()) if not sold_df.empty else 0.0
    # Chỉ tính lợi nhuận đã THỰC sự thu về từ giao dịch pack (không cộng giá trị âm của pack chưa bán)
    profit_bulk   = float(bulk_history["Lợi Nhuận Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    net_profit    = profit_single + profit_bulk

    stock_count_single = int(df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)].shape[0])
    stock_count_bulk   = int(pd.to_numeric(
        bulk_df[bulk_df["Trạng Thái"]=="Available"]["Còn Lại"], errors="coerce"
    ).fillna(0).sum())
    total_stock = stock_count_single + stock_count_bulk

    # ── KPI Row ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">📊 Tổng Quan</div>', unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💰 Lợi nhuận ròng",   fmt_vnd(net_profit))
        k2.metric("📈 Tổng doanh thu",   fmt_vnd(total_rev))
        k3.metric("📥 Tổng vốn nhập",    fmt_vnd(total_cost))
        k4.metric("📦 Pet đang tồn",     f"{total_stock:,}")

    # ── Hôm nay: pet bán chi tiết ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🌅 Hoạt Động Hôm Nay</div>', unsafe_allow_html=True)

        _td_today = now_vn().date()

        def _td_is_today(ts_str):
            if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                return False
            try:
                dt = datetime.fromisoformat(str(ts_str))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=VN_TZ)
                return dt.astimezone(VN_TZ).date() == _td_today
            except Exception:
                return False

        def _td_bulk_is_today(d_str):
            if not d_str or str(d_str).strip() in ("", "nan", "None", "-"):
                return False
            try:
                return datetime.strptime(str(d_str).strip(), "%d/%m/%Y %H:%M").date() == _td_today
            except Exception:
                return False

        _td_sold_le   = sold_df[sold_df["time_ban"].apply(_td_is_today)].copy() if not sold_df.empty else pd.DataFrame()
        _td_sold_bulk = bulk_history[bulk_history["Ngày Bán"].apply(_td_bulk_is_today)].copy() \
            if not bulk_history.empty and "Ngày Bán" in bulk_history.columns else pd.DataFrame()

        _td_le_count   = len(_td_sold_le)
        _td_bulk_count = len(_td_sold_bulk)
        _td_profit_le  = float(pd.to_numeric(_td_sold_le["Lợi Nhuận"], errors="coerce").fillna(0).sum()) if not _td_sold_le.empty else 0.0
        _td_profit_bk  = float(pd.to_numeric(_td_sold_bulk["Lợi Nhuận Giao Dịch"], errors="coerce").fillna(0).sum()) if not _td_sold_bulk.empty else 0.0
        _td_profit_tot = _td_profit_le + _td_profit_bk
        _td_rev_le     = float(pd.to_numeric(_td_sold_le["Doanh Thu"], errors="coerce").fillna(0).sum()) if not _td_sold_le.empty else 0.0
        _td_rev_bk     = float(pd.to_numeric(_td_sold_bulk["Doanh Thu Giao Dịch"], errors="coerce").fillna(0).sum()) if not _td_sold_bulk.empty else 0.0
        _td_rev_tot    = _td_rev_le + _td_rev_bk
        _td_nhap_count = int(df["time_nhap"].apply(_td_is_today).sum()) if not df.empty else 0

        _td_c1, _td_c2, _td_c3, _td_c4 = st.columns(4)
        _td_c1.metric("🛒 Đã bán hôm nay", f"{_td_le_count + _td_bulk_count}",
                      help=f"Lẻ: {_td_le_count} · Lô pack: {_td_bulk_count}")
        _td_c2.metric("💰 Lợi nhuận hôm nay", fmt_vnd(_td_profit_tot))
        _td_c3.metric("📈 Doanh thu hôm nay", fmt_vnd(_td_rev_tot))
        _td_c4.metric("📥 Nhập hôm nay", f"{_td_nhap_count}")

        # Bảng tổng hợp pet lẻ + lô bán hôm nay — gọn, sắp xếp theo bán gần nhất
        _td_rows = []

        if not _td_sold_le.empty:
            _le_tmp = _td_sold_le.copy()
            # Chuẩn hoá cột thời gian → datetime để sort
            _le_tmp["_sort_ts"] = pd.to_datetime(_le_tmp["time_ban"], errors="coerce", utc=True)
            _le_tmp["_sort_ts"] = _le_tmp["_sort_ts"].dt.tz_convert(VN_TZ)
            for _, _r in _le_tmp.iterrows():
                _title = str(_r.get("Auto Title") or _r.get("Tên Pet") or "—")
                _ngay_ban = _r["_sort_ts"].strftime("%H:%M:%S") if pd.notna(_r["_sort_ts"]) else "—"
                _ngay_ton = _r.get("Ngày Tồn", 0)
                try: _ngay_ton = int(float(_ngay_ton))
                except: _ngay_ton = 0
                _td_rows.append({
                    "_sort_ts":     _r["_sort_ts"] if pd.notna(_r["_sort_ts"]) else pd.Timestamp.min.tz_localize(VN_TZ),
                    "Tên / Lô":    _title,
                    "Loại":        "🐾 Lẻ",
                    "Ngày Bán":    _ngay_ban,
                    "Ngày Tồn":   _ngay_ton,
                    "Giá Nhập":   float(pd.to_numeric(_r.get("Giá Nhập"), errors="coerce") or 0),
                    "Giá Bán":    float(pd.to_numeric(_r.get("Giá Bán"),  errors="coerce") or 0),
                    "Lợi Nhuận":  float(pd.to_numeric(_r.get("Lợi Nhuận"), errors="coerce") or 0),
                })

        if not _td_sold_bulk.empty:
            for _, _r in _td_sold_bulk.iterrows():
                _ngay_ban_raw = str(_r.get("Ngày Bán", "") or "")
                try:
                    _bk_ts = datetime.strptime(_ngay_ban_raw.strip(), "%d/%m/%Y %H:%M")
                    _bk_ts = _bk_ts.replace(tzinfo=VN_TZ)
                    _sort_ts_bk = pd.Timestamp(_bk_ts)
                    _ngay_ban_fmt = _bk_ts.strftime("%H:%M")
                except Exception:
                    _sort_ts_bk = pd.Timestamp.min.tz_localize(VN_TZ)
                    _ngay_ban_fmt = _ngay_ban_raw
                _td_rows.append({
                    "_sort_ts":    _sort_ts_bk,
                    "Tên / Lô":   str(_r.get("Tên Lô") or "—"),
                    "Loại":       "🗃️ Lô",
                    "Ngày Bán":   _ngay_ban_fmt,
                    "Ngày Tồn":  "—",
                    "Giá Nhập":  float(pd.to_numeric(_r.get("Giá Nhập Tổng"), errors="coerce") or 0),
                    "Giá Bán":   float(pd.to_numeric(_r.get("Doanh Thu Giao Dịch"), errors="coerce") or 0),
                    "Lợi Nhuận": float(pd.to_numeric(_r.get("Lợi Nhuận Giao Dịch"), errors="coerce") or 0),
                })

        if _td_rows:
            _td_tbl = (
                pd.DataFrame(_td_rows)
                .sort_values("_sort_ts", ascending=False)
                .drop(columns=["_sort_ts"])
                .reset_index(drop=True)
            )
            _td_tbl.index = _td_tbl.index + 1   # STT từ 1
            st.dataframe(
                _td_tbl,
                use_container_width=True,
                column_config={
                    "Tên / Lô":  st.column_config.TextColumn("Tên / Lô", width="large"),
                    "Loại":      st.column_config.TextColumn("Loại",     width="small"),
                    "Ngày Bán":  st.column_config.TextColumn("Giờ Bán",  width="small"),
                    "Ngày Tồn":  st.column_config.Column("Ngày Tồn",    width="small"),
                    "Giá Nhập":  st.column_config.NumberColumn("Giá Nhập (₫)",  format="%,.0f", width="medium"),
                    "Giá Bán":   st.column_config.NumberColumn("Giá Bán",        width="medium"),
                    "Lợi Nhuận": st.column_config.NumberColumn("Lợi Nhuận (₫)", format="%,.0f", width="medium"),
                },
            )
        else:
            st.caption("Chưa có giao dịch nào hôm nay.")

    # ── Waterfall: Dòng Chảy Tài Chính ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🌊 Dòng Chảy Tài Chính</div>', unsafe_allow_html=True)

        if total_rev > 0 or total_cost > 0:
            _margin_pct = net_profit / total_rev * 100 if total_rev > 0 else 0
            _roi_pct    = net_profit / total_cost * 100 if total_cost > 0 else 0
            _sold_cnt   = len(sold_df)
            if not bulk_history.empty and "Số Lượng Bán" in bulk_history.columns:
                _sold_cnt += int(pd.to_numeric(bulk_history["Số Lượng Bán"], errors="coerce").fillna(0).sum())
            _cap_remain = float(
                pd.to_numeric(
                    df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]["Giá Nhập"],
                    errors="coerce"
                ).fillna(0).sum()
            )
            if not bulk_df.empty:
                _bdf2 = bulk_df.copy()
                _bdf2["_orig"] = pd.to_numeric(_bdf2["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
                _bdf2["_left"] = pd.to_numeric(_bdf2["Còn Lại"],       errors="coerce").fillna(0)
                _bdf2["_cost"] = pd.to_numeric(_bdf2["Giá Nhập Tổng"], errors="coerce").fillna(0)
                _cap_remain += float((_bdf2["_cost"] / _bdf2["_orig"] * _bdf2["_left"]).sum())

            _wr1, _wr2, _wr3, _wr4 = st.columns(4)
            _wr1.metric("📊 Margin",          f"{_margin_pct:.1f}%")
            _wr2.metric("💹 ROI",             f"{_roi_pct:.1f}%")
            _wr3.metric("🛒 Con đã bán",      f"{_sold_cnt:,}")
            _wr4.metric("🏦 Vốn còn tồn",    fmt_vnd(_cap_remain))

            _wf_labels = ["Tổng Doanh Thu", "Tổng Vốn", "Lợi Nhuận Ròng"]
            _wf_vals   = [total_rev, total_cost, abs(net_profit)]
            _wf_colors = ["#34d399", "#f87171", "#a78bfa" if net_profit >= 0 else "#f87171"]

            _fig_wf = go.Figure(go.Bar(
                x=_wf_labels,
                y=_wf_vals,
                marker_color=_wf_colors,
                text=[fmt_short(v) for v in _wf_vals],
                textposition="outside",
                textfont=dict(color="#e2e8f0", size=12, family="Inter"),
                hovertemplate="<b>%{x}</b><br>%{y:,.0f}₫<extra></extra>",
                width=[0.45, 0.45, 0.45],
            ))
            # Overlay a "+" or "-" annotation on LN bar to show sign
            _ln_sign_text = ("+" if net_profit >= 0 else "−") + fmt_short(abs(net_profit))
            _fig_wf.add_annotation(
                x="Lợi Nhuận Ròng", y=abs(net_profit),
                text=f"<b>{'+ ' if net_profit >= 0 else '- '}{fmt_short(abs(net_profit))}</b>",
                showarrow=False, yshift=22,
                font=dict(color="#a78bfa" if net_profit >= 0 else "#f87171", size=13)
            )
            _fig_wf.update_layout(
                paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf"),
                xaxis=dict(tickfont=dict(color="#e2e8f0", size=13), gridcolor="#1a1528", zeroline=False),
                yaxis=dict(tickfont=dict(color="#9d8fbf"), gridcolor="#1a1528",
                           tickformat=",.0f", zeroline=False),
                margin=dict(l=10, r=10, t=50, b=10),
                height=340,
                showlegend=False,
                bargap=0.35,
            )
            st.plotly_chart(_fig_wf, use_container_width=True)
            st.caption("🟢 Doanh thu · 🔴 Chi phí vốn · 🟣 Lợi nhuận ròng (tất cả các thanh bắt đầu từ 0)")
        else:
            st.info("Chưa có dữ liệu tài chính.")


        # ── Build unified profit-by-date dataframe ──
        frames = []
        # Single sold
        if not sold_df.empty:
            tmp = sold_df[["Ngày Bán","Lợi Nhuận"]].copy()
            tmp.columns = ["Ngày","Lợi Nhuận"]
            frames.append(tmp)
        # Bulk history
        if not bulk_history.empty:
            tmp2 = bulk_history[["Ngày Bán","Lợi Nhuận Giao Dịch"]].copy()
            tmp2.columns = ["Ngày","Lợi Nhuận"]
            frames.append(tmp2)

        pbd = pd.DataFrame(columns=["Ngày","Lợi Nhuận"])
        if frames:
            pbd = pd.concat(frames, ignore_index=True)

        has_data = not pbd.empty

        if has_data:
            pbd["Ngày DT"] = pd.to_datetime(pbd["Ngày"], dayfirst=True, errors="coerce")
            pbd = pbd.dropna(subset=["Ngày DT"])
            pbd["Lợi Nhuận"] = pd.to_numeric(pbd["Lợi Nhuận"], errors="coerce").fillna(0)

        # ── Period selector ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">📉 Biểu Đồ Lợi Nhuận</div>', unsafe_allow_html=True)
        period_col, _ = st.columns([2, 3])
        period = period_col.radio(
            "Xem theo",
            ["Theo ngày", "Theo tuần", "Theo tháng"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if has_data and not pbd.empty:
            chart_df = pbd.copy()

            if period == "Theo ngày":
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("%d/%m/%Y")
                sort_key = chart_df["Ngày DT"].dt.normalize()
            elif period == "Theo tuần":
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("W%V/%Y")
                sort_key = (
                    chart_df["Ngày DT"]
                    - pd.to_timedelta(chart_df["Ngày DT"].dt.dayofweek, unit="d")
                ).dt.normalize()
            else:
                chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("%m/%Y")
                sort_key = chart_df["Ngày DT"].dt.strftime("%Y-%m")

            chart_df["SortKey"] = sort_key
            agg = (
                chart_df.groupby(["Period","SortKey"], as_index=False)["Lợi Nhuận"]
                .sum()
                .sort_values("SortKey")
            )
            agg["Label"] = agg["Lợi Nhuận"].apply(fmt_short)

            # Dark bar chart like reference image
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=agg["Period"],
                y=agg["Lợi Nhuận"],
                text=agg["Label"],
                textposition="outside",
                textfont=dict(size=11, color="#e2e8f0", family="Inter"),
                marker=dict(
                    color="#c084fc",
                    line=dict(color="#c084fc", width=0),
                ),
                cliponaxis=False,
            ))
            fig.update_layout(
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf", size=11),
                xaxis=dict(
                    type="category",
                    tickfont=dict(size=10, color="#9d8fbf"),
                    gridcolor="#1a1528",
                    linecolor="#2d2540",
                ),
                yaxis=dict(
                    title="Lợi nhuận (VNĐ)",
                    tickfont=dict(size=10, color="#9d8fbf"),
                    gridcolor="#1a1528",
                    linecolor="#2d2540",
                    tickformat=",.0f",
                ),
                margin=dict(l=10, r=10, t=30, b=10),
                height=420,
                bargap=0.35,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Period stats below chart ──
            period_label = {"Theo ngày":"ngày","Theo tuần":"tuần","Theo tháng":"tháng"}[period]
            last_row = agg.iloc[-1] if not agg.empty else None
            prev_row = agg.iloc[-2] if len(agg) >= 2 else None

            c1, c2, c3 = st.columns(3)
            if last_row is not None:
                delta = None
                if prev_row is not None:
                    delta_val = last_row["Lợi Nhuận"] - prev_row["Lợi Nhuận"]
                    # Streamlit detects sign from string prefix — must put "-" before "₫"
                    _delta_cmp_lbl = {
                        "Theo ngày":  "so với hôm qua",
                        "Theo tuần":  "so với tuần trước",
                        "Theo tháng": "so với tháng trước",
                    }.get(period, "")
                    delta = ("-" if delta_val < 0 else "") + f"₫{abs(delta_val):,.0f}" + (f" {_delta_cmp_lbl}" if _delta_cmp_lbl else "")
                _period_delta_label = {
                    "Theo ngày":  "so với hôm qua",
                    "Theo tuần":  "so với tuần trước",
                    "Theo tháng": "so với tháng trước",
                }.get(period, "")
                _this_period_lbl = {
                    "Theo ngày":  "hôm nay",
                    "Theo tuần":  "tuần này",
                    "Theo tháng": "tháng này",
                }.get(period, period_label)
                c1.metric(
                    f"Lợi nhuận {_this_period_lbl} ({last_row['Period']})",
                    fmt_vnd(last_row["Lợi Nhuận"]),
                    delta=delta,
                    help=f"So sánh {_period_delta_label}",
                )
                c2.metric(f"Số {period_label} có giao dịch",  f"{len(agg):,}")
                c3.metric(f"Lợi nhuận trung bình mỗi {period_label}",  fmt_vnd(agg['Lợi Nhuận'].mean()))
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

        # ── Cumulative Profit Line ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">📈 Lợi Nhuận Tích Lũy</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            # Group by date → one data point per day
            _cum_daily = (
                pbd[["Ngày DT","Lợi Nhuận"]]
                .dropna(subset=["Ngày DT"])
                .assign(_date=lambda d: d["Ngày DT"].dt.date)
                .groupby("_date", as_index=False)["Lợi Nhuận"].sum()
                .sort_values("_date")
                .copy()
            )
            _cum_daily["Tích Lũy"] = _cum_daily["Lợi Nhuận"].cumsum()
            _cum_daily["Ngày DT"]  = pd.to_datetime(_cum_daily["_date"])

            # milestone annotations (only those reached)
            _cum_milestones = [10_000_000, 20_000_000, 30_000_000, 50_000_000, 100_000_000]
            _annotations = []
            for _ms_val in _cum_milestones:
                _cross = _cum_daily[_cum_daily["Tích Lũy"] >= _ms_val]
                if not _cross.empty:
                    _ms_row = _cross.iloc[0]
                    _annotations.append(dict(
                        x=_ms_row["Ngày DT"], y=_ms_val,
                        text=f"🏆 {_ms_val//1_000_000}M",
                        showarrow=True, arrowhead=2, arrowcolor="#fef08a",
                        font=dict(color="#fef08a", size=10),
                        bgcolor="#1a1528", bordercolor="#fef08a", borderwidth=1,
                        ax=0, ay=-30,
                    ))

            _bar_colors = ["#34d399" if v >= 0 else "#f87171" for v in _cum_daily["Lợi Nhuận"]]

            _fig_cum = go.Figure()
            _fig_cum.add_trace(go.Bar(
                x=_cum_daily["Ngày DT"], y=_cum_daily["Lợi Nhuận"],
                name="LN ngày",
                yaxis="y2",
                marker=dict(color=_bar_colors, opacity=0.55),
                hovertemplate="%{x|%d/%m/%Y}<br>LN ngày: <b>%{y:,.0f}₫</b><extra></extra>",
            ))
            _fig_cum.add_trace(go.Scatter(
                x=_cum_daily["Ngày DT"], y=_cum_daily["Tích Lũy"],
                mode="lines",
                fill="tozeroy",
                fillcolor="rgba(167,139,250,0.12)",
                line=dict(color="#a78bfa", width=2.5),
                name="Tích lũy",
                hovertemplate="%{x|%d/%m/%Y}<br>Tích lũy: <b>%{y:,.0f}₫</b><extra></extra>",
            ))

            _fig_cum.update_layout(
                paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf"),
                annotations=_annotations,
                xaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#9d8fbf"), showgrid=False),
                yaxis=dict(
                    title="Tích lũy (₫)", gridcolor="#1a1528",
                    tickfont=dict(color="#9d8fbf"), tickformat=",.0f",
                    zeroline=True, zerolinecolor="#2d2040",
                ),
                yaxis2=dict(
                    title="LN ngày (₫)", overlaying="y", side="right",
                    showgrid=False, tickfont=dict(color="#9d8fbf"),
                    tickformat=",.0f",
                ),
                legend=dict(orientation="h", x=0, y=1.08, font=dict(color="#9d8fbf")),
                margin=dict(l=10, r=10, t=40, b=10),
                height=360,
                hovermode="x unified",
                bargap=0.2,
            )
            st.plotly_chart(_fig_cum, use_container_width=True)

            # Summary KPIs
            _cum_total     = float(_cum_daily["Tích Lũy"].iloc[-1])
            _cum_best_day  = float(_cum_daily["Lợi Nhuận"].max())
            _cum_worst_day = float(_cum_daily["Lợi Nhuận"].min())
            _cum_pos_days  = int((_cum_daily["Lợi Nhuận"] > 0).sum())
            _cum_total_days = len(_cum_daily)
            _kc1, _kc2, _kc3, _kc4 = st.columns(4)
            _kc1.metric("Tổng tích lũy", fmt_vnd(_cum_total))
            _kc2.metric("📈 Ngày đỉnh", fmt_vnd(_cum_best_day))
            _kc3.metric("📉 Ngày thấp nhất", fmt_vnd(_cum_worst_day))
            _kc4.metric("✅ Ngày có lời", f"{_cum_pos_days} / {_cum_total_days} ngày")
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

        # ── Revenue channel split ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🔀 Phân Tích Kênh & Sản Phẩm</div>', unsafe_allow_html=True)
        c_left, c_right = st.columns(2)

        with c_left:
            # So sánh Doanh thu đã thu vs Tổng vốn tồn kho
            _dt_sold_total = float(pd.to_numeric(sold_df["Doanh Thu"], errors="coerce").fillna(0).sum()) if not sold_df.empty else 0.0
            _von_ton_total = _von_le + _von_lo
            _compare_df = pd.DataFrame({
                "Hạng mục": ["Doanh thu", "Vốn tồn"],
                "Giá trị":   [_dt_sold_total, _von_ton_total],
            })
            fig_cmp = go.Figure(go.Bar(
                x=_compare_df["Hạng mục"],
                y=_compare_df["Giá trị"],
                marker_color=["#c084fc", "#e879f9"],
                text=_compare_df["Giá trị"].apply(fmt_short),
                textposition="outside",
                textfont=dict(color="#e2e8f0"),
            ))
            fig_cmp.update_layout(
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf"),
                title=dict(text="Doanh thu - Vốn tồn", font=dict(size=13, color="#e2e8f0")),
                margin=dict(l=10, r=10, t=50, b=10),
                height=300,
                yaxis_title="VNĐ",
                xaxis=dict(tickfont=dict(color="#e2e8f0")),
            )
            if _dt_sold_total > 0 or _von_ton_total > 0:
                st.plotly_chart(fig_cmp, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

        with c_right:
            # Top 10 pets by profit
            if not sold_df.empty:
                top_pets = (
                    sold_df.groupby("Tên Pet", as_index=False)["Lợi Nhuận"]
                    .sum()
                    .sort_values("Lợi Nhuận", ascending=True)
                    .tail(10)
                )
                fig_bar = go.Figure(go.Bar(
                    x=top_pets["Lợi Nhuận"],
                    y=top_pets["Tên Pet"],
                    orientation="h",
                    marker=dict(color="#c084fc"),
                    text=top_pets["Lợi Nhuận"].apply(fmt_short),
                    textposition="outside",
                    textfont=dict(color="#e2e8f0", size=10),
                ))
                fig_bar.update_layout(
                    paper_bgcolor="#0a0a0f",
                    plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    title=dict(text="Top 10 Pet Lợi nhuận cao", font=dict(size=13, color="#e2e8f0")),
                    xaxis=dict(gridcolor="#1a1528", tickformat=",.0f", tickfont=dict(color="#9d8fbf")),
                    yaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#e2e8f0")),
                    margin=dict(l=10, r=10, t=50, b=10),
                    height=300,
                    showlegend=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu.")

        # ── Bubble Scatter: Volume vs Margin per Mutation ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🫧 Hiệu Quả Theo Mutation — Volume vs Margin</div>', unsafe_allow_html=True)

        if not sold_df.empty and "Mutation" in sold_df.columns:
            _tm_df = sold_df.copy()
            _tm_df["_mut"] = _tm_df["Mutation"].astype(str).str.strip().replace("", "Không rõ")
            _tm_df["_dt"]  = pd.to_numeric(_tm_df["Doanh Thu"], errors="coerce").fillna(0)
            _tm_df["_ln"]  = pd.to_numeric(_tm_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _tm_grp = (
                _tm_df.groupby("_mut", as_index=False)
                .agg(DT=("_dt","sum"), LN_total=("_ln","sum"), Count=("_ln","count"))
                .query("Count > 0")
            )
            _tm_grp["LN_per_unit"] = _tm_grp["LN_total"] / _tm_grp["Count"]
            _tm_grp["Margin_pct"]  = (_tm_grp["LN_total"] / _tm_grp["DT"].replace(0, float("nan")) * 100).fillna(0)

            if not _tm_grp.empty:
                # Quadrant reference lines at medians
                _med_x = float(_tm_grp["Count"].median())
                _med_y = float(_tm_grp["LN_per_unit"].median())

                # Color palette per mutation (distinct vivid colors)
                _MUT_PALETTE = {
                    "Normal":"#94a3b8","Gold":"#fbbf24","Diamond":"#67e8f9",
                    "Bloodrot":"#f87171","Candy":"#f9a8d4","Divine":"#c084fc",
                    "Lava":"#fb923c","Galaxy":"#818cf8","Yin-Yang":"#e2e8f0",
                    "Radioactive":"#86efac","Cursed":"#4ade80","Rainbow":"#f472b6",
                    "Không rõ":"#6b7280",
                }
                _dot_colors = [_MUT_PALETTE.get(m, "#a78bfa") for m in _tm_grp["_mut"]]

                _fig_bub = go.Figure()

                # Quadrant shading
                _fig_bub.add_hrect(y0=_med_y, y1=_tm_grp["LN_per_unit"].max()*1.2,
                                   fillcolor="rgba(52,211,153,0.04)", line_width=0)
                _fig_bub.add_hrect(y0=_tm_grp["LN_per_unit"].min()*1.2, y1=_med_y,
                                   fillcolor="rgba(248,113,113,0.04)", line_width=0)

                # Quadrant lines
                _fig_bub.add_hline(y=_med_y, line=dict(color="#2d2040", width=1, dash="dot"))
                _fig_bub.add_vline(x=_med_x, line=dict(color="#2d2040", width=1, dash="dot"))

                # Quadrant labels
                for _ql_x, _ql_y, _ql_txt in [
                    (_tm_grp["Count"].max()*0.92, _tm_grp["LN_per_unit"].max()*1.1, "⭐ Ngôi sao"),
                    (_tm_grp["Count"].max()*0.03, _tm_grp["LN_per_unit"].max()*1.1, "💎 Hiếm & lời"),
                    (_tm_grp["Count"].max()*0.92, _med_y*0.02, "📦 Bán nhiều, ít lời"),
                    (_tm_grp["Count"].max()*0.03, _med_y*0.02, "⚠️ Cần xem xét"),
                ]:
                    _fig_bub.add_annotation(
                        x=_ql_x, y=_ql_y, text=_ql_txt,
                        showarrow=False, font=dict(color="#4a3f6b", size=9),
                        xanchor="left",
                    )

                # Bubbles
                for _, _row in _tm_grp.iterrows():
                    _col = _MUT_PALETTE.get(str(_row["_mut"]), "#a78bfa")
                    _sz  = max(20, min(80, _row["DT"] / (_tm_grp["DT"].max() or 1) * 70 + 12))
                    _fig_bub.add_trace(go.Scatter(
                        x=[_row["Count"]],
                        y=[_row["LN_per_unit"]],
                        mode="markers+text",
                        name=str(_row["_mut"]),
                        marker=dict(
                            size=_sz,
                            color=_col,
                            opacity=0.85,
                            line=dict(color="#0a0a0f", width=1.5),
                        ),
                        text=[str(_row["_mut"])],
                        textposition="top center",
                        textfont=dict(color="#e2e8f0", size=10),
                        hovertemplate=(
                            f"<b>{_row['_mut']}</b><br>"
                            f"Số con: {int(_row['Count'])}<br>"
                            f"LN TB/con: {_row['LN_per_unit']:,.0f}₫<br>"
                            f"Tổng LN: {_row['LN_total']:,.0f}₫<br>"
                            f"Doanh thu: {_row['DT']:,.0f}₫<br>"
                            f"Margin: {_row['Margin_pct']:.1f}%"
                            "<extra></extra>"
                        ),
                        showlegend=False,
                    ))

                _fig_bub.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    xaxis=dict(
                        title="Số con đã bán (volume)",
                        gridcolor="#1a1528", tickfont=dict(color="#9d8fbf"),
                        zeroline=False,
                    ),
                    yaxis=dict(
                        title="LN trung bình / con (₫)",
                        gridcolor="#1a1528", tickfont=dict(color="#9d8fbf"),
                        tickformat=",.0f", zeroline=True, zerolinecolor="#4a3f6b",
                    ),
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=420,
                    hovermode="closest",
                )
                st.plotly_chart(_fig_bub, use_container_width=True)
                st.caption("Kích thước bubble = tổng doanh thu · Kẻ đứt = median")
            else:
                st.info("Chưa có dữ liệu.")
        else:
            st.info("Chưa có dữ liệu.")

        # ── Pet Performance Scatter ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🔵 Hiệu Quả Theo Tên Pet — Giá vs Lợi Nhuận</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            _pp_df = sold_df.copy()
            _pp_df["_gn"]  = pd.to_numeric(_pp_df["Giá Nhập"],  errors="coerce").fillna(0)
            _pp_df["_ln"]  = pd.to_numeric(_pp_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _pp_df["_pet"] = _pp_df["Tên Pet"].astype(str).str.strip()
            _pp_grp = (
                _pp_df.groupby("_pet", as_index=False)
                .agg(AvgCost=("_gn","mean"), AvgLN=("_ln","mean"),
                     TotalDT=("_gn","sum"),  Count=("_ln","count"))
            )
            _pp_grp["Margin"] = _pp_grp["AvgLN"] / (_pp_grp["AvgCost"].replace(0, float("nan"))) * 100
            _pp_grp = _pp_grp[_pp_grp["AvgCost"] > 0].dropna(subset=["Margin"])

            if not _pp_grp.empty:
                _med_px = float(_pp_grp["AvgCost"].median())
                _med_py = float(_pp_grp["AvgLN"].median())

                _fig_pp = go.Figure()
                _fig_pp.add_hline(y=_med_py, line=dict(color="#2d2040", width=1, dash="dot"))
                _fig_pp.add_vline(x=_med_px, line=dict(color="#2d2040", width=1, dash="dot"))

                _pp_xmax = float(_pp_grp["AvgCost"].max())
                _pp_ymax = float(_pp_grp["AvgLN"].max())
                for _qx2, _qy2, _qt2 in [
                    (_pp_xmax * 0.65, _pp_ymax * 1.05, "💰 Đắt & lời nhiều"),
                    (_pp_xmax * 0.01, _pp_ymax * 1.05, "💎 Rẻ & lời nhiều"),
                    (_pp_xmax * 0.65, _med_py * 0.05,  "📦 Đắt, lời ít"),
                    (_pp_xmax * 0.01, _med_py * 0.05,  "⚠️ Rẻ, lời ít"),
                ]:
                    _fig_pp.add_annotation(
                        x=_qx2, y=_qy2, text=_qt2,
                        showarrow=False, font=dict(color="#4a3f6b", size=9), xanchor="left"
                    )

                _PP_PALETTE = [
                    "#a78bfa","#34d399","#f472b6","#fbbf24","#38bdf8",
                    "#fb923c","#4ade80","#e879f9","#67e8f9","#f87171",
                    "#c084fc","#86efac","#fdba74","#a5b4fc","#f9a8d4",
                    "#6ee7b7","#fde68a","#bae6fd","#ddd6fe","#bbf7d0",
                ]
                for _pi, (_, _pr) in enumerate(_pp_grp.iterrows()):
                    _sz2 = max(14, min(60, _pr["Count"] / max(float(_pp_grp["Count"].max()), 1) * 46 + 14))
                    _m2  = float(_pr["Margin"])
                    _c2  = _PP_PALETTE[_pi % len(_PP_PALETTE)]
                    _fig_pp.add_trace(go.Scatter(
                        x=[_pr["AvgCost"]], y=[_pr["AvgLN"]],
                        mode="markers",
                        name=str(_pr["_pet"]),
                        marker=dict(size=_sz2, color=_c2, opacity=0.88,
                                    line=dict(color="#0a0a0f", width=1.5)),
                        hovertemplate=(
                            f"<b>{_pr['_pet']}</b><br>"
                            f"Giá nhập TB: {_pr['AvgCost']:,.0f}₫<br>"
                            f"LN TB/con: {_pr['AvgLN']:,.0f}₫<br>"
                            f"Margin: {_m2:.1f}%<br>"
                            f"Số lần bán: {int(_pr['Count'])}"
                            "<extra></extra>"
                        ),
                        showlegend=True,
                    ))

                _fig_pp.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    xaxis=dict(title="Giá nhập TB (₫)", gridcolor="#1a1528",
                               tickfont=dict(color="#9d8fbf"), tickformat=",.0f", zeroline=False),
                    yaxis=dict(title="LN TB / con (₫)", gridcolor="#1a1528",
                               tickfont=dict(color="#9d8fbf"), tickformat=",.0f",
                               zeroline=True, zerolinecolor="#4a3f6b"),
                    legend=dict(
                        orientation="v", x=1.01, y=1,
                        font=dict(color="#9d8fbf", size=10),
                        bgcolor="rgba(10,10,15,0.7)",
                        bordercolor="#2d2040", borderwidth=1,
                    ),
                    margin=dict(l=10, r=180, t=20, b=10),
                    height=440,
                    hovermode="closest",
                )
                st.plotly_chart(_fig_pp, use_container_width=True)
                st.caption("Kích thước = số lần bán · Mỗi màu = 1 loại pet · Hover để xem chi tiết · Kẻ đứt = median")
            else:
                st.info("Chưa có dữ liệu.")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── Avg days to sell + Top mutation ──
    # ── Weekly / Monthly summary table ──
    if has_data and not pbd.empty:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">📋 Bảng Thống Kê Theo Tháng</div>', unsafe_allow_html=True)
            monthly = (
                pbd.assign(
                    Tháng=pbd["Ngày DT"].dt.strftime("%m/%Y"),
                    SortKey=pbd["Ngày DT"].dt.strftime("%Y-%m"),
                )
                .groupby(["Tháng","SortKey"], as_index=False)["Lợi Nhuận"].sum()
                .sort_values("SortKey", ascending=False)
                .drop(columns=["SortKey"])
            )
            monthly_display = monthly[["Tháng","Lợi Nhuận"]].copy()
            monthly_display["Lợi Nhuận VNĐ"] = monthly_display["Lợi Nhuận"].apply(fmt_vnd)
            monthly_display["Tổng Giao Dịch"] = monthly_display["Tháng"].map(
                pbd.assign(Tháng=pbd["Ngày DT"].dt.strftime("%m/%Y")).groupby("Tháng")["Lợi Nhuận"].count()
            ).fillna(0).astype(int)

            st.dataframe(
                monthly_display[["Tháng","Lợi Nhuận VNĐ","Tổng Giao Dịch"]],
                use_container_width=True, hide_index=True
            )

    with st.container(border=True):
        st.markdown('<div class="sec-heading">🚀 Hiệu Suất Bán Hàng</div>', unsafe_allow_html=True)
        _perf_c1, _perf_c2 = st.columns(2)

        with _perf_c1:
            st.markdown("**Vòng Quay Hàng — Thời gian tồn kho TB trước khi bán**")
            if not sold_df.empty:
                _sold_speed = sold_df.copy()
                _sold_speed["Ngày Tồn"] = pd.to_numeric(_sold_speed["Ngày Tồn"], errors="coerce").fillna(0)
                _avg_days = _sold_speed["Ngày Tồn"].mean()
                _med_days = _sold_speed["Ngày Tồn"].median()
                _sp1, _sp2 = st.columns(2)
                _sp1.metric("Trung bình", f"{int(round(_avg_days))} ngày")
                _sp2.metric("Trung vị", f"{int(round(_med_days))} ngày")

                # Biểu đồ theo tên pet (top 10 bán chậm nhất)
                _spd_by_pet = (
                    _sold_speed.groupby("Tên Pet", as_index=False)["Ngày Tồn"]
                    .mean()
                    .sort_values("Ngày Tồn", ascending=False)
                    .head(10)
                )
                fig_spd = go.Figure(go.Bar(
                    x=_spd_by_pet["Ngày Tồn"],
                    y=_spd_by_pet["Tên Pet"],
                    orientation="h",
                    marker=dict(color="#f472b6"),
                    text=_spd_by_pet["Ngày Tồn"].apply(lambda v: f"{int(round(v))}d"),
                    textposition="outside",
                    textfont=dict(color="#e2e8f0", size=10),
                ))
                fig_spd.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    title=dict(text="Top 10 Pet bán chậm nhất (ngày TB)", font=dict(size=12, color="#e2e8f0")),
                    xaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#9d8fbf")),
                    yaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#e2e8f0")),
                    margin=dict(l=10, r=20, t=45, b=10),
                    height=300, showlegend=False,
                )
                st.plotly_chart(fig_spd, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu bán.")

        with _perf_c2:
            st.markdown("**Hiệu Suất Theo Mutation**")
            if not sold_df.empty:
                _mut_perf = (
                    sold_df.copy()
                    .assign(LN=lambda d: pd.to_numeric(d["Lợi Nhuận"], errors="coerce").fillna(0))
                    .groupby("Mutation", as_index=False)
                    .agg(LN_mean=("LN","mean"), LN_total=("LN","sum"), Count=("LN","count"))
                    .sort_values("LN_mean", ascending=True)
                )
                fig_mut = go.Figure(go.Bar(
                    x=_mut_perf["LN_mean"],
                    y=_mut_perf["Mutation"],
                    orientation="h",
                    marker=dict(color="#a78bfa"),
                    text=_mut_perf["LN_mean"].apply(fmt_short),
                    textposition="outside",
                    textfont=dict(color="#e2e8f0", size=10),
                    customdata=_mut_perf[["LN_total","Count"]].values,
                    hovertemplate="<b>%{y}</b><br>TB/con: %{x:,.0f}₫<br>Tổng: %{customdata[0]:,.0f}₫<br>Số con: %{customdata[1]}<extra></extra>",
                ))
                fig_mut.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    title=dict(text="Lợi nhuận TB theo Mutation", font=dict(size=12, color="#e2e8f0")),
                    xaxis=dict(gridcolor="#1a1528", tickformat=",.0f", tickfont=dict(color="#9d8fbf")),
                    yaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#e2e8f0")),
                    margin=dict(l=10, r=20, t=45, b=10),
                    height=300, showlegend=False,
                )
                st.plotly_chart(fig_mut, use_container_width=True)

                # Bảng tóm tắt
                _mut_disp = _mut_perf.sort_values("LN_mean", ascending=False).copy()
                _mut_disp["LN TB/con"] = _mut_disp["LN_mean"].apply(fmt_vnd)
                _mut_disp["Tổng LN"]   = _mut_disp["LN_total"].apply(fmt_vnd)
                _mut_disp = _mut_disp.rename(columns={"Count":"Số con"})
                st.dataframe(_mut_disp[["Mutation","Số con","LN TB/con","Tổng LN"]], use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có dữ liệu bán.")

        # ── Phân tích theo NameStock ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🏷️ Phân Tích Theo NameStock</div>', unsafe_allow_html=True)

        if not sold_df.empty and "NameStock" in sold_df.columns:
            _ns_grp = sold_df.copy()
            _ns_grp["LN"] = pd.to_numeric(_ns_grp["Lợi Nhuận"], errors="coerce").fillna(0)
            _ns_grp["DT"] = pd.to_numeric(_ns_grp["Doanh Thu"], errors="coerce").fillna(0)
            _ns_grp["NS"] = _ns_grp["NameStock"].astype(str).str.strip().replace("", "(trống)")
            _ns_perf = (
                _ns_grp.groupby("NS", as_index=False)
                .agg(LN_total=("LN","sum"), DT_total=("DT","sum"), Count=("LN","count"))
                .sort_values("LN_total", ascending=False)
            )
            _ns_disp = _ns_perf.rename(columns={"NS":"NameStock","Count":"Số con"}).copy()
            _ns_disp["Lợi nhuận"] = _ns_disp["LN_total"].apply(fmt_vnd)
            _ns_disp["Doanh thu"] = _ns_disp["DT_total"].apply(fmt_vnd)
            st.dataframe(_ns_disp[["NameStock","Số con","Lợi nhuận","Doanh thu"]], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu bán.")

    # ── Phân tích khung giờ bán hàng ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🕐 Phân Tích Khung Giờ Bán Hàng</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            def _extract_hour(ts_str):
                if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                    return None
                try:
                    dt = datetime.fromisoformat(str(ts_str))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=VN_TZ)
                    return dt.astimezone(VN_TZ).hour
                except Exception:
                    return None

            _hour_df = sold_df.copy()
            _hour_df["Giờ"] = _hour_df["time_ban"].apply(_extract_hour)
            _hour_df = _hour_df.dropna(subset=["Giờ"])
            _hour_df["Giờ"] = _hour_df["Giờ"].astype(int)

            if not _hour_df.empty:
                _hour_count = (
                    _hour_df.groupby("Giờ", as_index=False)
                    .agg(Đơn=("Giờ", "count"))
                )
                # Fill missing hours with 0 for full 0-23 axis
                _all_hours = pd.DataFrame({"Giờ": range(24)})
                _hour_count = _all_hours.merge(_hour_count, on="Giờ", how="left").fillna(0)
                _hour_count["Đơn"] = _hour_count["Đơn"].astype(int)

                _peak_hour = int(_hour_count.loc[_hour_count["Đơn"].idxmax(), "Giờ"])
                _colors = ["#e879f9" if h == _peak_hour else "#7c3aed" for h in _hour_count["Giờ"]]

                fig_hour = go.Figure(go.Bar(
                    x=[f"{h:02d}:00" for h in _hour_count["Giờ"]],
                    y=_hour_count["Đơn"],
                    marker_color=_colors,
                    text=_hour_count["Đơn"].apply(lambda v: str(v) if v > 0 else ""),
                    textposition="outside",
                ))
                fig_hour.update_layout(
                    xaxis_title="Khung giờ (giờ VN)",
                    yaxis_title="Số đơn bán",
                    margin=dict(t=30, b=40),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    xaxis=dict(tickangle=-45),
                    height=340,
                )
                st.plotly_chart(fig_hour, use_container_width=True)
                st.caption(f"Cao điểm: **{_peak_hour:02d}:00 – {_peak_hour:02d}:59** · {int(_hour_count.loc[_hour_count['Giờ']==_peak_hour,'Đơn'].values[0])} giao dịch")
            else:
                st.info("Chưa có dữ liệu thời gian bán hàng.")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── #27 Heatmap ngày × giờ ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🗓️ Heatmap: Thứ × Giờ</div>', unsafe_allow_html=True)

        if not sold_df.empty:
            def _extract_dt_parts(ts_str):
                """Returns (hour, weekday) or (None, None)."""
                if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                    return None, None
                try:
                    dt = datetime.fromisoformat(str(ts_str))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=VN_TZ)
                    dt = dt.astimezone(VN_TZ)
                    return dt.hour, dt.weekday()  # weekday: 0=Mon … 6=Sun
                except Exception:
                    return None, None

            _hmap_rows = sold_df["time_ban"].apply(_extract_dt_parts)
            _hmap_df2 = pd.DataFrame(_hmap_rows.tolist(), columns=["Giờ_h", "Thứ_w"])
            _hmap_df2 = _hmap_df2.dropna()
            _hmap_df2["Giờ_h"] = _hmap_df2["Giờ_h"].astype(int)
            _hmap_df2["Thứ_w"] = _hmap_df2["Thứ_w"].astype(int)

            if not _hmap_df2.empty:
                _pivot_hm = _hmap_df2.groupby(["Thứ_w", "Giờ_h"]).size().unstack(fill_value=0)
                for _hc in range(24):
                    if _hc not in _pivot_hm.columns:
                        _pivot_hm[_hc] = 0
                _pivot_hm = _pivot_hm[[c for c in range(24)]]
                for _rd in range(7):
                    if _rd not in _pivot_hm.index:
                        _pivot_hm.loc[_rd] = 0
                _pivot_hm = _pivot_hm.sort_index()
                _days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
                fig_hmap = go.Figure(go.Heatmap(
                    z=_pivot_hm.values,
                    x=[f"{h:02d}:00" for h in range(24)],
                    y=[_days_vn[i] for i in _pivot_hm.index],
                    colorscale="YlOrRd",
                    text=_pivot_hm.values,
                    texttemplate="%{text}",
                    showscale=True,
                ))
                fig_hmap.update_layout(
                    xaxis_title="Giờ (giờ VN)",
                    yaxis_title="Thứ",
                    margin=dict(t=30, b=50),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    height=310,
                    xaxis=dict(tickangle=-45),
                )
                st.plotly_chart(fig_hmap, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu thời gian bán hàng.")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── AJ: Streak & Thành tích ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🏆 Thành Tích & Kỷ Lục</div>', unsafe_allow_html=True)

        _all_sold_ch = sold_df.copy()

        def _parse_ban_date_ch(ts_str):
            if not ts_str or str(ts_str).strip() in ("", "nan", "None", "-"):
                return None
            try:
                dt = datetime.fromisoformat(str(ts_str))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=VN_TZ)
                return dt.astimezone(VN_TZ).date()
            except Exception:
                return None

        _today_ch = now_vn().date()
        _ban_dates_ch = _all_sold_ch["time_ban"].apply(_parse_ban_date_ch).dropna()
        _unique_days_ch = sorted(set(_ban_dates_ch), reverse=True)
        _streak_ch = 0
        if _unique_days_ch:
            _chk = _today_ch
            for _d in _unique_days_ch:
                if _d == _chk:
                    _streak_ch += 1
                    _chk = _chk - __import__("datetime").timedelta(days=1)
                elif _d < _chk:
                    break

        _total_sold_ch = len(_all_sold_ch)
        _SELL_MILESTONES = [
            (500, "🏆 Legend Trader"),
            (200, "💎 Diamond Seller"),
            (100, "🥇 Century Club"),
            (50,  "🥈 Half Century"),
            (20,  "🥉 Getting Started"),
            (1,   "🌱 First Sale"),
        ]
        _badge_ch = next((b for n, b in _SELL_MILESTONES if _total_sold_ch >= n), None)
        _next_sell_ms = next(((n, b) for n, b in reversed(_SELL_MILESTONES) if _total_sold_ch < n), None)
        _streak_icon_ch = "🔥" if _streak_ch >= 3 else ("✨" if _streak_ch >= 1 else "💤")

        _ach_c1, _ach_c2, _ach_c3 = st.columns(3)
        _ach_c1.metric("Chuỗi ngày", f"{_streak_icon_ch} {_streak_ch} ngày")
        _ach_c2.metric("Tổng giao dịch", f"{_total_sold_ch}")
        _ach_c3.metric("Cấp độ", _badge_ch or "—")
        if _next_sell_ms:
            st.caption(f"Cột mốc tiếp theo · **{_next_sell_ms[1]}**: còn **{_next_sell_ms[0] - _total_sold_ch}** giao dịch")

        # ── AK: Personal Records ──
        st.markdown("**Kỷ Lục**")
        if not _all_sold_ch.empty:
            _ln_col_ch = pd.to_numeric(_all_sold_ch["Lợi Nhuận"], errors="coerce").fillna(0)
            _ton_col_ch = pd.to_numeric(_all_sold_ch["Ngày Tồn"], errors="coerce").fillna(999)

            _best_ln_row_ch = _all_sold_ch.loc[_ln_col_ch.idxmax()]
            _best_ln_val_ch = float(_ln_col_ch.max())
            _fast_valid = _ton_col_ch[_ton_col_ch >= 0]
            _fast_row_ch = _all_sold_ch.loc[_fast_valid.idxmin()] if not _fast_valid.empty else None
            _fast_days_ch = float(_fast_valid.min()) if not _fast_valid.empty else 0.0

            _day_df_ch = _all_sold_ch.copy()
            _day_df_ch["_bd"] = _day_df_ch["time_ban"].apply(_parse_ban_date_ch)
            _day_df_ch["_ln"] = pd.to_numeric(_day_df_ch["Lợi Nhuận"], errors="coerce").fillna(0)
            _day_profit_ch = _day_df_ch.dropna(subset=["_bd"]).groupby("_bd")["_ln"].sum()
            _best_day_ch = _day_profit_ch.idxmax() if not _day_profit_ch.empty else None
            _best_day_val_ch = float(_day_profit_ch.max()) if not _day_profit_ch.empty else 0.0

            _rec_c1, _rec_c2, _rec_c3 = st.columns(3)
            _rec_c1.metric("Giao dịch tốt nhất", fmt_vnd(_best_ln_val_ch),
                           help=str(_best_ln_row_ch.get('Tên Pet','?')))
            _rec_c2.metric("Chốt nhanh nhất", fmt_ngay_ton(_fast_days_ch),
                           help=str(_fast_row_ch.get('Tên Pet','?')) if _fast_row_ch is not None else "")
            _rec_c3.metric("Ngày đỉnh cao", fmt_vnd(_best_day_val_ch),
                           help=str(_best_day_ch) if _best_day_ch else "")
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── Mốc lợi nhuận tích lũy ──
        st.markdown("**Cột Mốc Lợi Nhuận**")
        _total_ln_ch = float(_ln_col_ch.sum()) if not _all_sold_ch.empty else 0.0
        _ln_m_ch = _total_ln_ch / 1_000_000
        _LN_MS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        _nxt_ln_ms = next((m for m in _LN_MS if _ln_m_ch < m), None)
        _lst_ln_ms = next((m for m in reversed(_LN_MS) if _ln_m_ch >= m), None)
        st.caption(f"Lợi nhuận tích lũy: **{fmt_vnd(_total_ln_ch)}**")
        if _nxt_ln_ms:
            _base_ch = (_lst_ln_ms or 0) * 1_000_000
            _tgt_ch = _nxt_ln_ms * 1_000_000
            _pct_ch = min((_total_ln_ch - _base_ch) / (_tgt_ch - _base_ch), 1.0) if _tgt_ch > _base_ch else 1.0
            st.progress(max(_pct_ch, 0.0),
                        text=f"Mốc {_nxt_ln_ms}M: {fmt_vnd(_total_ln_ch)} / {fmt_vnd(_tgt_ch)} ({_pct_ch*100:.0f}%)")
        else:
            st.progress(1.0, text="🏆 Đã vượt 100M tích lũy!")
        _ms_row1, _ms_row2 = st.columns(5), st.columns(5)
        for _ci, _ms in enumerate(_LN_MS):
            _done = _ln_m_ch >= _ms
            (_ms_row1 if _ci < 5 else _ms_row2)[_ci % 5].markdown(
                f"{'✅' if _done else '⬜'} **{_ms}M**"
            )

        # ── SANKEY: Dòng chảy vốn theo Mutation ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">💰 Sankey — Dòng Chảy Vốn Theo Mutation</div>', unsafe_allow_html=True)

        _sk_src, _sk_tgt, _sk_val, _sk_labels, _sk_muts = [], [], [], [], []
        if not df.empty and "Mutation" in df.columns:
            _sk_all = df.copy()
            # Chuẩn hoá mutation: bỏ "nan", "" → "Không rõ"
            _sk_all["_mut"] = _sk_all["Mutation"].astype(str).str.strip()
            _sk_all.loc[_sk_all["_mut"].isin(["", "nan", "None"]), "_mut"] = "Không rõ"
            _sk_all["_gn"]  = pd.to_numeric(_sk_all["Giá Nhập"], errors="coerce").fillna(0)
            _sk_all["_st"]  = _sk_all["Trạng Thái"].astype(str)
            _sk_muts   = sorted(_sk_all["_mut"].unique().tolist())
            _sk_labels = ["Tổng vốn nhập"] + _sk_muts + ["Đã bán", "Còn tồn"]
            _sk_n_sold  = 1 + len(_sk_muts)
            _sk_n_stock = 2 + len(_sk_muts)

            # Dùng Giá Nhập nếu có, fallback sang số lượng pet
            _use_cost = (_sk_all["_gn"] > 0).any()

            for _i, _m in enumerate(_sk_muts):
                _mdf = _sk_all[_sk_all["_mut"] == _m]
                if _use_cost:
                    _v_all   = float(_mdf["_gn"].sum())
                    _v_sold  = float(_mdf[_mdf["_st"].str.contains("Đã bán",   na=False)]["_gn"].sum())
                    _v_stock = float(_mdf[_mdf["_st"].str.contains("Còn hàng", na=False)]["_gn"].sum())
                else:
                    # Fallback: dùng số lượng pet thay cho giá trị
                    _v_all   = float(len(_mdf))
                    _v_sold  = float(_mdf["_st"].str.contains("Đã bán",   na=False).sum())
                    _v_stock = float(_mdf["_st"].str.contains("Còn hàng", na=False).sum())

                if _v_all > 0:
                    _sk_src.append(0);       _sk_tgt.append(1 + _i);      _sk_val.append(_v_all)
                if _v_sold > 0:
                    _sk_src.append(1 + _i); _sk_tgt.append(_sk_n_sold);  _sk_val.append(_v_sold)
                if _v_stock > 0:
                    _sk_src.append(1 + _i); _sk_tgt.append(_sk_n_stock); _sk_val.append(_v_stock)

        if _sk_src:
            _mut_palette = ["#c084fc","#818cf8","#f472b6","#a78bfa","#e879f9",
                            "#d8b4fe","#c4b5fd","#a5b4fc","#f0abfc","#ddd6fe"]
            _sk_node_colors = (
                ["#9333ea"]
                + [_mut_palette[i % len(_mut_palette)] for i in range(len(_sk_muts))]
                + ["#c084fc", "#e879f9"]
            )
            try:
                fig_sk = go.Figure(go.Sankey(
                    node=dict(
                        pad=15, thickness=18,
                        label=_sk_labels,
                        color=_sk_node_colors,
                    ),
                    link=dict(
                        source=_sk_src,
                        target=_sk_tgt,
                        value=_sk_val,
                        color="rgba(100,120,220,0.18)",
                        hovertemplate="%{source.label} → %{target.label}: %{value:,.0f}<extra></extra>",
                    ),
                ))
                fig_sk.update_layout(
                    paper_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#e2e8f0", size=11),
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=420,
                )
                st.plotly_chart(fig_sk, use_container_width=True)
                _sk_mode_note = "Chiều rộng luồng = giá trị vốn nhập (₫)" if _use_cost else "Chiều rộng luồng = số lượng pet (Giá Nhập chưa nhập)"
                st.caption(_sk_mode_note)
            except Exception as _sk_err:
                st.warning(f"Không thể hiển thị Sankey: {_sk_err}")
        else:
            st.info("Chưa đủ dữ liệu.")

        # ── CALENDAR HEATMAP: GitHub-style lợi nhuận ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">📅 Lịch Lợi Nhuận — 1 Năm Gần Nhất</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            import datetime as _dtm
            _cal_today = now_vn().date()
            _cal_start = _cal_today - _dtm.timedelta(days=364)
            _cal_pbd = pbd.copy()
            _cal_pbd["_date"] = _cal_pbd["Ngày DT"].dt.date
            _cal_pbd["_ln"]   = pd.to_numeric(_cal_pbd["Lợi Nhuận"], errors="coerce").fillna(0)
            _day_map = _cal_pbd.groupby("_date")["_ln"].sum().to_dict()

            _all_days_cal = [_cal_start + _dtm.timedelta(days=i) for i in range(365)]
            _start_dow   = _all_days_cal[0].weekday()          # 0=Mon
            _padded_cal  = [None] * _start_dow + _all_days_cal
            while len(_padded_cal) % 7 != 0:
                _padded_cal.append(None)
            _n_weeks_cal = len(_padded_cal) // 7

            _z_cal, _text_cal = [], []
            _dow_labels_cal = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
            for _dow in range(7):
                _rz, _rt = [], []
                for _wk in range(_n_weeks_cal):
                    _d = _padded_cal[_wk * 7 + _dow]
                    if _d is None:
                        _rz.append(None); _rt.append("")
                    else:
                        _p = _day_map.get(_d, 0)
                        _rz.append(float(_p))
                        _rt.append(
                            f"{_d.strftime('%d/%m/%Y')}<br>{fmt_vnd(_p)}" if _p
                            else f"{_d.strftime('%d/%m/%Y')}<br>—"
                        )
                _z_cal.append(_rz); _text_cal.append(_rt)

            _week_x_labels = []
            for _wk in range(_n_weeks_cal):
                _fd = next((x for x in _padded_cal[_wk*7:_wk*7+7] if x is not None), None)
                _week_x_labels.append(_fd.strftime("%d/%m") if _fd else "")

            _zmax_cal = max((v for v in _day_map.values() if v > 0), default=1)
            fig_cal = go.Figure(go.Heatmap(
                z=_z_cal,
                x=list(range(_n_weeks_cal)),
                y=_dow_labels_cal,
                text=_text_cal,
                hovertemplate="%{text}<extra></extra>",
                colorscale=[
                    [0.0,  "#110f1a"],
                    [0.01, "#0e4429"],
                    [0.3,  "#006d32"],
                    [0.6,  "#26a641"],
                    [1.0,  "#39d353"],
                ],
                zmin=0,
                zmax=_zmax_cal,
                showscale=True,
                colorbar=dict(thickness=10, len=0.8, tickfont=dict(size=9, color="#9d8fbf")),
                xgap=2, ygap=2,
            ))
            fig_cal.update_layout(
                paper_bgcolor="#0a0a0f",
                plot_bgcolor="#0a0a0f",
                font=dict(family="Inter", color="#9d8fbf", size=10),
                xaxis=dict(
                    tickmode="array",
                    tickvals=list(range(0, _n_weeks_cal, 4)),
                    ticktext=[_week_x_labels[i] for i in range(0, _n_weeks_cal, 4)],
                    tickfont=dict(size=9, color="#9d8fbf"),
                    showgrid=False, zeroline=False,
                ),
                yaxis=dict(
                    tickfont=dict(size=10, color="#9d8fbf"),
                    showgrid=False, zeroline=False,
                    autorange="reversed",
                ),
                margin=dict(l=40, r=20, t=15, b=40),
                height=210,
            )
            st.plotly_chart(fig_cal, use_container_width=True)

            _cal_active = sum(1 for v in _day_map.values() if v > 0)
            _cal_max_d  = max(_day_map, key=_day_map.get) if _day_map else None
            _calcc1, _calcc2 = st.columns(2)
            _calcc1.caption(f"Ngày có giao dịch: **{_cal_active}** / 365 ngày")
            if _cal_max_d:
                _calcc2.caption(f"Ngày đỉnh cao: **{_cal_max_d.strftime('%d/%m/%Y')}** · {fmt_vnd(_day_map[_cal_max_d])}")
        else:
            st.info("Chưa có dữ liệu.")

        # ── ⚡ Xu Hướng Bán Theo Tuần ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">⚡ Xu Hướng Bán Theo Tuần</div>', unsafe_allow_html=True)

        if has_data and not pbd.empty:
            import datetime as _dtm2
            _wk_df = pbd.copy()
            # Floor to Monday of each week (timezone-safe)
            _wk_df["_week"] = _wk_df["Ngày DT"] - pd.to_timedelta(
                _wk_df["Ngày DT"].dt.dayofweek, unit="d"
            )
            _wk_df["_week"] = _wk_df["_week"].dt.normalize()

            # Merge single sold count
            _wk_count_df = pd.DataFrame(columns=["_week","Số con"])
            if not sold_df.empty:
                _sc = sold_df.copy()
                _sc["_dt"] = pd.to_datetime(_sc["Ngày Bán"], dayfirst=True, errors="coerce")
                _sc["_week"] = (_sc["_dt"] - pd.to_timedelta(_sc["_dt"].dt.dayofweek, unit="d")).dt.normalize()
                _wk_count_df = _sc.groupby("_week", as_index=False).agg(**{"Số con": ("_week","count")})
            # Merge bulk sold count
            if not bulk_history.empty:
                _bh = bulk_history.copy()
                _bh["_dt"] = pd.to_datetime(_bh["Ngày Bán"], dayfirst=True, errors="coerce")
                _bh["_week"] = (_bh["_dt"] - pd.to_timedelta(_bh["_dt"].dt.dayofweek, unit="d")).dt.normalize()
                _bh_qty = _bh.groupby("_week", as_index=False).agg(
                    _bqty=("Số Lượng Bán" if "Số Lượng Bán" in _bh.columns else "Ngày Bán", "sum"
                           if "Số Lượng Bán" in _bh.columns else "count")
                ).rename(columns={"_bqty": "Số con bulk"})
                if not _wk_count_df.empty:
                    _wk_count_df = _wk_count_df.merge(_bh_qty, on="_week", how="outer").fillna(0)
                    _wk_count_df["Số con"] = _wk_count_df.get("Số con", 0) + _wk_count_df.get("Số con bulk", 0)
                else:
                    _wk_count_df = _bh_qty.rename(columns={"Số con bulk": "Số con"})

            _wk_ln = _wk_df.groupby("_week", as_index=False)["Lợi Nhuận"].sum()
            if not _wk_count_df.empty:
                _wk_merged = _wk_ln.merge(
                    _wk_count_df[["_week","Số con"]] if "Số con" in _wk_count_df.columns else _wk_ln[["_week"]],
                    on="_week", how="left"
                ).fillna(0)
            else:
                _wk_merged = _wk_ln.copy()
                _wk_merged["Số con"] = 0
            _wk_merged = _wk_merged.sort_values("_week").tail(16)  # last 16 weeks
            _wk_merged["_label"] = _wk_merged["_week"].dt.strftime("%d/%m/%Y")

            if len(_wk_merged) >= 1:
                # Trend line via simple linear regression
                import numpy as np
                _x = np.arange(len(_wk_merged))
                _y = _wk_merged["Lợi Nhuận"].values.astype(float)
                try:
                    _m_coef, _b_coef = np.polyfit(_x, _y, 1)
                except (np.linalg.LinAlgError, ValueError):
                    _m_coef, _b_coef = 0.0, float(_y.mean()) if len(_y) else 0.0
                _trend_y = _m_coef * _x + _b_coef
                _trend_color = "#34d399" if _m_coef >= 0 else "#f87171"
                _trend_label = f"Xu hướng {'↑ tăng' if _m_coef >= 0 else '↓ giảm'} {abs(_m_coef / max(abs(_y.mean()), 1) * 100):.1f}%/tuần"

                _bar_colors = ["#34d399" if v >= 0 else "#f87171" for v in _wk_merged["Lợi Nhuận"]]
                _fig_wk = go.Figure()
                _fig_wk.add_trace(go.Bar(
                    x=_wk_merged["_label"], y=_wk_merged["Lợi Nhuận"],
                    name="LN/tuần", marker_color=_bar_colors, opacity=0.7,
                    text=_wk_merged["Lợi Nhuận"].apply(fmt_short),
                    textposition="outside", textfont=dict(color="#e2e8f0", size=9),
                    hovertemplate="<b>%{x}</b><br>Lợi nhuận: %{y:,.0f}₫<extra></extra>",
                    yaxis="y1",
                ))
                _fig_wk.add_trace(go.Scatter(
                    x=_wk_merged["_label"], y=_wk_merged["Số con"],
                    name="Số con bán", mode="lines+markers",
                    line=dict(color="#c084fc", width=2),
                    marker=dict(size=6, color="#c084fc"),
                    hovertemplate="<b>%{x}</b><br>Số con: %{y:,.0f}<extra></extra>",
                    yaxis="y2",
                ))
                _fig_wk.add_trace(go.Scatter(
                    x=_wk_merged["_label"], y=_trend_y.tolist(),
                    name=_trend_label, mode="lines",
                    line=dict(color=_trend_color, width=2, dash="dash"),
                    hoverinfo="skip", yaxis="y1",
                ))
                _fig_wk.update_layout(
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    xaxis=dict(tickfont=dict(color="#e2e8f0", size=10), gridcolor="#1a1528"),
                    yaxis=dict(title="Lợi nhuận (₫)", gridcolor="#1a1528",
                               tickfont=dict(color="#9d8fbf"), tickformat=",.0f",
                               zeroline=True, zerolinecolor="#4a3f6b"),
                    yaxis2=dict(title="Số con", overlaying="y", side="right",
                                tickfont=dict(color="#c084fc"), zeroline=False, showgrid=False),
                    legend=dict(orientation="h", x=0, y=1.08, font=dict(color="#9d8fbf")),
                    margin=dict(l=10, r=50, t=40, b=10),
                    height=360, barmode="overlay",
                )
                st.plotly_chart(_fig_wk, use_container_width=True)

                # 4 KPI cho tuần này vs tuần trước
                _last2 = _wk_merged.tail(2)
                if len(_last2) == 2:
                    _this = _last2.iloc[-1]
                    _prev = _last2.iloc[-2]
                    _wkc1, _wkc2, _wkc3, _wkc4 = st.columns(4)
                    _wkc1.metric("Lợi nhuận tuần này", fmt_vnd(_this["Lợi Nhuận"]),
                                 delta=fmt_short(_this["Lợi Nhuận"] - _prev["Lợi Nhuận"]))
                    _wkc2.metric("Tuần trước", fmt_vnd(_prev["Lợi Nhuận"]))
                    _wkc3.metric("Số con tuần này", f"{int(_this['Số con']):,}")
                    _avg_wk = float(_wk_merged["Lợi Nhuận"].mean())
                    _wkc4.metric("Trung bình mỗi tuần", fmt_vnd(_avg_wk))
        else:
            st.info("Chưa có dữ liệu.")

        # ── 🧬 Phân Tích Trait ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🧬 Phân Tích Theo Trait</div>', unsafe_allow_html=True)

        if not sold_df.empty and "Số Trait" in sold_df.columns:
            _tr_df = sold_df.copy()
            _tr_df["_ln"]    = pd.to_numeric(_tr_df["Lợi Nhuận"], errors="coerce").fillna(0)
            _tr_df["_dt"]    = pd.to_numeric(_tr_df["Doanh Thu"],  errors="coerce").fillna(0)
            _tr_df["_gn"]    = pd.to_numeric(_tr_df["Giá Nhập"],   errors="coerce").fillna(0)
            _tr_df["_trait"] = _tr_df["Số Trait"].astype(str).str.strip().replace({"": "None", "nan": "None", "0": "None"})

            _tr_grp = (
                _tr_df.groupby("_trait", as_index=False)
                .agg(LN_mean=("_ln","mean"), LN_total=("_ln","sum"),
                     DT_total=("_dt","sum"),  GN_mean=("_gn","mean"), Count=("_ln","count"))
            )
            _tr_grp["Margin"] = (_tr_grp["LN_total"] / _tr_grp["DT_total"].replace(0, float("nan")) * 100).fillna(0)
            _sort_order = {"None":0}
            _tr_grp["_s"] = _tr_grp["_trait"].map(lambda x: _sort_order.get(x, 99))
            _tr_grp = _tr_grp.sort_values(["_s","LN_mean"], ascending=[True, False]).drop(columns=["_s"])

            _trc1, _trc2 = st.columns(2)
            with _trc1:
                _tr_colors = ["#94a3b8" if t == "None" else
                              "#34d399" if i % 3 == 1 else
                              "#a78bfa" if i % 3 == 2 else "#f472b6"
                              for i, t in enumerate(_tr_grp["_trait"])]
                _fig_tr = go.Figure(go.Bar(
                    x=_tr_grp["_trait"], y=_tr_grp["LN_mean"],
                    marker_color=_tr_colors, opacity=0.85,
                    text=_tr_grp["LN_mean"].apply(fmt_short),
                    textposition="outside", textfont=dict(color="#e2e8f0", size=10),
                    customdata=_tr_grp[["LN_total","Count","Margin"]].values,
                    hovertemplate=(
                        "<b>Trait: %{x}</b><br>"
                        "LN TB/con: %{y:,.0f}₫<br>"
                        "Tổng LN: %{customdata[0]:,.0f}₫<br>"
                        "Số con: %{customdata[1]}<br>"
                        "Margin: %{customdata[2]:.1f}%"
                        "<extra></extra>"
                    ),
                ))
                _fig_tr.update_layout(
                    title=dict(text="Lợi Nhuận TB / Con theo Trait", font=dict(size=12, color="#e2e8f0")),
                    paper_bgcolor="#0a0a0f", plot_bgcolor="#0a0a0f",
                    font=dict(family="Inter", color="#9d8fbf"),
                    xaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#e2e8f0")),
                    yaxis=dict(gridcolor="#1a1528", tickfont=dict(color="#9d8fbf"),
                               tickformat=",.0f", zeroline=True, zerolinecolor="#4a3f6b"),
                    margin=dict(l=10, r=10, t=40, b=10), height=300, showlegend=False,
                )
                st.plotly_chart(_fig_tr, use_container_width=True)

            with _trc2:
                _tr_disp = _tr_grp.copy()
                _tr_disp["LN TB/con"]  = _tr_disp["LN_mean"].apply(fmt_vnd)
                _tr_disp["Tổng LN"]    = _tr_disp["LN_total"].apply(fmt_vnd)
                _tr_disp["Giá nhập TB"] = _tr_disp["GN_mean"].apply(fmt_vnd)
                _tr_disp["Margin %"]   = _tr_disp["Margin"].apply(lambda v: f"{v:.1f}%")
                _tr_disp = _tr_disp.rename(columns={"_trait":"Trait","Count":"Số con"})
                st.markdown("**Bảng chi tiết theo Trait**")
                st.dataframe(
                    _tr_disp[["Trait","Số con","LN TB/con","Tổng LN","Giá nhập TB","Margin %"]],
                    use_container_width=True, hide_index=True, height=300,
                )
        else:
            st.info("Chưa có dữ liệu bán.")

        # ── 🏦 Hiệu Suất Vốn ──
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🏦 Hiệu Suất Vốn</div>', unsafe_allow_html=True)

        # Capital inputs
        _cap_invested_single = float(pd.to_numeric(df["Giá Nhập"], errors="coerce").fillna(0).sum()) if not df.empty else 0.0
        _cap_invested_bulk   = float(pd.to_numeric(bulk_df["Giá Nhập Tổng"], errors="coerce").fillna(0).sum()) if not bulk_df.empty else 0.0
        _cap_invested_total  = _cap_invested_single + _cap_invested_bulk

        # Capital returned (cost of sold items)
        _cap_returned_single = float(pd.to_numeric(sold_df["Giá Nhập"], errors="coerce").fillna(0).sum()) if not sold_df.empty else 0.0
        _cap_returned_bulk   = 0.0
        if not bulk_df.empty and not bulk_history.empty:
            _bdf_cost_rate = bulk_df.copy()
            _bdf_cost_rate["_orig"] = pd.to_numeric(_bdf_cost_rate["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
            _bdf_cost_rate["_cost"] = pd.to_numeric(_bdf_cost_rate["Giá Nhập Tổng"], errors="coerce").fillna(0)
            _bdf_cost_rate["_unit_cost"] = _bdf_cost_rate["_cost"] / _bdf_cost_rate["_orig"]
            _bdf_map = dict(zip(_bdf_cost_rate["Tên Lô"].astype(str), _bdf_cost_rate["_unit_cost"]))
            if "Tên Lô" in bulk_history.columns and "Số Lượng Bán" in bulk_history.columns:
                _bh2 = bulk_history.copy()
                _bh2["_qty"]  = pd.to_numeric(_bh2["Số Lượng Bán"], errors="coerce").fillna(0)
                _bh2["_rate"] = _bh2["Tên Lô"].astype(str).map(_bdf_map).fillna(0)
                _cap_returned_bulk = float((_bh2["_qty"] * _bh2["_rate"]).sum())
        _cap_returned_total = _cap_returned_single + _cap_returned_bulk

        # Locked capital (still in stock)
        _cap_locked_single = float(pd.to_numeric(
            df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]["Giá Nhập"],
            errors="coerce"
        ).fillna(0).sum()) if not df.empty else 0.0
        _cap_locked_bulk = 0.0
        if not bulk_df.empty:
            _bdf3 = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"].copy()
            if not _bdf3.empty:
                _bdf3["_orig"] = pd.to_numeric(_bdf3["Số Lượng Gốc"], errors="coerce").fillna(1).replace(0, 1)
                _bdf3["_left"] = pd.to_numeric(_bdf3["Còn Lại"], errors="coerce").fillna(0)
                _bdf3["_cost"] = pd.to_numeric(_bdf3["Giá Nhập Tổng"], errors="coerce").fillna(0)
                _cap_locked_bulk = float((_bdf3["_cost"] / _bdf3["_orig"] * _bdf3["_left"]).sum())
        _cap_locked_total = _cap_locked_single + _cap_locked_bulk

        _recovery_pct = _cap_returned_total / _cap_invested_total * 100 if _cap_invested_total > 0 else 0.0
        _lock_pct     = _cap_locked_total   / _cap_invested_total * 100 if _cap_invested_total > 0 else 0.0

        # Ước tính thời gian hoàn vốn: dựa trên tốc độ thu hồi vốn hiện tại
        _days_active = max((now_vn().replace(tzinfo=None) - pd.to_datetime(
            df["Ngày Nhập"].dropna().replace("", float("nan")),
            dayfirst=True, errors="coerce"
        ).dropna().min().replace(tzinfo=None)).days, 1) if not df.empty else 1
        _daily_recovery = _cap_returned_total / _days_active if _days_active > 0 else 0
        _days_to_recover = int(_cap_locked_total / _daily_recovery) if _daily_recovery > 0 else 0

        # Gauge chart: Recovery %
        _fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=_recovery_pct,
            delta={"reference": 80, "suffix": "%", "increasing": {"color": "#34d399"}, "decreasing": {"color": "#f87171"}},
            number={"suffix": "%", "font": {"size": 36, "color": "#e2e8f0", "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#4a3f6b",
                         "tickfont": {"color": "#9d8fbf", "size": 10}},
                "bar":  {"color": "#a78bfa", "thickness": 0.25},
                "bgcolor": "#0a0a0f",
                "bordercolor": "#2d2040",
                "steps": [
                    {"range": [0,  40], "color": "rgba(248,113,113,0.12)"},
                    {"range": [40, 70], "color": "rgba(251,191,36,0.10)"},
                    {"range": [70,100], "color": "rgba(52,211,153,0.10)"},
                ],
                "threshold": {
                    "line": {"color": "#fbbf24", "width": 2},
                    "thickness": 0.8, "value": 80,
                },
            },
            title={"text": "% Vốn Đã Thu Hồi", "font": {"size": 13, "color": "#9d8fbf", "family": "Inter"}},
        ))
        _fig_gauge.update_layout(
            paper_bgcolor="#0a0a0f",
            font=dict(family="Inter", color="#9d8fbf"),
            margin=dict(l=20, r=20, t=30, b=10),
            height=260,
        )

        _gc1, _gc2 = st.columns([1.1, 1])
        with _gc1:
            st.plotly_chart(_fig_gauge, use_container_width=True)
        with _gc2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            _cv1, _cv2 = st.columns(2)
            _cv1.metric("Tổng vốn đã bỏ ra",    fmt_vnd(_cap_invested_total))
            _cv2.metric("Vốn đã thu về",         fmt_vnd(_cap_returned_total))
            _cv3, _cv4 = st.columns(2)
            _cv3.metric("Vốn đang kẹt trong kho", fmt_vnd(_cap_locked_total),
                        delta=f"-{_lock_pct:.1f}% vốn")
            _cv4.metric("Ước tính hoàn vốn còn lại",
                        f"~{_days_to_recover} ngày" if _days_to_recover > 0 and _days_to_recover < 3650 else "—",
                        help="Dựa trên tốc độ thu hồi vốn trung bình hiện tại")

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 3: TỒN LÂU
    # ─────────────────────────────────────────────────────────────────────────────
with tab_ton:
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Hàng Tồn Lâu</div>', unsafe_allow_html=True)

        with st.form("form_ton_lau"):
            _fc1, _fc2, _fc3, _fc4 = st.columns([1, 1, 1.2, 1])
            age_thresh  = _fc1.number_input("Tồn từ (ngày)", min_value=0, max_value=365, value=0, step=1)
            age_max     = _fc2.number_input("Tối đa (ngày, 0=∞)", min_value=0, max_value=3650, value=0, step=1)
            loai_filter = _fc3.selectbox("Loại hàng", ["Tất cả", "Pet Lẻ", "Lô (Pack)"])
            sort_by     = _fc4.selectbox("Sắp xếp theo", ["Ngày Tồn (giảm)", "Giá trị vốn (giảm)", "Tên Pet"])
            st.form_submit_button("🔍 Lọc", use_container_width=False)

        # Pet lẻ — dùng Ngày Tồn đã tính sẵn trong df (tránh recalc lỗi khi time_nhap rỗng)
        single_old = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)].copy()
        if "Ngày Tồn" not in single_old.columns or single_old["Ngày Tồn"].isna().all():
            single_old = apply_ngay_ton(single_old)
        single_old["Ngày Tồn"] = pd.to_numeric(single_old["Ngày Tồn"], errors="coerce").fillna(0)
        single_old = single_old[single_old["Ngày Tồn"] >= age_thresh]
        if age_max > 0:
            single_old = single_old[single_old["Ngày Tồn"] <= age_max]
        single_old["Loại"]               = "Pet Lẻ"
        single_old["Item"]               = single_old["Tên Pet"].astype(str)
        single_old["Số lượng còn"]       = 1
        single_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(single_old["Giá Nhập"], errors="coerce").fillna(0)
        sv = single_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]] if not single_old.empty else pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

        # Pack tồn
        pack_old = bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"].copy()
        if not pack_old.empty:
            pack_old["Ngày DT"]  = pd.to_datetime(pack_old["Ngày Nhập"], dayfirst=True, errors="coerce")
            pack_old["Ngày Tồn"] = (now_vn().replace(tzinfo=None) - pack_old["Ngày DT"].dt.tz_localize(None)).dt.days.fillna(0).astype(float)
            pack_old = pack_old[pack_old["Ngày Tồn"] >= age_thresh]
            if age_max > 0:
                pack_old = pack_old[pack_old["Ngày Tồn"] <= age_max]
            pack_old["Loại"]               = "Lô (Pack)"
            pack_old["Item"]               = pack_old["Tên Lô"].astype(str)
            pack_old["Số lượng còn"]       = pd.to_numeric(pack_old["Còn Lại"], errors="coerce").fillna(0).astype(int)
            pack_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(pack_old["Giá Nhập Tổng"], errors="coerce").fillna(0)
            pv = pack_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]]
        else:
            pv = pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

        old_items = pd.concat([sv, pv], ignore_index=True)

        # Lọc theo loại
        if loai_filter != "Tất cả" and not old_items.empty:
            old_items = old_items[old_items["Loại"] == loai_filter]

        if old_items.empty:
            _age_label = f"{age_thresh}–{age_max} ngày" if age_max > 0 else (f"≥ {age_thresh} ngày" if age_thresh > 0 else "toàn bộ")
            st.info(f"Không có mục nào tồn {_age_label} — kho luân chuyển tốt.")
        else:
            if sort_by == "Ngày Tồn (giảm)":
                old_items = old_items.sort_values("Ngày Tồn", ascending=False)
            elif sort_by == "Giá trị vốn (giảm)":
                old_items = old_items.sort_values("Giá trị vốn (VNĐ)", ascending=False)
            else:
                old_items = old_items.sort_values("Item")

            total_stuck_val = old_items["Giá trị vốn (VNĐ)"].sum()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Mục tồn", f"{len(old_items):,}")
            m2.metric("Vốn bị giữ", fmt_vnd(total_stuck_val))
            m3.metric("Tồn lâu nhất", fmt_ngay_ton(old_items['Ngày Tồn'].max()))
            m4.metric("Trung bình tồn", fmt_ngay_ton(old_items['Ngày Tồn'].mean()))

            old_items["Giá trị vốn"] = old_items["Giá trị vốn (VNĐ)"].apply(fmt_vnd)
            old_items["Tồn"]         = old_items["Ngày Tồn"].apply(fmt_ngay_ton)
            _ton_disp = old_items[["Loại","Item","Số lượng còn","Ngày Nhập","Tồn","Giá trị vốn","Auto Title"]].copy()

            st.dataframe(
                _ton_disp, use_container_width=True, hide_index=True, height=420,
                column_config={
                    "Auto Title":   st.column_config.TextColumn("Auto Title", width="large"),
                    "Tồn":          st.column_config.TextColumn("Tồn"),
                    "Item":         st.column_config.TextColumn("Item"),
                    "Loại":         st.column_config.TextColumn("Loại"),
                    "Số lượng còn": st.column_config.NumberColumn("Số lượng còn"),
                    "Giá trị vốn":  st.column_config.TextColumn("Giá trị vốn"),
                    "Ngày Nhập":    st.column_config.TextColumn("Ngày Nhập"),
                },
            )

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 4: LÔ PACK
    # ─────────────────────────────────────────────────────────────────────────────
with tab_pack:
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Quản Lý Lô (Pack)</div>', unsafe_allow_html=True)

        pack_in, pack_sell = st.columns([1.15, 1], gap="medium")

        with pack_in:
            with st.container(border=True):
                st.markdown("**Nhập Lô Mới**")
                with st.form("form_nhap_lo2", clear_on_submit=True):
                    b_pet2 = st.selectbox("Tên Pet", get_name_options(pet_db), key="bp1t2")
                    b1t, b2t, b3t = st.columns(3)
                    b_qty2    = b1t.number_input("Số lượng", min_value=1, max_value=999, value=10, key="bqt2")
                    b_ms_raw2 = b2t.text_input("M/s", placeholder="975", key="bp2t2")
                    b_mut2    = b3t.selectbox("Mutation", MUTATION_OPTIONS, key="bp3t2")
                    b_ns2     = st.selectbox("NameStock", [""]+get_name_options(ns_db,""), key="bp5t2")
                    b_cost_raw2 = st.text_input("Tổng vốn nhập (₫)", placeholder="2.000.000", key="bp4t2")
                    pack_ok2  = st.form_submit_button("Lưu Lô Hàng", type="primary", use_container_width=True)
                if pack_ok2:
                    b_cost2 = parse_vnd(b_cost_raw2)
                    b_ms2   = parse_usd(b_ms_raw2)
                    errs2 = []
                    if b_pet2 == "None":  errs2.append("Chọn tên Pet")
                    if b_ms2 <= 0:        errs2.append("M/s phải > 0")
                    if b_cost2 <= 0:      errs2.append("Giá nhập phải > 0")
                    if not b_ns2.strip(): errs2.append("Chọn NameStock")
                    if errs2:
                        for e in errs2: st.error(f"{e}")
                    else:
                        # Guard chống double-submit lô pack
                        lo_submit_key = f"nhap_lo_{b_pet2}_{b_qty2}_{b_cost2}_{b_ns2}"
                        if st.session_state.get("last_lo_key") == lo_submit_key:
                            st.warning("Lô này đã được lưu. Tải lại trang nếu cần.")
                            st.stop()
                        st.session_state.last_lo_key = lo_submit_key
                        bid2 = next_id(bulk_df, "ID")
                        auto_title2 = generate_auto_title(b_pet2, b_mut2, "None", b_ms2, b_ns2)
                        row2 = {
                            "ID": bid2,
                            "Tên Lô": f"Pack {b_pet2} (x{int(b_qty2)})",
                            "Số Lượng Gốc": int(b_qty2),
                            "Còn Lại": int(b_qty2),
                            "Ngày Nhập": now_str(),
                            "Giá Nhập Tổng": b_cost2,
                            "Doanh Thu Tích Lũy": 0.0,
                            "Lợi Nhuận": -b_cost2,
                            "Trạng Thái": "Available",
                            "Auto Title": auto_title2,
                            "NameStock": b_ns2,
                        }
                        bulk_df = append_row(bulk_df, row2, BULK_SCHEMA)
                        st.session_state.bulk_df = bulk_df
                        if USE_SUPABASE:
                            db_row2 = to_db(row2)
                            db_row2.pop("id", None)
                            sb_insert("bulk_inventory", db_row2)
                            # Tải lại để update ID từ database cho bản ghi mới thêm
                            load_bulk.clear()
                            st.session_state.bulk_df = load_bulk()
                        st.toast("Lô hàng đã được lưu", icon="✅")
                        st.rerun()

        with pack_sell:
            with st.container(border=True):
                st.markdown("**Bán Từ Lô**")

                # ── UNDO banner ──
                if st.session_state.get("last_sale_undo", {}).get("type") == "bulk":
                    _undo_bk = st.session_state["last_sale_undo"]
                    _ub1, _ub2 = st.columns([3, 1])
                    _ub1.info(f"↩️ Vừa bán: **{_undo_bk['label']}**  —  Bán nhầm? Hoàn tác ngay!")
                    if _ub2.button("↩️ Hoàn tác", key="undo_bulk_btn", use_container_width=True):
                        _ud_bk = st.session_state.pop("last_sale_undo")
                        # Restore bulk_inventory row
                        if USE_SUPABASE:
                            sb_update("bulk_inventory", {
                                "con_lai":            _ud_bk["old_con_lai"],
                                "doanh_thu_tich_luy": _ud_bk["old_dt"],
                                "loi_nhuan":          _ud_bk["old_loi_nhuan"],
                                "trang_thai":         _ud_bk["old_trang_thai"],
                            }, "id", _ud_bk["bulk_id"])
                            # Delete the history record that was just inserted
                            if _ud_bk.get("hist_db_id"):
                                sb_delete("bulk_history", "id", _ud_bk["hist_db_id"])
                            load_bulk.clear()
                            load_bulk_history.clear()
                            st.session_state.bulk_df      = load_bulk()
                            st.session_state.bulk_history = load_bulk_history()
                        else:
                            # Restore local state directly
                            _bdf3 = st.session_state.bulk_df.copy()
                            _idx3 = _bdf3.index[_bdf3["ID"] == _ud_bk["bulk_id"]]
                            if len(_idx3):
                                _bdf3.at[_idx3[0], "Còn Lại"]            = _ud_bk["old_con_lai"]
                                _bdf3.at[_idx3[0], "Doanh Thu Tích Lũy"] = _ud_bk["old_dt"]
                                _bdf3.at[_idx3[0], "Lợi Nhuận"]          = _ud_bk["old_loi_nhuan"]
                                _bdf3.at[_idx3[0], "Trạng Thái"]         = _ud_bk["old_trang_thai"]
                                st.session_state.bulk_df = _bdf3
                        st.toast("Đã hoàn tác giao dịch lô", icon="↩️")
                        st.rerun()

                avail2 = bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"]
                if not avail2.empty:
                    _bid_map = {int(r["ID"]): r for _, r in avail2.iterrows()}
                    def _bulk_fmt(bid):
                        r = _bid_map[bid]
                        auto_t = str(r.get("Auto Title", "") or "")
                        # Lấy phần trước boilerplate "🌸Cheapest..."
                        short = auto_t.split("🌸Cheapest")[0].lstrip("🌸").strip()
                        if not short:
                            short = str(r.get("Tên Lô", ""))
                        ns = str(r.get("NameStock", "") or "").strip()
                        con_lai = int(float(r["Còn Lại"]))
                        gia_tong = float(r["Giá Nhập Tổng"])
                        orig = max(float(r["Số Lượng Gốc"]), 1)
                        don_gia = gia_tong / orig
                        ns_part = f" · {ns}" if ns else ""
                        return f"#{bid}  {short}{ns_part}  ·  còn {con_lai}  ·  ~{fmt_short(don_gia)}/con"
                    sel_b2 = st.selectbox(
                        "Chọn lô", list(_bid_map.keys()),
                        format_func=_bulk_fmt,
                        label_visibility="collapsed", key="sel_b2",
                    )
                    target_id2 = sel_b2
                    target2 = avail2[avail2["ID"]==target_id2].iloc[0]
                    # ── Hiển thị đầy đủ Auto Title để copy ──
                    _at_full = str(target2.get("Auto Title", "") or "")
                    if _at_full:
                        st.code(_at_full, language="text")
                    _don_gia2 = float(target2["Giá Nhập Tổng"]) / max(float(target2["Số Lượng Gốc"]), 1)
                    _ngay_nhap2 = str(target2.get("Ngày Nhập", ""))[:10]
                    st.caption(
                        f"📦 Còn: **{int(target2['Còn Lại'])}** / {int(float(target2['Số Lượng Gốc']))} con"
                        f" · Vốn tổng: **{fmt_vnd(float(target2['Giá Nhập Tổng']))}**"
                        f" · Giá/con: **{fmt_vnd(_don_gia2)}**"
                        f" · Nhập: {_ngay_nhap2}"
                    )

                    with st.form("form_ban_lo2", clear_on_submit=False):
                        s1t, s2t = st.columns(2)
                        s_qty2     = s1t.number_input("Số lượng", min_value=1, max_value=int(target2["Còn Lại"]), key="sqty2")
                        s_prc_raw2 = s2t.text_input("Đơn giá ($/unit)", placeholder="3.5", key="sprc2")
                        sell_ok2   = st.form_submit_button("Xác Nhận Giao Dịch", type="primary", use_container_width=True)

                    # ── Step 1: save pending on first click ──
                    if sell_ok2:
                        s_prc2 = parse_usd(s_prc_raw2)
                        if s_prc2 <= 0:
                            st.error("Đơn giá phải lớn hơn 0")
                        else:
                            _idx2_pre = bulk_df[bulk_df["ID"]==target2["ID"]].index[0]
                            st.session_state["pending_bulk_sale"] = {
                                "bulk_id":       int(target2["ID"]),
                                "ten_lo":        str(target2["Tên Lô"]),
                                "s_qty":         s_qty2,
                                "s_prc":         s_prc2,
                                "old_con_lai":   int(float(bulk_df.at[_idx2_pre, "Còn Lại"])),
                                "old_dt":        float(bulk_df.at[_idx2_pre, "Doanh Thu Tích Lũy"]),
                                "old_loi_nhuan": float(bulk_df.at[_idx2_pre, "Lợi Nhuận"]),
                                "old_trang_thai":str(bulk_df.at[_idx2_pre, "Trạng Thái"]),
                                "so_luong_goc":  float(target2["Số Lượng Gốc"]),
                                "gia_nhap_tong": float(target2["Giá Nhập Tổng"]),
                            }
                            st.rerun()

                    # ── Step 2: confirmation block ──
                    _pnd_bulk = st.session_state.get("pending_bulk_sale")
                    if _pnd_bulk and _pnd_bulk["bulk_id"] == int(target2["ID"]):
                        _rev_bk = _pnd_bulk["s_qty"] * _pnd_bulk["s_prc"] * EXCHANGE_RATE
                        _base_u = _pnd_bulk["gia_nhap_tong"] / max(_pnd_bulk["so_luong_goc"], 1)
                        _ln_bk  = _rev_bk - (_base_u * _pnd_bulk["s_qty"])
                        st.warning(
                            f"⚠️ **Xác nhận bán** · {_pnd_bulk['ten_lo']}\n\n"
                            f"Số lượng: **{_pnd_bulk['s_qty']}** @ **${_pnd_bulk['s_prc']}/unit** "
                            f"→ {fmt_vnd(_rev_bk)} · LN giao dịch: **{fmt_vnd(_ln_bk)}**"
                        )
                        _bf1, _bf2 = st.columns(2)
                        _do_confirm_bk = _bf1.button("✅ Xác nhận bán", key="confirm_sell_bulk", type="primary", use_container_width=True)
                        _do_cancel_bk  = _bf2.button("❌ Hủy", key="cancel_sell_bulk", use_container_width=True)

                        if _do_cancel_bk:
                            st.session_state.pop("pending_bulk_sale", None)
                            st.rerun()

                        if _do_confirm_bk:
                            _pnd_b = st.session_state.pop("pending_bulk_sale")
                            _idx2 = bulk_df[bulk_df["ID"]==_pnd_b["bulk_id"]].index[0]
                            _rev_vnd2 = _pnd_b["s_qty"] * _pnd_b["s_prc"] * EXCHANGE_RATE
                            _new_con_lai2   = max(0.0, float(bulk_df.at[_idx2,"Còn Lại"]) - float(_pnd_b["s_qty"]))
                            _new_dt2        = float(bulk_df.at[_idx2,"Doanh Thu Tích Lũy"]) + _rev_vnd2
                            _new_loi_nhuan2 = _new_dt2 - float(bulk_df.at[_idx2,"Giá Nhập Tổng"])
                            _new_status2    = "Sold Out" if _new_con_lai2 <= 0 else "Available"

                            bulk_df.at[_idx2,"Còn Lại"]            = _new_con_lai2
                            bulk_df.at[_idx2,"Doanh Thu Tích Lũy"] = _new_dt2
                            bulk_df.at[_idx2,"Lợi Nhuận"]          = _new_loi_nhuan2
                            bulk_df.at[_idx2,"Trạng Thái"]         = _new_status2

                            _base_unit2 = _pnd_b["gia_nhap_tong"] / max(_pnd_b["so_luong_goc"], 1)
                            _hist_row2 = {
                                "Ngày Bán":            now_str(),
                                "Tên Lô":              _pnd_b["ten_lo"],
                                "Số Lượng Bán":        _pnd_b["s_qty"],
                                "Lợi Nhuận Giao Dịch": _rev_vnd2 - (_base_unit2 * _pnd_b["s_qty"]),
                                "Doanh Thu Giao Dịch": _rev_vnd2,
                            }
                            bulk_history = append_row(bulk_history, _hist_row2, HISTORY_SCHEMA)
                            st.session_state.bulk_df      = bulk_df
                            st.session_state.bulk_history = bulk_history

                            _hist_db_id = None
                            _write_ok = True
                            if USE_SUPABASE:
                                _inserted = sb_insert_returning("bulk_history", to_db(_hist_row2))
                                _hist_db_id = _inserted.get("id") if _inserted else None
                                _write_ok2 = sb_update("bulk_inventory", {
                                    "con_lai":            int(_new_con_lai2),
                                    "doanh_thu_tich_luy": _new_dt2,
                                    "loi_nhuan":          _new_loi_nhuan2,
                                    "trang_thai":         _new_status2,
                                }, "id", _pnd_b["bulk_id"])
                                _write_ok = bool(_inserted) and _write_ok2
                                if _write_ok:
                                    load_bulk.clear()
                                    load_bulk_history.clear()
                                    st.session_state.bulk_df      = load_bulk()
                                    st.session_state.bulk_history = load_bulk_history()
                                else:
                                    st.session_state.last_ban_lo_key = None

                            if _write_ok:
                                st.session_state["last_sale_undo"] = {
                                    "type":          "bulk",
                                    "label":         f"{_pnd_b['ten_lo']} x{_pnd_b['s_qty']} @ ${_pnd_b['s_prc']}",
                                    "bulk_id":       _pnd_b["bulk_id"],
                                    "hist_db_id":    _hist_db_id,
                                    "old_con_lai":   _pnd_b["old_con_lai"],
                                    "old_dt":        _pnd_b["old_dt"],
                                    "old_loi_nhuan": _pnd_b["old_loi_nhuan"],
                                    "old_trang_thai":_pnd_b["old_trang_thai"],
                                }
                                st.toast("✅ Giao dịch hoàn tất · Nhấn Hoàn Tác nếu bán nhầm", icon="✅")
                                st.rerun()
                            else:
                                st.error("Ghi dữ liệu thất bại, vui lòng thử lại.")
                else:
                    st.info("Hiện không có lô hàng khả dụng.")

        st.markdown("---")
        st.markdown("**Danh Sách Lô Hàng**")
        bulk_cols_display2 = ["ID","Tên Lô","NameStock","Số Lượng Gốc","Còn Lại","Ngày Nhập",
                              "Giá Nhập Tổng","Doanh Thu Tích Lũy","Lợi Nhuận","Trạng Thái","Auto Title"]

        # ── THANH CÔNG CỤ LÔ PACK ──
        _bk1, _bk2, _bk3 = st.columns([2, 2, 1])
        bulk_status_filter = _bk1.radio(
            "Lọc lô",
            ["Available", "Sold Out", "Tất cả"],
            horizontal=True,
            label_visibility="collapsed",
            key="bulk_status_radio",
        )
        bulk_search = _bk2.text_input(
            "Tìm kiếm",
            placeholder="Tên lô, auto title...",
            label_visibility="collapsed",
            key=f"bulk_table_search_{_sv()}",
        )

        view_bulk_base = bulk_df[[c for c in bulk_cols_display2 if c in bulk_df.columns]].copy()
        if bulk_status_filter == "Available":
            view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Available"]
        elif bulk_status_filter == "Sold Out":
            view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Sold Out"]
        if bulk_search.strip():
            _tokens_bk = re.split(r'[\s\-]+', bulk_search.strip().lower())
            _tokens_bk = [t for t in _tokens_bk if t]
            _bk_cols = ["Tên Lô","NameStock","Auto Title"]
            _bk_haystack = view_bulk_base[[c for c in _bk_cols if c in view_bulk_base.columns]] \
                .astype(str).apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
            _bk_combined = _bk_haystack.apply(lambda row: ' '.join(row), axis=1)
            bk_mask = pd.Series([True] * len(view_bulk_base), index=view_bulk_base.index)
            for _tok in _tokens_bk:
                bk_mask &= _bk_combined.str.contains(_tok, regex=False, na=False)
            view_bulk_base = view_bulk_base[bk_mask]

        _bk3.metric("Tổng số", len(view_bulk_base))
        if not view_bulk_base.empty:
            csv_bulk = view_bulk_base.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "⬇️ Xuất CSV",
                data=csv_bulk,
                file_name=f"lo_pack_{now_vn().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_bulk_csv",
            )

        view_bulk2 = view_bulk_base
        _is_bulk_searching = bool(bulk_search.strip()) or bulk_status_filter != "Tất cả"
        if not view_bulk2.empty:
            before_bulk2x = view_bulk2.copy()
            edited_bulk2 = st.data_editor(
                before_bulk2x, key=f"editor_bulk2_{st.session_state.get('editor_bulk_ver', 0)}",
                use_container_width=True, hide_index=True,
                num_rows="fixed" if _is_bulk_searching else "dynamic",
                disabled=["ID"],
                column_config={
                    "NameStock": st.column_config.TextColumn("NameStock", width="small"),
                    "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                    "Giá Nhập Tổng": st.column_config.NumberColumn("Vốn nhập (VNĐ)", format="%d"),
                    "Doanh Thu Tích Lũy": st.column_config.NumberColumn("Doanh thu (VNĐ)", format="%d"),
                    "Lợi Nhuận": st.column_config.NumberColumn("Lợi nhuận (VNĐ)", format="%d"),
                },
            )

            # CẬP NHẬT: Không được reindex vào cột ID để không phá hỏng Primary Key của Supabase
            schema_bulk_view = {c: BULK_SCHEMA.get(c,"") for c in bulk_cols_display2 if c in bulk_df.columns}
            ab2  = normalize_df(edited_bulk2, schema_bulk_view)
            bb2  = normalize_df(before_bulk2x, schema_bulk_view)

            if not ab2.astype(str).equals(bb2.astype(str)):
                # Merge phần đã chỉnh sửa với phần bị ẩn (do filter/search) để không mất dữ liệu
                hidden_rows = bulk_df[[c for c in bulk_cols_display2 if c in bulk_df.columns]].copy()
                # Normalize to int trước khi so sánh tránh "1" vs "1.0" dtype mismatch (data_editor trả về float64)
                visible_ids = set(pd.to_numeric(ab2["ID"], errors="coerce").fillna(0).astype(int).astype(str).tolist()) if "ID" in ab2.columns else set()
                hidden_rows = hidden_rows[~pd.to_numeric(hidden_rows["ID"], errors="coerce").fillna(0).astype(int).astype(str).isin(visible_ids)]
                full_ab2 = normalize_df(pd.concat([ab2, hidden_rows], ignore_index=True), schema_bulk_view)

                save_bulk_supabase(full_ab2, st.session_state.bulk_df)
                # ── Luôn reload từ Supabase để lấy ID thật, tránh id=0 gây duplicate ──
                if USE_SUPABASE:
                    load_bulk.clear()
                    st.session_state.bulk_df = load_bulk()
                else:
                    st.session_state.bulk_df = normalize_df(full_ab2, BULK_SCHEMA)
                # Bump version key để reset widget state
                st.session_state.editor_bulk_ver = st.session_state.get("editor_bulk_ver", 0) + 1
                st.toast("Đã lưu thay đổi", icon="✅")
                st.rerun()
        else:
            st.info("Chưa có lô hàng nào.")

    # ─────────────────────────────────────────────────────────────────────────────
    # TAB 5: CÀI ĐẶT (Chỉ danh mục)
    # ─────────────────────────────────────────────────────────────────────────────
with tab_settings:
    with st.container(border=True):
        st.markdown('<div class="sec-heading">Quản Lý Danh Mục</div>', unsafe_allow_html=True)

        cat_cols = st.columns(3)

        def manage_category(col, label: str, db: pd.DataFrame, file: str, icon: str):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{icon} {label}**")
                    with st.form(f"form_add_{file}", clear_on_submit=True):
                        c1, c2 = st.columns([3, 1])
                        new_val = c1.text_input("Thêm", placeholder=f"Tên {label}...", label_visibility="collapsed")
                        add_ok  = c2.form_submit_button("➕", use_container_width=True)
                    if add_ok:
                        v = new_val.strip()
                        if not v:
                            st.warning("Vui lòng nhập tên.")
                        elif v.lower() in [x.lower() for x in db["Name"].astype(str).tolist()]:
                            st.info("Mục này đã tồn tại.")
                        else:
                            db = append_row(db, {"Name": v}, LIST_SCHEMA)
                            save_csv(db, file)
                            st.toast(f"Đã thêm: {v}", icon="✅")
                            st.rerun()

                    st.dataframe(db, use_container_width=True, hide_index=True, height=140)

                    if not db.empty:
                        with st.form(f"form_del_{file}"):
                            d1, d2 = st.columns([2.5, 1.5])
                            sel_del = d1.selectbox("Xóa", db["Name"].astype(str).tolist(), label_visibility="collapsed")
                            del_ok  = d2.form_submit_button("🗑️", use_container_width=True)
                        if del_ok:
                            db = db[db["Name"].astype(str) != sel_del].reset_index(drop=True)
                            save_csv(db, file)
                            st.rerun()

        manage_category(cat_cols[0], "Pet",       pet_db,   PET_LIST_FILE, "🐾")
        manage_category(cat_cols[1], "NameStock", ns_db,    NS_LIST_FILE,  "🏷️")
        manage_category(cat_cols[2], "Trait",     trait_db, TRAIT_LIST,    "🧬")

        # ── Kiểm tra trùng lặp ──
        if USE_SUPABASE:
            st.markdown("---")
            st.markdown("### 🔍 Kiểm tra trùng lặp Database")
            st.caption("⚠️ Hệ thống chỉ phát hiện và báo cáo — việc xóa do bạn quyết định trực tiếp trong bảng.")
            c_m1, c_m2 = st.columns(2)
            run_inv  = c_m1.button("Kiểm Tra Hàng Lẻ",  use_container_width=True)
            run_bulk = c_m2.button("Kiểm Tra Lô Hàng", use_container_width=True)

            if run_inv:
                dup_inv = find_duplicates("inventory")
                if dup_inv.empty:
                    st.success("Hàng lẻ — không phát hiện trùng lặp.")
                else:
                    st.warning(f"Phát hiện **{len(dup_inv)} bản ghi** trùng lặp:")
                    st.dataframe(dup_inv[["id"] + [c for c in dup_inv.columns if c != "id"]], use_container_width=True, hide_index=True)
                    st.caption("Truy cập Supabase Dashboard → Table Editor → inventory → xoá thủ công theo ID.")

            if run_bulk:
                dup_bulk = find_duplicates("bulk_inventory")
                if dup_bulk.empty:
                    st.success("Lô hàng — không phát hiện trùng lặp.")
                else:
                    st.warning(f"Phát hiện **{len(dup_bulk)} bản ghi** trùng lặp:")
                    st.dataframe(dup_bulk[["id"] + [c for c in dup_bulk.columns if c != "id"]], use_container_width=True, hide_index=True)
                    st.caption("Truy cập Supabase Dashboard → Table Editor → bulk_inventory → xoá thủ công theo ID.")

        # ── Tài Nguyên Hệ Thống ──
        st.markdown("---")
    with st.container(border=True):
        st.markdown('<div class="sec-heading">🖥️ Tình Trạng Tài Nguyên</div>', unsafe_allow_html=True)

        import sys, os, gc

        # ── Process metrics via psutil ──
        try:
            import psutil
            _proc   = psutil.Process(os.getpid())
            _mem_mi = _proc.memory_info()
            _rss_mb = _mem_mi.rss / 1024 / 1024
            _vms_mb = _mem_mi.vms / 1024 / 1024
            _cpu_p  = _proc.cpu_percent(interval=0.1)
            _sys_mem   = psutil.virtual_memory()
            _sys_used  = _sys_mem.used  / 1024 / 1024 / 1024
            _sys_total = _sys_mem.total / 1024 / 1024 / 1024
            _sys_pct   = _sys_mem.percent
            _has_psutil = True
        except ImportError:
            _has_psutil = False

        # ── Session state metrics ──
        import pickle
        def _est_size_bytes(obj):
            try:
                return sys.getsizeof(pickle.dumps(obj, protocol=2))
            except Exception:
                return sys.getsizeof(obj)

        _ss_keys     = list(st.session_state.keys())
        _ss_total_b  = sum(_est_size_bytes(st.session_state[k]) for k in _ss_keys)
        _ss_mb       = _ss_total_b / 1024 / 1024

        _df_inv      = st.session_state.get("df", pd.DataFrame())
        _df_bulk     = st.session_state.get("bulk_df", pd.DataFrame())
        _df_hist     = st.session_state.get("bulk_history", pd.DataFrame())

        # ── Row 1: system / process ──
        _rc1, _rc2, _rc3, _rc4 = st.columns(4)

        if _has_psutil:
            _rss_color  = "normal" if _rss_mb < 300 else ("off" if _rss_mb < 600 else "inverse")
            _cpu_color  = "normal" if _cpu_p  < 30  else ("off" if _cpu_p  < 70  else "inverse")
            _ram_delta  = f"RAM hệ thống: {_sys_pct:.0f}%"
            _rc1.metric("💾 RAM Process (RSS)", f"{_rss_mb:.1f} MB", delta=f"VMS {_vms_mb:.0f} MB")
            _rc2.metric("⚙️ CPU Process", f"{_cpu_p:.1f}%")
            _rc3.metric("🖥️ RAM Hệ Thống", f"{_sys_used:.2f} / {_sys_total:.2f} GB", delta=f"{_sys_pct:.0f}% dùng")
        else:
            _rc1.metric("💾 RAM Process", "N/A", delta="Cài psutil để đo")
            _rc2.metric("⚙️ CPU Process", "N/A")
            _rc3.metric("🖥️ RAM Hệ Thống", "N/A")

        _rc4.metric("🗂️ Session State", f"{_ss_mb:.2f} MB", delta=f"{len(_ss_keys)} keys")

        # ── Row 2: DataFrame sizes ──
        _rd1, _rd2, _rd3, _rd4 = st.columns(4)
        _rd1.metric("📋 Tồn kho lẻ",    f"{len(_df_inv):,} hàng",  delta=f"~{_est_size_bytes(_df_inv)//1024} KB")
        _rd2.metric("📦 Lô hàng",        f"{len(_df_bulk):,} lô",   delta=f"~{_est_size_bytes(_df_bulk)//1024} KB")
        _rd3.metric("📜 Lịch sử lô",     f"{len(_df_hist):,} giao dịch", delta=f"~{_est_size_bytes(_df_hist)//1024} KB")
        _gc_objs = gc.get_count()
        _rd4.metric("♻️ GC Objects",     f"{sum(_gc_objs):,}", delta=f"gen {_gc_objs[0]}/{_gc_objs[1]}/{_gc_objs[2]}")

        # ── Session state detail expander ──
        with st.expander("🔍 Chi tiết Session State Keys"):
            _ss_rows = []
            for _k in sorted(_ss_keys):
                try:
                    _sz = _est_size_bytes(st.session_state[_k])
                    _tp = type(st.session_state[_k]).__name__
                    if isinstance(st.session_state[_k], pd.DataFrame):
                        _tp = f"DataFrame ({len(st.session_state[_k])} rows)"
                    _ss_rows.append({"Key": _k, "Type": _tp, "Size (bytes)": _sz})
                except Exception:
                    _ss_rows.append({"Key": _k, "Type": "?", "Size (bytes)": 0})
            _ss_detail_df = pd.DataFrame(_ss_rows).sort_values("Size (bytes)", ascending=False).reset_index(drop=True)
            st.dataframe(_ss_detail_df, use_container_width=True, hide_index=True,
                         column_config={"Size (bytes)": st.column_config.NumberColumn(format="%,d")})

        # ── Manual GC + clear cache buttons ──
        _rb1, _rb2 = st.columns(2)
        if _rb1.button("♻️ Chạy Garbage Collector", use_container_width=True):
            _before = sum(gc.get_count())
            _collected = gc.collect()
            st.success(f"GC: thu hồi {_collected} objects · còn {sum(gc.get_count())} (trước: {_before})")
        if _rb2.button("🧹 Xoá Cache Streamlit", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Đã xoá toàn bộ cache @st.cache_data và @st.cache_resource.")
