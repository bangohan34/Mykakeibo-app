import streamlit as st
import datetime
import pandas as pd
import time

import const as c
import gsheets
import api
import charts

# --- 画面設定 ---
st.set_page_config(page_title="家計簿", page_icon="💰")
st.markdown(c.hide_streamlit_style, unsafe_allow_html=True)

# --- ログイン ---
if "target_sheet" not in st.session_state:
    st.session_state["target_sheet"] = ""
if "current_user_name" not in st.session_state:
    st.session_state["current_user_name"] = ""

query_params = st.query_params
url_user_id = query_params.get("u", None)
users_cfg = st.secrets.get("users", {})

if url_user_id in users_cfg:
    user_data = users_cfg[url_user_id]
    st.session_state["target_sheet"] = user_data["sheet"]
    st.session_state["current_user_name"] = user_data["name"]
else:
    st.error("⚠️ アクセス権限がありません。正しいURLからアクセスしてください。")
    st.stop()

# --- データの準備 ---
# ★ 日本時間 (JST) を厳密に設定
JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
today_jst = datetime.datetime.now(JST).date()
today_ts = pd.Timestamp.now(tz='Asia/Tokyo').normalize().tz_localize(None)

worksheet = gsheets.get_worksheet(st.session_state["target_sheet"])
df = gsheets.load_kakeibo_data(worksheet)
df_investment = gsheets.load_investment_data(worksheet)

if "subscriptions_auto_added" not in st.session_state:
    added_count = gsheets.auto_add_subscriptions(worksheet, df)
    if added_count > 0:
        st.toast(f"📅 今月のサブスク {added_count}件 を自動で家計簿に追加しました！", icon="✅")
        df = gsheets.load_kakeibo_data(worksheet)
    st.session_state["subscriptions_auto_added"] = True

# ==========================================
# 入力フォーム
# ==========================================
st.subheader("収支入力")
balance_type = st.radio("区分", ["支出","収入","投資"], horizontal=True, label_visibility="collapsed")
category, amount, memo, sub_category = None, 0, "", ""
investment_name, investment_amount = "", 0.0000

if balance_type == "支出":
    st.caption("支出の詳細を選んでください")
    category = st.radio('項目', c.EXPENSE_CATEGORIES, horizontal=True, label_visibility="collapsed")
    sub_options = c.EXPENSE_SUB_CATEGORIES.get(category)
    if sub_options:
        st.caption(f"{category}の詳細を選んでください")
        sub_category = st.radio(f"{category}詳細", sub_options, horizontal=True, label_visibility="collapsed")
elif balance_type == "収入":
    st.caption("収入の詳細を選んでください")
    category = st.radio('項目', c.INCOME_CATEGORIES, horizontal=True, label_visibility="collapsed")

with st.form(key='entry_form', clear_on_submit=True):
    date = st.date_input('日付', today_jst) # ★ JSTを適用
    if balance_type in ["支出", "収入"]:
        amount = st.number_input('金額', min_value=0, step=1, value=None, placeholder="0")
    if balance_type == "投資":
        category = "投資"
        investment_name = st.text_input("銘柄名")
        investment_amount = st.number_input('数量', min_value=0.0, step=0.00000001, value=None, placeholder="0.0",format="%.8f")
        amount = st.number_input('支払い金額', min_value=0, step=1, value=None, placeholder="0")
    memo = st.text_input('メモ（任意）')
    submit_btn = st.form_submit_button('登録する')

