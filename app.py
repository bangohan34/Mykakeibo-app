import streamlit as st
import const as c
import gsheets

# 各画面パーツの読み込み
import ui_input
import ui_dashboard
import ui_history
import ui_subscription
import ui_tools

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- ログイン ---
if "target_sheet" not in st.session_state:
    st.session_state["target_sheet"] = ""
if "current_user_name" not in st.session_state:
    st.session_state["current_user_name"] = ""

query_params = st.query_params
url_user_id = query_params.get("u", None)
users_cfg = st.secrets["users"]

if url_user_id in users_cfg:
    user_data = users_cfg[url_user_id]
    st.session_state["target_sheet"] = user_data["sheet"]
    st.session_state["current_user_name"] = user_data["name"]
else:
    st.error("⚠️ アクセス権限がありません。専用のURLからアクセスしてください。")
    st.stop()

# --- データの準備 ---
worksheet = gsheets.get_worksheet(st.session_state["target_sheet"])
df = gsheets.load_kakeibo_data(worksheet)
df_investment = gsheets.load_investment_data(worksheet)

# サブスクの自動追加
if "subscriptions_auto_added" not in st.session_state:
    added_count = gsheets.auto_add_subscriptions(worksheet, df)
    if added_count > 0:
        st.toast(f"📅 今月のサブスク {added_count}件 を自動で家計簿に追加しました！", icon="✅")
        df = gsheets.load_kakeibo_data(worksheet)
    st.session_state["subscriptions_auto_added"] = True

# ==========================================
# 画面の描画（各ファイルを順番に呼び出すだけ）
# ==========================================

# 1. 収支入力
ui_input.render(worksheet, url_user_id)
st.divider()

# 2. 資産表示・グラフ（戻り値として日本円資産額を受け取る）
yen_assets = ui_dashboard.render(df, df_investment, url_user_id)
st.divider()

# 3. 入力履歴と削除
ui_history.render(df, worksheet)
st.divider()

# 4. サブスク管理
ui_subscription.render(worksheet, url_user_id)

# 5. 資産確認（u1のみ表示）
if url_user_id == "u1":
    st.divider()
    ui_tools.render_asset_check(worksheet, yen_assets)

# 6. なんでもメモ
st.divider()
ui_tools.render_memo(worksheet)