import streamlit as st
import pandas as pd
import api
import charts
import const as c

def render(df, df_investment, today_ts):
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
            df_grouped = df_investment.groupby('銘柄', as_index=False).sum(numeric_only=True).sort_values(by='評価額(円)', ascending=False)
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
            display_df = display_df.groupby('銘柄', as_index=False).sum(numeric_only=True)
            display_df['評価額'] = display_df['評価額'].astype(int)
            display_df = display_df.sort_values(by='評価額', ascending=False)
            st.dataframe(
                display_df.style.format({"評価額": "{:,} 円"}).set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}),
                hide_index=True, use_container_width=True
            )
    else:
        st.info("投資資産の登録はまだありません。")

    st.divider()

    # --- グラフ表示 ---
    st.subheader("資産・支出推移")
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
                st.caption("現金残高推移")
                st.altair_chart(charts.create_balance_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0), use_container_width=True)
                st.caption("支出推移")
                st.altair_chart(charts.create_expense_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0), use_container_width=True)
            with tab_week:
                df_30w = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today_ts)]
                if not df_30w.empty:
                    st.caption("現金残高推移")
                    st.altair_chart(charts.create_balance_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
                    st.caption("支出推移")
                    st.altair_chart(charts.create_expense_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
            with tab_day:
                df_30d = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today_ts)]
                if not df_30d.empty:
                    st.caption("現金残高推移")
                    st.altair_chart(charts.create_balance_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
                    st.caption("支出推移")
                    st.altair_chart(charts.create_expense_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)

    st.divider()

    # --- 光熱費の比較 ---
    st.subheader("光熱費の比較")
    if not df.empty:
        utils_df = df[(df['区分'] == '支出') & (df['カテゴリー'] == '生活費')].copy()
        def classify_utility(memo):
            memo_str = str(memo)
            if '電気' in memo_str: return '電気'
            if 'ガス' in memo_str: return 'ガス'
            if '水道' in memo_str: return '水道'
            return None
        
        utils_df['種類'] = utils_df['メモ'].apply(classify_utility)
        utils_df = utils_df.dropna(subset=['種類'])
        
        if not utils_df.empty:
            utils_df['年月'] = utils_df['日付'].apply(lambda x: x.replace(day=1).strftime('%Y-%m'))
            utils_grouped = utils_df.groupby(['年月', '種類'])['金額'].sum().reset_index()
            st.altair_chart(charts.create_utilities_chart(utils_grouped), use_container_width=True)
        else:
            st.info("光熱費のデータがありません（生活費カテゴリー内でメモに「ガス」「電気」「水道」を含むデータが対象です）")

    st.divider()

    # --- 支出内訳 (横棒グラフ) ---
    st.subheader("支出内訳 (月別)")
    if not df.empty:
        pie_df = df.copy()
        pie_df['年月'] = pie_df['日付'].apply(lambda x: x.replace(day=1))
        months_series = pie_df['年月'].drop_duplicates()
        months_list = months_series[(months_series >= pd.to_datetime('2026-01-01')) & (months_series <= today_ts.replace(day=1))].sort_values(ascending=False)
        
        if not months_list.empty:
            tabs = st.tabs(months_list.dt.strftime('%Y/%m').tolist())
            for tab, month_date in zip(tabs, months_list):
                with tab:
                    target_month_df = pie_df[(pie_df['年月'] == month_date) & (pie_df['区分'] == '支出')]
                    month_total = target_month_df['金額'].sum()
                    st.metric(label=f"{month_date.strftime('%Y/%m')}の支出合計", value=f"{month_total:,} 円")
                    
                    if month_total > 0:
                        cat_grouped = target_month_df.groupby('カテゴリー')['金額'].sum().sort_values(ascending=False)
                        bars_html = ""
                        legend_html = ""
                        for cat, val in cat_grouped.items():
                            ratio = (val / month_total) * 100
                            color = c.PIE_CHART_CATEGORIES_COLORS.get(cat, '#CFCFCF')
                            bars_html += f'<div style="width: {ratio}%; background-color: {color};" title="{cat}: {ratio:.1f}%"></div>'
                            legend_html += f' <span style="display:inline-block; margin: 4px 10px 4px 0;"><span style="color:{color};">■</span> {cat} ({val:,}円)</span>'
                        
                        st.markdown(f"""
                        <div style="display: flex; width: 100%; height: 24px; background-color: #e0e0e0; border-radius: 5px; overflow: hidden; margin-bottom: 8px;">{bars_html}</div>
                        <div style="font-size: 13px; color: #333; line-height: 1.5;">{legend_html}</div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info(f"{month_date.strftime('%Y/%m')} の支出データはありません")

    return yen_assets