if submit_btn:
    final_memo = f"{sub_category} {memo}" if sub_category and memo else sub_category or memo
    if balance_type == "投資":
        final_memo = f"{investment_name} 購入 {final_memo}" if final_memo else f"{investment_name} 購入"
    
    if balance_type in ["支出", "収入"]:
        if amount is None:
            st.warning('金額が0円です。入力してください。')
        else:
            try:
                gsheets.add_entry(worksheet, date, balance_type, category, amount, final_memo)
                msg = f'お疲れさま！ {category} : {amount}円を登録しました。' if balance_type == "収入" else f'{category} ({sub_category if sub_category else ""}) : {amount}円を登録しました。'
                st.success(msg) if balance_type == "収入" else st.info(msg)
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー: {e}')
    elif balance_type == "投資":
        if not investment_name: st.warning('銘柄名を入力してください。')
        elif amount is None or amount == 0: st.warning('金額を入力してください。')
        else:
            try:
                gsheets.add_entry(worksheet, date, "支出", "投資費", amount, final_memo)
                gsheets.add_investment_data(worksheet, date, investment_name, investment_amount, amount, final_memo)
                st.success(f'{investment_name}を登録しました！')
                st.balloons()
                time.sleep(3)
                st.rerun()
            except Exception as e:
                st.error(f'書き込みエラー:{e}')

st.divider()

# ==========================================
# 資産表示・ダッシュボード
# ==========================================
if not df.empty:
    df_current = df[df['日付'] <= today_ts]
    totals = df_current.groupby('区分')['金額'].sum()
    yen_assets = totals.get('収入', 0) - totals.get('支出', 0)
else:
    yen_assets = 0

total_investment_assets = 0
if not df_investment.empty:
    all_prices = {}
    symbols = df_investment['銘柄'].unique().tolist()
    try:
        all_prices.update(api.get_crypto_prices(symbols))
        all_prices.update(api.get_meme_prices(symbols))
        all_prices.update(api.get_metal_prices(symbols))
    except Exception as e:
        st.error(f"価格取得中にエラーが発生しました: {e}")
    df_investment['現在レート'] = df_investment['銘柄'].map(all_prices).fillna(0)
    df_investment['評価額(円)'] = df_investment['数量'] * df_investment['現在レート']
    total_investment_assets = df_investment['評価額(円)'].sum()
    df_crypto = df_investment.sort_values(by='評価額(円)', ascending=False)

