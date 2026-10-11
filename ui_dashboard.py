import streamlit as st
import pandas as pd
import datetime
import api
import charts
import const as c
import gsheets

def extract_salary_type(memo):
    """給与内訳を3種類（本給・超勤手当・その他）に分類する"""
    memo_str = str(memo)
    if '本給' in memo_str: return '本給'
    if '超勤手当' in memo_str: return '超勤手当'
    return 'その他'

def get_bonus_season(date_val):
    month = date_val.month
    if 6 <= month <= 8: return f"{date_val.year}年 夏季"
    if 11 <= month <= 12: return f"{date_val.year}年 冬季"
    if month == 1: return f"{date_val.year - 1}年 冬季"
    return f"{date_val.year}年 {month}月"

def render(df, df_investment, today_ts, worksheet):
    if not df.empty:
        df_current = df[df['日付'] <= today_ts]
        totals = df_current.groupby('区分')['金額'].sum()
        # 現金残高は「税金」を含めた全ての支出を引いて算出（手取り基準）
        yen_assets = totals.get('収入', 0) - totals.get('支出', 0)
    else:
        yen_assets = 0

    total_investment_assets = 0
    timestamp_display = ""
    df_hist = pd.DataFrame()
    
    if not df_investment.empty:
        all_prices = {}
        symbols = df_investment['銘柄'].unique().tolist()
        api_success = True
        
        try:
            prices1 = api.get_crypto_prices(symbols)
            prices2 = api.get_meme_prices(symbols)
            prices3 = api.get_metal_prices(symbols)
            if isinstance(prices1, dict): all_prices.update(prices1)
            if isinstance(prices2, dict): all_prices.update(prices2)
            if isinstance(prices3, dict): all_prices.update(prices3)
            
            if not all_prices or all(v == 0 for v in all_prices.values()):
                api_success = False
        except Exception:
            api_success = False

        JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
        current_time_str = datetime.datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")

        if api_success:
            gsheets.save_price_cache(worksheet, all_prices, current_time_str)
            timestamp_display = f"{current_time_str} 更新"
            
        cached_prices, cached_time, df_hist = gsheets.load_price_cache(worksheet)
        
        if not api_success:
            if cached_prices:
                all_prices = cached_prices
                timestamp_display = f"{cached_time} の履歴データを表示中"
            else:
                timestamp_display = "取得失敗"

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

    if timestamp_display:
        st.caption(f"💡 投資資産レート: {timestamp_display}")

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

    st.divider()

    # ==================================================
    # 投資資産の推移グラフ
    # ==================================================
    st.subheader("投資資産の推移")
    if not df_hist.empty and not df_investment.empty:
        df_inv = df_investment.copy()
        df_inv['日付'] = pd.to_datetime(df_inv['日付'])
        
        hist_dates = sorted(df_hist['日付'].unique())
        trend_data = []
        
        for d in hist_dates:
            current_inv = df_inv[df_inv['日付'] <= d]
            qty_sum = current_inv.groupby('銘柄')['数量'].sum()
            prices_on_d = df_hist[df_hist['日付'] == d].set_index('銘柄')['価格']
            
            total_val = 0
            for sym, qty in qty_sum.items():
                price = prices_on_d.get(sym, 0)
                total_val += qty * price
            
            if total_val > 0:
                trend_data.append({'日付': d, '評価額': int(total_val)})
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            st.altair_chart(charts.create_investment_history_chart(df_trend), use_container_width=True)
        else:
            st.info("投資履歴データがまだありません。")
    else:
        st.info("投資推移データがまだありません。1時間ごとのレート取得後に表示されます。")

    st.divider()

    # ==================================================
    # 収入の推移（給与推移グラフとボーナス一覧）
    # ==================================================
    st.subheader("収入の推移")
    
    if not df.empty:
        df_salary = df[(df['区分'] == '収入') & (df['カテゴリー'] == '給与')].copy()
        if not df_salary.empty:
            df_salary['項目'] = df_salary['メモ'].apply(extract_salary_type)
            df_salary['年月'] = df_salary['日付'].dt.strftime('%Y/%m')
            sal_grouped = df_salary.groupby(['年月', '項目'])['金額'].sum().reset_index()
            st.caption("月別 給与推移")
            st.altair_chart(charts.create_salary_chart(sal_grouped), use_container_width=True)
            
        df_bonus = df[(df['区分'] == '収入') & (df['カテゴリー'] == '賞与')].copy()
        if not df_bonus.empty:
            with st.expander("賞与（ボーナス）一覧を見る", expanded=False):
                df_bonus['時期'] = df_bonus['日付'].apply(get_bonus_season)
                # 日付を除外し、時期・金額・メモだけを表示する
                df_bonus_disp = df_bonus[['時期', '金額', 'メモ']].copy()
                df_bonus_disp['金額'] = df_bonus_disp['金額'].apply(lambda x: f"{int(x):,} 円")
                st.dataframe(df_bonus_disp.style.set_properties(**{'background-color': '#ede4ce', 'border-color': '#A1A3A6', 'border-style': 'solid'}), hide_index=True, use_container_width=True)

    st.divider()

    # ==================================================
    # グラフ表示 ── 税金を除外した支出推移 ──
    # ==================================================
    st.subheader("資産・支出推移")
    if not df.empty:
        base_df = df.copy()
        base_df['グラフ金額'] = base_df.apply(lambda x