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

# --- 資産の表示＆非表示 ---
def format_money(amount, is_visible):
    if is_visible:
        return f"{int(amount):,} 円"
    else:
        return "***,***,*** 円"

# --- 家計簿データの操作 ---
def load_kakeibo_data():
    all_rows = worksheet.get_all_values()
    columns=['No','日付','区分','カテゴリー','金額','メモ']
    if len(all_rows) < 2:
        return pd.DataFrame(columns=columns)
    data = []
    for i, row in enumerate(all_rows):
        if i == 0: continue
        row_num = i
        row_data = [row_num] + row[:5]
        data.append(row_data)
    df = pd.DataFrame(data, columns=columns)
    # 「日付」が入っていない空っぽの行を削除
    df = df[df['日付'].astype(str).str.strip() != ""]
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    return df

def add_entry(date, balance_type,category, amount, memo):
    col_a_values = worksheet.col_values(1)
    next_row = len(col_a_values) + 1
    row_data = [[str(date), balance_type, category, amount, memo]]
    range_str = f"A{next_row}:E{next_row}"
    worksheet.update(range_name=range_str,values=row_data)

def delete_entry(row_index):
    current_data = worksheet.get('A:E')
    target_list_index = int(row_index) - 1
    if 0 <= target_list_index < len(current_data):
        current_data.pop(target_list_index)
        worksheet.batch_clear(['A:E'])
        worksheet.update('A1', current_data)

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
    prices = {}
    valid_symbols = []
    for s in symbols:
        if s is not None and str(s).strip() != "":
            valid_symbols.append(str(s))
    upper_symbols = list(set([s.upper() for s in symbols]))
    if not upper_symbols:
        return {}
    meme_symbols = []
    normal_symbols = []
    for s in symbols:
        if s.upper() in c.MEME_CONTRACTS:
            meme_symbols.append(s.upper())
        else:
            normal_symbols.append(s)
    for sym in meme_symbols:
        address = c.MEME_CONTRACTS[sym]
        prices[sym] = get_meme_price(address)
    if normal_symbols:
        upper_symbols = list(set([s.upper() for s in normal_symbols]))
        api_symbols = [s for s in upper_symbols if c.CRYPTO_ID_MAP.get(s) != 'FIXED_JPY']
        if api_symbols:
            fsyms = ",".join(api_symbols)
            url = "https://min-api.cryptocompare.com/data/pricemulti"
            params = {'fsyms': fsyms, 'tsyms': 'JPY'}
            try:
                response = requests.get(url, params=params)
                data = response.json()
                for sym in normal_symbols:
                    key = sym.upper()
                    if key in data and 'JPY' in data[key]:
                        prices[sym] = data[key]['JPY']
                    elif sym not in prices:
                        prices[sym] = 0
            except:
                pass
    return prices

@st.cache_data(ttl=3600)
def get_usd_jpy_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["JPY"]
    except:
        return 150.0 # エラー時は仮のレート

# ミームコイン価格取得
@st.cache_data(ttl=600)
def get_meme_price(token_address):
    dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        dex_response = requests.get(dex_url, timeout=5)
        dex_data = dex_response.json()
        # データがない場合
        if dex_data.get("pairs") is None or len(dex_data["pairs"]) == 0:
            return 0.0
        # メインのペアからUSD価格を取り出す
        price_usd_str = dex_data["pairs"][0].get("priceUsd")
        if not price_usd_str:
            return 0.0
        price_usd = float(price_usd_str)
        # 日本円に換算
        usd_jpy_rate = get_usd_jpy_rate()
        price_jpy = price_usd * usd_jpy_rate
        return price_jpy
    except Exception as e:
        print(f"Meme Price Error: {e}")
        return 0.0

# --- 履歴表示 ---
def color_coding(val):
    if val == '収入':
        return 'color: green; font-weight: bold;'
    elif val == '支出':
        return 'color: red; font-weight: bold;'
    return ''

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