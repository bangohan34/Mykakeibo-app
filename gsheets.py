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

# ★ キャッシュを追加して、Google認証の時間をスキップ（劇的に速くなります）
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
        return sh.sheet1
    except Exception as e:
        st.error(f"接続エラー: スプレッドシート '{sheet_name}' が見つかりません。共有設定を確認してください。エラー詳細: {e}")
        st.stop()

def load_kakeibo_data(worksheet):
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
    df = df[df['日付'].astype(str).str.strip() != ""]
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    df['日付'] = df['日付'].astype(str).str.strip().str.replace('-','/')
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    return df

def add_entry(worksheet, date, balance_type, category, amount, memo):
    col_a_values = worksheet.col_values(1)
    next_row = len(col_a_values) + 1
    row_data = [[str(date), balance_type, category, amount, memo]]
    range_str = f"A{next_row}:E{next_row}"
    worksheet.update(range_name=range_str, values=row_data)

def delete_entry(worksheet, row_index):
    current_data = worksheet.get('A:E')
    target_list_index = int(row_index) - 1
    if 0 <= target_list_index < len(current_data):
        current_data.pop(target_list_index)
        worksheet.batch_clear(['A:E'])
        worksheet.update(range_name='A1', values=current_data)

def delete_callback():
    target_no = st.session_state.get("delete_input_no")
    if target_no:
        try:
            real_row_index = int(target_no) + 1
            target_sheet_name = st.session_state.get("target_sheet")
            if not target_sheet_name:
                raise Exception("ログイン情報が見つかりません")
            ws = get_worksheet(target_sheet_name)
            delete_entry(ws, real_row_index)
            st.session_state["delete_input_no"] = None
            st.session_state["del_confirm_ckeck"] = False
            st.session_state["menu_reset_id"] += 1
            st.session_state["delete_msg"] = f"No.{target_no} を削除しました！"
        except Exception as e:
            st.session_state["delete_msg"] = f"削除エラー: {e}"

def load_investment_data(worksheet):
    raw_data = worksheet.get('I:M')
    cols = ['日付','銘柄','数量','支払金額','メモ']
    if len(raw_data) < 2:
        return pd.DataFrame(columns=cols)
    data_rows = raw_data[1:]
    clean_data = []
    for row in data_rows:
        padded_row = (row + [""] * 5)[:5]
        clean_data.append(padded_row)
    df = pd.DataFrame(data_rows, columns=cols)
    df['数量'] = pd.to_numeric(df['数量'], errors='coerce').fillna(0.0)
    return df

def add_investment_data(worksheet, date, investment_name, investment_amount, pay_amount, memo):
    col_a_values = worksheet.col_values(9)
    next_row = len(col_a_values) + 1
    row_data = [[str(date), investment_name, investment_amount, pay_amount, memo]]
    range_str = f"I{next_row}:M{next_row}"
    worksheet.update(range_name=range_str, values=row_data)

def load_subscription_data(worksheet):
    cols = ['サービス名', '金額', 'カテゴリー', '支払日', 'メモ']
    try:
        raw_data = worksheet.get('N:R')
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

def add_subscription(worksheet, service_name, amount, category, pay_day, memo):
    col_n_values = worksheet.col_values(14)
    next_row = len(col_n_values) + 1
    if next_row == 1:
        worksheet.update(range_name='N1:R1', values=[['サービス名', '金額', 'カテゴリー', '支払日', 'メモ']])
        next_row = 2
    row_data = [[service_name, amount, category, pay_day, memo]]
    worksheet.update(range_name=f'N{next_row}:R{next_row}', values=row_data)

def delete_subscription(worksheet, row_index):
    current_data = worksheet.get('N:R')
    target_list_index = int(row_index) - 1
    if 0 <= target_list_index < len(current_data):
        current_data.pop(target_list_index)
        worksheet.batch_clear(['N:R'])
        if current_data:
            worksheet.update(range_name='N1', values=current_data)

def auto_add_subscriptions(worksheet, df_kakeibo):
    try:
        df_sub = load_subscription_data(worksheet)
    except Exception:
        return 0
    if df_sub.empty:
        return 0
    
    # ★ ここもJSTで現在時刻を取得
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
            add_entry(worksheet, pay_date, '支出', row['カテゴリー'], int(row['金額']), memo_with_id)
            added_count += 1
    return added_count

def get_anything_memo(worksheet):
    try:
        current_memo = worksheet.acell('G2').value
        if current_memo is None:
            current_memo = ""
    except:
        current_memo = ""
    return current_memo

def update_anything_memo(worksheet, text):
    worksheet.update_acell('G2', text)

def format_money(amount, is_visible):
    if is_visible:
        return f"{int(amount):,} 円"
    else:
        return "******* 円"

def color_coding(val):
    if val == '収入':
        return 'color: #379c72; font-weight: bold;'
    elif val == '支出':
        return 'color: #A03333; font-weight: bold;'
    return ''