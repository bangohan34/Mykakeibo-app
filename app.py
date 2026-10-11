import streamlit as st
import datetime
import pandas as pd
import gsheets
import ui_input
import ui_dashboard
import ui_history
import ui_subscription
import ui_tools

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰", layout="centered")

try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ==========================================
# セキュリティー: ログイン画面
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown("<h3 style='text-align: center; margin-top: 50px;'>🔒 家計簿ログイン</h3>", unsafe_allow_html=True)
    pwd = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン", use_container_width=True):
        if pwd == st.secrets.get("users", {}).get("password", "1234"): 
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    st.stop()

# --- データの準備 ---
st.session_state["target_sheet"] = st.secrets.get("users", {}).get("sheet", "")
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
today_jst = datetime.datetime.now(JST).date()
today_ts = pd.Timestamp.now(tz='Asia/Tokyo').normalize().tz_localize(None)

worksheet = gsheets.get_worksheet(st.session_state["target_sheet"])
df = gsheets.load_kakeibo_data(worksheet)
df_investment = gsheets.load_investment_data(worksheet)

if "subscriptions_auto_added" not in st.session_state:
    added_count = gsheets.auto_add_subscriptions(worksheet, df)
    if added_count > 0:
        st.toast(f"📅 今月のサブスク {added_count}件 を自動で家計簿に追加しました！", icon="✅")
        df = gsheets.load_kakeibo_data(worksheet)
    st.session_state["subscriptions_auto_added"] = True

# ==========================================
# ご指定の順番で画面を描画
# ==========================================
# 1. 収支入力
ui_input.render(worksheet, today_jst)

# 2. 入力履歴（アコーディオン）
ui_history.render(df, worksheet)
st.divider()

# 3. ダッシュボード（資産状況、収入、支出内訳、推移、光熱費）
yen_assets = ui_dashboard.render(df, df_investment, today_ts, worksheet)
st.divider()

# 4. その他管理ツール
ui_subscription.render(worksheet)
st.divider()
ui_tools.render_asset_check(worksheet, yen_assets, today_jst)
st.divider()
ui_tools.render_memo(worksheet)