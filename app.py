import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
import pandas as pd

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
    worksheet = sh.sheet1
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# --- 関数 ---
#データ読み込み
def load_data():
    all_rows = worksheet.get_all_values()
    if len(all_rows) < 2:
        return pd.DataFrame(columns=['日付','区分','カテゴリー','金額','メモ'])
    df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
    # 金額を数値に変換
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    # 日付を日付型へ変換
    df['日付'] = pd.to_datetime(df['日付'])
    return df

# --- アプリ画面 ---
st.title('マイ家計簿')

df = load_data()

# --- 資産合計 ---
total_income = df[df['区分'] == '収入']['金額'].sum()
total_expense = df[df['区分'] == '支出']['金額'].sum()
total_assets = total_income - total_expense
st.metric(lebel="現在の合計資産", value=f"￥{total_assets:,}")

# 入力フォー￥
balance_type = st.radio("区分",["支出","収入"], horizontal=True)
with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', datetime.date.today())
    if balance_type == "支出":
        category = st.radio('カテゴリー', EXPENSE_CATEGORIES)
    else:
        category = st.radio('カテゴリー', INCOME_CATEGORIES)
    amount = st.number_input('金額', min_value=0, step=1)
    memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')

if submit_btn:
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
        except Exception as e:
            st.error(f'書き込みエラー: {e}')

# --- 履歴表示 ---
st.divider()
st.subheader("入力履歴")

if not df.empty:
    # インデックスを1からに変更
    df.index = df.index + 1
    # 日付列を見やすいように
    df['日付'] = pd.to_datetime(df['日付']).dt.strftime('%Y-%m-%d')
    # データの並び方（新しい順）
    st.dataframe(df.iloc[::-1], use_container_width=True)
else:
    st.info("まだデータがありません。")

# データの削除
st.subheader("データの削除")
with st.expander("削除メニューを開く"):
    delete_options = df.index
    selected_row = st.selectbox("削除する行番号を選択", delete_options)
    # 削除の実行
    if st.button("削除実行"):
        try:
            target_row = selected_row + 1
            worksheet.delete_rows(int(target_row))
            st.rerun()
        except Exception as e:
            st.error(f"削除エラー: {e}")