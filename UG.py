import sqlite3
import pandas as pd
import streamlit as st
import datetime

# 預設 17 款專屬菜單清單
my_menu_data = [
    ("咖啡", "大吉摩卡咖啡", 150), ("咖啡", "大吉黑咖啡", 130), ("咖啡", "大吉特調拿鐵咖啡", 130),
    ("特製飲品", "大吉巧克力拿鐵", 150), ("特製飲品", "可可抹茶拿鐵", 150), ("特製飲品", "莓果蜜桃拿鐵咖啡", 130),
    ("茶飲", "大吉蜜香美人茶", 130), ("茶飲", "玫瑰蜜桃茶", 120), ("茶飲", "馥麗莓果茶", 120),
    ("清香昭和冰品", "清香昭和冰咖啡", 150), ("清香昭和冰品", "清香昭和冰可可", 150), ("清香昭和冰品", "清香昭和冰抹茶", 150),
    ("甜點", "昭和巧克力硬布丁", 120), ("甜點", "75%巧克力冰淇淋", 120), ("甜點", "巧克力瑞士捲切片", 80),
    ("甜點", "巧克力瑞士捲整條", 450), ("甜點", "乳酪巧克力切片", 80)
]

# === 1. 初始化資料庫 ===
def init_db():
    conn = sqlite3.connect("daji_cafe_v2.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, category TEXT, name TEXT UNIQUE, price INTEGER)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY, customer_name TEXT, order_id TEXT, time TEXT, 
            category TEXT, item TEXT, note TEXT, qty INTEGER, total INTEGER
        )
    """)
    conn.commit()
    conn.close()

def force_import_menu():
    conn = sqlite3.connect("daji_cafe_v2.db")
    cursor = conn.cursor()
    for cat, name, price in my_menu_data:
        try: cursor.execute("INSERT INTO menu (category, name, price) VALUES (?, ?, ?)", (cat, name, price))
        except sqlite3.IntegrityError: pass
    conn.commit()
    conn.close()

# === 2. 資料庫操作函數 ===
def get_menu():
    conn = sqlite3.connect("daji_cafe_v2.db")
    df = pd.read_sql_query("SELECT category, name, price FROM menu", conn)
    conn.close()
    return df

def manage_menu(action, category, name, price=0):
    conn = sqlite3.connect("daji_cafe_v2.db")
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

def add_orders_from_cart(customer_name, cart_list):
    conn = sqlite3.connect("daji_cafe_v2.db")
    cursor = conn.cursor()
    order_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in cart_list:
        cursor.execute("""
            INSERT INTO orders (customer_name, order_id, time, category, item, note, qty, total) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, order_id, now_time, item["category"], item["item"], item["note"], item["qty"], item["total"]))
    conn.commit()
    conn.close()

def get_sales_summary():
    conn = sqlite3.connect("daji_cafe_v2.db")
    df = pd.read_sql_query("SELECT customer_name, order_id, time, category, item, note, qty, total FROM orders ORDER BY id DESC", conn)
    conn.close()
    return df

