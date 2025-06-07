
import streamlit as st
import requests
from datetime import datetime

# Constants
USD_TO_AUD = 1.52  # Fallback conversion rate
CRYPTO_PAIRS = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "SOL/USDT", "XRP/USDT"]
EXCHANGES = ["Binance", "Kraken", "CoinSpot", "IndependentReserve", "Coinbase", "CoinJar", "Crypto.com"]

# Page config
st.set_page_config(page_title="Crypto Arbitrage Scanner", layout="wide")
st.title("🔍 Live Crypto Arbitrage Scanner")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    selected_pair = st.selectbox("Select Crypto Pair", CRYPTO_PAIRS, index=0)
    min_profit = st.slider("Minimum Profit (%)", 0.5, 10.0, 1.0)
    investment = st.number_input("Investment (AUD)", min_value=10, value=1000)
    selected_exchanges = st.multiselect("Exchanges", EXCHANGES, default=EXCHANGES)

# Fetch functions
def fetch_binance(pair):
    try:
        symbol = pair.replace("/", "")
        r = requests.get(f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}").json()
        return {'buy': float(r['askPrice']) * USD_TO_AUD, 'sell': float(r['bidPrice']) * USD_TO_AUD, 'fee': 0.001}
    except:
        return None

def fetch_kraken(pair):
    try:
        mapping = {"BTC/USDT": "XXBTZUSD", "ETH/USDT": "XETHZUSD"}
        r = requests.get(f"https://api.kraken.com/0/public/Ticker?pair={pair.replace('/', '')}").json()
        key = mapping.get(pair, "")
        data = r["result"][key]
        return {'buy': float(data["a"][0]) * USD_TO_AUD, 'sell': float(data["b"][0]) * USD_TO_AUD, 'fee': 0.0026}
    except:
        return None

def fetch_coinspot():
    try:
        r = requests.get("https://www.coinspot.com.au/pubapi/v2/latest").json()
        return {
            "BTC/USDT": {'buy': float(r['prices']['BTC']['ask']), 'sell': float(r['prices']['BTC']['bid']), 'fee': 0.01},
            "ETH/USDT": {'buy': float(r['prices']['ETH']['ask']), 'sell': float(r['prices']['ETH']['bid']), 'fee': 0.01}
        }
    except:
        return {}

def fetch_independent_reserve():
    try:
        r = requests.get("https://api.independentreserve.com/Public/GetMarketSummary?primaryCurrencyCode=Xbt&secondaryCurrencyCode=Aud").json()
        return {"BTC/USDT": {'buy': float(r['CurrentLowestOfferPrice']), 'sell': float(r['CurrentHighestBidPrice']), 'fee': 0.005}}
    except:
        return {}

def fetch_coinbase(pair):
    try:
        r = requests.get(f"https://api.exchange.coinbase.com/products/{pair}/ticker").json()
        return {'buy': float(r['ask']) * USD_TO_AUD, 'sell': float(r['bid']) * USD_TO_AUD, 'fee': 0.006}
    except:
        return None

def fetch_coinjar(pair):
    try:
        slug = pair.replace("/", "").lower()
        r = requests.get(f"https://data.exchange.coinjar.com/products/{slug}/ticker").json()
        return {'buy': float(r['ask']) * USD_TO_AUD, 'sell': float(r['bid']) * USD_TO_AUD, 'fee': 0.005}
    except:
        return None

def fetch_crypto_com(pair):
    try:
        symbol = pair.replace("/", "_")
        r = requests.get(f"https://api.crypto.com/v2/public/get-ticker?instrument_name={symbol}").json()
        data = r["result"]["data"]
        return {'buy': float(data["a"]) * USD_TO_AUD, 'sell': float(data["b"]) * USD_TO_AUD, 'fee': 0.004}
    except:
        return None

FETCH_FUNCTIONS = {
    "Binance": fetch_binance,
    "Kraken": fetch_kraken,
    "CoinSpot": lambda p: fetch_coinspot().get(p),
    "IndependentReserve": lambda p: fetch_independent_reserve().get(p),
    "Coinbase": fetch_coinbase,
    "CoinJar": fetch_coinjar,
    "Crypto.com": fetch_crypto_com
}

# Collect data
exchange_data = {}
for ex in selected_exchanges:
    func = FETCH_FUNCTIONS.get(ex)
    if func:
        data = func(selected_pair)
        if data:
            exchange_data[ex] = data

# Compute arbitrage
if exchange_data:
    best_buy = min(exchange_data.items(), key=lambda x: x[1]["buy"])
    best_sell = max(exchange_data.items(), key=lambda x: x[1]["sell"])
    spread = best_sell[1]["sell"] - best_buy[1]["buy"]
    gross_pct = (spread / best_buy[1]["buy"]) * 100

    buy_fee_amt = best_buy[1]["buy"] * best_buy[1]["fee"]
    sell_fee_amt = best_sell[1]["sell"] * best_sell[1]["fee"]
    net_profit_aud = investment * ((spread - buy_fee_amt - sell_fee_amt) / best_buy[1]["buy"])
    net_pct = (net_profit_aud / investment) * 100
    timestamp = datetime.now().strftime("%H:%M:%S")

    if net_pct >= min_profit:
        st.success(f"🚀 Opportunity Found! {timestamp}")
        st.write(f"🛒 Buy from: {best_buy[0]} at **AUD ${best_buy[1]['buy']:,.2f}**")
        st.write(f"💰 Sell on: {best_sell[0]} at **AUD ${best_sell[1]['sell']:,.2f}**")
        st.write(f"🔄 Spread: **AUD ${spread:,.2f} ({gross_pct:.2f}%)**")
        st.write(f"💸 Net Profit: **{net_pct:.2f}%** | **AUD ${net_profit_aud:,.2f}**")
        st.write(f"🧾 Fees: Buy Fee = AUD ${buy_fee_amt:,.2f}, Sell Fee = AUD ${sell_fee_amt:,.2f}")
    else:
        st.warning(f"No arbitrage opportunity above {min_profit}% right now.")
else:
    st.error("⚠️ No data available from selected exchanges.")
