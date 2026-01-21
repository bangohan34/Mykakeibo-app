# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー taiki
EXPENSE_CATEGORIES = ['食費', '交通費', '生活費', '娯楽費', '交際費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES = {
    "食費": ["朝食","昼食","夕食","間食","自炊","その他"],
    "交通費": ["電車","バス","車","原付","その他"],
    "生活費": ["衣類","美容","光熱費","日用品","医療","その他"],
    "娯楽費": ["ゲーム","スポーツ","本","その他"],
    "交際費": ["さやさん","友達","飲み会","冠婚葬祭","その他"],
}

# 家計簿のカテゴリー saya
EXPENSE_CATEGORIES_saya = ['食費', 'チャリガッチャン費', '交通費', '生活費', '娯楽費', '交際費', 'その他']
INCOME_CATEGORIES_saya = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES_saya = {
    "食費": ["朝食","昼食","夕食","間食","自炊","その他"],
    "交通費": ["電車","バス","車","原付","その他"],
    "生活費": ["衣類","美容","光熱費","日用品","医療","その他"],
    "娯楽費": ["ゲーム","スポーツ","本","その他"],
    "交際費": ["さやさん","友達","飲み会","冠婚葬祭","その他"],
}

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

# スプレッドシート名
SPREADSHEET_NAME = 'MyKakeibo'

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