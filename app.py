import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

# --- 設定 ---
# 接続するスプレッドシートの名前
SPREADSHEET_NAME = 'MyKakeibo'
# カテゴリのリスト　ラジオボタンにしたい
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

# --- アプリ画面 ---
st.title('マイ家計簿')

# 入力フォーム
with st.form(key='entry_form'):
    # 収支の切り替えスイッチ
    balance_type = st.radio("区分",["支出","収入"], horizontal=True)
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
            st.success(f'{balance_type} - {category} : {amount}円 を登録しました！')
            st.balloons()
        except Exception as e:
            st.error(f'書き込みエラー: {e}')
