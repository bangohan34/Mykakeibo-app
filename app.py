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
today = pd.to_datetime("today").normalize()

# --- 入力フォーム ---
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
                # 暗号資産の保有量を増やす
                df_curr = u.load_crypto_data()
                # 既存の保有量を取得
                if crypto_name in df_curr['銘柄'].values:
                    current_val = df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'].values[0]
                    new_val = current_val + crypto_amount
                    df_curr.loc[df_curr['銘柄'] == crypto_name, '保有量'] = new_val
                else:
                    new_row = pd.DataFrame({'銘柄': [crypto_name], '保有量': [crypto_amount]})
                    df_curr = pd.concat([df_curr, new_row], ignore_index=True)
                u.save_crypto_data(df_curr)
                # 家計簿に「支出」として記録する（金額が1円以上の場合）
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

st.divider()

# --- 資産表示 ---
# 収支の計算
if not df.empty:
    df_current = df[df['日付'] <= today]
    total_income = df_current[df['区分'] == '収入']['金額'].sum()
    total_expense = df_current[df['区分'] == '支出']['金額'].sum()
    yen_assets = total_income - total_expense
else:
    yen_assets = 0
# 暗号資産の価値計算
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
            {f"{int(yen_assets):,} 円"}
        </div>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center;">
        <div style="font-size: 14px; color: gray;">暗号資産</div>
        <div style="font-size: 30px; font-weight: bold; color: #ff8c00;">
            {f"{int(crypto_total_val):,} 円"}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 資産割合バー ---
if total_all_assets > 0:
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
    # 暗号資産のバー作成
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

# --- 暗号資産の内訳リスト ---
st.write("")
if not df_crypto.empty:
    with st.expander("暗号資産の内訳を見る", expanded=False):
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
    st.info("暗号資産の登録はまだありません。")

# --- 現金グラフ ---
st.subheader("📊 現金推移")
if not df.empty:
    # 共通データの作成（全期間で計算）
    base_df = df.copy()
    base_df['グラフ金額'] = base_df.apply(
        lambda x: -x['金額'] if x['区分'] == '支出' else x['金額'], 
        axis=1
    )
    base_df = base_df.sort_values('日付')
    base_df['現金推移'] = base_df['グラフ金額'].cumsum()
    base_df['年月'] = base_df['日付'].dt.strftime('%Y-%m')
    # 表示期間の絞り込み
    graph_df = base_df[
        (base_df['日付'] >= pd.to_datetime('2026-01-01')) &
        (base_df['日付'] <= pd.to_datetime('2026-04-30')) 
    ]
    if not graph_df.empty:
        # タブを作成
        tab_month, tab_day = st.tabs(["月ごと", "日ごと"])
        # 月ごとのグラフ
        with tab_month:
            # 月次集計
            bar_data_m = graph_df.groupby(['年月', '区分'])['グラフ金額'].sum().reset_index()
            line_data_m = graph_df.groupby('年月')['現金推移'].last().reset_index()
            common_x_m = alt.X('年月', axis=alt.Axis(title=None, labelAngle=0))
            bars_m = alt.Chart(bar_data_m).mark_bar().encode(
                x=common_x_m,
                y=alt.Y('グラフ金額', axis=alt.Axis(title='月間収支 & 保有現金 (円)', grid=True)),
                color=alt.Color('区分', scale=alt.Scale(domain=['収入', '支出'], range=["#35c787", "#cf4242"]), legend=None),
                tooltip=['年月', '区分', alt.Tooltip('グラフ金額', format=',', title='金額')]
            )
            line_m = alt.Chart(line_data_m).mark_line(color="#498dd1", point=True).encode(
                x=common_x_m,
                y='現金推移',
                tooltip=[alt.Tooltip('年月', title='年月'), alt.Tooltip('現金推移', format=',', title='残高')]
            )
            combo_m = alt.layer(bars_m, line_m).resolve_scale(y='shared').properties(height=300)
            st.altair_chart(combo_m, use_container_width=True)
        # 日ごとのグラフ
        with tab_day:
            # 日次集計
            bar_data_d = graph_df.groupby(['日付', '区分'])['グラフ金額'].sum().reset_index()
            # その日の「最終的な残高」を取得
            line_data_d = graph_df.groupby('日付')['現金推移'].last().reset_index()
            # 日付のフォーマット（例: 1/15）
            common_x_d = alt.X('日付', axis=alt.Axis(format='%m/%d', title=None, labelAngle=-45))
            bars_d = alt.Chart(bar_data_d).mark_bar().encode(
                x=common_x_d,
                y=alt.Y('グラフ金額', axis=alt.Axis(title='日次収支 & 保有現金 (円)', grid=True)),
                color=alt.Color('区分', scale=alt.Scale(domain=['収入', '支出'], range=["#35c787", "#cf4242"]), legend=None),
                tooltip=[
                    alt.Tooltip('日付', format='%Y/%m/%d', title='日付'),
                    '区分', 
                    alt.Tooltip('グラフ金額', format=',', title='金額')
                ]
            )
            line_d = alt.Chart(line_data_d).mark_line(color="#498dd1", point=True).encode(
                x=common_x_d,
                y='現金推移',
                tooltip=[
                    alt.Tooltip('日付', format='%Y/%m/%d', title='日付'),
                    alt.Tooltip('現金推移', format=',', title='残高')
                ]
            )
            combo_d = alt.layer(bars_d, line_d).resolve_scale(y='shared').properties(height=300)
            st.altair_chart(combo_d, use_container_width=True)
    else:
        st.info("指定期間のデータはありません。")
else:
    st.info("データがありません。")

st.divider()

# --- 履歴表示 ---
st.subheader("入力履歴")
if not df.empty:
    df_display = df.copy()
    df_display.index = df_display.index + 1
    df_display['日付'] = df_display['日付'].dt.strftime('%y/%m/%d')
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

st.divider()

# --- なんでもメモ ---
st.subheader("なんでもメモ")
# データの準備
if 'my_memo_content' not in st.session_state:
    st.session_state['my_memo_content'] = u.get_anything_memo()
if "memo_area" not in st.session_state:
    st.session_state["memo_area"] = st.session_state['my_memo_content']
saved_text = st.session_state['my_memo_content']
line_count = saved_text.count('\n') + 1
dynamic_height = max(150, line_count * 25)
# 入力欄
current_text = st.text_area(
    "メモ",
    key="memo_area",
    height=dynamic_height,
    label_visibility="collapsed"
)
# 入力内容と保存済み内容が同じかどうか
is_unsaved = (current_text != saved_text)
if is_unsaved:
    st.markdown(":warning: **<span style='color:#ff4b4b'>変更が保存されていません。</span>**", unsafe_allow_html=True)
    btn_type = "primary"
    btn_label = "変更を保存する"
else:
    btn_type = "secondary"
    btn_label = "保存済み"
# 保存ボタンが押されたときだけ書き込む
if st.button(btn_label, type=btn_type):
    if is_unsaved:
        new_text = st.session_state["memo_area"]
        u.update_anything_memo(new_text)
        st.session_state['my_memo_content'] = new_text
        st.success("保存しました！")
        time.sleep(0.5)
        st.rerun()
    else:
        st.info("変更点はありません。")
