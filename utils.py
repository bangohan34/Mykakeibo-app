import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import requests
import const as c
import altair as alt
import yfinance as yf

# --- 認証と接続 ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
# キャッシュを使って認証を高速化
def get_worksheet(sheet_name):
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
        if len(sheet_name) > 30 and " " not in sheet_name:
            sh = gc.open_by_key(sheet_name)
        else:
            sh = gc.open(sheet_name)
        return sh.sheet1
    except Exception as e:
        st.error(f"接続エラー: スプレッドシート '{sheet_name}' が見つかりません。共有設定を確認してください。エラー詳細: {e}")
        st.stop()

# --- 資産の表示＆非表示 ---
def format_money(amount, is_visible):
    if is_visible:
        return f"{int(amount):,} 円"
    else:
        return "******* 円"

# --- 家計簿データの操作 ---
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
    # 「日付」が入っていない空っぽの行を削除
    df = df[df['日付'].astype(str).str.strip() != ""]
    df['金額'] = pd.to_numeric(df['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    # 日付の書き方を統一
    df['日付'] = df['日付'].astype(str).str.strip().str.replace('-','/')
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    return df
def add_entry(worksheet, date, balance_type,category, amount, memo):
    col_a_values = worksheet.col_values(1)
    next_row = len(col_a_values) + 1
    row_data = [[str(date), balance_type, category, amount, memo]]
    range_str = f"A{next_row}:E{next_row}"
    worksheet.update(range_name=range_str,values=row_data)
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

# --- 暗号資産データの操作 ---
def load_crypto_data(worksheet):
    raw_data = worksheet.get('I:J')
    if len(raw_data) < 2:
        return pd.DataFrame(columns=['銘柄','保有量'])
    df_crypto = pd.DataFrame(raw_data[1:],columns=['銘柄','保有量'])
    df_crypto['保有量'] = pd.to_numeric(df_crypto['保有量'], errors='coerce').fillna(0.0)
    return df_crypto
def save_crypto_data(worksheet, df_crypto):
    data_to_save = [df_crypto.columns.tolist()] + df_crypto.values.tolist()
    worksheet.batch_clear(['I:J'])
    worksheet.update(range_name='I1', values=data_to_save)
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

# --- 貴金属データの操作 ---
def get_metal_prices_jpy_per_gram():
    try:
        tickers = ["XAU-USD", "XAG-USD", "JPY=X"]
        df = yf.download(tickers, period="5d", interval="1m", progress=False)['Close'].iloc[-1]
        data = df.ffill().iloc[-1]
        # 最新価格を取得（取得できない場合は安全策で0にする）
        gold_usd_oz = data.get('XAU-USD', 0)
        gold_usd_oz
        silver_usd_oz = data.get('XAG-USD', 0)
        usd_jpy = data.get('JPY=X', 0)
        # 1トロイオンス = 31.1035グラム
        GRAMS_PER_OZ = 31.1035
        # 円/グラムに換算
        # 計算式: (ドル価格 × ドル円レート) ÷ 31.1035
        gold_jpy_g = (gold_usd_oz * usd_jpy) / GRAMS_PER_OZ
        silver_jpy_g = (silver_usd_oz * usd_jpy) / GRAMS_PER_OZ
        return {
            'GOLD': gold_jpy_g,
            'SILVER': silver_jpy_g
        }
    except Exception as e:
        # エラー時はログに出すか、0を返す
        print(f"貴金属データ取得エラー: {e}")
        return {'GOLD': 0, 'SILVER': 0}

# --- グラフ ---
def create_combo_chart(data, x_col, x_format, tooltip_format, x_label_angle=0):
    # 棒グラフ
    bar_data = data.groupby([x_col, '区分'])['グラフ金額'].sum().reset_index()
    bars = alt.Chart(bar_data).mark_bar().encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None, labelAngle=x_label_angle)),
        y=alt.Y('グラフ金額', axis=alt.Axis(title='収支 & 残高 (円)', grid=True)),
        color=alt.Color('区分', scale=alt.Scale(domain=['収入', '支出'], range=["#379c72", "#A03333"]), legend=None),
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            '区分',
            alt.Tooltip('グラフ金額', format=',', title='金額')
        ]
    )
    # 折れ線グラフ
    line_data = data.groupby(x_col)['現金推移'].last().reset_index()
    line = alt.Chart(line_data).mark_line(color="#498dd1", point=True).encode(
        x=alt.X(x_col, axis=alt.Axis(format=x_format, title=None)),
        y='現金推移',
        tooltip=[
            alt.Tooltip(x_col, format=tooltip_format, title='期間'),
            alt.Tooltip('現金推移', format=',', title='残高')
        ]
    )
    # 重ね合わせ
    chart = alt.layer(bars, line).resolve_scale(y='shared').properties(height=300)
    return chart.configure_axis(
        labelColor='#703B3B',  # 軸の文字色
        titleColor='#703B3B',  # 軸タイトルの色
        gridColor='#e0e0e0'    # グリッド線を薄いグレーに
    )
def create_expense_pie_chart(data):
    # 支出データのみを抽出して集計
    expense_df = data[data['区分'] == '支出'].copy()
    # データがない場合は何もしない（エラー回避）
    if expense_df.empty:
        return None
    # カテゴリーごとの合計を計算
    pie_data = expense_df.groupby('カテゴリー', as_index=False)['金額'].sum()
    # 順番
    pie_data = pie_data.sort_values('金額', ascending=False)
    if 'その他' in pie_data['カテゴリー'].values:
        others_row = pie_data[pie_data['カテゴリー'] == 'その他']
        normal_rows = pie_data[pie_data['カテゴリー'] != 'その他']
        pie_data = pd.concat([normal_rows, others_row])
    pie_data['order_index'] = range(len(pie_data))
    sort_order = pie_data['カテゴリー'].tolist()
    # 色
    domain = []
    range_ = []
    for cat in sort_order:
        domain.append(cat)
        # 辞書に色が定義されていればそれを使い、なければグレー(#CFCFCF)を使う
        range_.append(c.PIE_CHART_CATEGORIES_COLORS.get(cat, '#CFCFCF'))
    # 割合（%）を計算して列に追加
    total_expense = pie_data['金額'].sum()
    pie_data['割合'] = pie_data['金額'] / total_expense
    # ドーナツチャートの作成
    base = alt.Chart(pie_data).encode(
        theta=alt.Theta("金額", stack=True), # 金額に応じて角度を決める
        color=alt.Color(
            "カテゴリー", 
            legend=alt.Legend(title="カテゴリー"), 
            sort=sort_order,
            scale=alt.Scale(domain=domain, range=range_) 
        ),
        order=alt.Order("order_index", sort="ascending"),
        tooltip=[
            "カテゴリー", 
            alt.Tooltip("金額", format=","),
            alt.Tooltip("割合", format=".1%", title="構成比") # %を表示
        ]
    )
    # ドーナツの「輪」の部分
    pie = base.mark_arc(
        innerRadius=50,
        outerRadius=90,
        stroke="#d3d3d3"
        ).properties(
            height=200
        )
    # グラフの設定（背景透明、文字色など）
    return pie.configure_view(
        strokeOpacity=0
    ).configure_legend(
        labelColor='#703B3B',
        titleColor='#703B3B',
        symbolStrokeWidth=0
    )
# --- 履歴表示 ---
def color_coding(val):
    if val == '収入':
        return 'color: #379c72; font-weight: bold;'
    elif val == '支出':
        return 'color: #A03333; font-weight: bold;'
    return ''

# --- なんでもメモの操作 ---
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