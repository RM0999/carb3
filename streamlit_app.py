
import streamlit as st
import requests
from datetime import datetime

# Constants
USD_TO_AUD = 1.52  # Static conversion fallback
SUPPORTED_COINS = ["BTC", "ETH", "XRP", "LTC", "ADA"]

# Streamlit UI
st.set_page_config(page_title="Multi-Coin Arbitrage Scanner", layout="wide")
st.title("🔁 Multi-Coin Crypto Arbitrage Scanner (Live APIs Only)")

with st.sidebar:
    st.header("⚙️ Settings")
    coin = st.selectbox("Select Coin", SUPPORTED_COINS)
    min_profit = st.slider("Minimum Profit (%)", 0.5, 10.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    refresh_rate = st.slider("Refresh Interval (sec)", 5, 60, 10)
    selected_exchanges = st.multiselect("Select Exchanges", [
        "Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"
    ], default=["Binance", "Kraken", "CoinSpot", "IndependentReserve"])

# === API Fetch Functions ===
def fetch_binance(symbol):
    try:
        sym = f"{symbol}USDT"
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={sym}").json()
        return {"buy": float(r['askPrice']) * USD_TO_AUD, "sell": float(r['bidPrice']) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

def fetch_kraken(symbol):
    try:
        kraken_map = {"BTC": "XBT", "ETH": "ETH", "XRP": "XRP", "LTC": "LTC", "ADA": "ADA"}
        sym = f"{kraken_map[symbol]}USDT"
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={sym}").json()
        result = list(r['result'].values())[0]
        return {"buy": float(result['a'][0]) * USD_TO_AUD, "sell": float(result['b'][0]) * USD_TO_AUD, "fee": 0.0026}
    except:
        return None

def fetch_coinspot(symbol):
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        coin_data = r['prices'].get(symbol)
        if coin_data:
            return {"buy": float(coin_data['ask']), "sell": float(coin_data['bid']), "fee": 0.01}
    except:
        return None

def fetch_independent_reserve(symbol):
    try:
        symbol_map = {"BTC": "Xbt", "ETH": "Eth", "XRP": "Xrp", "LTC": "Ltc", "ADA": "Ada"}
        url = f"https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode={symbol_map[symbol]}&secondaryCurrencyCode=Aud"
        r = requests.get(url).json()
        return {"buy": float(r['CurrentLowestOfferPrice']), "sell": float(r['CurrentHighestBidPrice']), "fee": 0.005}
    except:
        return None

def fetch_coinbase(symbol):
    try:
        r = requests.get(f"https://api.coinbase.com/v2/prices/{symbol}-USD/spot").json()
        price = float(r['data']['amount']) * USD_TO_AUD
        return {"buy": price * 1.001, "sell": price * 0.999, "fee": 0.005}
    except:
        return None

def fetch_coinjar(symbol):
    try:
        r = requests.get("https://data.exchange.coinjar.com/products").json()
        for p in r:
            if p["display_name"] == f"{symbol}/AUD":
                ask = float(p["ask"])
                bid = float(p["bid"])
                return {"buy": ask, "sell": bid, "fee": 0.005}
    except:
        return None

def fetch_crypto_com(symbol):
    try:
        sym = f"{symbol}_USDT"
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={sym}").json()
        data = r["result"]["data"]
        return {"buy": float(data["a"]) * USD_TO_AUD, "sell": float(data["b"]) * USD_TO_AUD, "fee": 0.001}
    except:
        return None

# Mapping
api_fetchers = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": fetch_coinspot,
    "IndependentReserve": fetch_independent_reserve,
    "Coinbase": fetch_coinbase,
    "CoinJar": fetch_coinjar,
    "Crypto.com": fetch_crypto_com
}

# Fetch and compute
data = {ex: api_fetchers[ex](coin) for ex in selected_exchanges if api_fetchers[ex](coin)}
valid_data = {ex: val for ex, val in data.items() if val and val['buy'] and val['sell']}

if valid_data:
    best_buy = min(valid_data.items(), key=lambda x: x[1]['buy'])
    best_sell = max(valid_data.items(), key=lambda x: x[1]['sell'])
    spread = best_sell[1]['sell'] - best_buy[1]['buy']
    net_profit_pct = round((spread - (best_buy[1]['buy'] * best_buy[1]['fee']) - (best_sell[1]['sell'] * best_sell[1]['fee'])) / best_buy[1]['buy'] * 100, 2)
    net_profit_aud = round(investment * (net_profit_pct / 100), 2)
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_profit_pct >= min_profit:
        st.success(f"🚀 Arbitrage Opportunity at {timestamp}")
        st.write(f"💸 Buy on **{best_buy[0]}** at **AUD ${best_buy[1]['buy']:.2f}**")
        st.write(f"💰 Sell on **{best_sell[0]}** at **AUD ${best_sell[1]['sell']:.2f}**")
        st.write(f"📈 Spread: AUD ${spread:.2f} | Net Profit: **{net_profit_pct}%** | **AUD ${net_profit_aud}**")
    else:
        st.warning("No positive arbitrage opportunity above your minimum threshold.")
else:
    st.error("⚠️ No valid pricing data available from selected exchanges.")
