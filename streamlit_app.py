import pandas as pd
import streamlit as st
from datetime import datetime
import time
from webull import paper_webull
from streamlit_autorefresh import st_autorefresh
from cryptography.fernet import Fernet
import os
import yfinance as yf
import matplotlib.pyplot as plt

# --- ENCRYPTION SETUP (Persistent) ---
FERNET_KEY_FILE = ".fernet_key"

if not os.path.exists(FERNET_KEY_FILE):
    with open(FERNET_KEY_FILE, "wb") as f:
        f.write(Fernet.generate_key())

with open(FERNET_KEY_FILE, "rb") as f:
    fernet = Fernet(f.read())

def encrypt_string(s):
    return fernet.encrypt(s.encode()).decode()

def decrypt_string(s):
    return fernet.decrypt(s.encode()).decode()

# --- SAFE SESSION STATE INIT ---
for key in ["logged_in", "webull_email", "webull_pass", "webull_logged_in"]:
    if key not in st.session_state:
        st.session_state[key] = False if "logged_in" in key else ""

# --- CONFIG ---
st.set_page_config(page_title="SPY Sniper", layout="centered")
st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; }
        .stButton>button { background-color: #1f222a; color: white; border-radius: 10px; }
        .css-1d391kg { background-color: #1f222a; }
        .logout-button {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 9999;
        }
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
start_time = time.time()

# --- LOGIN ---
VALID_EMAIL = "urielcontact2@gmail.com"
if "logged_in" not in st.session_state:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email == VALID_EMAIL and password:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")
else:
    st.markdown('<div class="logout-button">' + st.button("🚪 Logout", key="logout_button") * "" + '</div>', unsafe_allow_html=True)
    if st.session_state.get("logout_button"):
        st.session_state.clear()
        st.experimental_rerun()

    refresh_now = st.button("🔄 Refresh Now")

# --- FETCH SPY PRICE ---
def get_spy_price():
    try:
        return 604.15  # Replace with real API call later
    except Exception as e:
        st.error(f"🔴 Error fetching SPY price: {e}")
        return None

# --- MOCK DATA PLACEHOLDERS (Replace with real sources) ---
def calculate_rsi():
    return 62.5

def get_support_resistance_levels():
    return {'support': 600, 'resistance': 610, 'buy_zone': (602, 606)}

def get_market_momentum():
    return 'bullish'

def get_option_chain():
    try:
        options = wb.get_options('SPY')
        rows = []
        for item in options:
            for direction in ['call', 'put']:
                if direction in item:
                    contract = item[direction]
                    if contract and isinstance(contract, dict):
                        row = {
                            'type': direction.capitalize(),
                            'strike': float(contract.get('strikePrice', 0)),
                            'lastPrice': float(contract.get('askList')[0].get('price', 0)) if contract.get('askList') else 0,
                            'volume': int(contract.get('volume', 0)),
                            'openInterest': int(contract.get('openInterest', 0)),
                            'impliedVolatility': float(contract.get('impliedVolatility', 0)) or 1,
                            'expirationDate': contract.get('expireDate')
                        }
                        rows.append(row)
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Failed to fetch option chain: {e}")
        return pd.DataFrame()

# --- SCORING LOGIC ---
def score_option(row, rsi, current_price, levels, momentum):
    score = 0
    if pd.isna(row['impliedVolatility']) or row['volume'] == 0:
        return -1
    if not (current_price + 3 >= row['strike'] >= current_price + 1 or current_price - 3 <= row['strike'] <= current_price - 1):
        return -1

    score += row['volume'] / 1000
    score += row['openInterest'] / 1000
    score += 1 / row['impliedVolatility'] * 100
    if row['type'] == 'Call' and rsi < 70 and momentum == 'bullish' and current_price < row['strike'] + 3:
        score += 10
    elif row['type'] == 'Put' and rsi > 30 and momentum == 'bearish' and current_price > row['strike'] - 3:
        score += 10
    support, resistance = levels['support'], levels['resistance']
    if row['type'] == 'Call' and current_price > support:
        score += 5
    elif row['type'] == 'Put' and current_price < resistance:
        score += 5
    low, high = levels['buy_zone']
    if low <= current_price <= high:
        score += 5
    return score

# --- REFRESH CONTROL ---
current_time = time.time()
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0
should_refresh = False
if 'logged_in' in st.session_state:
    if refresh_now:
        should_refresh = True
        st.session_state.last_refresh = current_time
    elif current_time - st.session_state.last_refresh >= 60:
        should_refresh = True
        st.session_state.last_refresh = current_time

# --- DISPLAY ---
if 'logged_in' in st.session_state and should_refresh:
    price = get_spy_price()
    rsi = calculate_rsi()
    momentum = get_market_momentum()
    levels = get_support_resistance_levels()

    if price is not None:
        st.markdown(f"**📉 SPY Price**: ${price}")
    if rsi:
        st.markdown(f"**📊 RSI (14d)**: {rsi}")
    if momentum:
        st.markdown(f"**📈 Market Momentum**: {momentum.title()}")

    st.subheader("🔍 Best Option Based on Algo")
    st.markdown("---")

    if is_market_open():
        options_df = get_option_chain()
        if not options_df.empty:
            options_df = options_df.dropna(subset=['lastPrice'])
            options_df['score'] = options_df.apply(lambda row: score_option(row, rsi, price, levels, momentum), axis=1)

            valid_options = options_df[options_df['score'] > 0]
            if not valid_options.empty:
                best_option = valid_options.loc[valid_options['score'].idxmax()]
                st.markdown(f"**🔹 Type**: {best_option['type']} - **Strike**: {best_option['strike']} - Exp: {best_option['expirationDate']}")
                st.markdown(f"**💰 Last Price**: ${round(best_option['lastPrice'], 2)}")
                st.markdown(f"**🎯 Target (10%)**: ${round(best_option['lastPrice'] * 1.10, 2)}")
                st.markdown(f"**🚑 Stop (20%)**: ${round(best_option['lastPrice'] * 0.80, 2)}")
                st.markdown(f"**📊 Volume**: {int(best_option['volume'])} | **OI**: {int(best_option['openInterest'])}")
                st.markdown(f"**🧠 IV (proxy for delta)**: {round(best_option['impliedVolatility'], 4)}")
                st.info(f"📈 Strategy Insight: Chosen based on real-time volume, OI, momentum ('{momentum}'), RSI {round(rsi, 1)}, and price range alignment with support/resistance.")
                st.success("This contract has the highest potential to hit your 10% target today.")
            else:
                st.warning("⚠️ No safe SPY option trade found right now. Sit tight — no trash trades.")
        else:
            st.warning("⚠️ Could not load option chain. Try again later.")

# --- COUNTDOWN TIMER ---
if 'logged_in' in st.session_state and not refresh_now:
    while True:
        elapsed = int(time.time() - start_time)
        remaining = st_autorefresh_interval - (elapsed % st_autorefresh_interval)
        countdown.markdown(f"⏳ Auto-refresh in: **{remaining} seconds**")
        time.sleep(1)
        if remaining == 1:
            st.experimental_rerun()
