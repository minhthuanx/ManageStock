import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
from datetime import datetime
import streamlit.components.v1 as components
import json

# --- CONFIGURATION ---
DB_FILE = "inventory.csv"
BULK_FILE = "bulk_inventory.csv"
BULK_HISTORY = "bulk_history.csv"
PET_LIST_FILE = "pet_list.csv"
NS_LIST_FILE = "namestock_list.csv"
TRAIT_LIST_FILE = "traits_list.csv"
EXCHANGE_RATE = 20400

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df_loaded = pd.read_csv(file)
            if df_loaded.empty: return pd.DataFrame(columns=columns)
            df_loaded = df_loaded.dropna(how='all')
            for col in columns:
                if col not in df_loaded.columns: df_loaded[col] = 0.0
            return df_loaded
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# --- INITIALIZATION ---
main_cols = ["STT", "Tên Pet", "M/s", "Mutation", "Số Trait", "NameStock", "Giá Nhập", "Giá Bán", "Lợi Nhuận", "Doanh Thu", "Ngày Nhập", "Ngày Bán", "Auto Title", "Trạng Thái"]
bulk_cols = ["ID", "Tên Lô", "Số Lượng Gốc", "Còn Lại", "Giá Nhập Tổng", "Doanh Thu Tích Lũy", "Lợi Nhuận", "Trạng Thái", "Auto Title"]
hist_cols = ["Ngày Bán", "Tên Lô", "Số Lượng Bán", "Lợi Nhuận Giao Dịch", "Doanh Thu Giao Dịch"]

df = load_data(DB_FILE, main_cols)
bulk_df = load_data(BULK_FILE, bulk_cols)
bulk_history = load_data(BULK_HISTORY, hist_cols)
pet_db = load_data(PET_LIST_FILE, ["Name"])
ns_db = load_data(NS_LIST_FILE, ["Name"])
trait_db = load_data(TRAIT_LIST_FILE, ["Name"])

mutation_options = ["Normal", "Gold", "Diamond", "Bloodrot", "Candy", "Divine", "Lava", "Galaxy", "Yin-Yang", "Radioactive", "Cursed", "Rainbow"]

def generate_auto_title(pet_name, mutation, trait_str, ms_value, namestock):
    icons = {"gold": "👑", "diamond": "💎", "bloodrot": "🩸", "candy": "🍬", "divine": "✨", "lava": "🌋", "galaxy": "🌌", "yin-yang": "☯️", "radioactive": "☢️", "cursed": "🌋", "rainbow": "🌈"}
    icon = icons.get(str(mutation).lower(), "🌟")
    t_str = f" [{trait_str}]" if (trait_str and str(trait_str).lower() != "none") else ""
    display_ms = f"{ms_value/1000}B/s" if ms_value >= 1000 else f"{ms_value}M/s"
    ns_str = f" {namestock}" if namestock else ""
    if str(mutation).lower() == "normal" or not mutation: return f"🌸{pet_name} {display_ms}{t_str}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"
    return f"🌸{icon}{mutation} {pet_name} {display_ms}{t_str}{icon}🌸Cheapest🚛 Fast Delivery 🚛{ns_str}"

st.set_page_config(page_title="Inventory", layout="wide")
st.markdown("""
<style>
.stButton>button {width: 100%; border-radius: 5px; height: 2.2em; font-size: 0.9em;}
.stNumberInput, .stTextInput, .stSelectbox {margin-bottom: -8px;}
.stNumberInput>div>div>input, .stTextInput>div>div>input {font-size: 0.85em; padding: 0.4em;}
label {font-size: 0.8em !important; margin-bottom: 0.2em !important;}
.stCaption {font-size: 0.9em; margin-bottom: 0.5em;}
</style>
""", unsafe_allow_html=True)
st.title("📦 Management")

with st.sidebar:
    st.header("⚙️ Settings")
    def manage_sidebar(label, db, file, col):
        with st.expander(label):
            c1, c2 = st.columns([3, 1])
            new = c1.text_input(f"Add {label}", key=f"add_{file}", label_visibility="collapsed")
            if c2.button("+", key=f"btn_{file}") and new:
                if new not in db[col].values: save_data(pd.concat([db, pd.DataFrame([{col: new}])]), file); st.rerun()
            st.dataframe(db, use_container_width=True, hide_index=True, height=150)
            if st.button(f"Clear {label}", key=f"clr_{file}"): save_data(pd.DataFrame(columns=[col]), file); st.rerun()
    manage_sidebar("Pet", pet_db, PET_LIST_FILE, "Name")
    manage_sidebar("NameStock", ns_db, NS_LIST_FILE, "Name")
    manage_sidebar("Trait", trait_db, TRAIT_LIST_FILE, "Name")

tab1, tab2, tab3 = st.tabs(["📦 Single", "📦 Pack", "📊 Stats"])

