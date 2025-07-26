import shutil
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime
import os
import random
import json
from streamlit_autorefresh import st_autorefresh
from dateutil import parser
from helpers import generate_asset_page
import requests
from bs4 import BeautifulSoup
import finnhub
import sidebar

# --------------------------
# Auto-refresh every 60 seconds
# --------------------------
st_autorefresh(interval=60000, key="refresh")

# --------------------------
# Sidebar
# --------------------------
sidebar.render_sidebar()

# --------------------------
# Initialize session state
# --------------------------
if 'cash_balance' not in st.session_state:
    st.session_state.cash_balance = 100000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}
if 'history' not in st.session_state:
    st.session_state.history = []
if 'portfolio_value_log' not in st.session_state:
    st.session_state.portfolio_value_log = []
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# --------------------------
# Helper Functions
# --------------------------
def get_live_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
        else:
            return ticker.info.get("regularMarketPrice", None)
    except Exception as e:
        st.warning(f"⚠️ Live price not available for {symbol}")
        return None

def calculate_portfolio_value():
    total = 0
    for asset, shares in st.session_state.portfolio.items():
        price = get_live_price(asset)
        if price is not None:
            total += shares * price
    return total

def log_portfolio_value():
    value = calculate_portfolio_value() + st.session_state.cash_balance
    st.session_state.portfolio_value_log.append({
        "date": datetime.now().isoformat(),
        "value": value
    })

def dividends():
    total_dividends = 0
    for asset, shares in st.session_state.portfolio.items():
        try:
            info = yf.Ticker(asset).info
            yield_annual = info.get("dividendYield", 0)
            if yield_annual:
                monthly_yield = yield_annual / 12
                price = get_live_price(asset)
                if price:
                    total_dividends += shares * price * monthly_yield
        except:
            continue
    return total_dividends


def portfolio_health_score():
    assets = st.session_state.portfolio
    total_assets = len(assets)
    if total_assets == 0:
        return "Poor", "You haven't diversified yet. Try investing in multiple assets."
    elif total_assets == 1:
        return "Average", "Try diversifying across industries or sectors."
    elif total_assets >= 3:
        return "Great", "Well-diversified portfolio. Keep reviewing your positions!"
    else:
        return "Good", "Nice start! Add a few more asset types to reduce risk."

def risk_indicator():
    risky_assets = ["BTC-USD", "ETH-USD"]
    risky_weight = sum(
        st.session_state.portfolio.get(asset, 0) * get_live_price(asset)
        for asset in risky_assets if asset in st.session_state.portfolio
    )
    total = calculate_portfolio_value()
    if total == 0:
        return "N/A"
    ratio = risky_weight / total
    if ratio > 0.7:
        return "⚠️ High Risk - Too much in volatile assets"
    elif ratio > 0.4:
        return "🟡 Medium Risk"
    else:
        return "🟢 Low Risk"

def fetch_trending_stocks(limit=5):
    url = "https://finance.yahoo.com/trending-tickers"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        df = pd.read_html(str(table))[0]
        return df["Symbol"].head(limit).tolist()
    except Exception as e:
        st.warning("⚠️ Could not fetch trending stocks.")
        return []
def get_stock_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "name": info.get("shortName", "N/A"),
            "price": get_live_price(symbol),
            "summary": info.get("longBusinessSummary", "No description available."),
            "sector": info.get("sector", "N/A"),
        }
    except:
        return None


# --------------------------
# Theme Map
# --------------------------
theme_map = {
    "AAPL": "Tech", "MSFT": "Tech", "NVDA": "Tech", "GOOGL": "Tech", "META": "Tech",
    "TSLA": "Green Energy", "ICLN": "Green Energy",
    "AMZN": "Consumer", "PEP": "Consumer",
    "BTC-USD": "Crypto", "ETH-USD": "Crypto",
    "SPY": "Index ETF", "QQQ": "Index ETF"
}


# --------------------------
# Main App Interface
# --------------------------
st.title("Student Stock Simulator")
st.subheader("Start with $100,000 of free money and learn how to invest!")

nasdaq_df = pd.read_csv("extended_nasdaq_symbols.csv")
nasdaq_df["label"] = nasdaq_df["Symbol"] + " - " + nasdaq_df["Company Name"]
selected_label = st.selectbox("Select a stock:", nasdaq_df["label"])
user_ticker = selected_label.split(" - ")[0]
price = get_live_price(user_ticker)



if price:
    st.success(f"{user_ticker} current price: ${price:.2f}")
else:
    st.error("Price data not available.")

# Buy Section
st.markdown("### Buy Stocks")
shares_to_buy = st.number_input(f"How many shares of {user_ticker} to buy?", min_value=0.0, step=0.0001, format="%.6f")

