import streamlit as st
import datetime
import pandas as pd

import const as c
import utils as u

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- データの準備 ---
df = u.load_kakeibo_data()
df_crypto = u.load_crypto_data()
if not df_crypto.empty:
    df_crypto = df_crypto.sort_values(by='評価額(円)', ascending=False)

# --- アプリ画面 ---
st.title('マイ家計簿')

# --- 資産合計表示 ---
# 収支の計算
if not df.empty:
    total_income = df[df['区分'] == '収入']['金額'].sum()
    total_expense = df[df['区分'] == '支出']['金額'].sum()
    yen_assets = total_income - total_expense
else:
    yen_assets = 0
# 仮想通貨の価値計算
crypto_total_val = 0 
if not df_crypto.empty:
    # 現在価格を取得
    symbols = df_crypto['銘柄'].tolist()
    current_prices = u.get_crypto_prices(symbols)
    # データフレームに価格情報を結合
    # map関数を使って、銘柄に対応する価格を列に追加
    df_crypto['現在レート'] = df_crypto['銘柄'].map(current_prices).fillna(0)
    df_crypto['評価額(円)'] = df_crypto['保有量'] * df_crypto['現在レート']
    # 合計を計算
    crypto_total_val = df_crypto['評価額(円)'].sum()
# 総合計を表示（円 + 仮想通貨）
total_all_assets = yen_assets + crypto_total_val
st.metric(
    label="💰 総資産（円＋仮想通貨）", 
    value=f"￥{int(total_all_assets):,}",
    delta=f"うち仮想通貨: ￥{int(crypto_total_val):,}"
)

# 資産割合バー
if total_all_assets > 0:
    st.write("")
    st.caption("📊 資産内訳")
    # 色の指定
    COLOR_YEN = '#DB4437'
    SYMBOL_COLORS = {
        'BTC':'#F4B400',
        'ETH':'#9079ad',
        'XRP':'#afafb0',
        'IOST':'#00c8c8',
        'PI':'#9600ff'
    }
    # 指定がない銘柄用の予備カラー（順番に使われます）
    DEFAULT_COLORS = ['#F4B400', '#0F9D58', '#4285F4', '#AB47BC', '#00ACC1']
    # ベースのHTML
    yen_ratio = (yen_assets / total_all_assets) * 100
    bars_html = f'<div style="width: {yen_ratio}%; background-color:{COLOR_YEN};" title="日本円: {yen_ratio:.1f}%"></div>'
    legend_html = f'<span style="color:{COLOR_YEN}">■</span> 日本円 '
    # 2. 仮想通貨のバー作成（ループ）
    if not df_crypto.empty:
        default_color_index = 0
        for i, row in df_crypto.iterrows():
            if '評価額(円)' in row and row['評価額(円)'] > 0:
                ratio = (row['評価額(円)'] / total_all_assets) * 100
                name = row['銘柄']
                # 色を決定するロジック
                # 辞書に設定があればその色、なければ予備リストから順番に使う
                if name.upper() in SYMBOL_COLORS:
                    color = SYMBOL_COLORS[name.upper()]
                else:
                    color = DEFAULT_COLORS[default_color_index % len(DEFAULT_COLORS)]
                    default_color_index += 1
                bars_html += f'<div style="width: {ratio}%; background-color: {color};" title="{name}: {ratio:.1f}%"></div>'
                legend_html += f' <span style="color:{color}; margin-left:10px;">■</span> {name}'
    # 全体枠と合体
    final_html = f"""
    <div style="display: flex; width: 100%; height: 24px; background-color: #e0e0e0; border-radius: 12px; overflow: hidden;">
        {bars_html}
    </div>
    <div style="font-size: 12px; margin-top: 5px; color: #333;">
        {legend_html}
    </div>
    """
    st.markdown(final_html, unsafe_allow_html=True)

# 仮想通貨の内訳リストを表示
if not df_crypto.empty:
    st.subheader("仮想通貨内訳")
    display_df = df_crypto.copy()
    display_df['保有量'] = display_df['保有量'].apply(lambda x: f"{x:.8f}")
    display_df['現在レート'] = display_df['現在レート'].apply(lambda x: f"¥{x:,.4f}")
    display_df['評価額(円)'] = display_df['評価額(円)'].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(display_df, hide_index=True, use_container_width=True)