with tab1:
    c_in, c_sl = st.columns([1.2, 1])
    with c_in:
        st.caption("📥 Input Single")
        p_name = st.selectbox("Pet", pet_db["Name"].values if not pet_db.empty else ["None"], label_visibility="collapsed")
        r1c1, r1c2, r1c3 = st.columns([1, 1, 1])
        ms_raw = r1c1.text_input("M/s", "1000", label_visibility="collapsed")
        p_mut = r1c2.selectbox("Mut", mutation_options, label_visibility="collapsed")
        p_trait = r1c3.selectbox("Trait", ["None"] + list(trait_db["Name"].values), label_visibility="collapsed")
        r2c1, r2c2, r2c3 = st.columns([1.5, 1, 0.8])
        p_ns = r2c1.selectbox("NameStock", [""] + list(ns_db["Name"].values), label_visibility="collapsed")
        p_cost = r2c2.number_input("Cost (VNĐ)", min_value=0.0, step=1000.0, format="%.0f", label_visibility="collapsed")
        if r2c3.button("💾 Lưu", type="primary", use_container_width=True):
            ms = float(re.sub(r'[^0-9.]', '', ms_raw)) if ms_raw else 0.0
            stt = int(df["STT"].max() + 1) if not df.empty else 1
            save_data(pd.concat([df, pd.DataFrame([{"STT": stt, "Tên Pet": p_name, "M/s": ms, "Mutation": p_mut, "Số Trait": p_trait, "NameStock": p_ns, "Giá Nhập": p_cost, "Giá Bán": 0.0, "Lợi Nhuận": 0.0, "Doanh Thu": 0.0, "Ngày Nhập": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ngày Bán": "-", "Auto Title": generate_auto_title(p_name, p_mut, p_trait, ms, p_ns), "Trạng Thái": "Còn hàng"}])]), DB_FILE); st.rerun()
    with c_sl:
        st.caption("💰 Sale Single")
        active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        q = st.text_input("🔍 Search", placeholder="ID/Name", label_visibility="collapsed")
        if not active.empty:
            filt = active[active["STT"].astype(str).str.contains(q) | active["Auto Title"].astype(str).str.contains(q, case=False)]
            if not filt.empty:
                sel = st.selectbox("Select Item", filt["STT"].astype(str) + " - " + filt["Auto Title"], label_visibility="collapsed")
                selected_stt = int(sel.split(" - ")[0])
                selected_row = filt[filt["STT"] == selected_stt]
                auto_title = selected_row["Auto Title"].values[0]
                components.html(f'<button style="width:100%;padding:0.3em;font-size:0.85em;" onclick="navigator.clipboard.writeText({json.dumps(auto_title)})">📋 Copy Title</button>', height=35)
                s_price = st.number_input("Price ($)", min_value=0.0, label_visibility="collapsed")
                if st.button("✅ Bán", type="primary", use_container_width=True):
                    idx = df[df["STT"] == int(sel.split(" - ")[0])].index[0]
                    rev = s_price * EXCHANGE_RATE
                    df.loc[idx, ["Giá Bán", "Doanh Thu", "Lợi Nhuận", "Ngày Bán", "Trạng Thái"]] = [s_price, rev, rev - float(df.at[idx, "Giá Nhập"]), datetime.now().strftime("%d/%m/%Y %H:%M"), "Đã bán"]
                    save_data(df, DB_FILE); st.rerun()

    st.dataframe(df, use_container_width=True, hide_index=True, height=250)

    d_col1, d_col2, d_col3 = st.columns([1.5, 1, 1.5])
    with d_col1: d_id = st.number_input("STT Delete", min_value=0, step=1, label_visibility="collapsed")
    with d_col2:
        if st.button("🗑️ Xóa", use_container_width=True):
            save_data(df[df["STT"].astype(int) != d_id], DB_FILE); st.rerun()
    with d_col3:
        if st.checkbox("🔄 Reset All?"):
            if st.button("⚠️ CLEAR KHO LẺ", type="secondary", use_container_width=True):
                save_data(pd.DataFrame(columns=main_cols), DB_FILE); st.rerun()

with tab2:
    pin, psl = st.columns([1.2, 1])
    with pin:
        st.caption("📥 Input Pack")
        b_pet = st.selectbox("Pet", pet_db["Name"].values if not pet_db.empty else ["None"], key="b1", label_visibility="collapsed")
        br1, br2, br3 = st.columns([1, 1, 1])
        b_qty = br1.number_input("Qty", 1, 500, 10, label_visibility="collapsed")
        b_ms = br2.text_input("M/s", "1000", key="b2", label_visibility="collapsed")
        b_mut = br3.selectbox("Mut", mutation_options, key="b3", label_visibility="collapsed")
        b_ns = st.selectbox("NameStock", [""] + list(ns_db["Name"].values), key="b5", label_visibility="collapsed")
        r_cost = st.columns([1.5, 0.8])
        with r_cost[0]: b_cost = st.number_input("Total Cost (VNĐ)", min_value=0.0, step=1000.0, format="%.0f", key="b4", label_visibility="collapsed")
        with r_cost[1]:
            if st.button("💾 Lưu", type="primary", use_container_width=True):
                bid = int(bulk_df["ID"].max() + 1) if not bulk_df.empty else 1
                save_data(pd.concat([bulk_df, pd.DataFrame([{"ID": bid, "Tên Lô": f"Pack {b_pet} (x{b_qty})", "Số Lượng Gốc": b_qty, "Còn Lại": b_qty, "Giá Nhập Tổng": b_cost, "Doanh Thu Tích Lũy": 0.0, "Lợi Nhuận": -b_cost, "Trạng Thái": "Available", "Auto Title": generate_auto_title(b_pet, b_mut, "None", float(b_ms), b_ns)}])]), BULK_FILE); st.rerun()
    with psl:
        st.caption("💰 Sale Pack")
        avail = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"]
        if not avail.empty:
            sel_b = st.selectbox("Select Pack", avail["ID"].astype(str) + " - " + avail["Tên Lô"], label_visibility="collapsed")
            target = avail[avail["ID"] == int(sel_b.split(" - ")[0])].iloc[0]
            auto_title_pack = target["Auto Title"]
            components.html(f'<button style="width:100%;padding:0.3em;font-size:0.85em;" onclick="navigator.clipboard.writeText({json.dumps(auto_title_pack)})">📋 Copy Title</button>', height=35)
            sr1, sr2 = st.columns([1, 1])
            with sr1: s_qty = st.number_input("Qty", 1, int(target["Còn Lại"]), label_visibility="collapsed")
            with sr2: s_prc = st.number_input("$/pet", 0.0, label_visibility="collapsed")
            if st.button("✅ Bán Pack", type="primary", use_container_width=True):
                idx = bulk_df[bulk_df["ID"] == target["ID"]].index[0]
                rev = s_qty * s_prc * EXCHANGE_RATE
                bulk_df.at[idx, "Còn Lại"] -= s_qty
                bulk_df.at[idx, "Doanh Thu Tích Lũy"] += rev
                bulk_df.at[idx, "Lợi Nhuận"] = bulk_df.at[idx, "Doanh Thu Tích Lũy"] - bulk_df.at[idx, "Giá Nhập Tổng"]
                if bulk_df.at[idx, "Còn Lại"] <= 0: bulk_df.at[idx, "Trạng Thái"] = "Sold Out"
                save_data(pd.concat([bulk_history, pd.DataFrame([{"Ngày Bán": datetime.now().strftime("%d/%m/%Y"), "Tên Lô": target["Tên Lô"], "Số Lượng Bán": s_qty, "Lợi Nhuận Giao Dịch": (rev - (target["Giá Nhập Tổng"]/target["Số Lượng Gốc"]*s_qty)), "Doanh Thu Giao Dịch": rev}])]), BULK_HISTORY)
                save_data(bulk_df, BULK_FILE); st.rerun()
    st.dataframe(bulk_df, use_container_width=True, hide_index=True, height=220)

    p_col1, p_col2, p_col3 = st.columns([1.5, 1, 1.5])
    with p_col1: p_del = st.number_input("ID Pack", min_value=0, step=1, label_visibility="collapsed")
    with p_col2:
        if st.button("🗑️ Xóa", key="p_del", use_container_width=True):
            save_data(bulk_df[bulk_df["ID"].astype(int) != p_del], BULK_FILE); st.rerun()
    with p_col3:
        if st.checkbox("🔄 Reset All?", key="p_reset"):
            if st.button("⚠️ RESET ALL PACK", type="secondary", use_container_width=True):
                save_data(pd.DataFrame(columns=bulk_cols), BULK_FILE); save_data(pd.DataFrame(columns=hist_cols), BULK_HISTORY); st.rerun()

with tab3:
    st.subheader("📊 Analytics")
    m1, m2 = st.columns(2)
    m1.metric("Stock Value", f'{(df[df["Trạng Thái"]=="Còn hàng"]["Giá Nhập"].sum() + bulk_df[bulk_df["Trạng Thái"]=="Available"]["Giá Nhập Tổng"].sum()):,.0f} VNĐ')
    m2.metric("Net Profit", f'{(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)]["Lợi Nhuận"].sum() + bulk_df["Lợi Nhuận"].sum()):,.0f} VNĐ')

    def draw_chart(data, x_col, y_col, title):
        if not data.empty:
            data = data.copy()
            data['Day'] = pd.to_datetime(data[x_col], dayfirst=True).dt.strftime('%Y-%m-%d')
            fig = px.bar(data.groupby('Day')[y_col].sum().reset_index(), x='Day', y=y_col, title=title, text_auto='.2s')
            fig.update_xaxes(type='category', title="Ngày")
            st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1: draw_chart(df[df["Trạng Thái"].astype(str).str.contains("Đã bán", na=False)], "Ngày Bán", "Lợi Nhuận", "Lợi Nhuận Lẻ")
    with c2: draw_chart(bulk_history, "Ngày Bán", "Lợi Nhuận Giao Dịch", "Lợi Nhuận Pack")
