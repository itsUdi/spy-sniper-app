import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import time

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

# --- FETCH SPY PRICE ---
def get_spy_price():
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="1d", interval="1m")
        return round(hist['Close'].iloc[-1], 2)
    except:
        return None

# --- CALCULATE RSI ---
def calculate_rsi(symbol="SPY", window=14):
    try:
        spy = yf.Ticker(symbol)
        hist = spy.history(period="2mo")
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except:
        return None

# --- FETCH OPTION CHAIN ---
def get_option_chain(symbol="SPY"):
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        contracts = []
        for exp in expirations[:2]:
            opt_chain = ticker.option_chain(exp)
            calls = opt_chain.calls.copy()
            puts = opt_chain.puts.copy()
            calls['type'] = 'Call'
            puts['type'] = 'Put'
            combined = pd.concat([calls, puts])
            combined['expirationDate'] = exp
            contracts.append(combined)
        all_contracts = pd.concat(contracts)
        return all_contracts
    except:
        return pd.DataFrame()

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

if price is not None:
    st.markdown(f"**📉 SPY Price**: ${price}")
else:
    st.error("Failed to retrieve SPY price.")

if rsi is not None:
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

