# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー
EXPENSE_CATEGORIES = ['食費', '交通費', '生活費', '趣味費', '交際費', '医療費','投資費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES = {
    "食費": ["社食","外食","コンビニ","間食","スーパー","その他"],
    "交通費": ["電車","バス","車","その他"],
    "生活費": ["衣類","美容","日用品","医療","ガス","電気","水道","保険","その他"],
    "趣味費": ["ゲーム","スポーツ","本","電子工作","その他"],
    "交際費": ["さやさん","友達","飲み会","親孝行","冠婚葬祭","その他"],
    "投資費": ["株","暗号資産","その他"],
    "医療費": ["通院","薬","その他"],
}

# 資産確認用
ASSET_CHECK_ACCOUNTS = ['ゆうちょ', 'SMBC', 'PayPay']
ASSET_CHECK_CREDITS = ['JCB', 'メルカリ', 'SMBC']

# 暗号資産のIDマップ
CRYPTO_ID_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'XRP': 'ripple',
    'PI': 'pi-network',
    'IOST': 'iostoken',
    'DOGE': 'dogecoin',
    'BNB': 'binancecoin'
}
MEME_CONTRACTS = {
    '114514': 'AGdGTQa8iRnSx4fQJehWo4Xwbh1bzTazs55R6Jwupump',
    '42069': 'FquUHKWfMUdSMxxSU9ZWrSc98hvTXeMnQn9nksSKpump'
}

# 円グラフのカテゴリーの色（u2用の色を削除）
PIE_CHART_CATEGORIES_COLORS = {
    '食費': "#C54C2D",  
    '交通費': "#5572D1",
    '生活費': "#C3932B",
    '趣味費': "#2EC456",  
    '交際費': "#B44986",
    '医療費': "#34D5DB",
    '投資費': "#454444",
    'その他': '#CFCFCF'
}

# スタイルCSS
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container { padding-top: 1rem; }
            [data-testid="stNumberInput"] button { display: none; }
            </style>
            """