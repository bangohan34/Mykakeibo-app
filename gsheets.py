# ==========================================
# ★ 変更：投資資産の価格キャッシュを「履歴蓄積型」に変更
# ==========================================
def save_price_cache(sh, prices_dict, timestamp):
    """API取得が成功したときに、日付と価格をスプレッドシートに履歴として1日1回保存する"""
    try:
        ws = sh.worksheet('レート履歴')
    except Exception:
        # シートが無ければ作成
        ws = sh.add_worksheet(title='レート履歴', rows="1000", cols="3")
        ws.update(range_name='A1:C1', values=[['日付', '銘柄', '価格']])

    # 日付部分だけを取得（YYYY/MM/DD）
    date_only = str(timestamp).split(' ')[0]
    
    # 既存データを取得して今日の日付が既にあるかチェック
    all_values = ws.get_all_values()
    existing_dates = [row[0] for row in all_values[1:]] if len(all_values) > 1 else []
    
    # 今日まだ記録されていなければ追記する
    if date_only not in existing_dates:
        data_to_append = []
        for symbol, price in prices_dict.items():
            data_to_append.append([date_only, symbol, price])
        
        if data_to_append:
            ws.append_rows(data_to_append)

def load_price_cache(sh):
    """スプレッドシートの履歴から最新の価格と、全履歴データを読み込む"""
    try:
        ws = sh.worksheet('レート履歴')
        raw_data = ws.get_all_values()
        if len(raw_data) < 2:
            return {}, None, pd.DataFrame()
        
        # 履歴をDataFrame化
        df_hist = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        df_hist['価格'] = pd.to_numeric(df_hist['価格'], errors='coerce')
        df_hist['日付'] = pd.to_datetime(df_hist['日付'])
        
        # 最新の日付のデータを抽出して辞書にする
        latest_date = df_hist['日付'].max()
        df_latest = df_hist[df_hist['日付'] == latest_date]
        prices_dict = dict(zip(df_latest['銘柄'], df_latest['価格']))
        
        timestamp = latest_date.strftime("%Y/%m/%d")
        return prices_dict, timestamp, df_hist
    except Exception:
        return {}, None, pd.DataFrame()