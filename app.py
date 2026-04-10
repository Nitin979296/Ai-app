import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# Auto-refresh (agar library install hai toh chalega)
try:
    from streamlit_autorefresh import st_autorefresh
    count = st_autorefresh(interval=30000, limit=100, key="data_refresh")
except ImportError:
    st.warning("⚠️ streamlit-autorefresh install nahi hai. Manual refresh button use karo.")

st.set_page_config(page_title="Pro AI Trader", layout="wide", initial_sidebar_state="expanded")

st.title("🚀 Pro AI Trading Terminal")
st.markdown("Live Option Chain | AI Signals | BankNifty | Auto-Refresh 30s")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Settings")
selected_index = st.sidebar.selectbox("Market Select Karein:", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
st.sidebar.subheader("📱 Telegram Alerts")
telegram_token = st.sidebar.text_input("Bot Token (Optional)", type="password")
telegram_chatid = st.sidebar.text_input("Chat ID (Optional)", type="password")

tickers = {
    "NIFTY": {"yf": "^NSEI", "nse": "NIFTY"},
    "BANKNIFTY": {"yf": "^NSEBANK", "nse": "BANKNIFTY"},
    "FINNIFTY": {"yf": "NIFTY_FIN_SERVICE.NS", "nse": "FINNIFTY"}
}

# --- CACHING FUNCTIONS ---
@st.cache_data(ttl=30)
def fetch_market_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d", interval="15m")
        if data.empty:
            return None
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        
        # Improved RSI with NaN handling
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI_14'] = 100 - (100 / (1 + rs))
        data['RSI_14'] = data['RSI_14'].fillna(50)  # NaN ko safe value
        return data
    except:
        return None

@st.cache_data(ttl=60)
def fetch_option_chain(symbol):
    try:
        url = f'https://www.nseindia.com/api/option-chain-indices?symbol={symbol}'
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9'
        }
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        response = session.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def send_telegram_msg(msg):
    if telegram_token and telegram_chatid:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage?chat_id={telegram_chatid}&text={msg}"
            requests.get(url, timeout=5)
        except:
            pass

# --- DATA FETCH ---
yf_ticker = tickers[selected_index]["yf"]
nse_ticker = tickers[selected_index]["nse"]
live_data = fetch_market_data(yf_ticker)
oc_data = fetch_option_chain(nse_ticker)

# --- UI ---
if live_data is None:
    st.error("❌ Market Data nahi aa raha (Market closed ya yfinance issue).")
else:
    current_price = round(live_data['Close'].iloc[-1], 2)
    sma_10 = live_data['SMA_10'].iloc[-1]
    rsi_14 = live_data['RSI_14'].iloc[-1]

    # === OPTION CHAIN (Fixed Key) ===
    pcr_value = 0.0
    df_oc = pd.DataFrame()
    
    if oc_data and 'filtered' in oc_data:
        tot_ce = oc_data['filtered']['CE']['totOI']
        tot_pe = oc_data['filtered']['PE']['totOI']
        pcr_value = round(tot_pe / tot_ce, 2) if tot_ce > 0 else 0.0

        # FIXED: 'records' use kiya hai (yeh sahi key hai)
        records = oc_data.get('records', {}).get('data', [])
        option_rows = []
        for item in records:
            ce = item.get('CE', {})
            pe = item.get('PE', {})
            option_rows.append({
                "CE Chg OI": ce.get('changeinOpenInterest', 0),
                "CE OI": ce.get('openInterest', 0),
                "CE LTP": ce.get('lastPrice', 0),
                "STRIKE": item.get('strikePrice'),
                "PE LTP": pe.get('lastPrice', 0),
                "PE OI": pe.get('openInterest', 0),
                "PE Chg OI": pe.get('changeinOpenInterest', 0)
            })
        
        df_oc = pd.DataFrame(option_rows)
        # ATM strikes filter
        df_oc = df_oc[(df_oc['STRIKE'] > current_price - 500) & (df_oc['STRIKE'] < current_price + 500)]

    # --- AI SIGNAL ---
    is_bullish_price = current_price > sma_10
    is_bullish_pcr = pcr_value >= 1.0

    if is_bullish_price and is_bullish_pcr and rsi_14 < 70:
        signal = "STRONG BUY (CE) 🟢"
        signal_color = "success"
    elif not is_bullish_price and pcr_value < 0.9 and rsi_14 > 30:
        signal = "STRONG SELL (PE) 🔴"
        signal_color = "error"
    else:
        signal = "WAIT ⏳"
        signal_color = "warning"

    # Telegram Alert
    if "last_signal" not in st.session_state:
        st.session_state.last_signal = signal
    elif st.session_state.last_signal != signal and signal != "WAIT ⏳":
        send_telegram_msg(f"🚨 {selected_index} ALERT: {signal} | Price: {current_price}")
        st.session_state.last_signal = signal

    # --- METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Price", f"₹ {current_price}")
    col2.metric("Trend (SMA 10)", "BULLISH ⬆️" if is_bullish_price else "BEARISH ⬇️")
    col3.metric("RSI (14)", f"{rsi_14:.1f}")
    col4.metric("PCR", f"{pcr_value:.2f}")

    # --- MASTER SIGNAL ---
    if signal_color == "success":
        st.success(f"**{signal}** - Sab kuch bullish hai!")
    elif signal_color == "error":
        st.error(f"**{signal}** - Sab kuch bearish hai!")
    else:
        st.warning(f"**{signal}** - Market sideways hai. Trade mat lo.")

    # --- TABS ---
    tab1, tab2 = st.tabs(["📊 Live Chart", "📈 Full Option Chain"])
    
    with tab1:
        st.line_chart(live_data['Close'], use_container_width=True)
        st.caption(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")

    with tab2:
        if not df_oc.empty:
            st.dataframe(
                df_oc.set_index('STRIKE').style.background_gradient(cmap='Blues'),
                use_container_width=True
            )
        else:
            st.info("Option chain data aa raha hai... (NSE thoda slow hai)")

# --- MANUAL REFRESH ---
if st.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.rerun()

st.caption("Auto-refresh 30 sec | GitHub deploy ke liye requirements.txt mein 'streamlit-autorefresh' add kar do")