if st.button("Buy"):
    total_cost = price * shares_to_buy
    if total_cost > st.session_state.cash_balance:
        st.error("Not enough cash!")
    elif shares_to_buy > 0:
        st.session_state.cash_balance -= total_cost
        st.session_state.portfolio[user_ticker] = st.session_state.portfolio.get(user_ticker, 0) + shares_to_buy
        st.session_state.history.append({
            "date": datetime.now(),
            "action": "Buy",
            "asset": user_ticker,
            "shares": shares_to_buy,
            "price": price,
            "total": total_cost
        })
        generate_asset_page(user_ticker)
        log_portfolio_value()
        st.success(f"Bought {shares_to_buy:.6f} shares of {user_ticker} at ${price:.2f} each.")

# Sell Section
st.markdown("### Sell Stocks")
if st.session_state.portfolio:
    sell_asset = st.selectbox("Choose asset to sell", list(st.session_state.portfolio.keys()))
    max_shares = st.session_state.portfolio.get(sell_asset, 0)
    sell_shares = st.number_input(
        "How many shares to sell?",
        min_value=0.0,
        max_value=float(max_shares),
        step=0.0001,
        format="%.6f"
    )
    sell_shares = round(sell_shares, 6)

    if st.button("Sell"):
        sell_price = get_live_price(sell_asset)
        if sell_shares <= max_shares and sell_shares > 0 and sell_price:
            revenue = sell_shares * sell_price
            st.session_state.cash_balance += revenue
            st.session_state.portfolio[sell_asset] -= sell_shares
            st.session_state.portfolio[sell_asset] = round(st.session_state.portfolio[sell_asset], 6)

            if st.session_state.portfolio[sell_asset] <= 0:
                del st.session_state.portfolio[sell_asset]

            st.session_state.history.append({
                "date": datetime.now(),
                "action": "Sell",
                "asset": sell_asset,
                "shares": sell_shares,
                "price": sell_price,
                "total": revenue
            })
            log_portfolio_value()
            st.success(f"Sold {sell_shares} shares of {sell_asset} at ${sell_price:.2f}")
        else:
            st.error("Invalid sell amount or price unavailable.")

# Cash Display
st.metric(label=" Cash You Have", value=f"${st.session_state.cash_balance:,.2f}")
remaining_percent = st.session_state.cash_balance / 100000
st.progress(remaining_percent)
st.write(f"💵 You have {remaining_percent*100:.1f}% of your $100,000 remaining.")

# Portfolio Overview
st.markdown("### Your Portfolio")
if st.session_state.portfolio:
    df = pd.DataFrame([
        {
            "Asset": k,
            "Shares": v,
            "Current Price": get_live_price(k),
            "Value": v * get_live_price(k)
        } for k, v in st.session_state.portfolio.items()
        if get_live_price(k) is not None
    ])
    df["Value"] = df["Value"].round(2)
    st.dataframe(df.style.format({"Value": "${:,.2f}", "Current Price": "${:,.2f}"}))
    st.metric(label=" Portfolio Value", value=f"${df['Value'].sum():,.2f}")
else:
    st.info("You haven't bought anything yet.")

# Theme Breakdown
theme_summary = {}
for ticker, shares in st.session_state.portfolio.items():
    theme = theme_map.get(ticker, "Other")
    p = get_live_price(ticker)
    if p:
        value = shares * p
        theme_summary[theme] = theme_summary.get(theme, 0) + value

theme_df = pd.DataFrame(list(theme_summary.items()), columns=["Theme", "Total Value"])
theme_df["Total Value"] = theme_df["Total Value"].astype(float).round(2)
st.markdown("### 🎯 Portfolio Breakdown by Theme")
st.dataframe(theme_df)
st.plotly_chart(px.pie(theme_df, names="Theme", values="Total Value", title="Portfolio Allocation"))

# Portfolio Growth Tracking (auto-log every 60s)
if len(st.session_state.portfolio_value_log) == 0 or (
    datetime.now() - parser.parse(str(st.session_state.portfolio_value_log[-1]["date"]))
).seconds >= 60:
    log_portfolio_value()

st.markdown("### Portfolio Growth Tracker")
value_df = pd.DataFrame(st.session_state.portfolio_value_log)
fig = px.line(value_df, x="date", y="value", title="Portfolio Value Over Time")
st.plotly_chart(fig)

gain_percent = ((value_df["value"].iloc[-1] - 100000) / 100000) * 100
st.metric("Total Gain", f"{gain_percent:.2f}%")

# Analytics
st.markdown("## Analytics & Feedback")
score, feedback = portfolio_health_score()
st.success(f"**Portfolio Health Score:** {score} — {feedback}")
st.markdown("### Risk Level")
st.warning(risk_indicator())
st.markdown("### Estimated Monthly Dividends")
st.info(f"Estimated Monthly Dividends: ${dividends():.2f}")

# History
st.markdown("### Transaction History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history))
else:
    st.info("No transactions yet.")

# Tips
tips = [
    "💡 Tip: Diversify your investments.",
    "📉 Don’t panic when the market drops!",
    "📊 Review your portfolio weekly.",
    "🏆 Long-term thinking wins."
]
st.info(random.choice(tips))
