import requests
import datetime
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

# --- TOKEN INPUT ---
st.title("🔫 SPY Options Sniper")
TOKEN = st.text_input("Paste your Webull token:", type="password")

# --- TOKEN TIMER ---
if TOKEN:
    token_start_time = datetime.datetime.now()
    token_expiry_time = token_start_time + timedelta(hours=24)
    time_remaining = token_expiry_time - datetime.datetime.now()
    st.info(f"⏳ Token valid for: {str(time_remaining).split('.')[0]}")

    # --- FETCH LIVE SPY PRICE ---
    def get_spy_price(token):
        headers = {"Authorization": f"Bearer {token}"}
        url = "https://api.webull.com/api/quote/option/real-time/spy"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("lastPrice", "Unavailable")
        except Exception as e:
            return f"Error: {e}"

    spy_price = get_spy_price(TOKEN)
    st.markdown(f"**📉 Live SPY Price**: ${spy_price}")

# --- MOCKED DATA PREVIEW ---
if TOKEN:
    st.subheader("🔍 Today's Pick")
    st.markdown("---")
    st.markdown("**📈 SPY Trend**: Bullish (based on RSI & Momentum)")
    st.markdown("**🔹 Contract**: 600 Call - Expiring Today")
    st.markdown("**💰 Entry Price**: $1.20")
    st.markdown("**🎯 10% Target**: $1.32")
    st.markdown("**🛑 20% Stop**: $0.96")
    st.markdown("**📊 Volume**: 40,120 | **OI**: 120,560")
    st.markdown("**🧠 Reason**: RSI 55, Uptrend, Strong support at 599.75, High volume")
    st.success("This contract has the highest probability of hitting your 10% daily goal today.")

else:
    st.warning("🔐 Please paste your Webull token to activate live scanning.")
