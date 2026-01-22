# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー taiki
EXPENSE_CATEGORIES = ['食費', '交通費', '生活費', '趣味', '交際費', '医療費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES = {
    "食費": ["朝食","昼食","夕食","間食","自炊","その他"],
    "交通費": ["電車","バス","車","原付","その他"],
    "生活費": ["衣類","美容","光熱費","日用品","医療","その他"],
    "趣味": ["ゲーム","スポーツ","本","その他"],
    "交際費": ["さやさん","友達","飲み会","冠婚葬祭","その他"],
    "医療費": ["通院","薬","その他"],
}

# 家計簿のカテゴリー saya
EXPENSE_CATEGORIES_saya = ['食費', 'チャリガッチャン', '美容費', '交通費', '生活費', '趣味費', '交際費', '医療費', 'その他']
INCOME_CATEGORIES_saya = ['給与','賞与','その他']
EXPENSE_SUB_CATEGORIES_saya = {
    "食費": ["朝食","昼食","夕食","間食","自炊","その他"],
    "交通費": ["電車","バス","車","その他"],
    "美容費": ["髪の毛","まつ毛","化粧品","メイク道具","その他"],
    "生活費": ["衣類","光熱費","日用品","医療","薬","その他"],
    "趣味費": ["楽器","ゲーム","ヨガ","ファンクラブ","その他"],
    "交際費": ["たいきさん","友達","飲み会","冠婚葬祭","その他"],
    "医療費": ["通院","薬","その他"],
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

# スタイルCSS
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container { padding-top: 1rem; }
            [data-testid="stNumberInput"] button { display: none; }
            /* 入力フォーム */
            div[data-baseweb="input"],          /* 文字入力・数値入力の箱 */
            div[data-baseweb="select"] > div,   /* プルダウンの箱 */
            div[data-baseweb="textarea"] {      /* メモ帳の箱 */
                background-color: #f2ead8 !important;  /* ベージュ */
                border: 1px solid #A1A3A6 !important;  /* グレーの枠線 */
                border-radius: 4px !important;
            }
            input[type="text"],
            input[type="number"],
            textarea {
                background-color: transparent !important;
                color: #333 !important; /* 文字色：黒 */
            }
            /* なんでもメモ */
            /* 枠線の色 */
            .stTextArea div[data-baseweb="textarea"] {
                background-color: #f2ead8 !important;
                border: 1px solid #A1A3A6 !important;
            }
            /* 背景色 */
            .stTextArea textarea {
                background-color: transparent !important; /* 透明にして親の色を見せる */
                color: #333 !important;
            }
            </style>
            """