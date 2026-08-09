import streamlit as st
import datetime
import pandas as pd
import const as c
import gsheets

# 切り出した画面パーツを読み込む
import ui_input
import ui_dashboard
import ui_history
import ui_subscription
import ui_tools

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- ログイン ---
query_params = st.query_params
url_user_id = query_params.get("u", None)
users_cfg = st.secrets.get("users", {})

if url_user_id not in users_cfg:
    st.error("⚠️ アクセス権限がありません。正しいURLからアクセスしてください。")
    st.stop()

st.session_state["target_sheet"] = users_cfg[url_user_id]["sheet"]

# --- データの準備 (JSTを厳密に適用) ---
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
# 画面の描画（各ファイルを順番に呼び出す）
# ==========================================

ui_input.render(worksheet, today_jst)
st.divider()

# ★ 修正: キャッシュの保存/読込のために worksheet を引数に追加
yen_assets = ui_dashboard.render(df, df_investment, today_ts, worksheet)
st.divider()

ui_history.render(df, worksheet)
st.divider()

ui_subscription.render(worksheet)
st.divider()

ui_tools.render_asset_check(worksheet, yen_assets, today_jst)
st.divider()

ui_tools.render_memo(worksheet)