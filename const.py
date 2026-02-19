# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー taiki
EXPENSE_CATEGORIES = ['食費', '交通費', '生活費', '趣味費', '交際費', '医療費','投資費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES = {
    "食費": ["外食","間食","スーパー","その他"],
    "交通費": ["電車","バス","車","原付","その他"],
    "生活費": ["衣類","美容","光熱費","日用品","医療","その他"],
    "趣味費": ["ゲーム","スポーツ","本","電子工作","その他"],
    "交際費": ["さやさん","友達","飲み会","冠婚葬祭","その他"],
    "投資費": ["株","暗号資産","その他"],
    "医療費": ["通院","薬","その他"],
}

# 家計簿のカテゴリー saya
EXPENSE_CATEGORIES_saya = ['食費', 'チャリガッチャン', '美容費', '交通費', '生活費', '趣味費', '交際費', '医療費', 'その他']
INCOME_CATEGORIES_saya = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES_saya = {
    "食費": ["昼食","夕食","飲み物","間食","朝食","自炊","その他"],
    "交通費": ["電車","バス","車","その他"],
    "美容費": ["髪の毛","まつ毛","化粧品","メイク道具","その他"],
    "生活費": ["衣類","光熱費","日用品","医療","薬","その他"],
    "趣味費": ["楽器","ゲーム","ヨガ","ファンクラブ","その他"],
    "交際費": ["たいきさん","友達","飲み会","冠婚葬祭","その他"],
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
    'IOST': 'iostoken'
}
MEME_CONTRACTS = {
    '114514': 'AGdGTQa8iRnSx4fQJehWo4Xwbh1bzTazs55R6Jwupump',
    '42069': 'FquUHKWfMUdSMxxSU9ZWrSc98hvTXeMnQn9nksSKpump'
}

# 円グラフのカテゴリーの色
PIE_CHART_CATEGORIES_COLORS = {
    '食費': "#C54C2D",  
    '交通費': "#5572D1",
    '生活費': "#C3932B",
    '趣味費': "#2EC456",  
    '交際費': "#B44986",
    '医療費': "#34D5DB",
    '投資費': "#454444",
    'その他': '#CFCFCF',
    'チャリガッチャン': "#7970CA", # saya
    '美容費': "#CA4D71",
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