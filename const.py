# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー
EXPENSE_CATEGORIES = ['食費', '交通費', '生活費', '趣味費', '交際費', '医療費','投資費', '税金', 'その他']
INCOME_CATEGORIES = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES = {
    "食費": ["社食","外食","コンビニ","間食","スーパー","その他"],
    "交通費": ["電車","バス","車","その他"],
    "生活費": ["衣類","美容","日用品","医療","ガス","電気","水道","保険","その他"],
    "趣味費": ["ゲーム","スポーツ","本","電子工作","その他"],
    "交際費": ["さやさん","友達","飲み会","親孝行","冠婚葬祭","その他"],
    "投資費": ["株","暗号資産","その他"],
    "医療費": ["通院","薬","その他"],
    "税金": ["所得税","住民税","その他"],
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

# 円グラフ・内訳バーのカテゴリーの色
PIE_CHART_CATEGORIES_COLORS = {
    '食費': "#C54C2D",  
    '交通費': "#5572D1",
    '生活費': "#C3932B",
    '趣味費': "#2EC456",  
    '交際費': "#B44986",
    '医療費': "#34D5DB",
    '投資費': "#454444",
    '税金': "#A0522D",
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

# --- 給与内訳の初期値設定 ---
SALARY_DEFAULTS = {
    '本給': 30750,
    '超勤手当': 0,
    'リモートワーク手当': 0,
    '通勤手当': 0,
    'その他（収入）': 0,
    '健康保険': 12075,
    '厚年保険': 27450,
    '雇用保険': 0,
    '所得税': 0,
    '持株積立': 10000,
    '社宅利用料': 15600,
    '生命保険': 1500,
    '組合費': 8400,
    '食堂喫食代': 0,
    'その他（支出）': 0
}

# --- 賞与内訳の初期値設定（社宅利用料や積立項目は含まない） ---
BONUS_DEFAULTS = {
    '賞与額': 0,
    'その他（収入）': 0,
    '健康保険': 0,
    '厚年保険': 0,
    '雇用保険': 0,
    '所得税': 0,
    'その他（支出）': 0
}