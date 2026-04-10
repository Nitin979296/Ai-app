import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
import plotly.express as px
import time

st.set_page_config(page_title="AI Trading Bot", layout="wide", page_icon="📈")
st.title("📈 Mera Pehla AI Trading Dashboard")
st.write("**Real-time Nifty + Option Chain + AI Signals** 🔥")
st.divider()

# ================== CACHING (Sabse Important) ==================
@st.cache_data(ttl=45)  # 45 seconds mein refresh
def get_pcr():
    try:
        url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9'
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tot_ce = data['filtered']['CE']['totOI']
            tot_pe = data['filtered']['PE']['totOI']
            pcr_value = round(tot_pe / tot_ce, 2) if tot_ce > 0 else 0
            
            trend = "Tezi (Bullish) 🟢" if pcr_value > 1.0 else "Mandi (Bearish) 🔴"
            return pcr_value, trend, "✅ Live"
        else:
            return None, "NSE Blocked", "❌"
    except:
        return None, "Data Delay", "⚠️"

@st.cache_data(ttl=30)
def get_nifty_data():
    try:
        nifty = yf.Ticker("^NSEI")
        # 2d liya taaki market closed hone par bhi pichla data mile
        live_data = nifty.history(period="2d", interval="15m")
        
        if live_data.empty:
            raise ValueError("No data")
            
        live_price = round(live_data['Close'].iloc[-1], 2)
        open_price = round(live_data['Open'].iloc[0], 2) if len(live_data) > 1 else live_price
        point_change = round(live_price - open_price, 2)
        
        # Technical Indicators
        live_data['SMA_10'] = live_data['Close'].rolling(window=10).mean()
        live_data['SMA_20'] = live_data['Close'].rolling(window=20).mean()
        current_sma10 = live_data['SMA_10'].iloc[-1]
        
        market_trend = "BULLISH 🟢" if live_price > current_sma10 else "BEARISH 🔴"
        
        return live_data, live_price, point_change, market_trend, "✅ Live"
    except:
        return None, None, None, "ERROR", "❌"

# Data fetch
live_data, live_price, point_change, market_trend, price_status = get_nifty_data()
pcr_val, pcr_trend, pcr_status = get_pcr()

# ================== DASHBOARD ==================
col1, col2, col3, col4 = st.columns(4)

col1.metric("NIFTY 50 (Live)", 
            f"₹ {live_price}" if live_price else "Error", 
            f"{point_change} pts" if point_change else "0")

col2.metric("Chart Trend (SMA-10)", 
            market_trend, 
            delta="15m Candle", delta_color="off")

col3.metric("Put-Call Ratio (PCR)", 
            f"{pcr_val:.2f}" if pcr_val is not None else "Error", 
            pcr_trend, delta_color="off")

col4.metric("Market Status", price_status, pcr_status)

# ================== AI SIGNAL ==================
st.subheader("🤖 AI Trading Signal")
if live_price and pcr_val is not None:
    if market_trend == "BULLISH 🟢" and pcr_val > 1.1:
        signal = "🟢 **STRONG BUY** - Bullish + High PCR"
        color = "green"
    elif market_trend == "BEARISH 🔴" and pcr_val < 0.9:
        signal = "🔴 **STRONG SELL** - Bearish + Low PCR"
        color = "red"
    else:
        signal = "🟡 **NEUTRAL** - Wait for confirmation"
        color = "orange"
    st.markdown(f"<h3 style='color:{color};'>{signal}</h3>", unsafe_allow_html=True)

# ================== INTERACTIVE CHART ==================
st.subheader("📊 Nifty Intraday Trend (Live Chart)")
if live_data is not None:
    fig = px.line(live_data, y='Close', 
                  title=f"Nifty 50 - Last Updated: {datetime.now().strftime('%H:%M:%S')}",
                  template="plotly_dark",
                  markers=False)
    fig.add_hline(y=live_data['SMA_10'].iloc[-1], line_dash="dash", line_color="yellow", annotation_text="SMA 10")
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Nifty data nahi aa raha. Market band ho sakta hai.")

# ================== AUTO REFRESH BUTTON ==================
if st.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.rerun()

st.caption("Auto-refresh every 45 seconds (caching ke wajah se fast)")
