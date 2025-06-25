import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import time
import requests

# --- CONFIG ---
st.set_page_config(page_title="SPY Sniper", layout="centered")
st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; }
        .stButton>button { background-color: #1f222a; color: white; border-radius: 10px; }
        .css-1d391kg { background-color: #1f222a; }
    </style>
""", unsafe_allow_html=True)

st.title("🔫 SPY Options Sniper")

# --- MARKET HOURS CHECK ---
def is_market_open():
    now = datetime.now()
    weekday = now.weekday()
    pre = now.replace(hour=8, minute=0)
    open_ = now.replace(hour=8, minute=30)
    close = now.replace(hour=15, minute=0)
    after = now.replace(hour=15, minute=30)
    return weekday < 5 and pre <= now <= after

if not is_market_open():
    st.warning("⚠️ Market is currently closed. Hours: Mon–Fri | Pre-market: 8–8:30am | Open: 8:30am–3pm | After-hours: 3–3:30pm CT.")

# --- REFRESH ---
refresh_interval = 60
countdown = st.empty()
start_time = time.time()

# --- Webull Token (stored once per 24h session) ---
if "webull_token" not in st.session_state or "token_time" not in st.session_state or (datetime.now() - st.session_state.token_time).total_seconds() > 86400:
    st.session_state.webull_token = st.text_input("Paste your Webull token:", type="password")
    if st.session_state.webull_token:
        st.session_state.token_time = datetime.now()
else:
    st.success("✅ Token valid for 1 day.")

headers = {
    "access_token": st.session_state.webull_token,
    "app": "global",
    "platform": "web",
    "user-agent": "Mozilla/5.0",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9"
}

# --- GET SPY PRICE ---
def get_spy_price():
    try:
        url = "https://quotes-gw.webullfintech.com/api/quote/realTimeQuote?tickerId=913256135"
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        return float(data.get("lastSalePrice") or data.get("close"))
    except Exception as e:
        st.error(f"🔴 Error fetching SPY price: {e}")
        return None

# --- MOCK RSI ---
def get_rsi():
    return 62.5

# --- MOCK OPTIONS (real logic coming soon) ---
def get_options():
    return pd.DataFrame({
        'type': ['Call', 'Put'],
        'strike': [605, 608],
        'lastPrice': [1.2, 1.1],
        'volume': [40000, 35000],
        'openInterest': [120000, 110000],
        'impliedVolatility': [0.23, 0.27],
        'expirationDate': ['2025-06-24', '2025-06-24']
    })

# --- SCORE FUNCTION ---
def score(row, rsi, spy_price):
    if pd.isna(row['impliedVolatility']) or row['volume'] == 0:
        return -1
    score = row['volume'] / 1000 + row['openInterest'] / 1000 + (1 / row['impliedVolatility']) * 100
    if row['type'] == 'Call' and rsi < 70 and spy_price < row['strike'] + 3:
        score += 10
    elif row['type'] == 'Put' and rsi > 30 and spy_price > row['strike'] - 3:
        score += 10
    return score

# --- LIVE DATA ---
spy_price = get_spy_price()
rsi = get_rsi()

if spy_price:
    st.markdown(f"**📉 SPY Price**: ${spy_price}")
else:
    st.error("Failed to retrieve SPY price.")

if rsi:
    st.markdown(f"**📊 RSI (14d)**: {rsi}")
else:
    st.error("Failed to calculate RSI.")

# --- PICK BEST OPTION ---
st.subheader("🔍 Best Option Based on Algo")
st.markdown("---")

if is_market_open() and spy_price:
    df = get_options()
    df = df.dropna(subset=['lastPrice'])
    df['score'] = df.apply(lambda row: score(row, rsi, spy_price), axis=1)
    filtered = df[df['score'] > 0]

    if not filtered.empty:
        best = filtered.loc[filtered['score'].idxmax()]
        st.markdown(f"**🔹 Type**: {best['type']} - **Strike**: {best['strike']} - Exp: {best['expirationDate']}")
        st.markdown(f"**💰 Last Price**: ${round(best['lastPrice'], 2)}")
        st.markdown(f"**🎯 Target (10%)**: ${round(best['lastPrice'] * 1.10, 2)}")
        st.markdown(f"**🛑 Stop (20%)**: ${round(best['lastPrice'] * 0.80, 2)}")
        st.markdown(f"**📊 Volume**: {int(best['volume'])} | **OI**: {int(best['openInterest'])}")
        st.markdown(f"**🧠 IV (proxy for delta)**: {round(best['impliedVolatility'], 4)}")
        st.success("This contract has the highest probability of hitting your 10% goal today.")
    else:
        st.warning("⚠️ No trade meets your criteria. Sit tight.")
else:
    st.info("📴 Waiting for market to open or valid SPY price...")

# --- AUTO REFRESH TIMER ---
while True:
    elapsed = int(time.time() - start_time)
    left = refresh_interval - (elapsed % refresh_interval)
    countdown.markdown(f"⏳ Auto-refresh in: **{left} seconds**")
    time.sleep(1)
    if left == 1:
        st.experimental_rerun()
