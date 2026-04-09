import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
from datetime import datetime

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
st.markdown("""<style>.stButton>button {width: 100%; border-radius: 5px; height: 3em;} .stNumberInput, .stTextInput, .stSelectbox {margin-bottom: -10px;}</style>""", unsafe_allow_html=True)
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
    c_in, c_sl = st.columns(2)
    with c_in:
        st.caption("📥 Input Single")
        p_name = st.selectbox("Pet", pet_db["Name"].values if not pet_db.empty else ["None"])
        r1c1, r1c2, r1c3 = st.columns([1, 1, 1])
        ms_raw = r1c1.text_input("M/s", "1000")
        p_mut = r1c2.selectbox("Mutation", mutation_options)
        p_trait = r1c3.selectbox("Trait", ["None"] + list(trait_db["Name"].values))
        r2c1, r2c2 = st.columns([2, 1])
        p_ns = r2c1.selectbox("NameStock", [""] + list(ns_db["Name"].values))
        p_cost = r2c2.number_input("Cost (VNĐ)", min_value=0.0, step=1000.0, format="%.0f")
        if st.button("Lưu lẻ", type="primary"):
            ms = float(re.sub(r'[^0-9.]', '', ms_raw)) if ms_raw else 0.0
            stt = int(df["STT"].max() + 1) if not df.empty else 1
            save_data(pd.concat([df, pd.DataFrame([{"STT": stt, "Tên Pet": p_name, "M/s": ms, "Mutation": p_mut, "Số Trait": p_trait, "NameStock": p_ns, "Giá Nhập": p_cost, "Giá Bán": 0.0, "Lợi Nhuận": 0.0, "Doanh Thu": 0.0, "Ngày Nhập": datetime.now().strftime("%d/%m/%Y %H:%M"), "Ngày Bán": "-", "Auto Title": generate_auto_title(p_name, p_mut, p_trait, ms, p_ns), "Trạng Thái": "Còn hàng"}])]), DB_FILE); st.rerun()
    with c_sl:
        st.caption("💰 Sale Single")
        active = df[df["Trạng Thái"].astype(str).str.contains("Còn hàng", na=False)]
        q = st.text_input("🔍 Search ID/Name", placeholder="Quick search...")
        if not active.empty:
            filt = active[active["STT"].astype(str).str.contains(q) | active["Auto Title"].astype(str).str.contains(q, case=False)]
            if not filt.empty:
                sel = st.selectbox("Select Item", filt["STT"].astype(str) + " - " + filt["Auto Title"])
                sc1, sc2 = st.columns([1, 1])
                s_price = sc1.number_input("Price ($)", min_value=0.0)
                if sc2.button("Xác nhận bán", type="primary"):
                    idx = df[df["STT"] == int(sel.split(" - ")[0])].index[0]
                    rev = s_price * EXCHANGE_RATE
                    df.loc[idx, ["Giá Bán", "Doanh Thu", "Lợi Nhuận", "Ngày Bán", "Trạng Thái"]] = [s_price, rev, rev - float(df.at[idx, "Giá Nhập"]), datetime.now().strftime("%d/%m/%Y %H:%M"), "Đã bán"]
                    save_data(df, DB_FILE); st.rerun()

    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    # FIXED DELETE SECTION SINGLE
    del_row1_col1, del_row1_col2 = st.columns([1, 1])
    with del_row1_col1: d_id = st.number_input("STT to Delete", min_value=0, step=1, label_visibility="collapsed")
    with del_row1_col2: 
        if st.button("Xóa STT"): 
            save_data(df[df["STT"].astype(int) != d_id], DB_FILE); st.rerun()
    
    del_row2_col1, del_row2_col2 = st.columns([1, 1])
    with del_row2_col1: confirm_reset = st.checkbox("Reset All Single")
    with del_row2_col2:
        if confirm_reset and st.button("CLEAR KHO LẺ", type="secondary"):
            save_data(pd.DataFrame(columns=main_cols), DB_FILE); st.rerun()