def clear_sales_history():
    conn = sqlite3.connect("daji_cafe_v2.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()

# === 3. 主程式介面 ===
init_db()
st.set_page_config(layout="wide", page_title="大吉智慧點餐系統")
st.title("☕ 大吉智慧點餐與營業額系統")

if "multi_carts" not in st.session_state:
    st.session_state.multi_carts = {"客戶 1": [], "客戶 2": [], "客戶 3": []}

page = st.sidebar.radio("功能切換", ["🛒 多客戶點餐區", "📊 營業額報表", "⚙️ 菜單管理"])
menu_df = get_menu()

# --- 分頁 1：多客戶點餐區 ---
if page == "🛒 多客戶點餐區":
    st.header("🛍️ 櫃檯多客戶點餐 (接單掛帳)")
    col_cust1, col_cust2 = st.columns(2)
    with col_cust1:
        current_customer = st.selectbox("👤 請選擇要操作的客戶/桌號", list(st.session_state.multi_carts.keys()))
    with col_cust2:
        new_cust_name = st.text_input("➕ 建立新客戶/桌號名單")
        if st.button("確認建立") and new_cust_name:
            if new_cust_name not in st.session_state.multi_carts:
                st.session_state.multi_carts[new_cust_name] = []
                st.success(f"已建立：{new_cust_name}")
                st.rerun()

    st.markdown("---")
    if not menu_df.empty:
        col_select, col_cart = st.columns(2)
        with col_select:
            st.subheader(f"🔍 點餐至【{current_customer}】的購物車")
            categories = menu_df['category'].unique()
            selected_cat = st.selectbox("請選擇大分類", categories)
            filtered_menu = menu_df[menu_df['category'] == selected_cat]
            selected_item = st.selectbox("請選擇餐點", filtered_menu['name'])
            
            price = int(filtered_menu[filtered_menu['name'] == selected_item]['price'].values[0])
            st.info(f"💰 單價：{price} 元")
            
            if selected_cat in ["咖啡", "特製飲品", "茶飲"]:
                temp_option = st.radio("🌡️ 溫度調整", ["冰 (Ice)", "熱 (Hot)"], horizontal=True)
            elif selected_cat == "清香昭和冰品":
                temp_option = "固定冰"
                st.write("❄️ 溫度：固定冰")
            else: temp_option = "常溫"
            
            custom_note = st.text_input("📝 額外備註 (去冰/甜度/客製化)", placeholder="如：少冰微糖 / 不要鮮奶油")
            final_note = temp_option if not custom_note else f"{temp_option} | {custom_note}"
            qty = st.number_input("數量", min_value=1, value=1, step=1)
            item_total = price * qty
            st.markdown(f"**目前品項小計：`{item_total}` 元**")
            
            if st.button("➕ 加入購物車", type="secondary", use_container_width=True):
                st.session_state.multi_carts[current_customer].append({
                    "category": selected_cat, "item": selected_item, "note": final_note, "qty": qty, "price": price, "total": item_total
                })
                st.toast(f"已加入：{selected_item} ({final_note}) x {qty}")
                st.rerun()

        with col_cart:
            st.subheader(f"📋 【{current_customer}】目前購物車明細")
            customer_cart = st.session_state.multi_carts[current_customer]
            if customer_cart:
                st.markdown("---")
                grand_total = 0
                for idx, item in enumerate(customer_cart):
                    c_name, c_btn1, c_btn2, c_btn3 = st.columns([4.5, 1, 1, 1])
                    with c_name:
                        # 💥 核心修正：在價格式子前加上顯眼的綠色【 數量：X 份 】提示文字
                        st.markdown(f"**{item['item']}** ({item['note']})  \n`👉 數量：{item['qty']} 份`  \n`${item['price']} × {item['qty']} = ${item['total']} 元`")
                        grand_total += item['total']
                    with c_btn1:
                        if st.button("➕", key=f"plus_{idx}"):
                            st.session_state.multi_carts[current_customer][idx]['qty'] += 1
                            st.session_state.multi_carts[current_customer][idx]['total'] = st.session_state.multi_carts[current_customer][idx]['qty'] * st.session_state.multi_carts[current_customer][idx]['price']
                            st.rerun()
                    with c_btn2:
                        if st.button("➖", key=f"minus_{idx}"):
                            if st.session_state.multi_carts[current_customer][idx]['qty'] > 1:
                                st.session_state.multi_carts[current_customer][idx]['qty'] -= 1
                                st.session_state.multi_carts[current_customer][idx]['total'] = st.session_state.multi_carts[current_customer][idx]['qty'] * st.session_state.multi_carts[current_customer][idx]['price']
                                st.rerun()
                    with c_btn3:
                        if st.button("❌", key=f"del_item_{idx}"):
                            st.session_state.multi_carts[current_customer].pop(idx)
                            st.rerun()
                    st.markdown("<div style='margin: -15px 0px;'></div>", unsafe_allow_html=True)
                st.markdown(f"### 🔴 【{current_customer}】應收總金額：`$ {grand_total}` 元")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🧼 清空該客購物車", use_container_width=True):
                        st.session_state.multi_carts[current_customer] = []
                        st.rerun()
                with c2:
                    if st.button("✅ 該客確認結帳送出", type="primary", use_container_width=True):
                        add_orders_from_cart(current_customer, customer_cart)
                        st.success(f"🎉 {current_customer} 訂單已成功送出並計入營業額！")
                        st.session_state.multi_carts[current_customer] = []
                        st.rerun()
            else: st.write(f"【{current_customer}】目前沒有點任何東西。請從左側挑選。")
                
        st.markdown("---")
        st.subheader("👀 全場未結帳客戶明細快速查詢")
        for cust, items in st.session_state.multi_carts.items():
            if items:
                total_unpaid = sum(i["total"] for i in items)
                summary_text = "、".join([f"{i['item']}({i['note']}) x {i['qty']}" for i in items])
                st.markdown(f"🔸 **{cust}**（未結: `${total_unpaid}` 元）: {summary_text}")
    else:
        st.warning("⚠️ 系統偵測到目前資料庫內沒有任何餐點。")
        if st.button("⚡ 一鍵強制載入大吉原始菜單", type="primary", use_container_width=True):
            force_import_menu()
            st.success("🎉 17款大吉菜單已成功灌入新資料庫！請重新整理網頁。")
            st.rerun()

# --- 分頁 2：營業額報表 ---
elif page == "📊 營業額報表":
    st.header("📈 即時營業額統計")
    orders_df = get_sales_summary()
    if not orders_df.empty:
        total_sales = orders_df['total'].sum()
        st.metric(label="💰 累積總營業額", value=f"${total_sales} 元")
        excel_data = orders_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 導出營業額明細 (CSV/Excel)", data=excel_data, file_name=f"大吉營業額報表_{datetime.date.today()}.csv", mime="text/csv")
        st.write("📋 歷史點單明細紀錄：")
        st.dataframe(orders_df, column_config={"customer_name": "客戶/桌號", "order_id": "訂單編號", "time": "點餐時間", "category": "大分類", "item": "品項名稱", "note": "冷熱/備註", "qty": "數量", "total": "總計金額"}, hide_index=True, use_container_width=True)
        st.markdown("---")
        st.subheader("🚨 危險管理區")
        if st.button("🗑️ 清空所有歷史營業額紀錄"):
            clear_sales_history()
