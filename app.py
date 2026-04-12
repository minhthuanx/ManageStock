import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- SUPABASE ---
from supabase import create_client, Client

# =============================================================================
# PAGE CONFIG (must be first Streamlit call)
# =============================================================================
st.set_page_config(
    page_title="GhostlyStock",
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

def _init_supabase():
    global supabase_client, USE_SUPABASE
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        elif "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
            return
        supabase_client = create_client(url, key)
        USE_SUPABASE = True
    except Exception as e:
        st.toast(f"⚠️ Không thể kết nối Supabase: {e}", icon="⚠️")

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
def calc_ngay_ton(row) -> int:
    """
    - Nếu status = 'Đã bán' và có time_ban + time_nhap: chốt = time_ban - time_nhap
    - Ngược lại: now_vn() - time_nhap
    - Fallback: dùng Ngày Nhập (text) nếu time_nhap rỗng
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
        return 0

    if "Đã bán" in status:
        t_ban = _parse_ts(row.get("time_ban", "")) or _parse_text_date(row.get("Ngày Bán", ""))
        if t_ban:
            return max(0, (t_ban - t_nhap).days)

    return max(0, (now_vn() - t_nhap).days)


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
        with st.spinner("Đang tải dữ liệu từ Supabase..."):
            st.session_state.df           = apply_ngay_ton(load_inventory())
            st.session_state.bulk_df      = load_bulk()
            st.session_state.bulk_history = load_bulk_history()
            # Tải Groq key đã lưu (nếu có)
            if not st.session_state.get("groq_key"):
                _stored_key = _load_groq_key_from_supabase()
                if _stored_key:
                    st.session_state.groq_key = _stored_key
        st.session_state.initialized = True

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ─── Root variables ─── */
:root {
  --bg:        #0d1117;
  --surface:   #161b22;
  --surface2:  #1f2937;
  --border:    #30363d;
  --accent:    #38bdf8;
  --accent2:   #22d3ee;
  --green:     #4ade80;
  --red:       #f87171;
  --text:      #e6edf3;
  --muted:     #8b949e;
  --radius:    12px;
}

/* ─── Base ─── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
.block-container { padding: 1rem 1rem 3rem !important; max-width: 1400px; }

/* ─── Metric cards ─── */
div[data-testid="stMetric"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 0.7rem 0.9rem !important;
  transition: border-color 0.2s;
}
div[data-testid="stMetric"]:hover { border-color: var(--accent) !important; }
div[data-testid="stMetricValue"] { font-size: clamp(1rem, 2.5vw, 1.4rem) !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; color: var(--muted) !important; }

/* ─── Buttons ─── */
.stButton > button {
  border-radius: 8px !important;
  font-weight: 600 !important;
  transition: all 0.18s ease !important;
  width: 100%;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #0d1117 !important;
  border: none !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(56,189,248,0.3) !important; }

/* ─── Tabs ─── */
[data-testid="stTabs"] > div:first-child { gap: 0.3rem; border-bottom: 1px solid var(--border); }
[data-testid="stTab"] {
  border-radius: 8px 8px 0 0 !important;
  padding: 0.45rem 1rem !important;
  font-weight: 500 !important;
  color: var(--muted) !important;
  border: none !important;
  background: transparent !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
  background: transparent !important;
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
  box-shadow: 0 0 0 2px rgba(56,189,248,0.15) !important;
}

/* ─── Containers ─── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* ─── DataFrames ─── */
.stDataFrame { border-radius: var(--radius) !important; overflow: hidden !important; }

/* ─── Status badges ─── */
.badge-sold   { color: var(--green); font-weight: 600; }
.badge-stock  { color: var(--accent); font-weight: 600; }

/* ─── Hero banner ─── */
.hero-banner {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.9rem 1.2rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}
.hero-banner .logo { font-size: 2rem; }
.hero-banner h1 { margin: 0; font-size: clamp(1.1rem, 3vw, 1.5rem); font-weight: 700; }
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
.stat-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.stat-card .val  { font-size: 1.2rem; font-weight: 700; color: var(--accent); }
.stat-card .lbl  { font-size: 0.7rem; color: var(--muted); margin-top: 0.1rem; }

/* ─── Section headings ─── */
.sec-heading {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  border-left: 3px solid var(--accent);
  padding-left: 0.6rem;
  margin: 1rem 0 0.6rem;
}

/* ─── Mobile responsive ─── */
@media (max-width: 640px) {
  .block-container { padding: 0.5rem 0.5rem 3rem !important; }
  div[data-testid="stMetricValue"] { font-size: 1rem !important; }
  .stat-card .val { font-size: 1rem; }
  [data-testid="stTab"] { padding: 0.35rem 0.6rem !important; font-size: 0.8rem !important; }
}

/* ─── Toast override ─── */
[data-testid="stToast"] { font-size: 0.85rem !important; border-radius: 10px !important; }

/* ─── Hide Streamlit branding ─── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# Hero banner
st.markdown("""
<div class="hero-banner">
  <div class="logo">👻</div>
  <div>
    <h1>GhostlyStock</h1>
    <p>Quản lý kho Pet · Tự động hóa · Phân tích thông minh</p>
  </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR – Gemini Key only (categories moved to Tab 4)
# =============================================================================
with st.sidebar:
    st.markdown("---")
    st.caption(f"🕐 {now_vn().strftime('%d/%m/%Y %H:%M')} (VN)")
    if USE_SUPABASE:
        st.success("☁️ Supabase: Online", icon="✅")
    else:
        st.warning("💾 Local CSV mode")

    if st.button("🔄 Tải lại dữ liệu", use_container_width=True):
        st.cache_data.clear()
        del st.session_state["initialized"]
        st.rerun()

# =============================================================================
# MAIN TABS
# =============================================================================
tab_kho, tab_pack, tab_chart, tab_ton, tab_settings = st.tabs([
    "📦 Kho Lẻ", "📦 Lô (Pack)", "📊 Chart & Thống kê", "⏳ Tồn lâu", "⚙️ Cài đặt",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: KHO (Nhập + Bán + Bảng tồn kho)
# ─────────────────────────────────────────────────────────────────────────────
with tab_kho:
    col_in, col_sell = st.columns([1.15, 1], gap="medium")

    # ── NHẬP KHO ──
    with col_in:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">📥 Nhập Kho</div>', unsafe_allow_html=True)

            # =========================================================
            # AI VISION – Key setup + multi-image + dialog preview
            # =========================================================
            with st.expander("✨ Nhập hàng loạt bằng AI Vision", expanded=st.session_state.get("ai_expander", False)):

                # ── STEP 1: API KEY ──
                ai_key = st.session_state.get("groq_key", "")
                if ai_key:
                    # Key đã được cấu hình — hiển thị masked + nút cập nhật
                    _masked = ai_key[:6] + "*" * (len(ai_key) - 10) + ai_key[-4:] if len(ai_key) > 10 else "****"
                    _kc1, _kc2 = st.columns([3, 1])
                    _kc1.success(f"✅ Groq Key: `{_masked}` — Kết nối sẵn sàng")
                    if _kc2.button("🔄 Đổi key", use_container_width=True, key="btn_change_groq"):
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
                    st.info("🔐 Nhập Groq API Key ở trên để bắt đầu dùng AI Llama 3.2 90B Vision miễn phí.")
                    ai_key = ""

                    # ── STEP 2: MULTI-IMAGE UPLOAD ──
                    st.markdown("**📷 Upload nhiều ảnh Pet (hỗ trợ phân tích hàng loạt)**")
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
                        st.caption(f"🖼️ Đã chọn **{len(batch_imgs)}** ảnh")
                        # Preview thumbnails (luôn chia 5 cột để ảnh nhỏ vừa đủ)
                        thumb_cols = st.columns(5)
                        for i, img_f in enumerate(batch_imgs[:5]):
                            with thumb_cols[i]:
                                st.image(img_f, use_container_width=True, caption=img_f.name[:12])
                        if len(batch_imgs) > 5:
                            st.caption(f"+ {len(batch_imgs)-5} ảnh khác...")

                        scan_btn = st.button(
                            f"🚀 Quét {len(batch_imgs)} ảnh bằng AI",
                            type="primary",
                            use_container_width=True,
                            key="btn_ai_scan_batch",
                        )

                        if scan_btn:
                            import requests
                            import base64
                            import time
                            
                            results = []
                            progress = st.progress(0, text="Đang khởi tạo Groq AI...")
                            
                            prompt = """Extract the following from the image and return VALID JSON only:
{"Tên Pet": "Name of the pet", "Mutation": "Normal/Gold/Diamond/Divine/Rainbow/etc", "Tốc độ": "Normalize to Millions (M/s). If image says '1.2B/s', return '1200'. If '975M/s', return '975'. Always return a number.", "Số Trait": "Count the number of trait icons or medals above the pet's head. Return 'None' if 0, else return the number as string like '1', '2'"}
No markdown, no extra text, no explanation."""

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
                                
                            st.toast(f"Đang dùng AI Model: {target_model} (Groq)", icon="🦙")

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
                                    progress.progress(
                                        int(((idx + 1) / len(batch_imgs)) * 100),
                                        text=f"Xử lý xong ảnh {idx+1}. (Nghỉ 4s để tránh limit 15 RPM của Groq...)"
                                    )
                                    time.sleep(4.1)
                            
                            progress.progress(100, text="Hoàn thành phân tích!")
                            st.session_state.ai_batch_results = results
                            st.session_state.ai_show_dialog = True
                            st.rerun()

            # =========================================================
            # DIALOG PREVIEW + EDIT (hiện khi có kết quả AI)
            # =========================================================
            if st.session_state.get("ai_show_dialog") and st.session_state.get("ai_batch_results"):
                results = st.session_state.ai_batch_results

                @st.dialog("🤖 Xem trước kết quả AI — Chỉnh sửa trước khi lưu", width="large")
                def ai_preview_dialog():
                    global pet_db
                    pet_opts_dlg   = get_name_options(pet_db)
                    trait_opts_dlg = ["None"] + get_name_options(trait_db)
                    ns_opts_dlg    = [""] + get_name_options(ns_db, fallback="")

                    st.caption(f"🖼️ {len(results)} ảnh đã quét — Kiểm tra và chỉnh sửa rồi bấm Lưu tất cả")

                    edited_rows = []
                    all_valid = True

                    for i, res in enumerate(results):
                        fname = res.get("_filename", f"Image {i+1}")
                        is_ok = res.get("_ok", False)

                        with st.expander(
                            f"🖼️ {fname}" + (" — ❌ Lỗi nhận dạng" if not is_ok else ""),
                            expanded=True,
                        ):
                            if not is_ok:
                                st.warning(f"⚠️ AI không đọc được ảnh này: {res.get('_error','')} — Bạn có thể điền thủ công bên dưới.")

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
                                st.info(f"ℹ️ Còn thiếu: {', '.join(err_row)}. Vui lòng điền nốt để lưu.")
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
                        if st.button("❌ Hủy", use_container_width=True):
                            st.session_state.ai_show_dialog = False
                            st.session_state.ai_batch_results = []
                            st.rerun()

                    with col_save:
                        valid_count = sum(1 for r in edited_rows if r["_valid"])
                        save_label = f"💾 Lưu {valid_count}/{len(edited_rows)} pet hợp lệ"
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
                                st.toast(f"✅ Đã lưu {saved} pet AI thành công!", icon="🎉")
                                import time
                                time.sleep(1.5) # Để kịp hiển thị toast/error
                                st.rerun()

                ai_preview_dialog()

            # =========================================================
            # NHẬP THỦ CÔNG (Always visible)
            # =========================================================
            st.markdown("**📝 Nhập thủ công**")
            pet_opts   = get_name_options(pet_db)
            trait_opts = ["None"] + get_name_options(trait_db)
            ns_opts    = [""] + get_name_options(ns_db, fallback="")

            with st.form("form_nhap_le", clear_on_submit=True):
                p_name = st.selectbox("Tên Pet", pet_opts)
                c1, c2, c3 = st.columns(3)
                ms_raw   = c1.text_input("M/s", placeholder="VD: 975")
                p_mut    = c2.selectbox("Mutation", MUTATION_OPTIONS)
                p_trait  = c3.selectbox("Số Trait", trait_opts)
                c4, c5 = st.columns([1.5, 1])
                p_ns       = c4.selectbox("NameStock", ns_opts)
                p_cost_raw = c5.text_input("Giá nhập (VNĐ)", placeholder="150000")
                submitted = st.form_submit_button("💾 Lưu Pet Lẻ", type="primary", use_container_width=True)

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
                        st.warning("⚠️ Dữ liệu này đã được lưu. Vui lòng tải lại nếu cần.")
                        st.stop()
                    st.session_state.last_nhap_key = submit_key
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
                        st.cache_data.clear()
                        st.session_state.df = apply_ngay_ton(load_inventory())
                        
                    st.toast("✅ Đã lưu pet lẻ!", icon="💾")
                    st.info("📋 Copy title nhanh:")
                    st.code(row["Auto Title"], language="text")
                    st.rerun()

    # ── BÁN LẺ ──
    with col_sell:
        with st.container(border=True):
            st.markdown('<div class="sec-heading">💰 Bán Pet Lẻ</div>', unsafe_allow_html=True)

            active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)]
            q = st.text_input("🔍 Tìm theo STT hoặc title", placeholder="VD: 15 hoặc Rainbow")

            if not active.empty:
                filt = active[
                    active["STT"].astype(str).str.contains(q, regex=False) |
                    active["Auto Title"].astype(str).str.contains(q, case=False, na=False, regex=False)
                ]
                if not filt.empty:
                    sel = st.selectbox(
                        "Chọn Pet",
                        filt["STT"].astype(str) + " — " + filt["Auto Title"],
                        label_visibility="collapsed",
                    )
                    sel_stt = int(sel.split(" — ")[0])
                    sel_row = filt[filt["STT"] == sel_stt].iloc[0]

                    with st.container(border=True):
                        st.caption(f"🐾 **{sel_row['Tên Pet']}** | Nhập: **{fmt_vnd(float(sel_row['Giá Nhập']))}** | Tồn: **{int(sel_row['Ngày Tồn'])} ngày**")

                    with st.form("form_ban_le", clear_on_submit=True):
                        c1, c2 = st.columns([1.2, 1])
                        s_price_raw = c1.text_input("Giá bán ($)", placeholder="VD: 5.5")
                        s_place     = c2.text_input("Place (tuỳ chọn)", placeholder="Eldorado...")
                        sell_btn    = st.form_submit_button("✅ Xác nhận bán", type="primary", use_container_width=True)

                    if sell_btn:
                        s_price = parse_usd(s_price_raw)
                        if s_price <= 0:
                            st.error("❌ Giá bán phải > 0")
                        else:
                            ts_ban = now_iso()
                            rev_vnd = s_price * EXCHANGE_RATE
                            idx_list = df.index[df["STT"] == sel_stt].tolist()
                            if idx_list:
                                iloc_pos = df.index.get_loc(idx_list[0])
                                recs = df.to_dict("records")
                                recs[iloc_pos]["Giá Bán"]    = float(s_price)
                                recs[iloc_pos]["Doanh Thu"]  = float(rev_vnd)
                                recs[iloc_pos]["Lợi Nhuận"]  = float(rev_vnd - float(recs[iloc_pos]["Giá Nhập"]))
                                recs[iloc_pos]["Ngày Bán"]   = now_str()
                                recs[iloc_pos]["Trạng Thái"] = "Đã bán"
                                recs[iloc_pos]["time_ban"]   = ts_ban
                                recs[iloc_pos]["Place"]      = s_place
                                df = apply_ngay_ton(normalize_df(pd.DataFrame(recs), MAIN_SCHEMA))
                                st.session_state.df = df
                                if USE_SUPABASE:
                                    # Dùng "id" (primary key) thay "stt" để tránh cập nhật sai record
                                    _sell_id = int(float(recs[iloc_pos].get("id", 0) or 0))
                                    _update_col = "id" if _sell_id > 0 else "stt"
                                    _update_val = _sell_id if _sell_id > 0 else sel_stt
                                    sb_update("inventory", {
                                        "gia_ban":    float(s_price),
                                        "doanh_thu":  float(rev_vnd),
                                        "loi_nhuan":  float(rev_vnd - float(recs[iloc_pos]["Giá Nhập"])),
                                        "ngay_ban":   now_str(),
                                        "trang_thai": "Đã bán",
                                        "time_ban":   ts_ban,
                                        "place":      s_place,
                                        "ngay_ton":   int(recs[iloc_pos]["Ngày Tồn"]),
                                    }, _update_col, _update_val)
                                st.toast("💸 Bán thành công!", icon="✅")
                                st.rerun()
                else:
                    st.info("Không có kết quả phù hợp.")
            else:
                st.info("Không có pet lẻ nào đang còn hàng.")

    # ── BẢNG TỒN KHO ──
    st.markdown('<div class="sec-heading">📋 Tồn Kho Lẻ</div>', unsafe_allow_html=True)

    # ── THANH CÔNG CỤ ──
    _tb1, _tb2, _tb3 = st.columns([2, 2.5, 1])
    view_mode = _tb1.radio(
        "Lọc trạng thái",
        ["📦 Còn hàng", "✅ Đã bán", "🗂 Tất cả"],
        horizontal=True,
        label_visibility="collapsed",
    )
    inv_search = _tb2.text_input(
        "🔍 Tìm kiếm",
        placeholder="STT, tên pet, mutation, title...",
        label_visibility="collapsed",
        key="inv_table_search",
    )
    if view_mode == "📦 Còn hàng":
        view_df = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        show_all = False
    elif view_mode == "✅ Đã bán":
        view_df = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]
        show_all = True
    else:
        view_df = df.copy()
        show_all = True

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

    display_cols = ["id","STT","Tên Pet","M/s","Mutation","Số Trait","NameStock",
                    "Giá Nhập","Giá Bán","Lợi Nhuận","Ngày Nhập","Ngày Bán",
                    "Ngày Tồn","Trạng Thái","Auto Title","Place"]
    view_cols = [c for c in display_cols if c in view_df.columns]

    # Nút xuất CSV + đếm kết quả
    _tb3.metric("Kết quả", len(view_df))
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
        # Khi đang search: chỉ xem, không cho thêm/xoá dòng (tránh mất dữ liệu hàng ẩn)
        _is_searching = bool(inv_search.strip())
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
                "Ngày Tồn": st.column_config.NumberColumn("Ngày Tồn", disabled=True),
                "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                "Giá Nhập": st.column_config.NumberColumn("Giá Nhập (VNĐ)", format="%d"),
                "Giá Bán": st.column_config.NumberColumn("Giá Bán ($)"),
                "Lợi Nhuận": st.column_config.NumberColumn("Lợi Nhuận (VNĐ)", format="%d"),
            },
        )

        # Chỉ reindex STT khi xem "Tất cả" + không tìm kiếm → tránh STT conflict khi merge-back
        _can_reindex = (view_mode == "🗂 Tất cả") and not _is_searching
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
                visible_ids = set(after_reindexed["id"].astype(str).tolist()) if "id" in after_reindexed.columns else set()
                hidden_rows = full_df[~full_df["id"].astype(str).isin(visible_ids)]
                merged = pd.concat([after_reindexed, hidden_rows], ignore_index=True)
                full_updated = apply_ngay_ton(normalize_df(merged, MAIN_SCHEMA))
            elif view_mode == "🗂 Tất cả":
                full_updated = apply_ngay_ton(normalize_df(after_reindexed, MAIN_SCHEMA))
            elif view_mode == "✅ Đã bán":
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
                st.cache_data.clear()
                st.session_state.df = apply_ngay_ton(load_inventory())
            else:
                st.session_state.df = full_updated
            df = st.session_state.df
            # Bump version key để reset widget state, tránh vòng lặp lưu vô hạn
            st.session_state.editor_inv_ver = st.session_state.get("editor_inv_ver", 0) + 1
            st.toast("✅ Đã lưu thay đổi.", icon="💾")
            st.rerun()
    else:
        st.info("Không có dữ liệu để hiển thị.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: CHART & THỐNG KÊ
# ─────────────────────────────────────────────────────────────────────────────
with tab_chart:
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
    st.markdown('<div class="sec-heading">💎 Tổng quan</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Lợi nhuận ròng",   fmt_vnd(net_profit))
    k2.metric("📈 Tổng doanh thu",   fmt_vnd(total_rev))
    k3.metric("📥 Tổng vốn nhập",    fmt_vnd(total_cost))
    k4.metric("📦 Pet đang tồn",     f"{total_stock:,}")

    st.markdown("---")

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
    st.markdown('<div class="sec-heading">📊 Biểu đồ lợi nhuận</div>', unsafe_allow_html=True)
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
            sort_key = chart_df["Ngày DT"].dt.to_period("W").apply(lambda p: p.start_time)
        else:
            chart_df["Period"] = chart_df["Ngày DT"].dt.strftime("%m/%Y")
            sort_key = chart_df["Ngày DT"].dt.to_period("M").apply(lambda p: p.start_time)

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
                color="#38bdf8",
                line=dict(color="#38bdf8", width=0),
            ),
            cliponaxis=False,
        ))
        fig.update_layout(
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(family="Inter", color="#8b949e", size=11),
            xaxis=dict(
                type="category",
                tickfont=dict(size=10, color="#8b949e"),
                gridcolor="#1f2937",
                linecolor="#30363d",
            ),
            yaxis=dict(
                title="Lợi nhuận (VNĐ)",
                tickfont=dict(size=10, color="#8b949e"),
                gridcolor="#1f2937",
                linecolor="#30363d",
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
                delta = fmt_vnd(delta_val)
            c1.metric(f"Lợi nhuận {period_label} gần nhất ({last_row['Period']})",
                      fmt_vnd(last_row["Lợi Nhuận"]), delta=delta)
            c2.metric(f"Tổng {period_label} đã có",  f"{len(agg):,}")
            c3.metric(f"Trung bình/{period_label}",  fmt_vnd(agg['Lợi Nhuận'].mean()))
    else:
        st.info("Chưa có dữ liệu bán để vẽ biểu đồ.")

    st.markdown("---")
    # ── Revenue channel split ──
    st.markdown('<div class="sec-heading">📈 Phân tích kênh & sản phẩm</div>', unsafe_allow_html=True)
    c_left, c_right = st.columns(2)

    with c_left:
        rev_breakdown = pd.DataFrame({
            "Kênh": ["Pet Lẻ", "Lô (Pack)"],
            "Doanh Thu": [rev_single, rev_bulk],
        })
        if rev_breakdown["Doanh Thu"].sum() > 0:
            fig_pie = go.Figure(go.Pie(
                labels=rev_breakdown["Kênh"],
                values=rev_breakdown["Doanh Thu"],
                hole=0.48,
                marker=dict(colors=["#38bdf8","#4ade80"]),
                textfont=dict(family="Inter", color="#e2e8f0"),
            ))
            fig_pie.update_layout(
                paper_bgcolor="#0d1117",
                plot_bgcolor="#0d1117",
                font=dict(family="Inter", color="#8b949e"),
                title=dict(text="Tỷ trọng doanh thu", font=dict(size=13, color="#e2e8f0")),
                margin=dict(l=10, r=10, t=50, b=10),
                height=300,
                legend=dict(font=dict(color="#e2e8f0")),
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu doanh thu.")

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
                marker=dict(color="#38bdf8"),
                text=top_pets["Lợi Nhuận"].apply(fmt_short),
                textposition="outside",
                textfont=dict(color="#e2e8f0", size=10),
            ))
            fig_bar.update_layout(
                paper_bgcolor="#0d1117",
                plot_bgcolor="#0d1117",
                font=dict(family="Inter", color="#8b949e"),
                title=dict(text="Top 10 Pet Lợi nhuận cao", font=dict(size=13, color="#e2e8f0")),
                xaxis=dict(gridcolor="#1f2937", tickformat=",.0f", tickfont=dict(color="#8b949e")),
                yaxis=dict(gridcolor="#1f2937", tickfont=dict(color="#e2e8f0")),
                margin=dict(l=10, r=10, t=50, b=10),
                height=300,
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Chưa có pet lẻ đã bán.")

    # ── Weekly / Monthly summary table ──
    if has_data and not pbd.empty:
        st.markdown("---")
        st.markdown('<div class="sec-heading">📅 Bảng thống kê theo tháng</div>', unsafe_allow_html=True)
        monthly = (
            pbd.assign(Tháng=pbd["Ngày DT"].dt.strftime("%m/%Y"),
                       SortKey=pbd["Ngày DT"].dt.to_period("M").apply(lambda p: p.start_time))
            .groupby(["Tháng","SortKey"], as_index=False)["Lợi Nhuận"].sum()
            .sort_values("SortKey", ascending=False)
        )
        monthly["Doanh Thu tháng"] = monthly["Tháng"].map(
            pbd.assign(Tháng=pbd["Ngày DT"].dt.strftime("%m/%Y"))
               .groupby("Tháng")["Lợi Nhuận"].sum()
        )
        monthly_display = monthly[["Tháng","Lợi Nhuận"]].copy()
        monthly_display["Lợi Nhuận VNĐ"] = monthly_display["Lợi Nhuận"].apply(fmt_vnd)
        monthly_display = monthly_display.drop(columns=["Lợi Nhuận"])
        st.dataframe(monthly_display, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: TỒN LÂU
# ─────────────────────────────────────────────────────────────────────────────
with tab_ton:
    st.markdown('<div class="sec-heading">⏳ Hàng Tồn Lâu</div>', unsafe_allow_html=True)

    c_thresh, c_sort = st.columns([1, 2])
    age_thresh = c_thresh.slider("Số ngày tồn tối thiểu", 1, 120, 7)
    sort_by    = c_sort.selectbox("Sắp xếp theo", ["Ngày Tồn (giảm)", "Giá trị vốn (giảm)", "Tên Pet"])

    # Pet lẻ tồn
    single_old = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)].copy()
    single_old = apply_ngay_ton(single_old)
    single_old = single_old[single_old["Ngày Tồn"] >= age_thresh]
    single_old["Loại"]            = "Pet Lẻ"
    single_old["Item"]            = single_old["Tên Pet"].astype(str)
    single_old["Số lượng còn"]    = 1
    single_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(single_old["Giá Nhập"], errors="coerce").fillna(0)
    sv = single_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]] if not single_old.empty else pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

    # Pack tồn
    pack_old = bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"].copy()
    if not pack_old.empty:
        pack_old["Ngày DT"] = pd.to_datetime(pack_old["Ngày Nhập"], dayfirst=True, errors="coerce")
        pack_old["Ngày Tồn"] = (now_vn().replace(tzinfo=None) - pack_old["Ngày DT"].dt.tz_localize(None)).dt.days.fillna(0).astype(int)
        pack_old = pack_old[pack_old["Ngày Tồn"] >= age_thresh]
        pack_old["Loại"]            = "Lô (Pack)"
        pack_old["Item"]            = pack_old["Tên Lô"].astype(str)
        pack_old["Số lượng còn"]    = pd.to_numeric(pack_old["Còn Lại"], errors="coerce").fillna(0).astype(int)
        pack_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(pack_old["Giá Nhập Tổng"], errors="coerce").fillna(0)
        pv = pack_old[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"]]
    else:
        pv = pd.DataFrame(columns=["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn (VNĐ)","Auto Title"])

    old_items = pd.concat([sv, pv], ignore_index=True)
    if old_items.empty:
        st.info(f"✅ Không có item nào tồn trên {age_thresh} ngày.")
    else:
        if sort_by == "Ngày Tồn (giảm)":
            old_items = old_items.sort_values("Ngày Tồn", ascending=False)
        elif sort_by == "Giá trị vốn (giảm)":
            old_items = old_items.sort_values("Giá trị vốn (VNĐ)", ascending=False)
        else:
            old_items = old_items.sort_values("Item")

        # Summary metrics
        total_stuck_val = old_items["Giá trị vốn (VNĐ)"].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Số items tồn lâu", f"{len(old_items):,}")
        m2.metric("Giá trị vốn đang kẹt", fmt_vnd(total_stuck_val))
        m3.metric("Tồn lâu nhất", f"{int(old_items['Ngày Tồn'].max())} ngày")

        old_items["Giá trị vốn"] = old_items["Giá trị vốn (VNĐ)"].apply(fmt_vnd)
        st.dataframe(
            old_items[["Loại","Item","Số lượng còn","Ngày Nhập","Ngày Tồn","Giá trị vốn","Auto Title"]],
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "Auto Title": st.column_config.TextColumn("Auto Title", width="large"),
                "Ngày Tồn": st.column_config.NumberColumn("Ngày Tồn", format="%d ngày"),
            },
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: LÔ PACK
# ─────────────────────────────────────────────────────────────────────────────
with tab_pack:
    st.markdown('<div class="sec-heading">📦 Quản lý Lô (Pack)</div>', unsafe_allow_html=True)

    pack_in, pack_sell = st.columns([1.15, 1], gap="medium")

    with pack_in:
        with st.container(border=True):
            st.markdown("**📥 Nhập Lô mới**")
            with st.form("form_nhap_lo2", clear_on_submit=True):
                b_pet2 = st.selectbox("Tên Pet", get_name_options(pet_db), key="bp1t2")
                b1t, b2t, b3t = st.columns(3)
                b_qty2    = b1t.number_input("Số lượng", min_value=1, max_value=999, value=10, key="bqt2")
                b_ms_raw2 = b2t.text_input("M/s", placeholder="975", key="bp2t2")
                b_mut2    = b3t.selectbox("Mutation", MUTATION_OPTIONS, key="bp3t2")
                b_ns2     = st.selectbox("NameStock", [""]+get_name_options(ns_db,""), key="bp5t2")
                b_cost_raw2 = st.text_input("Tổng giá nhập (VNĐ)", placeholder="2.000.000", key="bp4t2")
                pack_ok2  = st.form_submit_button("💾 Lưu Lô", type="primary", use_container_width=True)
            if pack_ok2:
                b_cost2 = parse_vnd(b_cost_raw2)
                b_ms2   = parse_usd(b_ms_raw2)
                errs2 = []
                if b_pet2 == "None":  errs2.append("Chọn tên Pet")
                if b_ms2 <= 0:        errs2.append("M/s phải > 0")
                if b_cost2 <= 0:      errs2.append("Giá nhập phải > 0")
                if not b_ns2.strip(): errs2.append("Chọn NameStock")
                if errs2:
                    for e in errs2: st.error(f"❌ {e}")
                else:
                    # Guard chống double-submit lô pack
                    lo_submit_key = f"nhap_lo_{b_pet2}_{b_qty2}_{b_cost2}_{b_ns2}"
                    if st.session_state.get("last_lo_key") == lo_submit_key:
                        st.warning("⚠️ Lô này đã được lưu. Vui lòng tải lại nếu cần.")
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
                    }
                    bulk_df = append_row(bulk_df, row2, BULK_SCHEMA)
                    st.session_state.bulk_df = bulk_df
                    if USE_SUPABASE:
                        db_row2 = to_db(row2)
                        db_row2.pop("id", None)
                        sb_insert("bulk_inventory", db_row2)
                        # Tải lại để update ID từ database cho bản ghi mới thêm
                        st.cache_data.clear()
                        st.session_state.bulk_df = load_bulk()
                    st.toast("✅ Đã lưu lô pack!", icon="💾")
                    st.rerun()

    with pack_sell:
        with st.container(border=True):
            st.markdown("**💰 Bán từ Lô**")
            avail2 = bulk_df[bulk_df["Trạng Thái"].astype(str)=="Available"]
            if not avail2.empty:
                sel_b2 = st.selectbox(
                    "Chọn lô", avail2["ID"].astype(str)+" — "+avail2["Tên Lô"],
                    label_visibility="collapsed", key="sel_b2",
                )
                target_id2 = int(sel_b2.split(" — ")[0])
                target2 = avail2[avail2["ID"]==target_id2].iloc[0]
                st.caption(f"🏷 **{target2['Tên Lô']}** | Còn lại: **{int(target2['Còn Lại'])}** | Vốn: **{fmt_vnd(float(target2['Giá Nhập Tổng']))}**")

                with st.form("form_ban_lo2", clear_on_submit=True):
                    s1t, s2t = st.columns(2)
                    s_qty2     = s1t.number_input("Số lượng bán", min_value=1, max_value=int(target2["Còn Lại"]), key="sqty2")
                    s_prc_raw2 = s2t.text_input("Giá bán ($/pet)", placeholder="3.5", key="sprc2")
                    sell_ok2   = st.form_submit_button("✅ Bán Lô", type="primary", use_container_width=True)

                if sell_ok2:
                    s_prc2 = parse_usd(s_prc_raw2)
                    if s_prc2 <= 0:
                        st.error("❌ Giá bán phải > 0")
                    else:
                        # Guard chống double-submit bán lô
                        ban_lo_key = f"ban_lo_{int(target2['ID'])}_{s_qty2}_{s_prc2}"
                        if st.session_state.get("last_ban_lo_key") == ban_lo_key:
                            st.warning("⚠️ Giao dịch này đã được ghi. Vui lòng tải lại nếu cần.")
                            st.stop()
                        st.session_state.last_ban_lo_key = ban_lo_key
                        idx2 = bulk_df[bulk_df["ID"]==target2["ID"]].index[0]
                        rev_vnd2 = s_qty2 * s_prc2 * EXCHANGE_RATE
                        new_con_lai2   = max(0.0, float(bulk_df.at[idx2,"Còn Lại"]) - float(s_qty2))
                        new_dt2        = float(bulk_df.at[idx2,"Doanh Thu Tích Lũy"]) + rev_vnd2
                        new_loi_nhuan2 = new_dt2 - float(bulk_df.at[idx2,"Giá Nhập Tổng"])
                        new_status2    = "Sold Out" if new_con_lai2 <= 0 else "Available"

                        bulk_df.at[idx2,"Còn Lại"]            = new_con_lai2
                        bulk_df.at[idx2,"Doanh Thu Tích Lũy"] = new_dt2
                        bulk_df.at[idx2,"Lợi Nhuận"]          = new_loi_nhuan2
                        bulk_df.at[idx2,"Trạng Thái"]         = new_status2

                        base_unit2 = float(target2["Giá Nhập Tổng"]) / max(float(target2["Số Lượng Gốc"]),1)
                        hist_row2 = {
                            "Ngày Bán":            now_str(),
                            "Tên Lô":              target2["Tên Lô"],
                            "Số Lượng Bán":        s_qty2,
                            "Lợi Nhuận Giao Dịch": rev_vnd2 - (base_unit2 * s_qty2),
                            "Doanh Thu Giao Dịch": rev_vnd2,
                        }
                        bulk_history = append_row(bulk_history, hist_row2, HISTORY_SCHEMA)
                        st.session_state.bulk_df      = bulk_df
                        st.session_state.bulk_history = bulk_history

                        if USE_SUPABASE:
                            sb_insert("bulk_history", to_db(hist_row2))
                            sb_update("bulk_inventory", {
                                "con_lai":            new_con_lai2,
                                "doanh_thu_tich_luy": new_dt2,
                                "loi_nhuan":          new_loi_nhuan2,
                                "trang_thai":         new_status2,
                            }, "id", int(target2["ID"]))
                        st.toast("💸 Đã bán lô pack!", icon="✅")
                        st.rerun()
            else:
                st.info("Không có lô nào đang Available.")

    st.markdown("---")
    st.markdown("**📋 Danh sách lô pack**")
    bulk_cols_display2 = ["ID","Tên Lô","Số Lượng Gốc","Còn Lại","Ngày Nhập",
                          "Giá Nhập Tổng","Doanh Thu Tích Lũy","Lợi Nhuận","Trạng Thái","Auto Title"]

    # ── THANH CÔNG CỤ LÔ PACK ──
    _bk1, _bk2, _bk3 = st.columns([2, 2, 1])
    bulk_status_filter = _bk1.radio(
        "Lọc lô",
        ["🟢 Available", "⛔ Sold Out", "🗂 Tất cả"],
        horizontal=True,
        label_visibility="collapsed",
        key="bulk_status_radio",
    )
    bulk_search = _bk2.text_input(
        "🔍 Tìm lô",
        placeholder="Tên lô, auto title...",
        label_visibility="collapsed",
        key="bulk_table_search",
    )

    view_bulk_base = bulk_df[[c for c in bulk_cols_display2 if c in bulk_df.columns]].copy()
    if bulk_status_filter == "🟢 Available":
        view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Available"]
    elif bulk_status_filter == "⛔ Sold Out":
        view_bulk_base = view_bulk_base[view_bulk_base["Trạng Thái"].astype(str) == "Sold Out"]
    if bulk_search.strip():
        _tokens_bk = re.split(r'[\s\-]+', bulk_search.strip().lower())
        _tokens_bk = [t for t in _tokens_bk if t]
        _bk_cols = ["Tên Lô","Auto Title"]
        _bk_haystack = view_bulk_base[[c for c in _bk_cols if c in view_bulk_base.columns]] \
            .astype(str).apply(lambda col: col.str.lower().str.replace(r'[\-\s]+', ' ', regex=True))
        _bk_combined = _bk_haystack.apply(lambda row: ' '.join(row), axis=1)
        bk_mask = pd.Series([True] * len(view_bulk_base), index=view_bulk_base.index)
        for _tok in _tokens_bk:
            bk_mask &= _bk_combined.str.contains(_tok, regex=False, na=False)
        view_bulk_base = view_bulk_base[bk_mask]

    _bk3.metric("Kết quả", len(view_bulk_base))
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
    _is_bulk_searching = bool(bulk_search.strip()) or bulk_status_filter != "🗂 Tất cả"
    if not view_bulk2.empty:
        before_bulk2x = view_bulk2.copy()
        edited_bulk2 = st.data_editor(
            before_bulk2x, key=f"editor_bulk2_{st.session_state.get('editor_bulk_ver', 0)}",
            use_container_width=True, hide_index=True,
            num_rows="fixed" if _is_bulk_searching else "dynamic",
            disabled=["ID"],
            column_config={
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
            visible_ids = set(ab2["ID"].astype(str).tolist()) if "ID" in ab2.columns else set()
            hidden_rows = hidden_rows[~hidden_rows["ID"].astype(str).isin(visible_ids)]
            full_ab2 = normalize_df(pd.concat([ab2, hidden_rows], ignore_index=True), schema_bulk_view)

            save_bulk_supabase(full_ab2, st.session_state.bulk_df)
            # ── Luôn reload từ Supabase để lấy ID thật, tránh id=0 gây duplicate ──
            if USE_SUPABASE:
                st.cache_data.clear()
                st.session_state.bulk_df = load_bulk()
            else:
                st.session_state.bulk_df = normalize_df(full_ab2, BULK_SCHEMA)
            # Bump version key để reset widget state
            st.session_state.editor_bulk_ver = st.session_state.get("editor_bulk_ver", 0) + 1
            st.toast("✅ Đã lưu thay đổi lô pack.", icon="💾")
            st.rerun()
    else:
        st.info("Chưa có lô pack nào.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: CÀI ĐẶT (Chỉ danh mục)
# ─────────────────────────────────────────────────────────────────────────────
with tab_settings:
    st.markdown('<div class="sec-heading">⚙️ Quản lý danh mục</div>', unsafe_allow_html=True)

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
                        st.warning("Tên trống!")
                    elif v.lower() in [x.lower() for x in db["Name"].astype(str).tolist()]:
                        st.info("Đã tồn tại.")
                    else:
                        db = append_row(db, {"Name": v}, LIST_SCHEMA)
                        save_csv(db, file)
                        st.toast(f"✅ Đã thêm {label}: {v}", icon="✅")
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
        run_inv  = c_m1.button("🔍 Kiểm tra Kho Lẻ",  use_container_width=True)
        run_bulk = c_m2.button("🔍 Kiểm tra Lô/Pack", use_container_width=True)

        if run_inv:
            dup_inv = find_duplicates("inventory")
            if dup_inv.empty:
                st.success("✨ Kho Lẻ: không có dòng trùng lặp.")
            else:
                st.warning(f"⚠️ Tìm thấy **{len(dup_inv)} dòng** có nội dung trùng nhau (theo Database ID):")
                st.dataframe(dup_inv[["id"] + [c for c in dup_inv.columns if c != "id"]], use_container_width=True, hide_index=True)
                st.caption("💡 Vào Supabase Dashboard → Table Editor → inventory → xóa thủ công các ID cần bỏ.")

        if run_bulk:
            dup_bulk = find_duplicates("bulk_inventory")
            if dup_bulk.empty:
                st.success("✨ Lô/Pack: không có dòng trùng lặp.")
            else:
                st.warning(f"⚠️ Tìm thấy **{len(dup_bulk)} dòng** có nội dung trùng nhau (theo Database ID):")
                st.dataframe(dup_bulk[["id"] + [c for c in dup_bulk.columns if c != "id"]], use_container_width=True, hide_index=True)
                st.caption("💡 Vào Supabase Dashboard → Table Editor → bulk_inventory → xóa thủ công các ID cần bỏ.")
