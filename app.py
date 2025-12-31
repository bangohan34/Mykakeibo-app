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
    # 日付を日付型へ変換
    df['日付'] = pd.to_datetime(df['日付'])
    return df

# 仮想通貨データの読み込み
def load_crypto_data():
    raw_data = worksheet.get('I:J')
    if len(raw_data) < 2:
        return pd.DataFrame(columns=['銘柄','保有量'])
    df_crypto = pd.DataFrame(raw_data[1:],columns=['銘柄','保有量'])
    df_crypto['保有量'] = pd.to_numeric(df_crypto['保有量'], errors='coerce').fillna(0.0)
    return df_crypto

# 仮想通貨データの保存
def save_crypto_data(df_crypto):
    data_to_save = [df_crypto.columns.tolist()] + df_crypto.values.tolist()
    worksheet.batch_clear(['I:J'])
    worksheet.update('I1', data_to_save)

# --- アプリ画面 ---
st.title('マイ家計簿')

df = load_data()

# --- 資産合計表示 ---
total_income = df[df['区分'] == '収入']['金額'].sum()
total_expense = df[df['区分'] == '支出']['金額'].sum()
total_assets = total_income - total_expense
st.metric(label="現在の合計資産", value=f"￥{total_assets:,}")
# 仮想通貨の表示
df_crypto = load_crypto_data()
if not df_crypto.empty:
    display_df = df_crypto.copy()
    display_df['保有量'] = display_df['保有量'].apply(lambda x: f"{x:.8f}") 
    st.table(display_df)
else:
    st.info("仮想通貨の登録はまだありません。")

# 入力フォーム
balance_type = st.radio("区分",["支出","収入","資産移動"], horizontal=True)
with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', datetime.date.today())
    # 資産移動
    if balance_type == "資産移動":
        st.caption("円を使って仮想通貨を購入します")
        col1, col2 = st.columns(2)
        with col1:
            crypto_name = st.text_input("銘柄名（例: BTC, Pi）")
        with col2:
            crypto_amount = st.number_input("増える量（通貨）", min_value=0.0, step=0.0001, format="%.8f")
        # 支払う日本円
        amount = st.number_input('支払った日本円', min_value=0, step=1, help="家計簿には「支出」として記録されます")
        memo = st.text_input('メモ', value=f"{crypto_name}購入")
        # 家計簿用のカテゴリーは自動で「投資」などにする
        category = "投資"
    else:
        if balance_type == "支出":
            category = st.radio('カテゴリー', EXPENSE_CATEGORIES)
        else:
            category = st.radio('カテゴリー', INCOME_CATEGORIES)
        amount = st.number_input('金額', min_value=0, step=1)
        memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')

if submit_btn:
    # 資産移動
    if balance_type == "資産移動":
        if not crypto_name:
            st.warning("銘柄名を入力してください")
        elif crypto_amount == 0 and amount == 0:
            st.warning("数量または金額を入力してください")
        else:
            try:
                # 処理1：仮想通貨の保有量を増やす
                df_curr = load_crypto_data()
                # 既存の保有量を取得（なければ0）
                if crypto_name in df_curr['銘柄'].values:
                    current_val = df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'].values[0]
                    new_val = current_val + crypto_amount
                    df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'] = new_val
                else:
                    new_row = pd.DataFrame({'銘柄': [crypto_name], '保有量': [crypto_amount]})
                    df_curr = pd.concat([df_curr, new_row], ignore_index=True)
                save_crypto_data(df_curr)
                # 処理2：家計簿に「支出」として記録する（金額が1円以上の場合）
                if amount > 0:
                    # 区分はわかりやすく「支出」にするか、あえて「資産移動」と記録するか選べます
                    # ここでは資産集計の計算を合わせるため「支出」として記録します
                    row_data = [str(date), "支出", category, amount, memo]
                    worksheet.append_row(row_data)
                    msg = f"💰 {amount:,}円で {crypto_name} を {crypto_amount} 購入しました。"
                else:
                    msg = f"💎 {crypto_name} が {crypto_amount} 増えました。"
                st.success(msg)
                st.balloons()
            except Exception as e:
                st.error(f"資産移動エラー: {e}")

    else:
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
                st.rerun()
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

# --- データの削除 ---
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

# --- いろいろメモ ---
st.divider()
st.subheader("なんでもメモ")
# キャッシュに残っていないときだけ読み込む
if 'my_memo_content' not in st.session_state:
    try:
        current_memo = worksheet.acell('G2').value
        if current_memo is None:
            current_memo = ""
    except:
        current_memo = ""
    # 読み込んだデータを「記憶」に保存
    st.session_state['my_memo_content'] = current_memo
# 入力欄を表示（初期値は「記憶」から取り出す）
# key='my_memo_content' を指定することで、入力内容とセッション状態が同期します
new_memo = st.text_area(
    "ToDoや買い物リストなど", 
    value=st.session_state['my_memo_content'], 
    height=150
)
# 保存ボタンが押されたときだけ書き込む
if st.button("メモを保存"):
    try:
        # スプレッドシートを更新
        worksheet.update_acell('G2', new_memo)
        # キャッシュを新しい内容で上書き更新しておく
        st.session_state['my_memo_content'] = new_memo
        st.success("保存しました！")
    except Exception as e:
        st.error(f"保存失敗: {e}")