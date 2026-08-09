import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import calendar

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

@st.cache_resource(ttl=3600)
def get_worksheet(sheet_name):
    try:
        if "gcp_service_account" in st.secrets:
            secret_val = st.secrets["gcp_service_account"]
            if isinstance(secret_val, str):
                key_dict = json.loads(secret_val)
            else:
                key_dict = dict(secret_val)
            if "private_key" in key_dict:
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
            credentials = Credentials.from_service_account_info(key_dict, scopes=scopes)
        else:
            credentials = Credentials.from_service_account_file('secrets.json', scopes=scopes)
        gc = gspread.authorize(credentials)
        if len(sheet_name) > 30 and " " not in sheet_name:
            sh = gc.open_by_key(sheet_name)
        else:
            sh = gc.open(sheet_name)
        return sh
    except Exception as e:
        st.error(f"接続エラー: スプレッドシート '{sheet_name}' が見つかりません。共有設定を確認してください。エラー詳細: {e}")
        st.stop()

def load_kakeibo_data(sh):
    try:
        ws = sh.worksheet('家計簿')
        all_rows = ws.get_all_values()
    except Exception:
        return pd.DataFrame(columns=['No','日付','区分','カテゴリー','金額','メモ'])
    
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
    df = df[df['日付'].astype(str).str.strip() != ""]
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    df['日付'] = df['日付'].astype(str).str.strip().str.replace('-','/')
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    return df

def add_entry(sh, date, balance_type, category, amount, memo):
    ws = sh.worksheet('家計簿')
    col_a_values = ws.col_values(1)
    next_row = len(col_a_values) + 1
    row_data = [[str(date), balance_type, category, amount, memo]]
    ws.update(range_name=f"A{next_row}:E{next_row}", values=row_data)

def delete_entry(sh, row_index):
    ws = sh.worksheet('家計簿')
    current_data = ws.get('A:E')
    target_list_index = int(row_index) - 1
    if 0 <= target_list_index < len(current_data):
        current_data.pop(target_list_index)
        ws.batch_clear(['A:E'])
        if current_data:
            ws.update(range_name='A1', values=current_data)

def delete_callback():
    target_no = st.session_state.get("delete_input_no")
    if target_no:
        try:
            real_row_index = int(target_no) + 1
            target_sheet_name = st.session_state.get("target_sheet")
            if not target_sheet_name:
                raise Exception("ログイン情報が見つかりません")
            sh = get_worksheet(target_sheet_name)
            delete_entry(sh, real_row_index)
            st.session_state["delete_input_no"] = None
            st.session_state["del_confirm_ckeck"] = False
            st.session_state["menu_reset_id"] += 1
            st.session_state["delete_msg"] = f"No.{target_no} を削除しました！"
        except Exception as e:
            st.session_state["delete_msg"] = f"削除エラー: {e}"

def load_investment_data(sh):
    cols = ['日付','銘柄','数量','支払金額','メモ']
    try:
        ws = sh.worksheet('投資')
        raw_data = ws.get('A:E')
    except Exception:
        return pd.DataFrame(columns=cols)
    if not raw_data or len(raw_data) < 2:
        return pd.DataFrame(columns=cols)
        
    data_rows = raw_data[1:]
    clean_data = []
    for row in data_rows:
        padded_row = (row + [""] * 5)[:5]
        clean_data.append(padded_row)
    df = pd.DataFrame(clean_data, columns=cols)
    df['数量'] = pd.to_numeric(df['数量'], errors='coerce').fillna(0.0)
    return df

def add_investment_data(sh, date, investment_name, investment_amount, pay_amount, memo):
    ws = sh.worksheet('投資')
    col_a_values = ws.col_values(1)
    next_row = len(col_a_values) + 1
    if next_row == 1:
        ws.update(range_name='A1:E1', values=[['日付', '銘柄', '数量', '支払い金額', 'メモ']])
        next_row = 2
    row_data = [[str(date), investment_name, investment_amount, pay_amount, memo]]
    ws.update(range_name=f"A{next_row}:E{next_row}", values=row_data)

def load_subscription_data(sh):
    cols = ['サービス名', '金額', 'カテゴリー', '支払日', 'メモ']
    try:
        ws = sh.worksheet('サブスク')
        raw_data = ws.get('A:E')
    except Exception:
        return pd.DataFrame(columns=cols)
    if not raw_data or len(raw_data) < 2:
        return pd.DataFrame(columns=cols)
        
    data_rows = raw_data[1:]
    clean_data = []
    for row in data_rows:
        padded = (row + [""] * 5)[:5]
        clean_data.append(padded)
    df = pd.DataFrame(clean_data, columns=cols)
    df = df[df['サービス名'].astype(str).str.strip() != ""]
    if df.empty:
        return pd.DataFrame(columns=cols)
    df['金額'] = pd.to_numeric(df['金額'], errors='coerce').fillna(0).astype(int)
    df['支払日'] = pd.to_numeric(df['支払日'], errors='coerce').fillna(1).astype(int)
    df.insert(0, 'No', range(2, 2 + len(df)))
    return df

