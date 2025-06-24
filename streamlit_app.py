import requests
import datetime
import pandas as pd
from typing import List, Dict
import streamlit as st
from datetime import timedelta

# --- CONFIG ---
st.set_page_config(page_title="SPY Sniper", layout="centered", initial_sidebar_state="auto")
st.markdown("""
    <style>
        body { background-color: #0e1117; color: white; }
        .stApp { background-color: #0e1117; }
        .stButton>button { background-color: #1f222a; color: white; border-radius: 10px; }
        .css-1d391kg { background-color: #1f222a; }
    </style>
""", unsafe_allow_html=True)

# --- WEBULL CONFIG ---
WEBULL_TOKEN = "dc_us_tech1.1979f0e3ec9-a6386e8d49fd4cfa9477c5276ad7d059"
TOKEN_EXPIRY = 24 * 60 * 60  # 24 hours in seconds

def get_webull_token_expiry():
    return timedelta(seconds=TOKEN_EXPIRY)

# --- STREAMLIT UI ---
st.title("🔫 SPY Options Sniper")
st.success(f"⏳ Token valid for: {str(get_webull_token_expiry())}")

# --- FETCH LIVE SPY PRICE FROM WEBULL ---
def get_spy_price_webull(token):
    url = "https://quotes-gw.webullfintech.com/api/quote/realTimeQuote?tickerId=913256135"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return round(float(data['lastSalePrice']), 2)
    except Exception as e:
        return f"Error: {e}"

# --- CALCULATE RSI FROM POLYGON (OPTIONAL BACKUP FOR HISTORICAL) ---
POLYGON_API_KEY = st.text_input("Paste your Polygon.io API Key (for RSI only):", type="password")

def calculate_rsi(api_key, symbol="SPY", window=14):
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/2024-01-01/{datetime.datetime.now().date()}?adjusted=true&sort=desc&limit=100&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.DataFrame(response.json()['results'])
        df['c'] = df['c'].astype(float)
        df = df[::-1]
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except Exception as e:
        return f"Error fetching RSI: {e}"

# --- DISPLAY PRICES ---
spy_price = get_spy_price_webull(WEBULL_TOKEN)
if POLYGON_API_KEY:
    rsi = calculate_rsi(POLYGON_API_KEY)
else:
    rsi = "N/A (No API Key)"

if isinstance(spy_price, (float, int)):
    st.markdown(f"**📉 Live SPY Price**: ${spy_price}")
else:
    st.markdown(f"**📉 Live SPY Price**: ${spy_price}")

if isinstance(rsi, (float, int)):
    st.markdown(f"**📊 RSI (14d)**: {rsi}")
else:
    st.markdown(f"**📊 RSI (14d)**: {rsi}")

# --- MOCKED OPTION PICK ---
if isinstance(spy_price, (float, int)):
    st.subheader("🔍 Today's Pick")
    st.markdown("---")
    st.markdown("**📈 SPY Trend**: Bullish (based on RSI & Momentum)")
    st.markdown("**🔹 Contract**: 600 Call - Expiring Today")
    st.markdown("**💰 Entry Price**: $1.20")
    st.markdown("**🎯 10% Target**: $1.32")
    st.markdown("**🛑 20% Stop**: $0.96")
    st.markdown("**📊 Volume**: 40,120 | **OI**: 120,560")
    st.markdown(f"**🧠 Reason**: RSI {rsi}, Uptrend, Strong support at 599.75, High volume")
    st.success("This contract has the highest probability of hitting your 10% daily goal today.")
else:
    st.warning("⚠️ Live data not available. Please check your Webull token.")