st.markdown(f"""
<div style="display: flex; gap: 10px; justify-content: space-between;">
    <div style="flex: 1; padding: 10px; text-align: center;">
        <div style="font-size: 14px; color: gray;">現金・預金</div>
        <div style="font-size: 30px; font-weight: bold; color: #0068c9;">{int(yen_assets):,} 円</div>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center;">
        <div style="font-size: 14px; color: gray;">投資資産</div>
        <div style="font-size: 30px; font-weight: bold; color: #ff8c00;">{int(total_investment_assets):,} 円</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 資産割合バー
total_all_assets = yen_assets + total_investment_assets
if total_all_assets > 0:
    COLOR_YEN = '#DB4437'
    COLOR_OTHERS = "#9A9999"
    SYMBOL_COLORS = {'BTC':'#F4B400', 'ETH':'#9079ad', 'XRP':"#8585e7", 'IOST':'#00c8c8', 'PI':'#9600ff', 'GOLD': '#D4AF37', 'SILVER': '#C0C0C0'}
    DEFAULT_COLORS = ["#088146", '#4285F4', "#F43088", "#DA972B", "#81E495"]
    
    yen_ratio = (yen_assets / total_all_assets) * 100
    bars_html = f'<div style="width: {yen_ratio}%; background-color:{COLOR_YEN};" title="日本円: {yen_ratio:.1f}%"></div>'
    legend_html = f'<span style="color:{COLOR_YEN}">■</span> 日本円 '
    
    others_ratio = 0
    if not df_investment.empty:
        df_grouped = df_investment.groupby('銘柄', as_index=False).sum().sort_values(by='評価額(円)', ascending=False)
        default_color_index = 0
        for i, row in df_grouped.iterrows():
            if '評価額(円)' in row and row['評価額(円)'] > 0:
                ratio = (row['評価額(円)'] / total_all_assets) * 100
                name = row['銘柄']
                if ratio < 5.0:
                    others_ratio += ratio
                    continue
                color = SYMBOL_COLORS.get(str(name).upper(), DEFAULT_COLORS[default_color_index % len(DEFAULT_COLORS)])
                if color not in SYMBOL_COLORS.values(): default_color_index += 1
                bars_html += f'<div style="width: {ratio}%; background-color: {color};" title="{name}: {ratio:.1f}%"></div>'
                legend_html += f' <span style="color:{color}; margin-left:10px;">■</span> {name}'
    if others_ratio > 0:
        bars_html += f'<div style="width: {others_ratio}%; background-color: {COLOR_OTHERS};" title="その他: {others_ratio:.1f}%"></div>'
        legend_html += f' <span style="color:{COLOR_OTHERS}; margin-left:10px;">■</span> その他'
    
    st.markdown(f"""
    <div style="display: flex; width: 100%; height: 24px; background-color: #e0e0e0; border-radius: 5px; overflow: hidden;">{bars_html}</div>
    <div style="font-size: 12px; margin-top: 5px; color: #333;">{legend_html}</div>
    """, unsafe_allow_html=True)

st.write("")
if not df_investment.empty:
    with st.expander("資産の内訳を見る", expanded=False):
        display_df = df_investment[['銘柄', '評価額(円)']].copy().rename(columns={'評価額(円)': '評価額'})
        display_df = display_df.groupby('銘柄', as_index=False).sum()
        display_df['評価額'] = display_df['評価額'].astype(int)
        display_df = display_df.sort_values(by='評価額', ascending=False)
        st.dataframe(
            display_df.style.format({"評価額": "{:,} 円"}).set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}),
            hide_index=True, use_container_width=True
        )
else:
    st.info("投資資産の登録はまだありません。")

# グラフ
if not df.empty:
    base_df = df.copy()
    base_df['グラフ金額'] = base_df.apply(lambda x: -x['金額'] if x['区分'] == '支出' else x['金額'], axis=1)
    base_df = base_df.sort_values('日付')
    base_df['現金推移'] = base_df['グラフ金額'].cumsum()
    base_df['年月'] = base_df['日付'].apply(lambda x: x.replace(day=1))
    base_df['週'] = base_df['日付'] - pd.to_timedelta(base_df['日付'].dt.weekday, unit='D')
    graph_df = base_df[base_df['日付'] >= pd.to_datetime('2026-01-01')]
    
    if not graph_df.empty:
        tab_day, tab_week, tab_month = st.tabs(["日ごと", "週ごと", "月ごと"])
        with tab_month:
            st.altair_chart(charts.create_combo_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0), use_container_width=True)
        with tab_week:
            df_30w = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today_ts)]
            if not df_30w.empty: st.altair_chart(charts.create_combo_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
        with tab_day:
            df_30d = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today_ts)]
            if not df_30d.empty: st.altair_chart(charts.create_combo_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)

# 円グラフ
if not df.empty:
    pie_df = df.copy()
    pie_df['年月'] = pie_df['日付'].apply(lambda x: x.replace(day=1))
    months_series = pie_df['年月'].drop_duplicates()
    months_list = months_series[(months_series >= pd.to_datetime('2026-01-01')) & (months_series <= today_ts.replace(day=1))].sort_values(ascending=False)
    if not months_list.empty:
        tabs = st.tabs(months_list.dt.strftime('%Y/%m').tolist())
        for tab, month_date in zip(tabs, months_list):
            with tab:
                target_month_df = pie_df[pie_df['年月'] == month_date]
                month_total = target_month_df[target_month_df['区分'] == '支出']['金額'].sum()
                st.metric(label=f"{month_date.strftime('%Y/%m')}の支出合計", value=f"{month_total:,} 円")
                pie_chart = charts.create_expense_pie_chart(target_month_df)
                if pie_chart: st.altair_chart(pie_chart, use_container_width=True)
                else: st.info(f"{month_date.strftime('%Y/%m')} の支出データはありません")

st.divider()

# ==========================================
# 履歴表示・削除
# ==========================================
st.subheader("入力履歴")
if not df.empty:
    df_display = df[['No','日付','区分','金額','カテゴリー','メモ']].copy().rename(columns={'カテゴリー': '項目'})
    df_display['日付'] = df_display['日付'].dt.strftime('%y/%m/%d')
    df_display['メモ'] = df_display['メモ'].astype(str).apply(lambda x: (x[:3] + '..') if len(x) > 2 else x)
    st.dataframe(
        # ★ .head(50) を追加し、過去50件に制限
        df_display.iloc[::-1].head(50).style
        .map(gsheets.color_coding, subset=['区分'])
        .format({"金額": "{:,} 円"})
        .set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}),
        use_container_width=True, height=240, hide_index=True
    )
else:
    st.info("まだデータがありません")

st.subheader("データの削除")
if "delete_msg" not in st.session_state: st.session_state["delete_msg"] = None
if "menu_reset_id" not in st.session_state: st.session_state["menu_reset_id"] = 0
if "del_confirm_ckeck" not in st.session_state: st.session_state["del_confirm_ckeck"] = False

if st.session_state["delete_msg"]:
    if "エラー" in st.session_state["delete_msg"]: st.error(st.session_state["delete_msg"])
    else:
        st.success(st.session_state["delete_msg"])
        st.session_state["delete_msg"] = None
        time.sleep(1)
        st.rerun()

with st.expander("削除メニューを開く", expanded=False):
    if not df.empty:
        st.write("削除する **No** を入力してください")
        target_no = st.number_input("削除するNo", min_value=1, step=1, value=None, format="%d", label_visibility="collapsed", key="delete_input_no")
        if st.checkbox("削除対象を確認する", key="del_confirm_ckeck"):
            if target_no:
                target_row = df[df['No'] == target_no]
                if not target_row.empty:
                    st.warning("⚠️ 以下のデータを本当に削除しますか？")
                    preview_df = target_row[['No','日付','区分','金額','カテゴリー','メモ']].copy().rename(columns={'カテゴリー': '項目'})
                    preview_df['日付'] = preview_df['日付'].dt.strftime('%y/%m/%d')
                    st.dataframe(preview_df.style.map(gsheets.color_coding, subset=['区分']).format({"金額": "{:,} 円"}), use_container_width=True, hide_index=True)
                    st.button("はい、削除します", on_click=gsheets.delete_callback)
                else: st.error("そのNoのデータは見つかりませんでした。")
            else: st.info("Noを入力してください。")
    else: st.info("データがありません。")

st.divider()

# ==========================================
# サブスク管理
# ==========================================
st.subheader("サブスク管理")
df_sub = gsheets.load_subscription_data(worksheet)
if not df_sub.empty:
    monthly_total = df_sub['金額'].sum()
    yearly_total = monthly_total * 12
    st.markdown(f"""
    <div style="display: flex; gap: 10px; justify-content: space-between;">
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">月額合計</div>
            <div style="font-size: 30px; font-weight: bold; color: #b22222;">{monthly_total:,} 円</div>
        </div>
        <div style="flex: 1; padding: 10px; text-align: center;">
            <div style="font-size: 14px; color: gray;">年額換算</div>
            <div style="font-size: 30px; font-weight: bold; color: #b22222;">{yearly_total:,} 円</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    display_sub = df_sub[['サービス名', '金額', 'メモ']].copy()
    display_sub['金額'] = display_sub['金額'].apply(lambda x: f"{x:,} 円")
    st.dataframe(display_sub.style.set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}), hide_index=True, use_container_width=True)
