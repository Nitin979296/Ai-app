import streamlit as st
import pandas as pd
import yfinance as yf

# 1. Page Setup
st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("📈 Mera Pehla AI Trading Dashboard")
st.write("Jadu dekhiye: Ab yeh NIFTY ka LIVE data internet se khud la raha hai! 🌐")
st.divider()

# 2. LIVE NIFTY DATA FETCH KARNA
# Yahoo Finance par Nifty 50 ka symbol '^NSEI' hota hai
try:
    nifty = yf.Ticker("^NSEI")
    live_data = nifty.history(period="1d") # Aaj ke din ka data
    
    # Data nikalna
    live_price = round(live_data['Close'].iloc[-1], 2)
    open_price = round(live_data['Open'].iloc[0], 2)
    point_change = round(live_price - open_price, 2)
    
except Exception as e:
    live_price = "Data Error"
    point_change = "0"

# 3. Dashboard par dikhana
col1, col2, col3 = st.columns(3)

# Yeh wala dabba ab Asli Live Data dikhayega!
col1.metric(label="NIFTY 50 (Live)", value=live_price, delta=point_change)

# PCR aur Trend abhi ke liye dummy hain, inhe hum agle step mein banayenge
col2.metric(label="Put-Call Ratio (PCR)", value="1.25", delta="+0.10")
col3.metric(label="Market Trend", value="BULLISH 🟢", delta="Buy on Dips")

# Option Chain (Dummy for now)
st.subheader("Live Option Chain (Coming Soon...)")
st.write("Agle step mein hum NSE ki website se asli Option chain ka data yahan layenge.")
