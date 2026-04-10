import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time
from streamlit_autorefresh import st_autorefresh

# --- PAGE SETUP & THEME ---
st.set_page_config(page_title="Pro AI Trader", layout="wide", initial_sidebar_state="expanded")

# Auto-refresh har 30 second mein (Taki aapko refresh na karna pade)
count = st_autorefresh(interval=30000, limit=100, key="data_refresh")

st.title("🚀 Pro AI Trading Terminal")
st.markdown("Live Option Chain | AI Signals | BankNifty | Auto-Refresh 30s")
st.divider()

# --- SIDEBAR (Settings & Telegram) ---
st.sidebar.header("⚙️ Settings")
selected_index = st.sidebar.selectbox("Market Select Karein:", ["NIFTY", "BANKNIFTY", "FINNIFTY"])

st.sidebar.subheader("📱 Telegram Alerts")
telegram_token = st.sidebar.text_input("Bot Token (Optional)", type="password")
telegram_chatid = st.sidebar.text_input("Chat ID (Optional)", type="password")

# Index Ticker Mapping
tickers = {
    "NIFTY": {"yf": "^NSEI", "nse": "NIFTY"},
    "BANKNIFTY": {"yf": "^NSEBANK", "nse": "BANKNIFTY"},
    "FINNIFTY": {"yf": "NIFTY_FIN_SERVICE.NS", "nse": "FINNIFTY"}
}

# --- FUNCTIONS WITH CACHING (Jisse NSE block na kare) ---
@st.cache_data(ttl=30) # 30 second tak data save rakhega, baar-baar download nahi karega
def fetch_market_data(ticker):
    try:
        # Pichle 5 din ka data lenge taki SMA aur RSI sahi se ban sake
        data = yf.Ticker(ticker).history(period="5d", interval="15m")
        if data.empty:
            return None
        
        # Indicators: SMA (10) aur simple RSI (14)
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        
        # RSI Calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI_14'] = 100 - (100 / (1 + rs))
        
        return data
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def fetch_option_chain(symbol):
    try:
        url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9'
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except:
        return None

def send_telegram_msg(msg):
    if telegram_token and telegram_chatid:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chatid}&text={msg}"
        requests.get(url)

# --- FETCHING DATA ---
yf_ticker = tickers[selected_index]["yf"]
nse_ticker = tickers[selected_index]["nse"]

live_data = fetch_market_data(yf_ticker)
oc_data = fetch_option_chain(nse_ticker)

# --- UI LOGIC ---
if live_data is None:
    st.error("Market Data abhi available nahi hai (Market closed ya Yahoo Finance error).")
else:
    # Safe iloc (Weekend Error Fix)
    current_price = round(live_data['Close'].iloc[-1], 2)
    sma_10 = live_data['SMA_10'].iloc[-1]
    rsi_14 = live_data['RSI_14'].iloc[-1]
    
    # Process Option Chain
    pcr_value = 0
    pcr_status = "N/A"
    df_oc = pd.DataFrame()
    
    if oc_data and 'filtered' in oc_data:
        tot_ce = oc_data['filtered']['CE']['totOI']
        tot_pe = oc_data['filtered']['PE']['totOI']
        pcr_value = round(tot_pe / tot_ce, 2) if tot_ce > 0 else 0
        
        # Full Option Chain Table Banana
        records = []
        for item in oc_data['filtered']['data']:
            ce = item.get('CE', {})
            pe = item.get('PE', {})
            records.append({
                "CE Chg OI": ce.get('changeinOpenInterest', 0),
                "CE OI": ce.get('openInterest', 0),
                "CE LTP": ce.get('lastPrice', 0),
                "STRIKE": item.get('strikePrice'),
                "PE LTP": pe.get('lastPrice', 0),
                "PE OI": pe.get('openInterest', 0),
                "PE Chg OI": pe.get('changeinOpenInterest', 0)
            })
        df_oc = pd.DataFrame(records)
        
        # Sirf current price ke aas-paas (ATM) ki 10 strike dikhane ke liye filter
        df_oc = df_oc[(df_oc['STRIKE'] > current_price - 500) & (df_oc['STRIKE'] < current_price + 500)]
    
    # --- AI MULTI-SIGNAL ENGINE ---
    signal = "WAIT ⏳"
    signal_color = "warning"
    
    is_bullish_price = current_price > sma_10
    is_bullish_pcr = pcr_value >= 1.0
    
    if is_bullish_price and is_bullish_pcr and rsi_14 < 70:
        signal = "STRONG BUY (CE) 🟢"
        signal_color = "success"
    elif not is_bullish_price and pcr_value < 0.9 and rsi_14 > 30:
        signal = "STRONG SELL (PE) 🔴"
        signal_color = "error"
        
    # Send Telegram Alert (sirf jab signal badle)
    if "last_signal" not in st.session_state:
        st.session_state.last_signal = signal
    elif st.session_state.last_signal != signal and signal != "WAIT ⏳":
        send_telegram_msg(f"🚨 {selected_index} ALERT: {signal} at Price {current_price}")
        st.session_state.last_signal = signal

    # --- TOP DASHBOARD METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Price", f"{current_price}")
    col2.metric("Trend (SMA 10)", "BULLISH ⬆️" if is_bullish_price else "BEARISH ⬇️")
    col3.metric("RSI (Momentum)", f"{rsi_14:.1f}")
    col4.metric("PCR (Data)", f"{pcr_value}")

    # --- MASTER AI SIGNAL ---
    st.markdown(f"### AI Master Signal: ")
    if signal_color == "success":
        st.success(f"**{signal}** - Price upar hai, PCR positive hai, overbought nahi hai.")
    elif signal_color == "error":
        st.error(f"**{signal}** - Price niche hai, PCR negative hai, oversold nahi hai.")
    else:
        st.warning(f"**{signal}** - Market sideways hai. Faltu trade mat lena!")

    # --- TABS FOR CHARTS AND DATA ---
    tab1, tab2 = st.tabs(["📊 Live Chart", "📈 Full Option Chain"])
    
    with tab1:
        st.line_chart(live_data['Close'])
        
    with tab2:
        if not df_oc.empty:
            st.dataframe(df_oc.set_index('STRIKE').style.background_gradient(cmap='Blues'), use_container_width=True)
        else:
            st.error("NSE Server ne block kar diya hai. Cloud par NSE kabhi-kabhi data nahi deta. Local laptop par test karein.")
