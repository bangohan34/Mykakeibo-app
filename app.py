import streamlit as st
import datetime
import pandas as pd
import gsheets
import ui_input
import ui_dashboard
import ui_history
import ui_subscription
import ui_tools
import const as c

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰", layout="centered")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

try:
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ==========================================
# 元のURL認証方式（?u=...）に戻す
# ==========================================
query_params = st.query_params
url_user_id = query_params.get("u", None)
users_cfg = st.secrets.get("users", {})

if url_user_id not in users_cfg:
    st.error("⚠️ アクセス権限がありません。正しいURLからアクセスしてください。")
    st.stop()

st.session_state["target_sheet"] = users_cfg[url_user_id]["sheet"]

# --- データの準備 ---
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
# 画面の描画（ご指定の順番）
# ==========================================
# 1. 収支入力
ui_input.render(worksheet, today_jst)

# 2. 入力履歴（タップして編集可能なアコーディオン）
ui_history.render(df, worksheet)
st.divider()

# 3. ダッシュボード（資産状況、収入、支出内訳、推移、光熱費の順に ui_dashboard 側で並んでいます）
yen_assets = ui_dashboard.render(df, df_investment, today_ts, worksheet)
st.divider()

# 4. サブスク管理・資産確認・メモ
ui_subscription.render(worksheet)
st.divider()
ui_tools.render_asset_check(worksheet, yen_assets, today_jst)
st.divider()
ui_tools.render_memo(worksheet)