import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("📈 Mera Pehla AI Trading Dashboard")
st.write("Jadu dekhiye: Ab isme Asli Option Chain ka PCR (Put-Call Ratio) bhi aa gaya hai! 🔥")
st.divider()

# --- 1. NSE OPTION CHAIN DATA (PCR CALCULATION) ---
def get_pcr():
    try:
        url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9'
        }
        session = requests.Session()
        # Pehle base url par ja kar cookies leni padti hain, warna NSE block kar deta hai
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tot_ce = data['filtered']['CE']['totOI']
            tot_pe = data['filtered']['PE']['totOI']
            pcr_value = round(tot_pe / tot_ce, 2)
            
            if pcr_value > 1.0:
                return pcr_value, "Tezi (Bullish) 🟢"
            else:
                return pcr_value, "Mandi (Bearish) 🔴"
        else:
            return "Error", "NSE Blocked"
    except Exception as e:
        return "Loading...", "Data Delay"

pcr_val, pcr_trend = get_pcr()

# --- 2. NIFTY LIVE DATA & TREND ALGORITHM ---
try:
    nifty = yf.Ticker("^NSEI")
    live_data = nifty.history(period="1d", interval="15m") 
    
    live_price = round(live_data['Close'].iloc[-1], 2)
    open_price = round(live_data['Open'].iloc[0], 2)
    point_change = round(live_price - open_price, 2)
    
    live_data['SMA_10'] = live_data['Close'].rolling(window=10).mean()
    current_average = live_data['SMA_10'].iloc[-1]
    
    if live_price > current_average:
        market_trend = "BULLISH 🟢"
    else:
        market_trend = "BEARISH 🔴"
except Exception as e:
    live_price = "Error"
    point_change = "0"
    market_trend = "ERROR"

# --- 3. DASHBOARD UI ---
col1, col2, col3 = st.columns(3)

col1.metric(label="NIFTY 50 (Live)", value=live_price, delta=point_change)
col2.metric(label="Chart Trend (Algorithm)", value=market_trend, delta="Based on 15m SMA", delta_color="off")
col3.metric(label="Put-Call Ratio (PCR)", value=pcr_val, delta=pcr_trend, delta_color="off")

st.subheader("📊 Nifty Intraday Trend (Live Chart)")
st.line_chart(live_data['Close'])
