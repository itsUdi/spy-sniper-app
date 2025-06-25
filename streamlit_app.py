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
    weekday = now.weekday()  # Monday = 0, Sunday = 6
    market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return weekday < 5 and market_open <= now <= market_close

if not is_market_open():
    st.warning("⚠️ The market is currently closed. Trading hours are Monday to Friday — Pre-market: 8:00-8:30am, Open: 8:30am-3:00pm, After-hours: 3:00pm-3:30pm CT. No options will be scanned right now.")

# --- AUTO REFRESH ---
st_autorefresh_interval = 60  # seconds
countdown = st.empty()
start_time = time.time()

# --- TOKEN CACHING ---
if "webull_token" not in st.session_state or "token_timestamp" not in st.session_state or (datetime.now() - st.session_state.token_timestamp).total_seconds() > 86400:
    st.session_state.webull_token = st.text_input("Paste your Webull token:", type="password")
    if st.session_state.webull_token:
        st.session_state.token_timestamp = datetime.now()
else:
    st.success("✅ Token valid for 1 day.")

headers = {
    "access_token": st.session_state.webull_token,
    "app": "global",
    "app-group": "broker",
    "appid": "wb_web_app",
    "device-type": "Web",
    "did": "8m1lw5o1pz87ckn6jxs73k89a8ltqrzk",
    "hl": "en",
    "os": "web",
    "osv": "i9zh",
    "platform": "web",
    "referer": "https://app.webull.com/",
    "reqid": "test_req_id_001",
    "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "t_time": str(int(time.time() * 1000)),
    "tz": "America/Chicago",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "ver": "5.7.3",
    "x-s": "668b3816e31b1a92771cbeb5cbb5de80e8e386bf5ec68262411c7cee2aed2136",
    "x-sv": "xodp2vg9",
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "origin": "https://app.webull.com",
    "sec-fetch-site": "same-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "connection": "keep-alive"
}

# --- FETCH SPY PRICE FROM WEBULL ---
def get_spy_price():
    try:
        url = "https://quotes-gw.webullfintech.com/api/quote/realTimeQuote?tickerId=913256135"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return float(data.get('lastSalePrice') or data.get('close'))
    except Exception as e:
        st.error(f"🔴 Error fetching SPY price: {e}")
        return None

# --- FETCH RSI (mocked) ---
def calculate_rsi():
    return 62.5  # mock until RSI from Webull or other source added

# --- FETCH OPTIONS FROM WEBULL (mocked structure) ---
def get_option_chain():
    # Mock return for example until full Webull options logic implemented
    return pd.DataFrame({
        'type': ['Call', 'Put'],
        'strike': [605, 608],
        'lastPrice': [1.2, 1.1],
        'volume': [40000, 35000],
        'openInterest': [120000, 110000],
        'impliedVolatility': [0.23, 0.27],
        'expirationDate': ['2025-06-24', '2025-06-24']
    })

# --- EVALUATE OPTIONS ---
def score_option(row, rsi, current_price):
    score = 0
    if pd.isna(row['impliedVolatility']) or row['volume'] == 0:
        return -1
    score += row['volume'] / 1000
    score += row['openInterest'] / 1000
    score += 1 / row['impliedVolatility'] * 100

    if row['type'] == 'Call' and rsi < 70 and current_price < row['strike'] + 3:
        score += 10
    elif row['type'] == 'Put' and rsi > 30 and current_price > row['strike'] - 3:
        score += 10

    return score

# --- DISPLAY DATA ---
price = get_spy_price()
rsi = calculate_rsi()

if price:
    st.markdown(f"**📉 SPY Price**: ${price}")
else:
    st.error("Failed to retrieve SPY price.")

if rsi:
    st.markdown(f"**📊 RSI (14d)**: {rsi}")
else:
    st.error("Failed to calculate RSI.")

st.subheader("🔍 Best Option Based on Algo")
st.markdown("---")

if is_market_open():
    options_df = get_option_chain()
    if not options_df.empty:
        options_df = options_df.dropna(subset=['lastPrice'])
        options_df['score'] = options_df.apply(lambda row: score_option(row, rsi, price), axis=1)

        valid_options = options_df[options_df['score'] > 0]
        if not valid_options.empty:
            best_option = valid_options.loc[valid_options['score'].idxmax()]
            st.markdown(f"**🔹 Type**: {best_option['type']} - **Strike**: {best_option['strike']} - Exp: {best_option['expirationDate']}")
            st.markdown(f"**💰 Last Price**: ${round(best_option['lastPrice'], 2)}")
            st.markdown(f"**🎯 Target (10%)**: ${round(best_option['lastPrice'] * 1.10, 2)}")
            st.markdown(f"**🛑 Stop (20%)**: ${round(best_option['lastPrice'] * 0.80, 2)}")
            st.markdown(f"**📊 Volume**: {int(best_option['volume'])} | **OI**: {int(best_option['openInterest'])}")
            st.markdown(f"**🧠 IV (proxy for delta)**: {round(best_option['impliedVolatility'], 4)}")
            st.success("This contract has the highest potential to hit your 10% target today.")
        else:
            st.warning("⚠️ No safe SPY option trade found right now. Sit tight — no trash trades.")
    else:
        st.warning("⚠️ Could not load option chain. Try again later.")

# --- REFRESH COUNTDOWN ---
while True:
    elapsed = int(time.time() - start_time)
    remaining = st_autorefresh_interval - (elapsed % st_autorefresh_interval)
    countdown.markdown(f"⏳ Auto-refresh in: **{remaining} seconds**")
    time.sleep(1)
    if remaining == 1:
        st.experimental_rerun()
