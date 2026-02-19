import streamlit as st
import datetime
import pandas as pd
import time

import const as c
import utils as u

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- ログイン ---
if "target_sheet" not in st.session_state:
    st.session_state["target_sheet"] = ""
if "current_user_name" not in st.session_state:
    st.session_state["current_user_name"] = ""
# URLパラメータを取得
query_params = st.query_params
url_user_id = query_params.get("u",None)
# ユーザー情報の取得
users_cfg = st.secrets["users"]
# ログイン
if url_user_id in users_cfg:
    user_data = users_cfg[url_user_id]
    st.session_state["target_sheet"] = user_data["sheet"]
    st.session_state["current_user_name"] = user_data["name"]
else:
    # URLに ?u= がない場合
    st.error("⚠️ アクセス権限がありません。専用のURLからアクセスしてください。")
    st.stop()

# --- データの準備 ---
worksheet = u.get_worksheet(st.session_state["target_sheet"])
df = u.load_kakeibo_data(worksheet)
df_investment = u.load_investment_data(worksheet)
today = pd.Timestamp.now(tz='Asia/Tokyo').normalize().tz_localize(None)
# サブスク追加
if "subscriptions_auto_added" not in st.session_state:
    added_count = u.auto_add_subscriptions(worksheet, df)
    if added_count > 0:
        st.toast(f"📅 今月のサブスク {added_count}件 を自動で家計簿に追加しました！", icon="✅")
        df = u.load_kakeibo_data(worksheet)  # データを再読み込み
    st.session_state["subscriptions_auto_added"] = True

# --- 入力フォーム ---
st.subheader("収支入力")
balance_type = st.radio(
    "区分",
    ["支出","収入","投資"],
    horizontal=True,
    label_visibility="collapsed"
    )
category, amount, memo, sub_category = None, 0, "", ""
crypto_name, crypto_amount = "", 0.0000
# カテゴリ選択
if balance_type =="支出":
    st.caption("支出の詳細を選んでください")
    if(url_user_id =="u1"):
        category = st.radio('項目', c.EXPENSE_CATEGORIES, horizontal=True, label_visibility="collapsed")
        sub_options = c.EXPENSE_SUB_CATEGORIES.get(category)
        if sub_options:
            st.caption(f"{category}の詳細を選んでください")
            sub_category = st.radio(
                f"{category}詳細",
                sub_options,
                horizontal=True,
                label_visibility="collapsed"
            )
    elif(url_user_id =="u2"):
        category = st.radio('項目', c.EXPENSE_CATEGORIES_saya, horizontal=True, label_visibility="collapsed")
        sub_options = c.EXPENSE_SUB_CATEGORIES_saya.get(category)
        if sub_options:
            st.caption(f"{category}の詳細を選んでください")
            sub_category = st.radio(
                f"{category}詳細",
                sub_options,
                horizontal=True,
                label_visibility="collapsed"
            )
elif balance_type =="収入":
    st.caption("収入の詳細を選んでください")
    if(url_user_id =="u1"):
        category = st.radio('項目', c.INCOME_CATEGORIES, horizontal=True, label_visibility="collapsed")
    elif(url_user_id =="u2"):
        category = st.radio('項目', c.INCOME_CATEGORIES_saya, horizontal=True, label_visibility="collapsed")
# 入力欄
with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', datetime.date.today())
    # 支出・収入
    if balance_type == "支出" or balance_type == "収入":
        amount = st.number_input('金額', min_value=0, step=1, value=None, placeholder="0")
    # 投資
    if balance_type == "投資":
        category = "投資"
        investment_name = st.text_input("銘柄名")
        investment_amount = st.number_input('数量', min_value=0.0, step=0.00000001, value=None, placeholder="0.0",format="%.8f")
        amount = st.number_input('支払い金額', min_value=0, step=1, value=None, placeholder="0")
    memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')
# データ登録
if submit_btn:
    final_memo = memo
    if sub_category:
        if final_memo:
            final_memo = f"{sub_category} {final_memo}"
        else:
            final_memo = sub_category
    if balance_type == "投資":
        if final_memo:
            final_memo = f"{investment_name} 購入 {final_memo}"
        else:
            final_memo = f"{investment_name} 購入"
    # 支出、収入
    if balance_type == "支出" or balance_type == "収入":
        if amount == None:
            st.warning('金額が0円です。入力してください。')
        else:
            try:
                u.add_entry(worksheet, date, balance_type, category, amount, final_memo)
                if balance_type =="収入":
                    st.success(f'お疲れさま！ {category} : {amount}円を登録しました。')
                else:
                    st.info(f'{category} ({sub_category if sub_category else ""}) : {amount}円を登録しました。')
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')
    # 投資
    if balance_type == "投資":
        if not investment_name:
            st.warning('銘柄名を入力してください。')
        elif amount is None or amount == 0:
            st.warning('金額を入力してください。')
        else:
            try:
                u.add_entry(worksheet, date, "支出", "投資費", amount, final_memo)
                u.add_investment_data(worksheet, date, investment_name, investment_amount, amount, final_memo)
                st.success(f'{investment_name}を登録しました！')
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー:{e}')

