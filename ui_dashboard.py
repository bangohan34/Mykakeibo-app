import streamlit as st
import pandas as pd
import api
import charts
import const as c

def render(df, df_investment, url_user_id):
    today = pd.Timestamp.now(tz='Asia/Tokyo').normalize().tz_localize(None)
    
    # 収支の計算
    if not df.empty:
        df_current = df[df['日付'] <= today]
        totals = df_current.groupby('区分')['金額'].sum()
        total_income = totals.get('収入', 0)
        total_expense = totals.get('支出', 0)
        yen_assets = total_income - total_expense
        current_month = today.replace(day=1)
        df_this_month = df[df['日付'] >= current_month]
        current_month_expense = df_this_month[df_this_month['区分'] == '支出']['金額'].sum()
    else:
        yen_assets = 0
        current_month_expense = 0

    # 投資資産の価値計算
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

    # 資産表示カード
    if url_user_id == "u1":
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
    if url_user_id == "u2":
        st.markdown(f"""
        <div style="display: flex; gap: 10px; justify-content: space-between;">
            <div style="flex: 1; padding: 10px; text-align: center;">
                <div style="font-size: 20px; color: gray;">今月の支出</div>
                <div style="font-size: 48px; font-weight: bold; color: #A03333;">{int(current_month_expense):,} 円</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 資産割合バー
    if url_user_id == "u1":
        total_all_assets = yen_assets + total_investment_assets
        if total_all_assets > 0:
            COLOR_YEN = '#DB4437'
            COLOR_OTHERS = "#9A9999"
            SYMBOL_COLORS = {
                'BTC':'#F4B400', 'ETH':'#9079ad', 'XRP':"#8585e7", 'IOST':'#00c8c8',
                'PI':'#9600ff', 'GOLD': '#D4AF37', 'SILVER': '#C0C0C0'
            }
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
                    display_df.style.format({"評価額": "{:,} 円"}).set_properties(**{
                        'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'
                    }), hide_index=True, use_container_width=True
                )
        else:
            st.info("投資資産の登録はまだありません。")

    # グラフ表示
    if not df.empty:
        base_df = df.copy()
        base_df['グラフ金額'] = base_df.apply(lambda x: -x['金額'] if x['区分'] == '支出' else x['金額'], axis=1)
        base_df = base_df.sort_values('日付')
        base_df['現金推移'] = base_df['グラフ金額'].cumsum()
        base_df['年月'] = base_df['日付'].apply(lambda x: x.replace(day=1))
        base_df['週'] = base_df['日付'] - pd.to_timedelta(base_df['日付'].dt.weekday, unit='D')
        graph_df = base_df[base_df['日付'] >= pd.to_datetime('2026-01-01')]
        
        if url_user_id == "u1" and not graph_df.empty:
            tab_day, tab_week, tab_month = st.tabs(["日ごと", "週ごと", "月ごと"])
            with tab_month: st.altair_chart(charts.create_combo_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0), use_container_width=True)
            with tab_week:
                df_30w = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today)]
                if not df_30w.empty: st.altair_chart(charts.create_combo_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
            with tab_day:
                df_30d = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today)]
                if not df_30d.empty: st.altair_chart(charts.create_combo_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
        elif url_user_id == "u2" and not graph_df.empty:
            tab_day, tab_week, tab_month = st.tabs(["日ごと", "週ごと", "月ごと"])
            with tab_day:
                df_30d = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today)]
                if not df_30d.empty: st.altair_chart(charts.create_expense_bar_chart(df_30d, '日付', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
            with tab_week:
                df_30w = base_df[(base_df['日付'] >= pd.to_datetime('2026-01-01')) & (base_df['日付'] <= today)]
                if not df_30w.empty: st.altair_chart(charts.create_expense_bar_chart(df_30w, '週', '%m/%d', '%Y-%m-%d', -45), use_container_width=True)
            with tab_month: st.altair_chart(charts.create_expense_bar_chart(graph_df, '年月', '%Y-%m', '%Y-%m', 0), use_container_width=True)
    
    # 支出円グラフ
    if not df.empty:
        pie_df = df.copy()
        pie_df['年月'] = pie_df['日付'].apply(lambda x: x.replace(day=1))
        months_series = pie_df['年月'].drop_duplicates()
        months_list = months_series[(months_series >= pd.to_datetime('2026-01-01')) & (months_series <= today.replace(day=1))].sort_values(ascending=False)
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

    return yen_assets