else:
    st.info("仮想通貨の登録はまだありません。")

# 入力フォーム
st.divider()
balance_type = st.radio("区分",["支出","収入","資産移動"], horizontal=True)
with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', datetime.date.today())
    category, amount, memo = None, 0, ""
    crypto_name, crypto_amount = "", 0.0000
    # 資産移動
    if balance_type == "資産移動":
        st.caption("資産を移動します")
        col1, col2 = st.columns(2)
        with col1:
            crypto_name = st.text_input("銘柄名")
        with col2:
            crypto_amount = st.number_input("増える量", min_value=0.0, step=0.0001, format="%.8f")
        # 支払う日本円
        amount = st.number_input('支払った日本円', min_value=0, step=1, help="家計簿には「支出」として記録されます")
        memo = st.text_input('メモ', value=f"{crypto_name}購入")
        # 家計簿用のカテゴリーは自動で「投資」などにする
        category = "投資"
    # 支出、収入
    else:
        if balance_type == "支出":
            category = st.radio('カテゴリー', c.EXPENSE_CATEGORIES)
        else:
            category = st.radio('カテゴリー', c.INCOME_CATEGORIES)
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
                df_curr = u.load_crypto_data()
                # 既存の保有量を取得（なければ0）
                if crypto_name in df_curr['銘柄'].values:
                    current_val = df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'].values[0]
                    new_val = current_val + crypto_amount
                    df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'] = new_val
                else:
                    new_row = pd.DataFrame({'銘柄': [crypto_name], '保有量': [crypto_amount]})
                    df_curr = pd.concat([df_curr, new_row], ignore_index=True)
                u.save_crypto_data(df_curr)
                # 処理2：家計簿に「支出」として記録する（金額が1円以上の場合）
                if amount > 0:
                    # 区分はわかりやすく「支出」にするか、あえて「資産移動」と記録するか選べます
                    # ここでは資産集計の計算を合わせるため「支出」として記録します
                    u.add_entry(str(date), "支出", category, amount, memo)
                    msg = f"💰 {amount:,}円で {crypto_name} を {crypto_amount} 購入しました。"
                else:
                    msg = f"💎 {crypto_name} が {crypto_amount} 増えました。"
                st.success(msg)
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"資産移動エラー: {e}")
    # 支出、収入
    else:
        if amount == 0:
            st.warning('金額が0円です。入力してください。')
        else:
            try:
                u.add_entry(date, balance_type, category, amount, memo)
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
    df_display = df.copy()
    df_display.index = df_display.index + 1
    # 金額にカンマをつける
    df_display['金額'] = df_display['金額'].apply(lambda x: f"{x:,}")
    # データの並び方（新しい順）
    st.dataframe(df_display.iloc[::-1], use_container_width=True)
else:
    st.info("まだデータがありません。")

# --- データの削除 ---
st.subheader("データの削除")
with st.expander("削除メニューを開く"):
    if not df.empty:
        delete_options = df.index +1
        selected_index = st.selectbox("削除する行番号を選択", delete_options)
        # 削除の実行
        if st.button("削除実行"):
            try:
                target_row = selected_index + 1
                u.delete_entry(target_row)
                st.success("削除しました。")
                st.rerun()
            except Exception as e:
                st.error(f"削除エラー: {e}")
    else:
        st.info("削除できるデータがありません。")

# --- いろいろメモ ---
st.divider()
st.subheader("なんでもメモ")
# キャッシュに残っていないときだけ読み込む
if 'my_memo_content' not in st.session_state:
    st.session_state['my_memo_content'] = u.get_anything_memo()
new_memo = st.text_area( "", value=st.session_state['my_memo_content'], height=150 )
# 保存ボタンが押されたときだけ書き込む
if st.button("メモを保存"):
    u.update_anything_memo(new_memo)
    st.session_state['my_memo_content'] = new_memo
    st.success("保存しました！")