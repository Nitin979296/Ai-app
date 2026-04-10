import streamlit as st
import pandas as pd
import yfinance as yf

# 1. Page Setup
st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("📈 Mera Pehla AI Trading Dashboard")
st.write("Jadu dekhiye: Ab isme asli Algorithm (Brain) lag chuka hai jo Trend bata raha hai! 🧠")
st.divider()

# 2. DATA FETCH & ALGORITHM (The Brain)
try:
    nifty = yf.Ticker("^NSEI")
    # Aaj ka 15-minute ki candles ka data nikal rahe hain
    live_data = nifty.history(period="1d", interval="15m") 
    
    # Live Price nikalna
    live_price = round(live_data['Close'].iloc[-1], 2)
    open_price = round(live_data['Open'].iloc[0], 2)
    point_change = round(live_price - open_price, 2)
    
    # 🧠 ALGORITHM: 10-Candle Moving Average (Trend nikalne ke liye)
    live_data['SMA_10'] = live_data['Close'].rolling(window=10).mean()
    current_average = live_data['SMA_10'].iloc[-1]
    
    # AI Logic
    if live_price > current_average:
        market_trend = "BULLISH 🟢"
        trend_msg = "Price is above Average"
    else:
        market_trend = "BEARISH 🔴"
        trend_msg = "Price is below Average"

except Exception as e:
    live_price = "Data Error"
    point_change = "0"
    market_trend = "ERROR"
    trend_msg = "Connection Issue"

# 3. Dashboard par dikhana
col1, col2, col3 = st.columns(3)

col1.metric(label="NIFTY 50 (Live)", value=live_price, delta=point_change)

# Ab Trend wala dabba Asli Algorithm se chal raha hai!
col2.metric(label="Market Trend (Algorithmic)", value=market_trend, delta=trend_msg, delta_color="off")

# PCR abhi aage aayega
col3.metric(label="Put-Call Ratio (PCR)", value="Coming Soon", delta="Next Step")

# 4. Chart Dikhana (Ek naya feature!)
st.subheader("📊 Nifty Intraday Trend (Live Chart)")
st.line_chart(live_data['Close'])