st.divider()

# --- 資産表示 ---
# 収支の計算
if not df.empty:
    df_current = df[df['日付'] <= today]
    totals = df_current.groupby('区分')['金額'].sum()
    total_income = totals.get('収入', 0)
    total_expense = totals.get('支出', 0)
    yen_assets = total_income - total_expense
else:
    yen_assets = 0
# 投資資産の価値計算
total_investment_assets = 0
if not df_investment.empty:
    all_prices = {}
    symbols = df_investment['銘柄'].unique().tolist()
    try:
        all_prices.update(u.get_crypto_prices(symbols))
        all_prices.update(u.get_meme_prices(symbols))
        all_prices.update(u.get_metal_prices(symbols))
    except Exception as e:
        st.error(f"価格取得中にエラーが発生しました: {e}")
    df_investment['現在レート'] = df_investment['銘柄'].map(all_prices).fillna(0)
    df_investment['評価額(円)'] = df_investment['数量'] * df_investment['現在レート']
    total_investment_assets = df_investment['評価額(円)'].sum()
    df_crypto = df_investment.sort_values(by='評価額(円)', ascending=False)
# 表示
if(url_user_id =="u1"):
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-between;">
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">現金・預金</div>
            <div style="font-size: 30px; font-weight: bold; color: #0068c9;">
                {f"{int(yen_assets):,} 円"}
            </div>
        </div>
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">投資資産</div>
            <div style="font-size: 30px; font-weight: bold; color: #ff8c00;">
                {f"{int(total_investment_assets):,} 円"}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
if(url_user_id =="u2"):
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-between;">
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 20px; color: gray;">現金・預金</div>
            <div style="font-size: 48px; font-weight: bold; color: #0068c9;">
                {f"{int(yen_assets):,} 円"}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 資産割合バー ---
if(url_user_id =="u1"):
    total_all_assets = yen_assets + total_investment_assets
    if total_all_assets > 0:
        COLOR_YEN = '#DB4437'
        COLOR_OTHERS = "#9A9999"
        SYMBOL_COLORS = {
            'BTC':'#F4B400',
            'ETH':'#9079ad',
            'XRP':"#8585e7",
            'IOST':'#00c8c8',
            'PI':'#9600ff',
            'GOLD': '#D4AF37',
            'SILVER': '#C0C0C0'
        }
        # 指定がない銘柄用の予備カラー
        DEFAULT_COLORS = ["#088146", '#4285F4', "#F43088", "#DA972B", "#81E495"]
        # ベースのHTML
        yen_ratio = (yen_assets / total_all_assets) * 100
        bars_html = f'<div style="width: {yen_ratio}%; background-color:{COLOR_YEN};" title="日本円: {yen_ratio:.1f}%"></div>'
        legend_html = f'<span style="color:{COLOR_YEN}">■</span> 日本円 '
        # 投資資産のバー作成
        others_ratio = 0
        if not df_investment.empty:
            # 同じ銘柄を合算してからループ
            df_grouped = df_investment.groupby('銘柄', as_index=False).sum()
            df_grouped = df_grouped.sort_values(by='評価額(円)', ascending=False)
            default_color_index = 0
            for i, row in df_grouped.iterrows():
                if '評価額(円)' in row and row['評価額(円)'] > 0:
                    ratio = (row['評価額(円)'] / total_all_assets) * 100
                    name = row['銘柄']
                    # 5%未満は「その他」にまとめる
                    if ratio < 5.0:
                        others_ratio += ratio
                        continue
                    # 色の決定
                    upper_name = str(name).upper()
                    if upper_name in SYMBOL_COLORS:
                        color = SYMBOL_COLORS[upper_name]
                    else:
                        color = DEFAULT_COLORS[default_color_index % len(DEFAULT_COLORS)]
                        default_color_index += 1
                    bars_html += f'<div style="width: {ratio}%; background-color: {color};" title="{name}: {ratio:.1f}%"></div>'
                    legend_html += f' <span style="color:{color}; margin-left:10px;">■</span> {name}'
        if others_ratio > 0:
            bars_html += f'<div style="width: {others_ratio}%; background-color: {COLOR_OTHERS};" title="その他: {others_ratio:.1f}%"></div>'
            legend_html += f' <span style="color:{COLOR_OTHERS}; margin-left:10px;">■</span> その他'
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

