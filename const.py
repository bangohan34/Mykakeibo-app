# --- 変わらない定数の設定 ---

# 会計簿のカテゴリー
EXPENSE_CATEGORIES = ['食費', '交通費', '日用品', '趣味', '交際費', 'その他']
INCOME_CATEGORIES = ['給与','賞与','臨時収入','その他']

# 仮想通貨のIDマップ（CoinGecko用）
CRYPTO_ID_MAP = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'XRP': 'ripple',
    'PI': 'pi-network',
    'IOST': 'iostoken'
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