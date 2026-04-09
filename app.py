import json
import os
import re
import html
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
DB_FILE = "inventory.csv"
BULK_FILE = "bulk_inventory.csv"
BULK_HISTORY = "bulk_history.csv"
PET_LIST_FILE = "pet_list.csv"
NS_LIST_FILE = "namestock_list.csv"
TRAIT_LIST_FILE = "traits_list.csv"
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


def save_data(df_data: pd.DataFrame, file: str) -> None:
    df_data.to_csv(file, index=False)


def parse_ms_input(value: str) -> float:
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


def render_inventory_table_with_copy(data: pd.DataFrame, title: str, columns_order: list[str] | None = None):
    if data.empty:
        st.info("Không có dữ liệu để hiển thị.")
        return

    view = data.copy()
    if columns_order:
        cols = [c for c in columns_order if c in view.columns]
        view = view[cols]

    table_cols = list(view.columns)
    if "Auto Title" not in table_cols:
        st.dataframe(view, use_container_width=True, hide_index=True)
        return

    def _cell_value(row, col):
        value = row[col]
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    rows_html = []
    for _, row in view.iterrows():
        row_cells = []
        for col in table_cols:
            if col == "Auto Title":
                auto_title = _cell_value(row, col)
                auto_title_show = html.escape(auto_title)
                copy_payload = json.dumps(auto_title)
                row_cells.append(
                    f"""
                    <td style='padding:8px;border-bottom:1px solid #2d3748;min-width:300px;'>
                        <div style='display:flex;gap:8px;align-items:center;'>
                            <div style='flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;' title='{auto_title_show}'>{auto_title_show}</div>
                            <button onclick='navigator.clipboard.writeText({copy_payload})' style='border:1px solid #3b82f6;background:#1d4ed8;color:white;border-radius:6px;padding:4px 8px;cursor:pointer;'>📋</button>
                        </div>
                    </td>
                    """
                )
            else:
                cell_value = html.escape(_cell_value(row, col))
                row_cells.append(f"<td style='padding:8px;border-bottom:1px solid #2d3748;'>{cell_value}</td>")
        rows_html.append(f"<tr>{''.join(row_cells)}</tr>")

    header_html = "".join(
        [f"<th style='text-align:left;padding:8px;border-bottom:1px solid #2d3748;'>{html.escape(col)}</th>" for col in table_cols]
    )

    table_html = f"""
    <div style='border:1px solid #2d3748;border-radius:10px;overflow:hidden;margin-top:8px;'>
        <div style='padding:10px 12px;background:#111827;border-bottom:1px solid #2d3748;font-weight:600;'>{html.escape(title)}</div>
        <div style='max-height:260px;overflow:auto;'>
            <table style='width:max-content;min-width:100%;border-collapse:collapse;font-size:0.92em;'>
                <thead style='position:sticky;top:0;background:#0f172a;'>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
    </div>
    """
    components.html(table_html, height=340, scrolling=True)


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

.block-container {padding-top: 1.2rem; padding-bottom: 1.4rem;}

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
        <p>Tối ưu quản lý kho Pet/pack, giao diện gọn gàng hơn và dữ liệu an toàn hơn.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Danh mục")

    def manage_sidebar(label, db, file, col):
        with st.expander(f"{label}", expanded=False):
            c1, c2 = st.columns([3, 1])
            new = c1.text_input(f"Add {label}", key=f"add_{file}", label_visibility="collapsed")
            if c2.button("+", key=f"btn_{file}"):
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

            st.dataframe(db, use_container_width=True, hide_index=True, height=160)
            if st.button(f"Clear {label}", key=f"clr_{file}"):
                save_data(pd.DataFrame(columns=[col]), file)
                st.rerun()

    manage_sidebar("Pet", pet_db, PET_LIST_FILE, "Name")
    manage_sidebar("NameStock", ns_db, NS_LIST_FILE, "Name")
    manage_sidebar("Trait", trait_db, TRAIT_LIST_FILE, "Name")

tab1, tab2, tab3 = st.tabs(["📦 Pet", "📦 Pack", "📊 Thống kê"])

