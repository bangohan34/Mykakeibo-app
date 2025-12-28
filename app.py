import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json # これを追加

# --- 1. 設定セクション ---
SPREADSHEET_NAME = 'MyKakeibo' # あなたのスプレッドシート名に合わせてください
CATEGORIES = ['食費', '交通費', '日用品', '趣味', '交際費', 'その他']

# --- 2. 認証と接続（ここが進化！） ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    # A. クラウド上の「金庫」に鍵があるか確認
    if "gcp_service_account" in st.secrets:
        # 文字列として保存されたJSONを辞書に変換して読み込む
        key_dict = json.loads(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(key_dict, scopes=scopes)
    
    # B. なければ、手元の「secrets.json」を探す（開発用）
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