def add_subscription(sh, service_name, amount, category, pay_day, memo):
    ws = sh.worksheet('サブスク')
    col_a_values = ws.col_values(1)
    next_row = len(col_a_values) + 1
    if next_row == 1:
        ws.update(range_name='A1:E1', values=[['サービス名', '金額', 'カテゴリー', '支払日', 'メモ']])
        next_row = 2
    row_data = [[service_name, amount, category, pay_day, memo]]
    ws.update(range_name=f'A{next_row}:E{next_row}', values=row_data)

def delete_subscription(sh, row_index):
    ws = sh.worksheet('サブスク')
    current_data = ws.get('A:E')
    target_list_index = int(row_index) - 1
    if 0 <= target_list_index < len(current_data):
        current_data.pop(target_list_index)
        ws.batch_clear(['A:E'])
        if current_data:
            ws.update(range_name='A1', values=current_data)

def auto_add_subscriptions(sh, df_kakeibo):
    try:
        df_sub = load_subscription_data(sh)
    except Exception:
        return 0
    if df_sub.empty:
        return 0
    now = pd.Timestamp.now(tz='Asia/Tokyo')
    year = now.year
    month = now.month
    added_count = 0
    for _, row in df_sub.iterrows():
        service_name = str(row['サービス名']).strip()
        if not service_name:
            continue
        identifier = f"[サブスク_{year}{month:02d}_{service_name}]"
        already_added = False
        if not df_kakeibo.empty and 'メモ' in df_kakeibo.columns:
            already_added = df_kakeibo['メモ'].astype(str).str.contains(
                identifier, regex=False
            ).any()
        if not already_added:
            last_day = calendar.monthrange(year, month)[1]
            pay_day = min(int(row['支払日']), last_day)
            pay_date = pd.Timestamp(year=year, month=month, day=pay_day).date()
            memo_with_id = f"{row['メモ']} {identifier}".strip()
            add_entry(sh, pay_date, '支出', row['カテゴリー'], int(row['金額']), memo_with_id)
            added_count += 1
    return added_count

def get_anything_memo(sh):
    try:
        ws = sh.worksheet('なんでもメモ')
        current_memo = ws.acell('A2').value
        if current_memo is None:
            current_memo = ""
    except Exception:
        current_memo = ""
    return current_memo

def update_anything_memo(sh, text):
    try:
        ws = sh.worksheet('なんでもメモ')
        if str(ws.acell('A1').value) != 'なんでもメモ':
            ws.update_acell('A1', 'なんでもメモ')
        ws.update_acell('A2', text)
    except Exception:
        pass

def color_coding(val):
    if val == '収入':
        return 'color: #379c72; font-weight: bold;'
    elif val == '支出':
        return 'color: #A03333; font-weight: bold;'
    return ''

# ==========================================
# ★ 新設：投資資産の価格キャッシュ用関数
# ==========================================
def save_price_cache(sh, prices_dict, timestamp):
    """API取得が成功したときに、時刻と価格をスプレッドシートに保存する"""
    try:
        ws = sh.worksheet('価格キャッシュ')
    except Exception:
        # シートが無ければ作成
        ws = sh.add_worksheet(title='価格キャッシュ', rows="100", cols="3")
    
    data = []
    for symbol, price in prices_dict.items():
        data.append([str(timestamp), symbol, price])
    
    if data:
        ws.clear()
        ws.update(range_name='A1', values=[['取得日時', '銘柄', '価格']] + data)

def load_price_cache(sh):
    """API取得が失敗したときに、スプレッドシートのキャッシュを読み込む"""
    try:
        ws = sh.worksheet('価格キャッシュ')
        raw_data = ws.get_all_values()
        if len(raw_data) < 2:
            return {}, None
        
        prices_dict = {}
        timestamp = raw_data[1][0] # A2のセルに記録されている時刻
        for row in raw_data[1:]:
            if len(row) >= 3:
                symbol = row[1]
                try:
                    price = float(row[2])
                    prices_dict[symbol] = price
                except ValueError:
                    pass
        return prices_dict, timestamp
    except Exception:
        return {}, None