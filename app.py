import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json

# --- 1. 設定セクション ---
SPREADSHEET_NAME = 'MyKakeibo'
CATEGORIES = ['食費', '交通費', '日用品', '趣味', '交際費', 'その他']

# --- 2. 認証と接続（エラー回避版） ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    # A. Streamlit CloudのSecretsから読み込む
    if "gcp_service_account" in st.secrets:
        secret_val = st.secrets["gcp_service_account"]
        
        # 【ここが重要】データが「文字」ならJSON変換、「辞書」ならそのまま使う
        if isinstance(secret_val, str):
            key_dict = json.loads(secret_val)
        else:
            # AttrDictなどの場合は、普通の辞書に変換する
            key_dict = dict(secret_val)

        # private_keyの改行文字(\n)が文字列のままになっている場合の対策
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")

        credentials = Credentials.from_service_account_info(key_dict, scopes=scopes)
    
    # B. 手元の secrets.json から読み込む (開発用)
    else:
        credentials = Credentials.from_service_account_file('secrets.json', scopes=scopes)

    gc = gspread.authorize(credentials)
    sh = gc.open(SPREADSHEET_NAME)
    worksheet = sh.sheet1

except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# --- 3. アプリの画面デザイン ---
st.title('💰 私の家計簿アプリ')

with st.form(key='entry_form'):
    date = st.date_input('日付', datetime.date.today())
    category = st.selectbox('費目', CATEGORIES)
    amount = st.number_input('金額', min_value=0, step=1)
    memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')

if submit_btn:
    if amount == 0:
        st.warning('金額が0円です。入力してください。')
    else:
        try:
            row_data = [str(date), category, amount, memo]
            worksheet.append_row(row_data)
            st.success(f'{category} : {amount}円 を登録しました！')
            st.balloons()
        except Exception as e:
            st.error(f'書き込みエラー: {e}')