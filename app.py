import json
import os
import re
import html
import shutil
from datetime import datetime
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# --- SUPABASE CONFIGURATION ---
from supabase import create_client, Client

# --- SUPABASE CONFIGURATION ---
# Supabase clients
supabase_client = None
USE_SUPABASE = False

# Initialize Supabase if secrets are available
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        supabase_client = create_client(supabase_url, supabase_key)
        USE_SUPABASE = True
        st.success("✅ Connected to Supabase!")
    except Exception as e:
        st.warning(f"⚠️ Could not connect to Supabase: {e}. Using local CSV files.")
        USE_SUPABASE = False
elif "supabase" in st.secrets and "url" in st.secrets["supabase"] and "key" in st.secrets["supabase"]:
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        supabase_client = create_client(supabase_url, supabase_key)
        USE_SUPABASE = True
        st.success("✅ Connected to Supabase!")
    except Exception as e:
        st.warning(f"⚠️ Could not connect to Supabase: {e}. Using local CSV files.")
        USE_SUPABASE = False

# --- SUPABASE CRUD FUNCTIONS ---
def supabase_insert(table_name: str, data: dict) -> bool:
    """Insert data into Supabase table"""
    if not USE_SUPABASE or not supabase_client:
        return False
    try:
        result = supabase_client.table(table_name).insert(data).execute()
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        st.error(f"❌ Lỗi khi thêm dữ liệu vào {table_name}: {e}")
        return False

def supabase_update(table_name: str, data: dict, condition_col: str, condition_value) -> bool:
    """Update data in Supabase table"""
    if not USE_SUPABASE or not supabase_client:
        return False
    try:
        result = supabase_client.table(table_name).update(data).eq(condition_col, condition_value).execute()
        return len(result.data) > 0 if result.data else False
    except Exception as e:
        st.error(f"❌ Lỗi khi cập nhật dữ liệu trong {table_name}: {e}")
        return False

def supabase_delete(table_name: str, condition_col: str, condition_value) -> bool:
    """Delete data from Supabase table"""
    if not USE_SUPABASE or not supabase_client:
        return False
    try:
        result = supabase_client.table(table_name).delete().eq(condition_col, condition_value).execute()
        return result.data is not None
    except Exception as e:
        st.error(f"❌ Lỗi khi xóa dữ liệu trong {table_name}: {e}")
        return False

def supabase_select(table_name: str, order_by: str = "id") -> pd.DataFrame:
    """Select all data from Supabase table"""
    if not USE_SUPABASE or not supabase_client:
        return pd.DataFrame()
    try:
        result = supabase_client.table(table_name).select("*").order(order_by).execute()
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc dữ liệu từ {table_name}: {e}")
        return pd.DataFrame()

def supabase_select_by_id(table_name: str, id_col: str, id_value) -> pd.DataFrame:
    """Select data by ID from Supabase table"""
    if not USE_SUPABASE or not supabase_client:
        return pd.DataFrame()
    try:
        result = supabase_client.table(table_name).select("*").eq(id_col, id_value).execute()
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc dữ liệu từ {table_name}: {e}")
        return pd.DataFrame()

def load_data_from_supabase(table_name: str, schema: dict, order_by: str = "id") -> pd.DataFrame:
    """Load data from Supabase with fallback to CSV"""
    if USE_SUPABASE:
        try:
            df_supabase = supabase_select(table_name, order_by)
            if not df_supabase.empty:
                st.info(f"📊 Đã tải {len(df_supabase)} dòng từ Supabase ({table_name})")
                return normalize_dataframe(df_supabase, schema)
        except Exception as e:
            st.warning(f"⚠️ Không thể đọc từ Supabase: {e}. Đang dùng CSV.")
    
    # Fallback to CSV
    return load_data(f"{table_name}.csv", schema)

