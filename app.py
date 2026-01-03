import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
import pandas as pd
import requests

# --- 設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /*タイトル上の余白を消す*/
            .block-container {
                padding-top: 1rem;
            }
            /* 数値入力の＋－ボタンを消す */
            [data-testid="stNumberInput"] button {
                display: none;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
SPREADSHEET_NAME = 'MyKakeibo'
EXPENSE_CATEGORIES = ['食費', '交通費', '日用品', '趣味', '交際費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','臨時収入','その他']

# --- 認証と接続 ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# キャッシュを使って認証を高速化
def get_worksheet():
    try:
        # A. Streamlit Cloud (本番)
        if "gcp_service_account" in st.secrets:
            secret_val = st.secrets["gcp_service_account"]
            # データが「文字」ならJSON変換、「辞書」ならそのまま使う
            if isinstance(secret_val, str):
                key_dict = json.loads(secret_val)
            else:
                key_dict = dict(secret_val)
            # 改行コードの修正
            if "private_key" in key_dict:
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            credentials = Credentials.from_service_account_info(key_dict, scopes=scopes)
        # B. ローカル (開発用)
        else:
            credentials = Credentials.from_service_account_file('secrets.json', scopes=scopes)
        # ログインして、スプレッドシートを開く
        gc = gspread.authorize(credentials)
        sh = gc.open(SPREADSHEET_NAME)
        return sh.sheet1
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()
worksheet = get_worksheet()

# --- 関数 ---
#データ読み込み
def load_data():
    all_rows = worksheet.get_all_values()
    columns=['日付','区分','カテゴリー','金額','メモ']
    if len(all_rows) < 2:
        return pd.DataFrame(columns=columns)
    fixed_rows = [row[:5] for row in all_rows]
    if fixed_rows[0][0] =='日付':
        data = fixed_rows[1:]
    else:
        data = fixed_rows
    df = pd.DataFrame(data, columns=columns)
    # 金額を数値に変換
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    return df

# 仮想通貨データの読み込み
def load_crypto_data():
    raw_data = worksheet.get('I:J')
    if len(raw_data) < 2:
        return pd.DataFrame(columns=['銘柄','保有量'])
    df_crypto = pd.DataFrame(raw_data[1:],columns=['銘柄','保有量'])
    df_crypto['保有量'] = pd.to_numeric(df_crypto['保有量'], errors='coerce').fillna(0.0)
    return df_crypto

# 仮想通貨データの保存
def save_crypto_data(df_crypto):
    data_to_save = [df_crypto.columns.tolist()] + df_crypto.values.tolist()
    worksheet.batch_clear(['I:J'])
    worksheet.update('I1', data_to_save)

# 仮想通貨の現在価格の取得
CRYPTO_ID_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'XRP': 'ripple',
    'PI': 'pi-network',  # PiはIOU価格（先物的な価格）を取得
    'IOST': 'iostoken'
}
@st.cache_data(ttl=600) # 10分間（600秒）キャッシュする（API制限対策）
def get_crypto_prices(symbols):
    # シンボル(BTC)をID(bitcoin)に変換
    ids = [CRYPTO_ID_MAP.get(s.upper(), s.lower()) for s in symbols]
    ids_str = ",".join(ids)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ids_str,
        'vs_currencies': 'jpy'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        # 使いやすい辞書形式 { 'BTC': 12000000, 'PI': 5000 } に変換して返す
        prices = {}
        for sym in symbols:
            c_id = CRYPTO_ID_MAP.get(sym.upper(), sym.lower())
            if c_id in data:
                prices[sym] = data[c_id]['jpy']
            else:
                prices[sym] = 0 # 取得できなかったら0
        return prices
    except Exception as e:
        # エラー時は空の辞書を返す（アプリを止めないため）
        return {}

# --- アプリ画面 ---
st.title('マイ家計簿')

df = load_data()

# --- 資産合計表示 ---
if not df.empty:
    df['日付_dt'] = pd.to_datetime(df['日付'])
    total_income = df[df['区分'] == '収入']['金額'].sum()
    total_expense = df[df['区分'] == '支出']['金額'].sum()
    yen_assets = total_income - total_expense
else:
    yen_assets = 0
# 仮想通貨の表示
df_crypto = load_crypto_data()
crypto_total_val = 0 
if not df_crypto.empty:
    # 現在価格を取得
    symbols = df_crypto['銘柄'].tolist()
    current_prices = get_crypto_prices(symbols)
    # データフレームに価格情報を結合
    # map関数を使って、銘柄に対応する価格を列に追加
    df_crypto['現在レート'] = df_crypto['銘柄'].map(current_prices).fillna(0)
    df_crypto['評価額(円)'] = df_crypto['保有量'] * df_crypto['現在レート']
    # 合計を計算
    crypto_total_val = df_crypto['評価額(円)'].sum()
# 総合計を表示（円 + 仮想通貨）
total_all_assets = yen_assets + crypto_total_val
st.metric(
    label="💰 総資産（円＋仮想通貨）", 
    value=f"￥{int(total_all_assets):,}",
    delta=f"うち仮想通貨: ￥{int(crypto_total_val):,}"
)
# 仮想通貨の内訳リストを表示
if not df_crypto.empty:
    st.subheader("仮想通貨内訳")
    display_df = df_crypto.copy()
    display_df['保有量'] = display_df['保有量'].apply(lambda x: f"{x:.4f}")
    display_df['現在レート'] = display_df['現在レート'].apply(lambda x: f"¥{x:,.0f}")
    display_df['評価額(円)'] = display_df['評価額(円)'].apply(lambda x: f"¥{x:,.0f}")
    st.table(display_df)
