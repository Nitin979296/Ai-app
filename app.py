import streamlit as st
import pandas as pd

# 1. Page ka Title aur Layout set karna
st.set_page_config(page_title="AI Trading Bot", layout="wide")
st.title("📈 Mera Pehla AI Trading Dashboard")

st.write("Welcome! Yeh mera khud ka banaya hua system hai.")
st.divider() # Ek line khichne ke liye

# 2. Autotender jaise 3 Data Box banana
col1, col2, col3 = st.columns(3)

col1.metric(label="NIFTY 50 (Live)", value="24,000.50", delta="+85.50")
col2.metric(label="Put-Call Ratio (PCR)", value="1.25", delta="+0.10")
col3.metric(label="Market Trend", value="BULLISH 🟢", delta="Buy on Dips")

# 3. Ek chota sa Data Table dikhana
st.subheader("Live Option Chain Data (Demo)")
dummy_data = {
    "Strike Price": [23900, 24000, 24100],
    "Call OI": [50000, 120000, 80000],
    "Put OI": [150000, 90000, 30000]
}
df = pd.DataFrame(dummy_data)
st.dataframe(df, use_container_width=True)