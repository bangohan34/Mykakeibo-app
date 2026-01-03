import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import requests
import const as c

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
        sh = gc.open(c.SPREADSHEET_NAME)
        return sh.sheet1
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

# --- worksheetを使えるように ---
worksheet = get_worksheet()

# --- 家計簿データの操作 ---
def load_kakeibo_data():
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

def add_entry(date, balance_type,category, amount, memo):
    row_data = [str(date), balance_type, category, amount, memo]
    worksheet.append_row(row_data)

def delete_entry(row_index):
    worksheet.delete_rows(int(row_index))

# --- 仮想通貨データの操作 ---
def load_crypto_data():
    raw_data = worksheet.get('I:J')
    if len(raw_data) < 2:
        return pd.DataFrame(columns=['銘柄','保有量'])
    df_crypto = pd.DataFrame(raw_data[1:],columns=['銘柄','保有量'])
    df_crypto['保有量'] = pd.to_numeric(df_crypto['保有量'], errors='coerce').fillna(0.0)
    return df_crypto

def save_crypto_data(df_crypto):
    data_to_save = [df_crypto.columns.tolist()] + df_crypto.values.tolist()
    worksheet.batch_clear(['I:J'])
    worksheet.update('I1', data_to_save)

@st.cache_data(ttl=600) # 600秒間、キャッシュする
def get_crypto_prices(symbols):
    ids = [c.CRYPTO_ID_MAP.get(s.upper(), s.lower()) for s in symbols]
    ids_str = ",".join(ids)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ids_str,
        'vs_currencies': 'jpy'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        prices = {}
        for sym in symbols:
            c_id = c.CRYPTO_ID_MAP.get(sym.upper(), sym.lower())
            if c_id in data:
                prices[sym] = data[c_id]['jpy']
            else:
                prices[sym] = 0
        return prices
    except Exception as e:
        return {}

# --- なんでもメモの操作 ---
def get_anything_memo():
    try:
        current_memo = worksheet.acell('G2').value
        if current_memo is None:
            current_memo = ""
    except:
        current_memo = ""
    return current_memo

def update_anything_memo(text):
    worksheet.update_acell('G2', text)