else:
    st.info("仮想通貨の登録はまだありません。")

# 入力フォーム
st.divider()
balance_type = st.radio("区分",["支出","収入","資産移動"], horizontal=True)
with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', datetime.date.today())
    # 資産移動
    if balance_type == "資産移動":
        st.caption("資産を移動します")
        col1, col2 = st.columns(2)
        with col1:
            crypto_name = st.text_input("銘柄名")
        with col2:
            crypto_amount = st.number_input("増える量", min_value=0.0, step=0.0001, format="%.8f")
        # 支払う日本円
        amount = st.number_input('支払った日本円', min_value=0, step=1, help="家計簿には「支出」として記録されます")
        memo = st.text_input('メモ', value=f"{crypto_name}購入")
        # 家計簿用のカテゴリーは自動で「投資」などにする
        category = "投資"
    else:
        if balance_type == "支出":
            category = st.radio('カテゴリー', EXPENSE_CATEGORIES)
        else:
            category = st.radio('カテゴリー', INCOME_CATEGORIES)
        amount = st.number_input('金額', min_value=0, step=1)
        memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')

if submit_btn:
    # 資産移動
    if balance_type == "資産移動":
        if not crypto_name:
            st.warning("銘柄名を入力してください")
        elif crypto_amount == 0 and amount == 0:
            st.warning("数量または金額を入力してください")
        else:
            try:
                # 処理1：仮想通貨の保有量を増やす
                df_curr = load_crypto_data()
                # 既存の保有量を取得（なければ0）
                if crypto_name in df_curr['銘柄'].values:
                    current_val = df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'].values[0]
                    new_val = current_val + crypto_amount
                    df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'] = new_val
                else:
                    new_row = pd.DataFrame({'銘柄': [crypto_name], '保有量': [crypto_amount]})
                    df_curr = pd.concat([df_curr, new_row], ignore_index=True)
                save_crypto_data(df_curr)
                # 処理2：家計簿に「支出」として記録する（金額が1円以上の場合）
                if amount > 0:
                    # 区分はわかりやすく「支出」にするか、あえて「資産移動」と記録するか選べます
                    # ここでは資産集計の計算を合わせるため「支出」として記録します
                    row_data = [str(date), "支出", category, amount, memo]
                    worksheet.append_row(row_data)
                    msg = f"💰 {amount:,}円で {crypto_name} を {crypto_amount} 購入しました。"
                else:
                    msg = f"💎 {crypto_name} が {crypto_amount} 増えました。"
                st.success(msg)
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"資産移動エラー: {e}")

    else:
        if amount == 0:
            st.warning('金額が0円です。入力してください。')
        else:
            try:
                # スプレッドシート用にデータを並べる
                row_data = [str(date), balance_type, category, amount, memo]
                # スプレッドシートの一番下の行に追加する
                worksheet.append_row(row_data)
                # 登録完了メッセージ
                if balance_type =="収入":
                    st.success(f'お疲れさま！ {category} : {amount}円の収入を登録しました。')
                else:
                    st.info(f'{category} : {amount}円を登録しました。')
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')

# --- 履歴表示 ---
st.divider()
st.subheader("入力履歴")
if not df.empty:
    df_display = df.copy()
    df_display.index = df_display.index + 1
    # 日付列を見やすいように
    df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
    # データの並び方（新しい順）
    st.dataframe(df_display.iloc[::-1], use_container_width=True)
else:
    st.info("まだデータがありません。")

# --- データの削除 ---
st.subheader("データの削除")
with st.expander("削除メニューを開く"):
    if not df.empty:
        delete_options = df.index +1
        selected_index = st.selectbox("削除する行番号を選択", delete_options)
        # 削除の実行
        if st.button("削除実行"):
            try:
                target_row = selected_index + 1
                worksheet.delete_rows(int(target_row))
                st.success("削除しました。")
                st.rerun()
            except Exception as e:
                st.error(f"削除エラー: {e}")
    else:
        st.info("削除できるデータがありません。")

# --- いろいろメモ ---
st.divider()
st.subheader("なんでもメモ")
# キャッシュに残っていないときだけ読み込む
if 'my_memo_content' not in st.session_state:
    try:
        current_memo = worksheet.acell('G2').value
        if current_memo is None:
            current_memo = ""
    except:
        current_memo = ""
    # 読み込んだデータを「記憶」に保存
    st.session_state['my_memo_content'] = current_memo
# 入力欄を表示（初期値は「記憶」から取り出す）
# key='my_memo_content' を指定することで、入力内容とセッション状態が同期します
new_memo = st.text_area(
    "ToDoや買い物リストなど", 
    value=st.session_state['my_memo_content'], 
    height=150
)
# 保存ボタンが押されたときだけ書き込む
if st.button("メモを保存"):
    try:
        # スプレッドシートを更新
        worksheet.update_acell('G2', new_memo)
        # キャッシュを新しい内容で上書き更新しておく
        st.session_state['my_memo_content'] = new_memo
        st.success("保存しました！")
    except Exception as e:
        st.error(f"保存失敗: {e}")