with tab1:
    col_input, col_sale = st.columns([1.2, 1])

    with col_input:
        with st.container(border=True):
            st.subheader("📥 Nhập Pet")
            pet_options = get_name_options(pet_db)
            trait_options = ["None"] + get_name_options(trait_db)
            ns_options = [""] + get_name_options(ns_db, fallback="")

            p_name = st.selectbox("Tên Pet", pet_options)

            r1c1, r1c2, r1c3 = st.columns([1, 1, 1])
            ms_raw = r1c1.text_input("Tốc độ (M/s)", "1000")
            p_mut = r1c2.selectbox("Mutation", mutation_options)
            p_trait = r1c3.selectbox("Số Trait", trait_options)

            r2c1, r2c2 = st.columns([1.5, 1])
            p_ns = r2c1.selectbox("NameStock", ns_options)
            p_cost = r2c2.number_input(
                "Giá nhập (VNĐ)", min_value=0.0, step=1000.0, format="%.0f"
            )

            if st.button("💾 Lưu Pet", type="primary", use_container_width=True, key="save_single"):
                ms = parse_ms_input(ms_raw)
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
                    st.success("Đã lưu Pet.")
                    st.rerun()

    with col_sale:
        with st.container(border=True):
            st.subheader("💰 Bán Pet")
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

                    s_price = st.number_input("Giá bán ($)", min_value=0.0, step=0.5)
                    if st.button("✅ Xác nhận bán", type="primary", use_container_width=True, key="sell_single"):
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
                st.info("Không có Pet nào để bán.")

    st.markdown("---")
    st.subheader("📋 Kho Pet")
    render_inventory_table_with_copy(df[main_cols], "📋 Kho Pet (Copy nằm trực tiếp trong ô Auto Title)", main_cols)

    with st.expander("⚙️ Quản lý Pet"):
        st.markdown("##### 🧹 Xóa Pet theo STT")
        del_s_col1, del_s_col2 = st.columns([2.2, 1])
        with del_s_col1:
            d_id = st.number_input("STT Pet cần xóa", min_value=0, step=1, key="delete_single_id")
        with del_s_col2:
            st.markdown("**Thao tác**")
            if st.button("🗑️ Xóa Pet", use_container_width=True, key="delete_single"):
                save_data(df[df["STT"].astype(int) != d_id], DB_FILE)
                st.rerun()

        st.markdown("---")
        st.markdown("##### ⚠️ Reset toàn bộ dữ liệu Pet")
        reset_s_col1, reset_s_col2 = st.columns([2.2, 1])
        with reset_s_col1:
            confirm_reset_single = st.checkbox("Xác nhận reset kho Pet", key="reset_single_check")
        with reset_s_col2:
            st.markdown("**Thực thi**")
            if confirm_reset_single and st.button(
                "⚠️ CLEAR KHO LẺ", type="secondary", use_container_width=True, key="reset_single_btn"
            ):
                save_data(pd.DataFrame(columns=main_cols), DB_FILE)
                st.rerun()

with tab2:
    col_pack_input, col_pack_sale = st.columns([1.2, 1])

    with col_pack_input:
        with st.container(border=True):
            st.subheader("📥 Nhập Pet")
            b_pet = st.selectbox(
                "Tên Pet",
                get_name_options(pet_db),
                key="b1",
            )

            br1, br2, br3 = st.columns([1, 1, 1])
            b_qty = br1.number_input("Số lượng", min_value=1, max_value=500, value=10)
            b_ms = br2.text_input("Tốc độ (M/s)", "1000", key="b2")
            b_mut = br3.selectbox("Mutation", mutation_options, key="b3")

            b_ns = st.selectbox("NameStock", [""] + get_name_options(ns_db, fallback=""), key="b5")
            b_cost = st.number_input(
                "Tổng giá nhập (VNĐ)", min_value=0.0, step=1000.0, format="%.0f", key="b4"
            )

            if st.button("💾 Lưu Pack", type="primary", use_container_width=True, key="save_pack"):
                if b_pet == "None":
                    st.error("Bạn cần thêm Pet ở sidebar trước khi tạo pack.")
                else:
                    bid = next_id(bulk_df, "ID")
                    ms_value = parse_ms_input(b_ms)
                    row = {
                        "ID": bid,
                        "Tên Lô": f"Pack {b_pet} (x{int(b_qty)})",
                        "Số Lượng Gốc": int(b_qty),
                        "Còn Lại": int(b_qty),
                        "Giá Nhập Tổng": b_cost,
                        "Doanh Thu Tích Lũy": 0.0,
                        "Lợi Nhuận": -b_cost,
                        "Trạng Thái": "Available",
                        "Auto Title": generate_auto_title(b_pet, b_mut, "None", ms_value, b_ns),
                    }
                    save_data(append_row(bulk_df, row, BULK_SCHEMA), BULK_FILE)
                    st.success("Đã lưu pack.")
                    st.rerun()

    with col_pack_sale:
        with st.container(border=True):
            st.subheader("💰 Bán Pet")
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
                    s_prc = st.number_input("Giá bán ($/pet)", min_value=0.0, step=0.5)

                if st.button("✅ Bán Pack", type="primary", use_container_width=True, key="sell_pack"):
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
                st.info("Không có Pet nào để bán.")

    st.markdown("---")
    st.subheader("📦 Kho Pet")
    render_inventory_table_with_copy(bulk_df[bulk_cols], "📦 Kho Pet (Copy nằm trực tiếp trong ô Auto Title)", bulk_cols)

    with st.expander("⚙️ Quản lý Pet"):
        st.markdown("##### 🧹 Xóa Pack theo ID")
        del_col1, del_col2 = st.columns([2.2, 1])
        with del_col1:
            p_del = st.number_input("ID Pack cần xóa", min_value=0, step=1, key="delete_pack_id")
        with del_col2:
            st.markdown("**Thao tác**")
            if st.button("🗑️ Xóa Pack", key="delete_pack", use_container_width=True):
                save_data(bulk_df[bulk_df["ID"].astype(int) != p_del], BULK_FILE)
                st.rerun()

        st.markdown("---")
        st.markdown("##### ⚠️ Reset toàn bộ dữ liệu Pack")
        reset_col1, reset_col2 = st.columns([2.2, 1])
        with reset_col1:
            confirm_reset_pack = st.checkbox("Xác nhận reset tất cả pack + lịch sử giao dịch", key="reset_pack_check")
        with reset_col2:
            st.markdown("**Thực thi**")
            if confirm_reset_pack and st.button(
                "⚠️ RESET ALL PACK", type="secondary", use_container_width=True, key="reset_pack_btn"
            ):
                save_data(pd.DataFrame(columns=bulk_cols), BULK_FILE)
                save_data(pd.DataFrame(columns=hist_cols), BULK_HISTORY)
                st.rerun()

