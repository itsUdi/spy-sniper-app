import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import time

from webull import paper_webull

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
    market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return weekday < 5 and market_open <= now <= market_close

if not is_market_open():
    st.warning("⚠️ The market is currently closed. Trading hours are Monday to Friday — Pre-market: 8:00-8:30am, Open: 8:30am-3:00pm, After-hours: 3:00pm-3:30pm CT. No options will be scanned right now.")

# --- AUTO REFRESH ---
st_autorefresh_interval = 60
countdown = st.empty()
start_time = time.time()

# --- LOGIN ---
if "webull_session" not in st.session_state:
    wb = paper_webull()
    email = st.text_input("Webull Email")
    password = st.text_input("Webull Password", type="password")
    if st.button("Login"):
        try:
            wb.login(email, password)
            st.session_state.webull_session = wb
            st.success("✅ Logged in to Webull successfully!")
        except Exception as e:
            st.error(f"Login failed: {e}")
else:
    wb = st.session_state.webull_session

# --- FETCH SPY PRICE ---
def get_spy_price():
    try:
        quote = wb.get_quote('SPY')
        if 'lastSalePrice' in quote:
            return quote['lastSalePrice']
        elif 'close' in quote:
            return quote['close']
        else:
            raise Exception("SPY price not found.")
    except Exception as e:
        st.error(f"🔴 Error fetching SPY price: {e}")
        return None

# --- MOCK RSI ---
def calculate_rsi():
    return 62.5

# --- MOCK OPTION CHAIN ---
def get_option_chain():
    return pd.DataFrame({
        'type': ['Call', 'Put'],
        'strike': [605, 608],
        'lastPrice': [1.2, 1.1],
        'volume': [40000, 35000],
        'openInterest': [120000, 110000],
        'impliedVolatility': [0.23, 0.27],
        'expirationDate': ['2025-06-24', '2025-06-24']
    })

# --- SCORING ---
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

# --- DISPLAY ---
if 'webull_session' in st.session_state:
    price = get_spy_price()
    rsi = calculate_rsi()

    if price:
        st.markdown(f"**📉 SPY Price**: ${price}")
    if rsi:
        st.markdown(f"**📊 RSI (14d)**: {rsi}")

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

# --- REFRESH TIMER ---
while True:
    elapsed = int(time.time() - start_time)
    remaining = st_autorefresh_interval - (elapsed % st_autorefresh_interval)
    countdown.markdown(f"⏳ Auto-refresh in: **{remaining} seconds**")
    time.sleep(1)
    if remaining == 1:
        st.experimental_rerun()
