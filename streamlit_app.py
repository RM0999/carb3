
import streamlit as st
import requests
from datetime import datetime

# Constants
USD_TO_AUD = 1.52  # Fallback exchange rate

# Streamlit UI Setup
st.set_page_config(page_title="Live Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔁 Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")
    pair = st.selectbox("Trading Pair", ["BTC/USDT"])
    min_profit = st.slider("Minimum Profit (%)", 0.5, 10.0, 2.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    refresh_rate = st.slider("Refresh Interval (sec)", 1, 60, 10)
    selected_exchanges = st.multiselect("Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve",
        "Bybit", "Crypto.com", "KuCoin", "OKX", "Bitget"
    ], default=["Binance", "Kraken", "CoinSpot", "IndependentReserve"])

# Exchange API fetchers
def fetch_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT").json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_kraken():
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD").json()
        data = r['result']['XXBTZUSD']
        return {'buy': float(data['a'][0]) * USD_TO_AUD, 'sell': float(data['b'][0]) * USD_TO_AUD, 'fee': 0.0026}
    except: return None

def fetch_coinspot():
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        return {'buy': float(r['prices']['BTC']['ask']), 'sell': float(r['prices']['BTC']['bid']), 'fee': 0.01}
    except: return None

def fetch_independent_reserve():
    try:
        r = requests.get("https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode=BTC&secondaryCurrencyCode=AUD").json()
        return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}
    except: return None

def fetch_bybit():
    try:
        r = requests.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT").json()
        item = r["result"][0]
        return {'buy': float(item['ask_price']) * USD_TO_AUD, 'sell': float(item['bid_price']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_crypto_com():
    try:
        r = requests.get("https://api.crypto.com/v2/public/get-ticker?instrument_name=BTC_USDT").json()
        data = r["result"]["data"]
        return {'buy': float(data['a']) * USD_TO_AUD, 'sell': float(data['b']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_kucoin():
    try:
        r = requests.get("https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT").json()
        data = r["data"]
        return {'buy': float(data['askPrice']) * USD_TO_AUD, 'sell': float(data['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_okx():
    try:
        r = requests.get("https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT").json()
        data = r["data"][0]
        return {'buy': float(data['askPx']) * USD_TO_AUD, 'sell': float(data['bidPx']) * USD_TO_AUD, 'fee': 0.001}
    except: return None

def fetch_bitget():
    try:
        r = requests.get("https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT").json()
        for d in r['data']:
            if d['symbol'] == 'BTCUSDT':
                return {'buy': float(d['askPx']) * USD_TO_AUD, 'sell': float(d['bidPx']) * USD_TO_AUD, 'fee': 0.001}
        return None
    except: return None

api_fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Bybit": fetch_bybit,
    "Crypto.com": fetch_crypto_com,
    "KuCoin": fetch_kucoin,
    "OKX": fetch_okx,
    "Bitget": fetch_bitget
}

# Fetch market data from selected exchanges
data = {ex: api_fetchers[ex]() for ex in selected_exchanges}
valid_data = {ex: val for ex, val in data.items() if val}

if valid_data:
    best_buy = min(valid_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid_data.items(), key=lambda x: x[1]['sell'])
    net_profit_pct = round(((best_sell[1]['sell'] * (1 - best_sell[1]['fee'])) - (best_buy[1]['buy'] * (1 + best_buy[1]['fee']))) / (best_buy[1]['buy'] * (1 + best_buy[1]['fee'])) * 100, 2)
    net_profit_aud = round(investment * (net_profit_pct / 100), 2)
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Opportunity Found! {timestamp}")
        st.write(f"Buy from **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}** (Fee: {best_buy[1]['fee']*100}%)")
        st.write(f"Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}** (Fee: {best_sell[1]['fee']*100}%)")
        st.write(f"📈 Net Profit: **{net_profit_pct}%** | **AUD ${net_profit_aud}**")
    else:
        st.warning(f"No arbitrage opportunity above {min_profit}% right now.")
else:
    st.error("No valid exchange data available.")
