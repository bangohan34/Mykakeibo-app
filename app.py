import streamlit as st
import datetime
import pandas as pd
import time
import altair as alt

import const as c
import utils as u

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- データの準備 ---
df = u.load_kakeibo_data()
df_crypto = u.load_crypto_data()

# --- タイトル＆資産表示・非表示 ---
st.markdown("""
<style>
    /* 1. 画面が狭くても横並びを維持する（縦並び防止） */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    /* 2. カラムが画面幅からはみ出ないように縮小可能にする（はみ出し防止） */
    div[data-testid="column"] {
        min-width: 0 !important;
        flex: 1 1 auto !important;
    }
    /* 3. トグルの余計なマージンを消して高さを合わせる */
    .stCheckbox {
        margin-top: -5px !important;
        white-space: nowrap !important; /* ラベルの折り返し禁止 */
    }
</style>
""", unsafe_allow_html=True)
col_title, col_toggle = st.columns([2.5, 1], gap="small", vertical_alignment="center")
with col_title:
    st.markdown("### マイ家計簿")
with col_toggle:
    show_assets = st.toggle("資産表示", value=True)

# --- 資産表示 ---
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
    # 評価額(円)で並び替え
    df_crypto = df_crypto.sort_values(by='評価額(円)', ascending=False)
# 合計の計算
total_all_assets = yen_assets + crypto_total_val
# 表示
st.markdown(f"""
<div style="display: flex; gap: 10px; justify-content: space-between;">
    <div style="flex: 1; padding: 10px; text-align: center;">
        <div style="font-size: 14px; color: gray;">現金・預金</div>
        <div style="font-size: 30px; font-weight: bold; color: #0068c9;">
            {u.format_money(yen_assets, show_assets)}
        </div>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center;">
        <div style="font-size: 14px; color: gray;">仮想通貨</div>
        <div style="font-size: 30px; font-weight: bold; color: #ff8c00;">
            {u.format_money(crypto_total_val, show_assets)}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 資産割合バー ---
if total_all_assets > 0:
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
    DEFAULT_COLORS = ['#0F9D58', '#4285F4', '#F4B400', '#AB47BC', '#00ACC1']
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
    <div style="display: flex; width: 100%; height: 24px; background-color: #e0e0e0; border-radius: 5px; overflow: hidden;">
        {bars_html}
    </div>
    <div style="font-size: 12px; margin-top: 5px; color: #333;">
        {legend_html}
    </div>
    """
    st.markdown(final_html, unsafe_allow_html=True)

# --- 仮想通貨の内訳リスト ---
st.write("")
if not df_crypto.empty:
    with st.expander("仮想通貨の内訳を見る", expanded=False):
        display_df = df_crypto[['銘柄', '保有量', '評価額(円)']].copy()
        display_df = display_df.rename(columns={'評価額(円)': '評価額'})
        display_df['保有量'] = display_df['保有量'].astype(float)
        display_df['評価額'] = display_df['評価額'].astype(int)
        st.dataframe(
            display_df.style.format({
                "保有量": "{:.8f}",
                "評価額": "{:,} 円" 
            }),
            hide_index=True,
            use_container_width=True
        )
else:
    st.info("仮想通貨の登録はまだありません。")

# --- 入力フォーム ---
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
                time.sleep(2)
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
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')

# --- 履歴表示 ---
st.divider()
st.subheader("入力履歴")
if not df.empty:
    df_display = df.copy()
    df_display.index = df_display.index + 1
    df_display['日付'] = df_display['日付'].dt.strftime('%m/%d')
    st.dataframe(
        df_display.iloc[::-1].style.map(u.color_coding, subset=['区分'])
        .format({"金額": "{:,} 円"}),
        use_container_width=True,
        height=240,
        hide_index=True
    )
else:
    st.info("まだデータがありません。")

# --- データの削除 ---
st.subheader("データの削除")
# 削除に関する変数の初期化
if "delete_msg" not in st.session_state:
    st.session_state["delete_msg"] = None
if "menu_reset_id" not in st.session_state:
    st.session_state["menu_reset_id"] = 0
if "del_confirm_ckeck" not in st.session_state:
    st.session_state["del_confirm_ckeck"] = False
# 処理完了後のメッセージ表示エリア
if st.session_state["delete_msg"]:
    if "エラー" in st.session_state["delete_msg"]:
        st.error(st.session_state["delete_msg"])
    else:
        st.success(st.session_state["delete_msg"])
        # メッセージを表示したら、次回のために空にする
        st.session_state["delete_msg"] = None
        time.sleep(1)
        st.rerun()
# 削除メニュー
current_menu_key = f"del_menu_{st.session_state['menu_reset_id']}"
with st.expander("削除メニューを開く", expanded=False):
    if not df.empty:
        st.write("削除する **No** を入力してください。")
        target_no = st.number_input(
            "削除するNo", min_value=1, step=1,
            value=None,
            format="%d",
            label_visibility="collapsed",
            key="delete_input_no"
        )
        # 確認用のチェックボックス
        if st.checkbox("削除対象を確認する", key="del_confirm_ckeck"):
            if target_no:
                target_row = df[df['No'] == target_no]
                # データが見つかった場合
                if not target_row.empty:
                    st.warning("⚠️ 以下のデータを本当に削除しますか？")
                    # 削除対象をプレビュー表示
                    st.dataframe(
                        target_row.style.format({"金額": "{:,} 円"}), 
                        hide_index=True
                    )
                    st.button("はい、削除します", on_click=u.delete_callback)
                else:
                    st.error("そのNoのデータは見つかりませんでした。")
            else:
                st.info("Noを入力してください。")
    else:
        st.info("データがありません。")

# --- 資産グラフ ---
st.divider()
# データの加工
chart_df = df.copy()
chart_df['年月'] = chart_df['日付'].dt.strftime('%Y-%m') # 年-月 の形にする
# 支出ならマイナス、収入ならプラスにする計算
chart_df['グラフ金額'] = chart_df.apply(
    lambda x: -x['金額'] if x['区分'] == '支出' else x['金額'], 
    axis=1
)
# 現金の累積を計算
line_df = chart_df.sort_values('日付')
line_df['現金推移'] = line_df['グラフ金額'].cumsum()
# 棒グラフ 現金の月ごとの合計
bars = alt.Chart(chart_df).mark_bar().encode(
    x='年月',
    y='sum(グラフ金額)',
    color=alt.Color('区分', scale=alt.Scale(range=['#28a745', '#dc3545']))
)
# 折れ線グラフ 現金推移
line = alt.Chart(line_df).mark_line(color='blue').encode(
    x='年月',
    y='max(現金推移)'
)
# 重ねて表示
st.altair_chart(alt.layer(bars, line).resolve_scale(y='shared'), use_container_width=True)

# --- いろいろメモ ---
st.divider()
st.subheader("なんでもメモ")
# キャッシュに残っていないときだけ読み込む
if 'my_memo_content' not in st.session_state:
    st.session_state['my_memo_content'] = u.get_anything_memo()
new_memo = st.text_area(
    "メモ",
    value=st.session_state['my_memo_content'],
    height=150,
    label_visibility="collapsed"
)
# 保存ボタンが押されたときだけ書き込む
if st.button("メモを保存"):
    u.update_anything_memo(new_memo)
    st.session_state['my_memo_content'] = new_memo
    st.success("保存しました！")