def save_data_to_supabase(df_data: pd.DataFrame, table_name: str, file: str) -> None:
    """Save data to Supabase with fallback to CSV"""
    # Always create backup for CSV
    create_backup(file)
    
    # Try to save to Supabase
    if USE_SUPABASE:
        try:
            # Convert DataFrame to list of dicts
            records = df_data.to_dict('records')
            
            # Clear table and insert new data (simple approach)
            # Note: For production, you might want to use upsert or handle updates more carefully
            for record in records:
                # Remove pandas index if present
                if 'index' in record:
                    del record['index']
            
            # Clear existing data and insert new (for simplicity)
            # In production, you'd want more sophisticated sync logic
            supabase_client.table(table_name).delete().neq('id', 0).execute()
            
            if records:
                result = supabase_client.table(table_name).insert(records).execute()
                if result.data:
                    st.success(f"✅ Đã lưu {len(result.data)} bản ghi lên Supabase ({table_name})")
                    # Also save to CSV as backup
                    df_data.to_csv(file, index=False, encoding='utf-8-sig')
                    return
            
        except Exception as e:
            st.error(f"❌ Lỗi khi lưu lên Supabase: {e}")
    
    # Fallback to CSV
    temp_file = f"{file}.tmp"
    try:
        df_data.to_csv(temp_file, index=False, encoding='utf-8-sig')
        os.replace(temp_file, file)
        if not USE_SUPABASE:
            st.info(f"💾 Đã lưu {len(df_data)} bản ghi vào CSV ({file})")
    except Exception as e:
        st.error(f"Lỗi khi lưu dữ liệu: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

# --- CONFIGURATION ---
DB_FILE = "inventory.csv"
BULK_FILE = "bulk_inventory.csv"
BULK_HISTORY = "bulk_history.csv"
PET_LIST_FILE = "pet_list.csv"
NS_LIST_FILE = "namestock_list.csv"
TRAIT_LIST_FILE = "traits_list.csv"
SQLITE_DB = "ghostlystock.db"
BACKUP_DIR = "backups"
EXCHANGE_RATE = 20400

MAIN_SCHEMA = {
    "STT": 0,
    "Tên Pet": "",
    "M/s": 0.0,
    "Mutation": "Normal",
    "Số Trait": "None",
    "NameStock": "",
    "Giá Nhập": 0.0,
    "Giá Bán": 0.0,
    "Lợi Nhuận": 0.0,
    "Doanh Thu": 0.0,
    "Ngày Nhập": "",
    "Ngày Bán": "-",
    "Auto Title": "",
    "Trạng Thái": "Còn hàng",
}

BULK_SCHEMA = {
    "ID": 0,
    "Tên Lô": "",
    "Số Lượng Gốc": 0,
    "Còn Lại": 0,
    "Ngày Nhập": "",
    "Giá Nhập Tổng": 0.0,
    "Doanh Thu Tích Lũy": 0.0,
    "Lợi Nhuận": 0.0,
    "Trạng Thái": "Available",
    "Auto Title": "",
}

HISTORY_SCHEMA = {
    "Ngày Bán": "",
    "Tên Lô": "",
    "Số Lượng Bán": 0,
    "Lợi Nhuận Giao Dịch": 0.0,
    "Doanh Thu Giao Dịch": 0.0,
}

LIST_SCHEMA = {"Name": ""}

mutation_options = [
    "Normal",
    "Gold",
    "Diamond",
    "Bloodrot",
    "Candy",
    "Divine",
    "Lava",
    "Galaxy",
    "Yin-Yang",
    "Radioactive",
    "Cursed",
    "Rainbow",
]


def normalize_dataframe(df_loaded: pd.DataFrame, schema: dict) -> pd.DataFrame:
    if df_loaded.empty:
        return pd.DataFrame(columns=schema.keys())

    df_loaded = df_loaded.dropna(how="all")

    for col, default in schema.items():
        if col not in df_loaded.columns:
            df_loaded[col] = default

    df_loaded = df_loaded[list(schema.keys())]

    for col, default in schema.items():
        if isinstance(default, (int, float)):
            df_loaded[col] = pd.to_numeric(df_loaded[col], errors="coerce").fillna(default)
        else:
            df_loaded[col] = df_loaded[col].fillna(default).astype(str)

    return df_loaded


def load_data(file: str, schema: dict) -> pd.DataFrame:
    if not os.path.exists(file):
        return pd.DataFrame(columns=schema.keys())

    try:
        return normalize_dataframe(pd.read_csv(file), schema)
    except (pd.errors.ParserError, UnicodeDecodeError, OSError) as err:
        st.warning(f"Không thể đọc file {file}: {err}. Đã tạo dữ liệu rỗng.")
        return pd.DataFrame(columns=schema.keys())


def create_backup(file: str) -> None:
    """Tạo backup tự động trước khi ghi dữ liệu"""
    if not os.path.exists(file):
        return
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{os.path.basename(file)}_{timestamp}.bak")
    shutil.copy2(file, backup_file)
    
    # Giữ chỉ 10 backup gần nhất cho mỗi file
    basename = os.path.basename(file)
    backup_files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(basename)])
    if len(backup_files) > 10:
        for old_file in backup_files[:-10]:
            os.remove(os.path.join(BACKUP_DIR, old_file))


