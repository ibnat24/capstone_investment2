import os

import pandas as pd

def get_transactions_for_asset(ticker):
    import streamlit as st

    # Ensure history exists in session
    if 'history' not in st.session_state:
        return pd.DataFrame()

    # Filter transactions for the specific asset
    data = [txn for txn in st.session_state.history if txn["asset"] == ticker]
    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)

def generate_asset_page(user_ticker):
    from streamlit_autorefresh import st_autorefresh
    directory = "pages"
    os.makedirs(directory, exist_ok=True)
    page_path = os.path.join(directory, f"{user_ticker}.py")
    if os.path.exists(page_path):
        return
    
    content = f'''
import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
from datetime import datetime
import feedparser
from streamlit_autorefresh import st_autorefresh
from helpers import get_transactions_for_asset
from sidebar import render_sidebar

render_sidebar()

ticker = "{user_ticker}"
st_autorefresh(interval=60000, key="refresh_{user_ticker}")

st.title("📉 " + ticker + " – Asset Dashboard")

info = yf.Ticker(ticker).info
price_data = yf.Ticker(ticker).history(period="1d")
price = price_data["Close"].iloc[-1] if not price_data.empty else None

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🏢 Company Info")
    st.markdown(f"**Name:** {{info.get('shortName', 'N/A')}}")
    st.markdown(f"**Industry:** {{info.get('industry', 'N/A')}}")
    st.markdown(f"**Sector:** {{info.get('sector', 'N/A')}}")

with col2:
    st.subheader("💰 Live Price")
    if price:
        st.metric(label=f"{{ticker}} Price", value=f"${{price:,.2f}}")
    else:
        st.write("N/A")

with col3:
    st.subheader("📊 Key Financials")
    market_cap = info.get('marketCap')
    pe_ratio = info.get('trailingPE')
    dividend_yield = info.get('dividendYield')

    st.metric(label="Market Cap", value=f"${{market_cap:,}}" if market_cap else "N/A", help="The total value of all a company's shares of stock.")
    st.metric(label="P/E Ratio", value=f"{{pe_ratio:.2f}}" if pe_ratio else "N/A", help="Price-to-Earnings ratio: shows how much investors are willing to pay per dollar of earnings.")
    st.metric(label="Dividend Yield", value=f"{{dividend_yield * 100:.2f}}%" if dividend_yield else "N/A", help="How much a company returns to shareholders as dividends, annually as a % of stock price.")

st.header("📊 Price Trend")
timeframe = st.radio("Select timeframe:", ["7 Days", "1 Month", "1 Year"], horizontal=True)
period_map = {{
    "7 Days": "7d",
    "1 Month": "1mo",
    "1 Year": "1y"
}}
period = period_map[timeframe]

try:
    df = yf.Ticker(ticker).history(period=period)
    fig = px.line(df, x=df.index, y="Close", title=ticker + " - Price Trend (" + timeframe + ")")
    st.plotly_chart(fig)
except Exception as e:
    st.warning("Error loading chart: " + str(e))

st.header("🧾 Your Transactions for This Asset")
txns = get_transactions_for_asset(ticker)

if not txns.empty:
    total_cost = (txns['price'] * txns['shares']).sum()
    total_shares = txns['shares'].sum()
    avg_buy_price = total_cost / total_shares if total_shares else 0
    gain = ((price - avg_buy_price) / avg_buy_price) * 100 if avg_buy_price else 0
    st.metric("📈 Unrealized Return", f"{{gain:.2f}}%", delta=f"${{price - avg_buy_price:.2f}}", help="Your % return if you sold at the current price vs. what you paid.")
else:
    st.info("No transactions for this asset yet.")

if not txns.empty:
    st.dataframe(txns)

st.header("📰 Latest News on " + ticker)
try:
    rss = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={{ticker}}")
    if rss.entries:
        for entry in rss.entries[:5]:
            st.markdown(f"- [{{entry.title}}]({{entry.link}})")
    else:
        st.info("No news articles found.")
except Exception as e:
    st.warning("Error fetching news: " + str(e))
'''



    try:
        with open(page_path, "w") as f:
            f.write(content)
        print(f"✅ Successfully generated: {page_path}")
    except Exception as e:
        print(f"❌ Failed to write page for {user_ticker}: {e}")
