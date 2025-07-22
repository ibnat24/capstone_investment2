
import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime
import feedparser
from streamlit_autorefresh import st_autorefresh
from helpers import get_transactions_for_asset

ticker = "BTC-USD"
st_autorefresh(interval=60000, key="refresh_BTC-USD")


st.title("📉 " + ticker + " – Asset Dashboard")

# Asset Info
info = yf.Ticker(ticker).info

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏢 Company Info")
    st.markdown(f"**Name**: {info.get('shortName', 'N/A')}")
    st.markdown(f"**Industry**: {info.get('industry', 'N/A')}")
    st.markdown(f"**Sector**: {info.get('sector', 'N/A')}")
    st.markdown(info.get("longBusinessSummary", "No description available."))

with col2:
    price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
    st.subheader("💰 Live Price")
    st.metric(label=ticker + " Price", value=f"${price:,.2f}")

with col3:
    st.subheader("📊 Key Financials")
    st.write(f"**Market Cap**: ${info.get('marketCap', 0):,}")
    st.write(f"**P/E Ratio**: {info.get('trailingPE', 'N/A')}")
    st.write(f"**Dividend Yield**: {info.get('dividendYield', 0) * 100:.2f}%")


# Timeframe selector
st.header("📊 Price Trend")
timeframe = st.radio("Select timeframe:", ["7 Days", "1 Month", "1 Year"], horizontal=True)
period_map = {
    "7 Days": "7d",
    "1 Month": "1mo",
    "1 Year": "1y"
}
period = period_map[timeframe]

try:
    df = yf.Ticker(ticker).history(period=period)
    fig = px.line(df, x=df.index, y="Close", title=ticker + " - Price Trend (" + timeframe + ")")
    st.plotly_chart(fig)
except Exception as e:
    st.warning("Error loading chart: " + str(e))

# Transaction history
st.header("🧾 Your Transactions for This Asset")
txns = get_transactions_for_asset(ticker)
# Unrealized Gain/Loss
if not txns.empty:
    total_cost = (txns['price'] * txns['shares']).sum()
    total_shares = txns['shares'].sum()
    avg_buy_price = total_cost / total_shares if total_shares else 0
    gain = ((price - avg_buy_price) / avg_buy_price) * 100 if avg_buy_price else 0
    st.metric("📈 Unrealized Return", f"{gain:.2f}%", delta=f"${price - avg_buy_price:.2f}")


if txns.empty:
    st.info("No transactions for this asset yet.")
else:
    st.dataframe(txns)


# News Section Placeholder
st.header("📰 Latest News on " + ticker)
try:
    rss = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    if rss.entries:
        for entry in rss.entries[:5]:
            st.markdown(f"- [{entry.title}]({entry.link})")
    else:
        st.info("No news articles found.")
except Exception as e:
    st.warning("Error fetching news: " + str(e))
