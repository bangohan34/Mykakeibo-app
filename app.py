import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. 設定セクション ---
# スプレッドシートの名前（あなたのファイル名に合わせてください）
SPREADSHEET_NAME = 'MyKakeibo'

# 家計簿の費目リスト（ここを好きに変えられます！）
CATEGORIES = ['食費', '交通費', '日用品', '趣味', '交際費', 'その他']

# --- 2. 認証と接続 ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    credentials = Credentials.from_service_account_file(
        'secrets.json',
        scopes=scopes
    )
    gc = gspread.authorize(credentials)
    sh = gc.open(SPREADSHEET_NAME)
    worksheet = sh.sheet1
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# --- 3. アプリの画面デザイン ---
st.title('マイ家計簿💰')

# 入力フォームを枠で囲む
with st.form(key='entry_form'):
    # 日付入力（デフォルトは今日）
    date = st.date_input('日付', datetime.date.today())
    
    # カテゴリ選択
    category = st.selectbox('費目', CATEGORIES)
    
    # 金額入力
    amount = st.number_input('金額', min_value=0, step=1)
    
    # メモ入力
    memo = st.text_input('メモ（任意）')

    # 送信ボタン
    submit_btn = st.form_submit_button('登録する')

# --- 4. ボタンが押されたときの処理 ---
if submit_btn:
    if amount == 0:
        st.warning('金額が0円です。入力してください。')
    else:
        try:
            # スプレッドシートに書き込むデータを作成
            # 日付は文字列に変換して保存します
            row_data = [str(date), category, amount, memo]
            
            # スプレッドシートの最終行に追加 (append_row)
            worksheet.append_row(row_data)
            
            st.success(f'{category} : {amount}円 を登録しました！')
            st.balloons() # お祝いのエフェクト
            
        except Exception as e:
            st.error(f'書き込みエラー: {e}')