else:
    st.info("サブスクはまだ登録されていません。")

with st.expander("サブスクを追加する", expanded=False):
    with st.form(key="sub_add_form", clear_on_submit=True):
        sub_service_name = st.text_input("サービス名（例：Netflix, Spotify）")
        sub_amount = st.number_input("月額金額", min_value=0, step=1, value=None, placeholder="0")
        sub_category = st.selectbox("カテゴリー", c.EXPENSE_CATEGORIES)
        sub_pay_day = st.number_input("毎月の支払日", min_value=1, max_value=31, step=1, value=1)
        sub_memo = st.text_input("メモ（任意）")
        sub_submit = st.form_submit_button("登録する")
    if sub_submit:
        if not sub_service_name or sub_amount is None or sub_amount == 0:
            st.warning("サービス名と金額を入力してください。")
        else:
            try:
                gsheets.add_subscription(worksheet, sub_service_name, sub_amount, sub_category, sub_pay_day, sub_memo)
                st.success(f"「{sub_service_name}」を登録しました！")
                st.rerun()
            except Exception as e: st.error(f"登録エラー: {e}")

with st.expander("サブスクを削除する", expanded=False):
    if not df_sub.empty:
        del_options = [""] + df_sub['サービス名'].tolist()
        del_target = st.selectbox("削除するサービスを選択", del_options, index=0)
        if del_target:
            target_row = df_sub[df_sub['サービス名'] == del_target]
            if st.checkbox("削除対象を確認する", key="sub_del_confirm"):
                st.warning("⚠️ 以下のサブスクを本当に削除しますか？")
                preview = target_row[['サービス名', '金額', 'メモ']].copy()
                preview['金額'] = preview['金額'].apply(lambda x: f"{x:,} 円")
                st.dataframe(preview.style.set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}), hide_index=True, use_container_width=True)
                if st.button("はい、削除します", key="sub_delete_btn"):
                    try:
                        gsheets.delete_subscription(worksheet, int(target_row.iloc[0]['No']))
                        st.success(f"「{del_target}」を削除しました！")
                        st.rerun()
                    except Exception as e: st.error(f"削除エラー: {e}")
    else: st.info("削除するサブスクがありません。")