with tab3:
    st.subheader("📊 Analytics")

    single_stock_value = float(df[df["Trạng Thái"] == "Còn hàng"]["Giá Nhập"].sum())
    pack_stock_value = float(bulk_df[bulk_df["Trạng Thái"] == "Available"]["Giá Nhập Tổng"].sum())
    stock_value = single_stock_value + pack_stock_value

    single_profit = float(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)]["Lợi Nhuận"].sum())
    pack_profit = float(bulk_df["Lợi Nhuận"].sum())
    net_profit = single_profit + pack_profit

    m1, m2, m3 = st.columns(3)
    m1.metric("Stock Value", format_vnd(stock_value))
    m2.metric("Single Profit", format_vnd(single_profit))
    m3.metric("Net Profit", format_vnd(net_profit))

    def draw_chart(data, x_col, y_col, title):
        if data.empty:
            st.info(f"Chưa có dữ liệu cho: {title}")
            return

        view = data.copy()
        view["Day"] = pd.to_datetime(view[x_col], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d")
        view = view.dropna(subset=["Day"])
        if view.empty:
            st.info(f"Không parse được ngày cho: {title}")
            return

        chart_data = view.groupby("Day", as_index=False)[y_col].sum()
        fig = px.bar(chart_data, x="Day", y=y_col, title=title, text_auto=".2s")
        fig.update_xaxes(type="category", title="Ngày")
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        draw_chart(
            df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)],
            "Ngày Bán",
            "Lợi Nhuận",
            "Lợi Nhuận Pet",
        )
    with col_chart2:
        draw_chart(bulk_history, "Ngày Bán", "Lợi Nhuận Giao Dịch", "Lợi Nhuận Pet")

    st.markdown("---")
    st.subheader("📈 Báo cáo quản lý dòng tiền & sản phẩm")

    # 1) Doanh thu theo kênh bán (Pet vs Pack)
    sold_single_rev = float(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False, regex=False)]["Doanh Thu"].sum())
    sold_pack_rev = float(bulk_history["Doanh Thu Giao Dịch"].sum()) if not bulk_history.empty else 0.0
    rev_mix = pd.DataFrame(
        {
            "Kênh": ["Pet", "Pack"],
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
                    "Nhóm": ["Pet"] * len(single_status) + ["Pack"] * len(pack_status),
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
                title="Top 10 Pet theo lợi nhuận",
                text_auto=".2s",
            )
            fig_top_single.update_layout(margin=dict(l=10, r=10, t=50, b=10), xaxis_title="Tên Pet", yaxis_title="Lợi nhuận (VNĐ)")
            st.plotly_chart(fig_top_single, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu Pet đã bán để xếp hạng lợi nhuận.")
