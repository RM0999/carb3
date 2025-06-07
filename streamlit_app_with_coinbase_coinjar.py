
import streamlit as st
import requests
from datetime import datetime

# AUD conversion rate (fallback)
USD_TO_AUD = 1.52

# Streamlit app config
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 Live Crypto Arbitrage Scanner</h1>", unsafe_allow_html=True)

# Sidebar settings
with st.sidebar:
    st.title("⚙️ Settings")
    pair = st.selectbox("Select Trading Pair", ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"])
    min_profit = st.slider("Minimum Profit (%)", 0.1, 10.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    refresh_rate = st.slider("Refresh Interval (sec)", 5, 60, 10)
    selected_exchanges = st.multiselect(
        "Exchanges",
        ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Bybit", "OKX", "KuCoin", "Crypto.com", "Coinbase", "CoinJar"],
        default=["Binance", "Kraken", "CoinSpot", "IndependentReserve"]
    )

# API functions
def fetch_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT").json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except:
        return None

def fetch_kraken():
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSDT").json()
        data = r["result"]["XXBTZUSD"]
        return {'buy': float(data["a"][0]) * USD_TO_AUD, 'sell': float(data["b"][0]) * USD_TO_AUD, 'fee': 0.0026}
    except:
        return None

def fetch_coinspot():
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        return {'buy': float(r['prices']['BTC']['ask']), 'sell': float(r['prices']['BTC']['bid']), 'fee': 0.01}
    except:
        return None

def fetch_independent_reserve():
    try:
        r = requests.get("https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode=Xbt&secondaryCurrencyCode=Aud").json()
        return {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}
    except:
        return None

def fetch_coinbase():
    try:
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/buy").json()
        buy = float(r['data']['amount'])
        r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/sell").json()
        sell = float(r['data']['amount'])
        return {'buy': buy * USD_TO_AUD, 'sell': sell * USD_TO_AUD, 'fee': 0.005}
    except:
        return None

def fetch_coinjar():
    try:
        r = requests.get("https://data.exchange.coinjar.com/products/BTC/AUD/ticker").json()
        return {'buy': float(r['ask']), 'sell': float(r['bid']), 'fee': 0.005}
    except:
        return None

# Map exchanges to their fetch functions
api_fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Coinbase": fetch_coinbase,
    "CoinJar": fetch_coinjar,
}

# Run arbitrage scan
data = {ex: api_fetchers[ex]() for ex in selected_exchanges if ex in api_fetchers and api_fetchers[ex]()}
valid_data = {ex: val for ex, val in data.items() if val}

if valid_data:
    best_buy = min(valid_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid_data.items(), key=lambda x: x[1]['sell'])
    profit_pct = round((best_sell[1]['sell'] - best_buy[1]['buy']) / best_buy[1]['buy'] * 100, 2)
    fee_pct = round((best_buy[1]['fee'] + best_sell[1]['fee']) * 100, 2)
    net_profit_pct = round(profit_pct - fee_pct, 2)
    profit_aud = round(investment * (net_profit_pct / 100), 2)
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_profit_pct > 0:
        st.success(f"🚀 Arbitrage Opportunity Found! ({timestamp})")
        st.write(f"Buy from **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}** (Fee: {best_buy[1]['fee']*100:.2f}%)")
        st.write(f"Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}** (Fee: {best_sell[1]['fee']*100:.2f}%)")
        st.write(f"📈 Gross Profit: **{profit_pct}%**, Fees: **{fee_pct}%**, Net: **{net_profit_pct}%**")
        st.write(f"💰 Estimated Net Profit: **AUD ${profit_aud}**")
    else:
        st.warning(f"No profitable arbitrage opportunity after fees. Net Profit: {net_profit_pct}%")
else:
    st.error("❌ No valid exchange data available.")