st.divider()

# ==========================================
# 資産確認・調整
# ==========================================
st.subheader("資産確認・調整")
with st.expander("資産確認を開く", expanded=False):
    st.caption("現在の残高・未払い額を入力してください")
    account_total = sum(st.number_input(account, min_value=0, step=1, value=0, key=f"ac_{account}") for account in c.ASSET_CHECK_ACCOUNTS)
    
    st.caption("クレカ未払い分（残高から引かれます）")
    credit_total = sum(st.number_input(credit, min_value=0, step=1, value=0, key=f"cr_{credit}") for credit in c.ASSET_CHECK_CREDITS)
    
    real_assets = account_total - credit_total
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("実際の資産", f"{real_assets:,} 円")
    col2.metric("アプリ上の資産", f"{int(yen_assets):,} 円")
    diff = real_assets - int(yen_assets)
    col3.metric("差額", f"{diff:,} 円", delta=f"{diff:,}")
    
    if diff != 0:
        st.warning(f"{'不足' if diff < 0 else '超過'} {abs(diff):,} 円のズレがあります")
        if st.button("この差額を家計簿に記入する"):
            b_type = '収入' if diff > 0 else '支出'
            gsheets.add_entry(worksheet, today_jst, b_type, 'その他', abs(diff), '資産調整')
            st.success(f"差額 {abs(diff):,} 円を「その他」で記入しました！")
            time.sleep(1)
            st.rerun()
    else:
        st.success("✅ アプリ上の資産と実際の資産が一致しています！")

st.divider()

# ==========================================
# なんでもメモ
# ==========================================
st.subheader("なんでもメモ")
if 'my_memo_content' not in st.session_state:
    st.session_state['my_memo_content'] = gsheets.get_anything_memo(worksheet)
if "memo_area" not in st.session_state:
    st.session_state["memo_area"] = st.session_state['my_memo_content']

saved_text = st.session_state['my_memo_content']
dynamic_height = max(150, (saved_text.count('\n') + 1) * 25)
current_text = st.text_area("メモ", key="memo_area", height=dynamic_height, label_visibility="collapsed")
is_unsaved = (current_text != saved_text)

if is_unsaved:
    st.markdown(":warning: **<span style='color:#ff4b4b'>変更が保存されていません。</span>**", unsafe_allow_html=True)
    btn_type, btn_label = "primary", "変更を保存する"
else:
    btn_type, btn_label = "secondary", "保存済み"

if st.button(btn_label, type=btn_type):
    if is_unsaved:
        new_text = st.session_state["memo_area"]
        gsheets.update_anything_memo(worksheet, new_text)
        st.session_state['my_memo_content'] = new_text
        st.success("保存しました！")
        time.sleep(0.5)
        st.rerun()
    else:
        st.info("変更点はありません。")