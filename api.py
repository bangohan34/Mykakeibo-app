import streamlit as st
import requests
import yfinance as yf
import const as c

@st.cache_data(ttl=3600)
def get_usd_jpy_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data["rates"]["JPY"]
    except:
        return 150.0

@st.cache_data(ttl=600)
def get_crypto_prices(symbols):
    prices = {}
    valid_symbols = [str(sym).upper() for sym in symbols if sym]
    cg_ids = [c.CRYPTO_ID_MAP[sym] for sym in valid_symbols if sym in c.CRYPTO_ID_MAP]
    if not cg_ids:
        return prices
    ids_str = ",".join(cg_ids)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ids_str,
        'vs_currencies': 'jpy'
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        for sym in valid_symbols:
            if sym in c.CRYPTO_ID_MAP:
                cg_id = c.CRYPTO_ID_MAP[sym]
                if cg_id in data and 'jpy' in data[cg_id]:
                    prices[sym] = float(data[cg_id]['jpy'])
    except Exception:
        pass
    return prices

@st.cache_data(ttl=600)
def get_meme_prices(symbols):
    prices = {}
    usd_jpy_rate = get_usd_jpy_rate()
    for sym in symbols:
        key = sym.upper()
        if key in c.MEME_CONTRACTS:
            address = c.MEME_CONTRACTS[key]
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            try:
                res = requests.get(dex_url, timeout=5).json()
                if res.get("pairs"):
                    price_usd = float(res["pairs"][0].get("priceUsd", 0))
                    prices[sym] = price_usd * usd_jpy_rate
            except:
                prices[sym] = 0.0
    return prices

def get_metal_prices(symbols):
    target_map = {"Gold": "GC=F", "Silver": "SI=F"}
    metal_prices = {}
    try:
        usd_jpy_rate = get_usd_jpy_rate()
        for sym in symbols:
            if sym in target_map:
                ticker = target_map[sym]
                data = yf.Ticker(ticker)
                price_usd = data.history(period="5d")['Close'].iloc[-1]
                metal_prices[sym] = float(price_usd * usd_jpy_rate * 1.1 / 31.1)
    except Exception:
        pass
    return metal_prices