# --- 投資資産の内訳リスト ---
if(url_user_id =="u1"):
    st.write("")
    if not df_crypto.empty:
        with st.expander("資産の内訳を見る", expanded=False):
            display_df = df_investment[['銘柄', '評価額(円)']].copy()
            display_df = display_df.rename(columns={'評価額(円)': '評価額'})
            display_df = display_df.groupby('銘柄', as_index=False).sum()
            display_df['評価額'] = display_df['評価額'].astype(int)
            display_df = display_df.sort_values(by='評価額', ascending=False)
            st.dataframe(
                display_df.style.format({
                    "評価額": "{:,} 円" 
                })
                .set_properties(**{
                'background-color': '#ede4ce',
                'border-color': '#A1A3A6',
                'border-style': 'solid',
                }),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("投資資産の登録はまだありません。")

# --- 現金グラフ ---
if not df.empty:
    # データの前処理
    base_df = df.copy()
    base_df['グラフ金額'] = base_df.apply(lambda x: -x['金額'] if x['区分'] == '支出' else x['金額'], axis=1)
    base_df = base_df.sort_values('日付')
    base_df['現金推移'] = base_df['グラフ金額'].cumsum()
    base_df['年月'] = base_df['日付'].apply(lambda x: x.replace(day=1))
    # 週の始まり（月曜）の日付を計算
    base_df['週'] = base_df['日付'] - pd.to_timedelta(base_df['日付'].dt.weekday, unit='D')
    # 表示期間の絞り込み（2026年以降）
    graph_df = base_df[base_df['日付'] >= pd.to_datetime('2026-01-01')]
    if not graph_df.empty:
        tab_month, tab_week, tab_day = st.tabs(["月ごと", "週ごと", "日ごと"])
        # 月ごと
        with tab_month:
            st.altair_chart(
                u.create_combo_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0),
                use_container_width=True
            )
        # 週ごと（直近30週)
        with tab_week:
            #start_date_30w = today - pd.Timedelta(weeks=30)
            #df_30w = base_df[(base_df['日付'] >= start_date_30w) & (base_df['日付'] <= today)]
            start_date_fixed = pd.to_datetime('2026-01-01')
            df_30w = base_df[(base_df['日付'] >= start_date_fixed) & (base_df['日付'] <= today)]
            if not df_30w.empty:
                st.altair_chart(
                    u.create_combo_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45),
                    use_container_width=True
                )
            else:
                st.info("直近30週のデータはありません。")
        # 日ごと（直近30日
        with tab_day:
            #start_date_30d = today - pd.Timedelta(days=30)
            #df_30d = base_df[(base_df['日付'] >= start_date_30d) & (base_df['日付'] <= today)]
            df_30d = base_df[(base_df['日付'] >= start_date_fixed) & (base_df['日付'] <= today)]
            if not df_30d.empty:
                st.altair_chart(
                    u.create_combo_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45),
                    use_container_width=True
                )
            else:
                st.info("直近30日のデータはありません。")
    else:
        st.info("指定期間のデータはありません。")
else:
    st.info("データがありません。")

# --- 支出円グラフ ---
if not df.empty:
    # 円グラフ用のデータを準備
    pie_df = df.copy()
    pie_df['年月'] = pie_df['日付'].apply(lambda x: x.replace(day=1)) # 月単位にまとめる
    start_limit = pd.to_datetime('2026-01-01')
    current_month = pd.to_datetime('today').replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    months_series = pie_df['年月'].drop_duplicates()
    months_list = months_series[
        (months_series >= start_limit) &   # 2025年12月以降
        (months_series <= current_month)   # 今月以前（未来は除外）
    ].sort_values(ascending=False)         # 新しい順（今月→先月...）
    if not months_list.empty:
        tab_labels = months_list.dt.strftime('%Y/%m').tolist()
        tabs = st.tabs(tab_labels)
        # 各タブの中に、その月の円グラフを表示する
        for tab, month_date in zip(tabs, months_list):
            with tab:
                # その月のデータだけを抜き出す
                target_month_df = pie_df[pie_df['年月'] == month_date]
                month_total = target_month_df[target_month_df['区分'] == '支出']['金額'].sum()
                st.metric(label=f"{month_date.strftime('%Y/%m')}の支出合計", value=f"{month_total:,} 円")
                # utils.py の関数を使って円グラフ作成
                pie_chart = u.create_expense_pie_chart(target_month_df)
                if pie_chart:
                    st.altair_chart(pie_chart, use_container_width=True)
                else:
                    st.info(f"{month_date.strftime('%Y/%m')} の支出データはありません")
    else:
        st.info("データがありません")

st.divider()