def save_data(df_data: pd.DataFrame, file: str) -> None:
    """Lưu dữ liệu với backup tự động"""
    # Tạo backup trước khi ghi
    create_backup(file)
    
    # Ghi dữ liệu an toàn với file tạm
    temp_file = f"{file}.tmp"
    try:
        df_data.to_csv(temp_file, index=False, encoding='utf-8-sig')
        os.replace(temp_file, file)
    except Exception as e:
        st.error(f"Lỗi khi lưu dữ liệu: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)


def reindex_sequential(df_data: pd.DataFrame, id_col: str) -> pd.DataFrame:
    df_data = df_data.reset_index(drop=True).copy()
    if id_col in df_data.columns:
        df_data[id_col] = pd.Series(range(1, len(df_data) + 1), dtype="int64")
    return df_data


def parse_ms_input(value: str) -> float:
    if not value:
        return 0.0
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def parse_money_input(value: str) -> float:
    if not value:
        return 0.0
    cleaned = re.sub(r"[^0-9.]", "", str(value))
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def next_id(df_data: pd.DataFrame, col: str) -> int:
    if df_data.empty:
        return 1
    return int(pd.to_numeric(df_data[col], errors="coerce").fillna(0).max() + 1)


def format_vnd(value: float) -> str:
    return f"{value:,.0f} VNĐ"


def generate_auto_title(pet_name, mutation, trait_str, ms_value, namestock):
    icons = {
        "gold": "👑",
        "diamond": "💎",
        "bloodrot": "🩸",
        "candy": "🍬",
        "divine": "✨",
        "lava": "🌋",
        "galaxy": "🌌",
        "yin-yang": "☯️",
        "radioactive": "☢️",
        "cursed": "😈",
        "rainbow": "🌈",
    }
    icon = icons.get(str(mutation).lower(), "🌟")
    t_str = f" [{trait_str}]" if (trait_str and str(trait_str).lower() != "none") else ""
    display_ms = f"{ms_value / 1000:.2f}B/s" if ms_value >= 1000 else f"{ms_value:.0f}M/s"
    ns_str = f" {namestock}" if namestock else ""
    if str(mutation).lower() == "normal" or not mutation:
        return f"🌸{pet_name} {display_ms}{t_str}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"
    return f"🌸{icon}{mutation} {pet_name} {display_ms}{t_str}{icon}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"


def get_name_options(db: pd.DataFrame, fallback: str = "None"):
    if db.empty:
        return [fallback]
    values = db["Name"].astype(str).str.strip()
    values = values[values != ""]
    return values.drop_duplicates().tolist() or [fallback]


def append_row(df_data: pd.DataFrame, row: dict, schema: dict) -> pd.DataFrame:
    updated = pd.concat([df_data, pd.DataFrame([row])], ignore_index=True)
    return normalize_dataframe(updated, schema)


def render_editable_inventory_table(
    data: pd.DataFrame,
    title: str,
    key_prefix: str,
    file: str,
    schema: dict,
    id_col: str,
    columns_order: list[str] | None = None,
):
    if data.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return

    view = normalize_dataframe(data.copy(), schema)
    if columns_order:
        cols = [c for c in columns_order if c in view.columns]
        view = view[cols]

    st.markdown(f"**{title}**")
    st.caption("✍️ Có thể sửa trực tiếp từng ô. Mỗi thay đổi sẽ tự lưu. Bạn cũng có thể thêm/xóa dòng ngay trong bảng.")

    edited = st.data_editor(
        view,
        key=f"editor_{key_prefix}",
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=[id_col] if id_col in view.columns else [],
    )

    before = reindex_sequential(normalize_dataframe(view, schema), id_col)
    after = reindex_sequential(normalize_dataframe(edited, schema), id_col)

    if "Auto Title" in after.columns:
        if id_col == "STT":
            after["Auto Title"] = after.apply(
                lambda r: generate_auto_title(
                    r["Tên Pet"],
                    r["Mutation"],
                    r["Số Trait"],
                    float(pd.to_numeric(r["M/s"], errors="coerce") if pd.notna(pd.to_numeric(r["M/s"], errors="coerce")) else 0),
                    r["NameStock"],
                ),
                axis=1,
            )
        elif id_col == "ID":
            after["Auto Title"] = after["Auto Title"].astype(str)

    if id_col == "ID":
        after["Lợi Nhuận"] = pd.to_numeric(after["Doanh Thu Tích Lũy"], errors="coerce").fillna(0) - pd.to_numeric(
            after["Giá Nhập Tổng"], errors="coerce"
        ).fillna(0)

    if not after.astype(str).equals(before.astype(str)):
        save_data(after, file)
        st.toast("✅ Đã tự động lưu thay đổi.", icon="💾")
        st.rerun()


# --- INITIALIZATION ---
df = load_data(DB_FILE, MAIN_SCHEMA)
bulk_df = load_data(BULK_FILE, BULK_SCHEMA)
bulk_history = load_data(BULK_HISTORY, HISTORY_SCHEMA)
pet_db = load_data(PET_LIST_FILE, LIST_SCHEMA)
ns_db = load_data(NS_LIST_FILE, LIST_SCHEMA)
trait_db = load_data(TRAIT_LIST_FILE, LIST_SCHEMA)

main_cols = list(MAIN_SCHEMA.keys())
bulk_cols = list(BULK_SCHEMA.keys())
hist_cols = list(HISTORY_SCHEMA.keys())

st.set_page_config(page_title="GhostlyStock Inventory", layout="wide")

st.markdown(
    """
<style>
:root {
    --card-bg: #111827;
    --muted: #9ca3af;
    --accent: #22c55e;
}

.block-container {padding-top: 2rem; padding-bottom: 2.5rem;}

.hero {
    background: linear-gradient(135deg, #111827 0%, #0f172a 50%, #1f2937 100%);
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

.hero h2 {margin: 0; font-size: 1.35rem;}
.hero p {margin: 0.25rem 0 0; color: var(--muted);}

div[data-testid="stMetric"] {
    background: var(--card-bg);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 0.45rem 0.6rem;
}

.stButton>button {
    width: 100%;
    border-radius: 8px;
    height: 2.55em;
    font-size: 0.92em;
    margin-top: 0.35em;
}

.stNumberInput, .stTextInput, .stSelectbox {margin-bottom: 0.45em;}

.stDataFrame {border-radius: 10px; border: 1px solid #2d3748;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h2>📦 GhostlyStock Management</h2>
        <p>Tối ưu quản lý kho pet lẻ/pack, giao diện gọn gàng hơn và dữ liệu an toàn hơn.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Danh mục")

    def manage_sidebar(label, db, file, col, icon="📁"):
        with st.expander(f"{icon} {label}", expanded=False):
            with st.form(key=f"form_add_{file}", clear_on_submit=True):
                c1, c2 = st.columns([3, 1])
                new = c1.text_input(f"Thêm {label}", key=f"add_{file}", label_visibility="collapsed", placeholder=f"Nhập {label} mới...")
                add_submit = c2.form_submit_button("➕", use_container_width=True)
            if add_submit:
                candidate = (new or "").strip()
                if not candidate:
                    st.warning("Tên không được để trống.")
                else:
                    db_values = db[col].astype(str).str.lower().tolist() if not db.empty else []
                    if candidate.lower() in db_values:
                        st.info("Tên đã tồn tại.")
                    else:
                        updated = append_row(db, {col: candidate}, {col: ""})
                        save_data(updated, file)
                        st.rerun()

            st.dataframe(db, use_container_width=True, hide_index=True, height=130)

            st.caption(f"Xóa nhanh 1 mục trong {label}")
            if not db.empty:
                with st.form(key=f"form_del_{file}"):
                    d1, d2 = st.columns([2.7, 1.3])
                    selected_item = d1.selectbox(
                        f"Chọn mục cần xóa ({label})",
                        db[col].astype(str).tolist(),
                        key=f"del_sel_{file}",
                        label_visibility="collapsed",
                    )
                    del_submit = d2.form_submit_button("🗑️ Xóa", use_container_width=True)
                if del_submit:
                    updated = db[db[col].astype(str) != str(selected_item)]
                    save_data(updated.reset_index(drop=True), file)
                    st.rerun()
            else:
                st.caption("Chưa có dữ liệu để xóa.")

            if st.button(f"🧹 Clear {label}", key=f"clr_{file}", use_container_width=True):
                save_data(pd.DataFrame(columns=[col]), file)
                st.rerun()

    manage_sidebar("Pet", pet_db, PET_LIST_FILE, "Name", icon="🐾")
    manage_sidebar("NameStock", ns_db, NS_LIST_FILE, "Name", icon="🏷️")
    manage_sidebar("Trait", trait_db, TRAIT_LIST_FILE, "Name", icon="🧬")

tab1, tab2, tab3, tab4 = st.tabs(["📦 Pet Lẻ", "📦 Pack", "📊 Thống kê", "⏳ Tồn lâu"])

with tab1:
    col_input, col_sale = st.columns([1.2, 1])

    with col_input:
        with st.container(border=True):
            st.subheader("📥 Nhập Pet Lẻ")
            pet_options = get_name_options(pet_db)
            trait_options = ["None"] + get_name_options(trait_db)
            ns_options = [""] + get_name_options(ns_db, fallback="")

            p_name = st.selectbox("Tên Pet", pet_options)

            r1c1, r1c2, r1c3 = st.columns([1, 1, 1])
            ms_raw = r1c1.text_input("Tốc độ (M/s)", placeholder="Ví dụ: 1000")
            p_mut = r1c2.selectbox("Mutation", mutation_options)
            p_trait = r1c3.selectbox("Số Trait", trait_options)

            r2c1, r2c2 = st.columns([1.5, 1])
            p_ns = r2c1.selectbox("NameStock", ns_options)
            p_cost_raw = r2c2.text_input(
                "Giá nhập (VNĐ)", 
                placeholder="Ví dụ: 150.000",
                help="Nhập giá theo dạng có dấu chấm (ví dụ: 150.000 = 150 nghìn VNĐ)"
            )

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                if st.button("💾 Lưu Pet Lẻ", type="primary", use_container_width=True, key="save_single"):
                    ms = parse_ms_input(ms_raw)
                    p_cost = parse_money_input(p_cost_raw)
                    if p_name == "None":
                        st.error("Bạn cần thêm Pet ở sidebar trước khi lưu.")
                    else:
                        stt = next_id(df, "STT")
                        row = {
                            "STT": stt,
                            "Tên Pet": p_name,
                            "M/s": ms,
                            "Mutation": p_mut,
                            "Số Trait": p_trait,
                            "NameStock": p_ns,
                            "Giá Nhập": p_cost,
                            "Giá Bán": 0.0,
                            "Lợi Nhuận": 0.0,
                            "Doanh Thu": 0.0,
                            "Ngày Nhập": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Ngày Bán": "-",
                            "Auto Title": generate_auto_title(p_name, p_mut, p_trait, ms, p_ns),
                            "Trạng Thái": "Còn hàng",
                        }
                        save_data(append_row(df, row, MAIN_SCHEMA), DB_FILE)
                        st.success("Đã lưu pet lẻ.")
                        st.rerun()
            with col_btn2:
                if st.button("🗑️ Xóa", use_container_width=True, key="clear_single"):
                    st.rerun()

    with col_sale:
        with st.container(border=True):
            st.subheader("💰 Bán Pet Lẻ")
            active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)]
            q = st.text_input("🔍 Tìm kiếm theo ID hoặc title", placeholder="VD: 15 hoặc Rainbow")

            if not active.empty:
                filt = active[
                    active["STT"].astype(str).str.contains(q, regex=False)
                    | active["Auto Title"].astype(str).str.contains(q, case=False, na=False, regex=False)
                ]

                if not filt.empty:
                    sel = st.selectbox(
                        "Chọn Pet cần bán", filt["STT"].astype(str) + " - " + filt["Auto Title"]
                    )
                    selected_stt = int(sel.split(" - ")[0])
                    selected_row = filt[filt["STT"] == selected_stt].iloc[0]
                    st.caption(
                        f"Pet: **{selected_row['Tên Pet']}** | Giá nhập: **{format_vnd(float(selected_row['Giá Nhập']))}**"
                    )

                    s_price_raw = st.text_input("Giá bán ($)", placeholder="Ví dụ: 5.5")
                    if st.button("✅ Xác nhận bán", type="primary", use_container_width=True, key="sell_single"):
                        s_price = parse_money_input(s_price_raw)
                        idx = df[df["STT"] == selected_stt].index[0]
                        rev_vnd = s_price * EXCHANGE_RATE
                        df.loc[idx, ["Giá Bán", "Doanh Thu", "Lợi Nhuận", "Ngày Bán", "Trạng Thái"]] = [
                            s_price,
                            rev_vnd,
                            rev_vnd - float(df.at[idx, "Giá Nhập"]),
                            datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Đã bán",
                        ]
                        save_data(normalize_dataframe(df, MAIN_SCHEMA), DB_FILE)
                        st.success("Bán pet thành công.")
                        st.rerun()
                else:
                    st.info("Không có kết quả phù hợp.")
            else:
                st.info("Không có pet lẻ nào để bán.")

    st.markdown("---")
    st.subheader("📋 Kho Pet Lẻ")
    render_editable_inventory_table(
        df[main_cols],
        "📋 Kho Pet Lẻ",
        "single_inventory",
        DB_FILE,
        MAIN_SCHEMA,
        "STT",
        main_cols,
    )

with tab2:
    col_pack_input, col_pack_sale = st.columns([1.2, 1])

    with col_pack_input:
        with st.container(border=True):
            st.subheader("📥 Nhập Pack Pet")
            b_pet = st.selectbox(
                "Tên Pet",
                get_name_options(pet_db),
                key="b1",
            )

            br1, br2, br3 = st.columns([1, 1, 1])
            b_qty = br1.number_input("Số lượng", min_value=1, max_value=500, value=10)
            b_ms = br2.text_input("Tốc độ (M/s)", key="b2", placeholder="Ví dụ: 1000")
            b_mut = br3.selectbox("Mutation", mutation_options, key="b3")

            b_ns = st.selectbox("NameStock", [""] + get_name_options(ns_db, fallback=""), key="b5")
            b_cost_raw = st.text_input(
                "Tổng giá nhập (VNĐ)", 
                key="b4", 
                placeholder="Ví dụ: 2.000.000",
                help="Nhập giá theo dạng có dấu chấm (ví dụ: 2.000.000 = 2 triệu VNĐ)"
            )

            col_pack_btn1, col_pack_btn2 = st.columns([3, 1])
            with col_pack_btn1:
                if st.button("💾 Lưu Pack", type="primary", use_container_width=True, key="save_pack"):
                    if b_pet == "None":
                        st.error("Bạn cần thêm Pet ở sidebar trước khi tạo pack.")
                    else:
                        bid = next_id(bulk_df, "ID")
                        ms_value = parse_ms_input(b_ms)
                        b_cost = parse_money_input(b_cost_raw)
                        row = {
                            "ID": bid,
                            "Tên Lô": f"Pack {b_pet} (x{int(b_qty)})",
                            "Số Lượng Gốc": int(b_qty),
                            "Còn Lại": int(b_qty),
                            "Ngày Nhập": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Giá Nhập Tổng": b_cost,
                            "Doanh Thu Tích Lũy": 0.0,
                            "Lợi Nhuận": -b_cost,
                            "Trạng Thái": "Available",
                            "Auto Title": generate_auto_title(b_pet, b_mut, "None", ms_value, b_ns),
                        }
                        save_data(append_row(bulk_df, row, BULK_SCHEMA), BULK_FILE)
                        st.success("Đã lưu pack.")
                        st.rerun()
            with col_pack_btn2:
                if st.button("🗑️ Xóa", use_container_width=True, key="clear_pack"):
                    st.rerun()

    with col_pack_sale:
        with st.container(border=True):
            st.subheader("💰 Bán Pack Pet")
            avail = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"]
            if not avail.empty:
                sel_b = st.selectbox("Chọn pack cần bán", avail["ID"].astype(str) + " - " + avail["Tên Lô"])
                target = avail[avail["ID"] == int(sel_b.split(" - ")[0])].iloc[0]
                st.caption(
                    f"Tên lô: **{target['Tên Lô']}** | Còn lại: **{int(target['Còn Lại'])}** | Giá nhập: **{format_vnd(float(target['Giá Nhập Tổng']))}**"
                )

                sr1, sr2 = st.columns([1, 1])
                with sr1:
                    s_qty = st.number_input("Số lượng bán", min_value=1, max_value=int(target["Còn Lại"]))
                with sr2:
                    s_prc_raw = st.text_input("Giá bán ($/pet)", placeholder="Ví dụ: 3.5")

                if st.button("✅ Bán Pack", type="primary", use_container_width=True, key="sell_pack"):
                    s_prc = parse_money_input(s_prc_raw)
                    idx = bulk_df[bulk_df["ID"] == target["ID"]].index[0]
                    rev_vnd = s_qty * s_prc * EXCHANGE_RATE
                    bulk_df.at[idx, "Còn Lại"] = max(0, float(bulk_df.at[idx, "Còn Lại"]) - float(s_qty))
                    bulk_df.at[idx, "Doanh Thu Tích Lũy"] = float(bulk_df.at[idx, "Doanh Thu Tích Lũy"]) + rev_vnd
                    bulk_df.at[idx, "Lợi Nhuận"] = float(bulk_df.at[idx, "Doanh Thu Tích Lũy"]) - float(bulk_df.at[idx, "Giá Nhập Tổng"])

                    if float(bulk_df.at[idx, "Còn Lại"]) <= 0:
                        bulk_df.at[idx, "Trạng Thái"] = "Sold Out"

                    base_qty = max(float(target["Số Lượng Gốc"]), 1.0)
                    base_unit_cost = float(target["Giá Nhập Tổng"]) / base_qty
                    history_row = {
                        "Ngày Bán": datetime.now().strftime("%d/%m/%Y"),
                        "Tên Lô": target["Tên Lô"],
                        "Số Lượng Bán": s_qty,
                        "Lợi Nhuận Giao Dịch": rev_vnd - (base_unit_cost * s_qty),
                        "Doanh Thu Giao Dịch": rev_vnd,
                    }

                    save_data(append_row(bulk_history, history_row, HISTORY_SCHEMA), BULK_HISTORY)
                    save_data(normalize_dataframe(bulk_df, BULK_SCHEMA), BULK_FILE)
                    st.success("Bán pack thành công.")
                    st.rerun()
            else:
                st.info("Không có pack pet nào để bán.")

    st.markdown("---")
    st.subheader("📦 Kho Pack Pet")
    render_editable_inventory_table(
        bulk_df[bulk_cols],
        "📦 Kho Pack Pet",
        "pack_inventory",
        BULK_FILE,
        BULK_SCHEMA,
        "ID",
        bulk_cols,
    )

with tab3:
    st.subheader("📊 Analytics")

    single_profit = float(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)]["Lợi Nhuận"].sum())
    pack_profit = float(bulk_df["Lợi Nhuận"].sum())
    net_profit = single_profit + pack_profit

    single_stock_count = int(df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)].shape[0])
    pack_stock_count = int(pd.to_numeric(bulk_df[bulk_df["Trạng Thái"] == "Available"]["Còn Lại"], errors="coerce").fillna(0).sum())
    total_stock = single_stock_count + pack_stock_count

    m1, m2 = st.columns(2)
    m1.metric("💵 Tổng lợi nhuận", format_vnd(net_profit))
    m2.metric("📦 Tổng stock", f"{total_stock:,}")

    st.markdown("---")
    st.subheader("💸 Dòng tiền ròng")
    total_cost_single = float(df["Giá Nhập"].sum()) if not df.empty else 0.0
    total_cost_pack = float(bulk_df["Giá Nhập Tổng"].sum()) if not bulk_df.empty else 0.0
    total_cost = total_cost_single + total_cost_pack

    total_revenue_single = float(df["Doanh Thu"].sum()) if not df.empty else 0.0
    total_revenue_pack = float(bulk_history["Doanh Thu Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    total_revenue = total_revenue_single + total_revenue_pack

    single_stock_value = float(df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)]["Giá Nhập"].sum())
    pack_stock_value = float(bulk_df[bulk_df["Trạng Thái"] == "Available"]["Giá Nhập Tổng"].sum())
    stock_value = single_stock_value + pack_stock_value

    cf1, cf2, cf3, cf4 = st.columns(4)
    cf1.metric("Vốn nhập", format_vnd(total_cost))
    cf2.metric("Doanh thu bán", format_vnd(total_revenue))
    cf3.metric("Lợi nhuận ròng", format_vnd(net_profit))
    cf4.metric("Tồn kho quy tiền", format_vnd(stock_value))

    def profit_text(v):
        v = float(v)
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:.3f}M"
        return f"{int(round(v)):,}".replace(",", "")

    single_day = df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)][["Ngày Bán", "Lợi Nhuận"]].copy()
    single_day.columns = ["Ngày", "Lợi Nhuận"]

    pack_day = bulk_history[["Ngày Bán", "Lợi Nhuận Giao Dịch"]].copy() if not bulk_history.empty else pd.DataFrame(columns=["Ngày Bán", "Lợi Nhuận Giao Dịch"])
    pack_day.columns = ["Ngày", "Lợi Nhuận"]

    profit_by_day = pd.concat([single_day, pack_day], ignore_index=True)

    if not profit_by_day.empty:
        parsed_dt = pd.to_datetime(profit_by_day["Ngày"], dayfirst=True, errors="coerce")
        parsed_dt = parsed_dt.dt.tz_localize("Asia/Ho_Chi_Minh", nonexistent="NaT", ambiguous="NaT")
        profit_by_day["NgàyDT"] = parsed_dt
        profit_by_day = profit_by_day.dropna(subset=["NgàyDT"])

        if not profit_by_day.empty:
            profit_by_day["Ngày"] = profit_by_day["NgàyDT"].dt.strftime("%d/%m/%Y")
            day_chart = (
                profit_by_day.groupby(["Ngày", "NgàyDT"], as_index=False)["Lợi Nhuận"]
                .sum()
                .sort_values("NgàyDT")
            )
            day_chart["Label"] = day_chart["Lợi Nhuận"].apply(profit_text)

            fig_profit_day = px.bar(day_chart, x="Ngày", y="Lợi Nhuận", title="Lợi nhuận theo ngày (Giờ VN)")
            fig_profit_day.update_traces(
                text=day_chart["Label"],
                textposition="outside",
                textfont=dict(size=16, color="#f9fafb", family="Source Sans Pro"),
                cliponaxis=False,
            )
            fig_profit_day.update_xaxes(type="category", title="Ngày")
            fig_profit_day.update_layout(
                margin=dict(l=10, r=10, t=60, b=10),
                yaxis_title="Lợi nhuận (VNĐ)",
            )
            st.plotly_chart(fig_profit_day, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu ngày hợp lệ để vẽ biểu đồ lợi nhuận theo ngày.")
    else:
        st.info("Chưa có dữ liệu lợi nhuận để vẽ biểu đồ theo ngày.")

    st.markdown("---")
    st.subheader("📈 Báo cáo quản lý dòng tiền & sản phẩm")

    # 1) Doanh thu theo kênh bán (Pet lẻ vs Pack)
    sold_single_rev = float(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)]["Doanh Thu"].sum())
    sold_pack_rev = float(bulk_history["Doanh Thu Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    rev_mix = pd.DataFrame(
        {
            "Kênh": ["Pet Lẻ", "Pack"],
            "Doanh Thu": [sold_single_rev, sold_pack_rev],
        }
    )

    # 2) Top sản phẩm lợi nhuận cao
    single_profit_by_pet = (
        df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)]
        .groupby("Tên Pet", as_index=False)["Lợi Nhuận"]
        .sum()
        .sort_values("Lợi Nhuận", ascending=False)
        .head(10)
    )

    pack_profit_by_name = (
        bulk_history.groupby("Tên Lô", as_index=False)["Lợi Nhuận Giao Dịch"]
        .sum()
        .sort_values("Lợi Nhuận Giao Dịch", ascending=False)
        .head(10)
        if not bulk_history.empty
        else pd.DataFrame(columns=["Tên Lô", "Lợi Nhuận Giao Dịch"])
    )

    # 3) Cơ cấu tồn kho theo trạng thái
    single_status = df.groupby("Trạng Thái", as_index=False).size().rename(columns={"size": "Số lượng"}) if not df.empty else pd.DataFrame(columns=["Trạng Thái", "Số lượng"])
    pack_status = bulk_df.groupby("Trạng Thái", as_index=False).size().rename(columns={"size": "Số lượng"}) if not bulk_df.empty else pd.DataFrame(columns=["Trạng Thái", "Số lượng"])

    c1, c2 = st.columns(2)
    with c1:
        if rev_mix["Doanh Thu"].sum() > 0:
            fig_mix = px.pie(rev_mix, names="Kênh", values="Doanh Thu", hole=0.45, title="Tỷ trọng doanh thu theo kênh")
            fig_mix.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_mix, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu doanh thu để vẽ tỷ trọng kênh bán.")

    with c2:
        if not single_status.empty or not pack_status.empty:
            status_mix = pd.DataFrame(
                {
                    "Nhóm": ["Pet Lẻ"] * len(single_status) + ["Pack"] * len(pack_status),
                    "Trạng Thái": single_status.get("Trạng Thái", pd.Series(dtype=str)).tolist()
                    + pack_status.get("Trạng Thái", pd.Series(dtype=str)).tolist(),
                    "Số lượng": single_status.get("Số lượng", pd.Series(dtype=float)).tolist()
                    + pack_status.get("Số lượng", pd.Series(dtype=float)).tolist(),
                }
            )
            fig_status = px.bar(
                status_mix,
                x="Nhóm",
                y="Số lượng",
                color="Trạng Thái",
                barmode="stack",
                title="Cơ cấu tồn kho theo trạng thái",
            )
            fig_status.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu tồn kho để phân tích trạng thái.")

    c3, c4 = st.columns(2)
    with c3:
        if not single_profit_by_pet.empty:
            fig_top_single = px.bar(
                single_profit_by_pet,
                x="Tên Pet",
                y="Lợi Nhuận",
                title="Top 10 Pet Lẻ theo lợi nhuận",
                text_auto=".2s",
            )
            fig_top_single.update_layout(margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Tên Pet", yaxis_title="Lợi nhuận (VNĐ)")
            st.plotly_chart(fig_top_single, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu pet lẻ đã bán để xếp hạng lợi nhuận.")

    with c4:
        if not pack_profit_by_name.empty:
            fig_top_pack = px.bar(
                pack_profit_by_name,
                x="Tên Lô",
                y="Lợi Nhuận Giao Dịch",
                title="Top 10 Pack theo lợi nhuận giao dịch",
                text_auto=".2s",
            )
            fig_top_pack.update_layout(margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Tên lô", yaxis_title="Lợi nhuận (VNĐ)")
            st.plotly_chart(fig_top_pack, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu giao dịch pack để xếp hạng lợi nhuận.")

with tab4:
    st.subheader("⏳ Danh sách item tồn quá lâu")
    age_threshold = st.slider("Số ngày tồn tối thiểu", min_value=1, max_value=90, value=7, step=1)

    # Pet lẻ còn hàng
    single_old = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False, regex=False)].copy()
    if not single_old.empty:
        single_old["Ngày Nhập DT"] = pd.to_datetime(single_old["Ngày Nhập"], dayfirst=True, errors="coerce")
        single_old["Ngày Tồn"] = (pd.Timestamp.now() - single_old["Ngày Nhập DT"]).dt.days
        single_old = single_old[single_old["Ngày Tồn"] >= age_threshold]
        single_old["Loại"] = "Pet Lẻ"
        single_old["Item"] = single_old["Tên Pet"].astype(str)
        single_old["Số lượng còn"] = 1
        single_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(single_old["Giá Nhập"], errors="coerce").fillna(0)
        single_old_view = single_old[["Loại", "Item", "Số lượng còn", "Ngày Nhập", "Ngày Tồn", "Giá trị vốn (VNĐ)", "Auto Title"]]
    else:
        single_old_view = pd.DataFrame(columns=["Loại", "Item", "Số lượng còn", "Ngày Nhập", "Ngày Tồn", "Giá trị vốn (VNĐ)", "Auto Title"])

    # Pack còn hàng
    pack_old = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"].copy()
    if not pack_old.empty:
        pack_old["Ngày Nhập DT"] = pd.to_datetime(pack_old["Ngày Nhập"], dayfirst=True, errors="coerce")
        pack_old["Ngày Tồn"] = (pd.Timestamp.now() - pack_old["Ngày Nhập DT"]).dt.days
        pack_old = pack_old[pack_old["Ngày Tồn"] >= age_threshold]
        pack_old["Loại"] = "Pack"
        pack_old["Item"] = pack_old["Tên Lô"].astype(str)
        pack_old["Số lượng còn"] = pd.to_numeric(pack_old["Còn Lại"], errors="coerce").fillna(0).astype(int)
        pack_old["Giá trị vốn (VNĐ)"] = pd.to_numeric(pack_old["Giá Nhập Tổng"], errors="coerce").fillna(0)
        pack_old_view = pack_old[["Loại", "Item", "Số lượng còn", "Ngày Nhập", "Ngày Tồn", "Giá trị vốn (VNĐ)", "Auto Title"]]
    else:
        pack_old_view = pd.DataFrame(columns=["Loại", "Item", "Số lượng còn", "Ngày Nhập", "Ngày Tồn", "Giá trị vốn (VNĐ)", "Auto Title"])

    old_items = pd.concat([single_old_view, pack_old_view], ignore_index=True)
    if old_items.empty:
        st.info("Không có item nào vượt ngưỡng tồn kho đã chọn.")
    else:
        old_items = old_items.sort_values(["Ngày Tồn", "Giá trị vốn (VNĐ)"], ascending=[False, False])
        st.dataframe(old_items, use_container_width=True, hide_index=True, height=380)