with tab2:
    pin, psl = st.columns(2)
    with pin:
        st.caption("📥 Input Pack")
        b_pet = st.selectbox("Pet", pet_db["Name"].values if not pet_db.empty else ["None"], key="b1")
        br1, br2, br3 = st.columns([1, 1, 1])
        b_qty = br1.number_input("Qty", 1, 500, 10)
        b_ms = br2.text_input("M/s", "1000", key="b2")
        b_mut = br3.selectbox("Mut", mutation_options, key="b3")
        b_cost = st.number_input("Total Cost (VNĐ)", min_value=0.0, step=1000.0, format="%.0f", key="b4")
        if st.button("Lưu Pack", type="primary"):
            bid = int(bulk_df["ID"].max() + 1) if not bulk_df.empty else 1
            save_data(pd.concat([bulk_df, pd.DataFrame([{"ID": bid, "Tên Lô": f"Pack {b_pet} (x{b_qty})", "Số Lượng Gốc": b_qty, "Còn Lại": b_qty, "Giá Nhập Tổng": b_cost, "Doanh Thu Tích Lũy": 0.0, "Lợi Nhuận": -b_cost, "Trạng Thái": "Available", "Auto Title": generate_auto_title(b_pet, b_mut, "None", float(b_ms), "")}])]), BULK_FILE); st.rerun()
    with psl:
        st.caption("💰 Sale Pack")
        avail = bulk_df[bulk_df["Trạng Thái"].astype(str) == "Available"]
        if not avail.empty:
            sel_b = st.selectbox("Select Pack", avail["ID"].astype(str) + " - " + avail["Tên Lô"])
            target = avail[avail["ID"] == int(sel_b.split(" - ")[0])].iloc[0]
            sr1, sr2, sr3 = st.columns([1, 1, 1])
            s_qty = sr1.number_input("Qty Sell", 1, int(target["Còn Lại"]))
            s_prc = sr2.number_input("$/pet", 0.0)
            if sr3.button("Bán Pack", type="primary"):
                idx = bulk_df[bulk_df["ID"] == target["ID"]].index[0]
                rev = s_qty * s_prc * EXCHANGE_RATE
                bulk_df.at[idx, "Còn Lại"] -= s_qty
                bulk_df.at[idx, "Doanh Thu Tích Lũy"] += rev
                bulk_df.at[idx, "Lợi Nhuận"] = bulk_df.at[idx, "Doanh Thu Tích Lũy"] - bulk_df.at[idx, "Giá Nhập Tổng"]
                if bulk_df.at[idx, "Còn Lại"] <= 0: bulk_df.at[idx, "Trạng Thái"] = "Sold Out"
                save_data(pd.concat([bulk_history, pd.DataFrame([{"Ngày Bán": datetime.now().strftime("%d/%m/%Y"), "Tên Lô": target["Tên Lô"], "Số Lượng Bán": s_qty, "Lợi Nhuận Giao Dịch": (rev - (target["Giá Nhập Tổng"]/target["Số Lượng Gốc"]*s_qty)), "Doanh Thu Giao Dịch": rev}])]), BULK_HISTORY)
                save_data(bulk_df, BULK_FILE); st.rerun()
    st.dataframe(bulk_df, use_container_width=True, hide_index=True, height=250)

    # FIXED DELETE SECTION PACK
    p_del_row1_col1, p_del_row1_col2 = st.columns([1, 1])
    with p_del_row1_col1: p_del = st.number_input("ID Pack", min_value=0, step=1, label_visibility="collapsed")
    with p_del_row1_col2:
        if st.button("Xóa Pack"): save_data(bulk_df[bulk_df["ID"].astype(int) != p_del], BULK_FILE); st.rerun()

    p_del_row2_col1, p_del_row2_col2 = st.columns([1, 1])
    with p_del_row2_col1: confirm_p_reset = st.checkbox("Reset Pack")
    with p_del_row2_col2:
        if confirm_p_reset and st.button("RESET ALL PACK", type="secondary"):
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