# --- 履歴表示 ---
st.subheader("入力履歴")
if not df.empty:
    df_display = df[['No','日付','区分','金額','カテゴリー','メモ']].copy()
    df_display = df_display.rename(columns={'カテゴリー': '項目'})
    df_display['日付'] = df_display['日付'].dt.strftime('%y/%m/%d')
    df_display['メモ'] = df_display['メモ'].astype(str).apply(lambda x: (x[:3] + '..') if len(x) > 2 else x)
    st.dataframe(
        df_display.iloc[::-1].style
        .map(u.color_coding, subset=['区分'])
        .format({"金額": "{:,} 円"})
        .set_properties(**{
                'background-color': '#ede4ce',
                'border-color': '#A1A3A6',
                'border-style': 'solid',
        }),
        use_container_width=True,
        height=240,
        hide_index=True
    )
else:
    st.info("まだデータがありません")

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
        st.write("削除する **No** を入力してください")
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
                    preview_df = target_row[['No','日付','区分','金額','カテゴリー','メモ']].copy()
                    preview_df = preview_df.rename(columns={'カテゴリー': '項目'})
                    preview_df['日付'] = preview_df['日付'].dt.strftime('%y/%m/%d')
                    st.dataframe(
                        preview_df.style.map(u.color_coding, subset=['区分'])
                        .format({"金額": "{:,} 円"}),
                        use_container_width=True,
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

# --- サブスク管理 ---
st.subheader("サブスク管理")
if url_user_id == "u1":
    sub_expense_categories = c.EXPENSE_CATEGORIES
elif url_user_id == "u2":
    sub_expense_categories = c.EXPENSE_CATEGORIES_saya
else:
    sub_expense_categories = c.EXPENSE_CATEGORIES
# サブスクデータ読み込み
df_sub = u.load_subscription_data(worksheet)
# 一覧表示
if not df_sub.empty:
    monthly_total = df_sub['金額'].sum()
    yearly_total = monthly_total * 12
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-between;">
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">月額合計</div>
            <div style="font-size: 30px; font-weight: bold; color: #7970CA;">
                {monthly_total:,} 円
            </div>
        </div>
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">年額換算</div>
            <div style="font-size: 30px; font-weight: bold; color: #7970CA;">
                {yearly_total:,} 円
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    display_sub = df_sub[['サービス名', '金額', 'メモ']].copy()
    display_sub['金額'] = display_sub['金額'].apply(lambda x: f"{x:,} 円")
    st.dataframe(
        display_sub.style.set_properties(**{
            'background-color': '#ede4ce',
            'border-color': '#A1A3A6',
            'border-style': 'solid',
        }),
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("サブスクはまだ登録されていません。")
# 追加
with st.expander("サブスクを追加する", expanded=False):
    with st.form(key="sub_add_form", clear_on_submit=True):
        sub_service_name = st.text_input("サービス名（例：Netflix, Spotify）")
        sub_amount = st.number_input("月額金額", min_value=0, step=1, value=None, placeholder="0")
        sub_category = st.selectbox("カテゴリー", sub_expense_categories)
        sub_pay_day = st.number_input("毎月の支払日", min_value=1, max_value=31, step=1, value=1)
        sub_memo = st.text_input("メモ（任意）")
        sub_submit = st.form_submit_button("登録する")
    if sub_submit:
        if not sub_service_name:
            st.warning("サービス名を入力してください。")
        elif sub_amount is None or sub_amount == 0:
            st.warning("金額を入力してください。")
        else:
            try:
                u.add_subscription(worksheet, sub_service_name, sub_amount, sub_category, sub_pay_day, sub_memo)
                st.success(f"「{sub_service_name}」を登録しました！")
                st.rerun()
            except Exception as e:
                st.error(f"登録エラー: {e}")
# 削除
with st.expander("サブスクを削除する", expanded=False):
    if not df_sub.empty:
        del_service_options = df_sub['サービス名'].tolist()
        del_target = st.selectbox("削除するサービスを選択", del_service_options)
        if st.button("削除する", key="sub_delete_btn"):
            target_row = df_sub[df_sub['サービス名'] == del_target]
            if not target_row.empty:
                row_index = int(target_row.iloc[0]['No'])
                try:
                    u.delete_subscription(worksheet, row_index)
                    st.success(f"「{del_target}」を削除しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"削除エラー: {e}")
    else:
        st.info("削除するサブスクがありません。")

# --- なんでもメモ ---
st.subheader("なんでもメモ")
# データの準備
if 'my_memo_content' not in st.session_state:
    st.session_state['my_memo_content'] = u.get_anything_memo(worksheet)
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
        u.update_anything_memo(worksheet, new_text)
        st.session_state['my_memo_content'] = new_text
        st.success("保存しました！")
        time.sleep(0.5)
        st.rerun()
    else:
        st.info("変更点はありません。")
