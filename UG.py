import sqlite3
import pandas as pd
import streamlit as st
import datetime

# 預設 17 款專屬菜單清單
my_menu_data = [
    ("咖啡", "大吉摩卡咖啡", 150),
    ("咖啡", "大吉黑咖啡", 130),
    ("咖啡", "大吉特調拿鐵咖啡", 130),
    ("特製飲品", "大吉巧克力拿鐵", 150),
    ("特製飲品", "可可抹茶拿鐵", 150),
    ("特製飲品", "莓果蜜桃拿鐵咖啡", 130),
    ("茶飲", "大吉蜜香美人茶", 130),
    ("茶飲", "玫瑰蜜桃茶", 120),
    ("茶飲", "馥麗莓果茶", 120),
    ("清香昭和冰品", "清香昭和冰咖啡", 150),
    ("清香昭和冰品", "清香昭和冰可可", 150),
    ("清香昭和冰品", "清香昭和冰抹茶", 150),
    ("甜點", "昭和巧克力硬布丁", 120),
    ("甜點", "75%巧克力冰淇淋", 120),
    ("甜點", "巧克力瑞士捲切片", 80),
    ("甜點", "巧克力瑞士捲整條", 450),
    ("甜點", "乳酪巧克力切片", 80)
]

# === 1. 初始化資料庫 ===
def init_db():
    conn = sqlite3.connect("daji_cafe.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY, 
            category TEXT,
            name TEXT UNIQUE, 
            price INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY, 
            time TEXT, 
            category TEXT,
            item TEXT, 
            qty INTEGER, 
            total INTEGER
        )
    """)
    conn.commit()
    conn.close()

# 強制匯入菜單函數
def force_import_menu():
    conn = sqlite3.connect("daji_cafe.db")
    cursor = conn.cursor()
    for cat, name, price in my_menu_data:
        try:
            cursor.execute("INSERT INTO menu (category, name, price) VALUES (?, ?, ?)", (cat, name, price))
        except sqlite3.IntegrityError:
            pass  # 如果重複了就跳過
    conn.commit()
    conn.close()

# === 2. 函數：資料庫操作 ===
def get_menu():
    conn = sqlite3.connect("daji_cafe.db")
    df = pd.read_sql_query("SELECT category, name, price FROM menu", conn)
    conn.close()
    return df

def manage_menu(action, category, name, price=0):
    conn = sqlite3.connect("daji_cafe.db")
    cursor = conn.cursor()
    if action == "add":
        try:
            cursor.execute("INSERT INTO menu (category, name, price) VALUES (?, ?, ?)", (category, name, price))
            conn.commit()
        except: pass
    elif action == "del":
        cursor.execute("DELETE FROM menu WHERE name = ?", (name,))
        conn.commit()
    conn.close()

def add_order(category, item, qty, total):
    conn = sqlite3.connect("daji_cafe.db")
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO orders (time, category, item, qty, total) VALUES (?, ?, ?, ?, ?)", (now, category, item, qty, total))
    conn.commit()
    conn.close()

def get_sales_summary():
    conn = sqlite3.connect("daji_cafe.db")
    df = pd.read_sql_query("SELECT time, category, item, qty, total FROM orders ORDER BY id DESC", conn)
    conn.close()
    return df

# === 3. 主程式介面 (Streamlit) ===
init_db()
st.set_page_config(layout="wide")
st.title("☕ 大吉智慧點餐與營業額系統")

page = st.sidebar.radio("功能切換", ["🛒 點餐區", "📊 營業額報表", "⚙️ 菜單管理"])
menu_df = get_menu()

# --- 分頁 1：點餐區 ---
if page == "🛒 點餐區":
    st.header("🛍️ 櫃檯點餐")
    if not menu_df.empty:
        categories = menu_df['category'].unique()
        selected_cat = st.selectbox("請選擇大分類", categories)
        
        filtered_menu = menu_df[menu_df['category'] == selected_cat]
        selected_item = st.selectbox("請選擇餐點", filtered_menu['name'])
        
        price = filtered_menu[filtered_menu['name'] == selected_item]['price'].values[0]
        st.write(f"💰 單價：{price} 元")
        
        qty = st.number_input("數量", min_value=1, value=1, step=1)
        total_price = int(price * qty)
        st.subheader(f"總計金額：{total_price} 元")
        
        if st.button("確認結帳送出", type="primary"):
            add_order(selected_cat, selected_item, qty, total_price)
            st.success(f"✅ 點餐成功！已存入資料庫：{selected_item} x {qty}")
    else:
        st.warning("目前沒有餐點。請切換到「⚙️ 菜單管理」並點擊【💡 一鍵強制載入大吉菜單】按鈕。")

# --- 分頁 2：營業額報表 ---
elif page == "📊 營業額報表":
    st.header("📈 即時營業額統計")
    orders_df = get_sales_summary()
    
    if not orders_df.empty:
        total_sales = orders_df['total'].sum()
        st.metric(label="💰 累積總營業額", value=f"${total_sales} 元")
        
        st.write("📋 歷史點單紀錄：")
        st.dataframe(
            orders_df,
            column_config={
                "time": "點餐時間", "category": "大分類", "item": "品項名稱", "qty": "數量", "total": "總計金額"
            },
            use_container_width=True
        )
    else:
        st.info("目前尚無任何點餐結帳紀錄。")

# --- 分頁 3：菜單管理 ---
elif page == "⚙️ 菜單管理":
    st.header("⚙️ 菜單與大分類管理")
    
    # 💥 一鍵載入按鈕放置在最顯眼處
    st.info("💡 如果系統剛安裝好，菜單清單是空的，請點擊下方按鈕自動匯入 17 款專屬菜單：")
    if st.button("⚡ 一鍵強制載入大吉原始菜單", type="secondary"):
        force_import_menu()
        st.success("🎉 17款大吉菜單已成功灌入資料庫！")
        st.rerun()
    st.markdown("---")

    st.subheader("➕ 手動新增新品項")
    with st.form("add_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_cat = st.text_input("大分類名稱 (如: 咖啡、甜點)")
        with col2:
            new_name = st.text_input("餐點名稱")
        with col3:
            new_price = st.number_input("價格 (元)", min_value=0, value=0, step=5)
            
        if st.form_submit_button("確認新增餐點"):
            if new_cat and new_name:
                manage_menu("add", new_cat, new_name, new_price)
                st.success(f"成功新增：[{new_cat}] {new_name}")
                st.rerun()
    
    st.subheader("❌ 刪除餐點")
    if not menu_df.empty:
        del_name = st.selectbox("選擇要刪除的餐點", ["請選擇..."] + list(menu_df['name']))
        if st.button("確認刪除") and del_name != "請選擇...":
            manage_menu("del", "", del_name)
            st.success(f"已成功刪除餐點：{del_name}")
            st.rerun()
    
    st.subheader("📋 目前現有菜單一覽")
    if not menu_df.empty:
        st.dataframe(
            menu_df.sort_values(by="category"),
            column_config={"category": "大分類", "name": "餐點名稱", "price": "單價"},
            use_container_width=True
        )
