# sidebar.py
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import finnhub

# Predefined sector tickers for growth comparison
SECTOR_TICKERS = {
    "Tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"],
    "ETFs": ["SPY", "QQQ", "VTI", "VOO", "ARKK"],
    "Banking": ["JPM", "BAC", "WFC", "C", "GS"],
    "Green Energy": ["TSLA", "ICLN", "ENPH", "NEE", "PLUG"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "XRP-USD"]
}

@st.cache_data(ttl=3600)
def get_top_gainers(tickers, period="3mo"):
    stock_data = []
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period=period)
            price = data["Close"][-1] if not data.empty else None
            if len(data) >= 2:
                growth = (data["Close"][-1] - data["Close"][0]) / data["Close"][0]
                stock_data.append((ticker, round(growth * 100, 2), round(price, 2) if price else None))
        except:
            continue
    return sorted(stock_data, key=lambda x: x[1], reverse=True)[:5]

# Trending stocks helper functions
def fetch_trending_stocks(limit=5):
    url = "https://finance.yahoo.com/trending-tickers"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        df = pd.read_html(str(table))[0]
        return df["Symbol"].head(limit).tolist()
    except:
        return []

def get_stock_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "name": info.get("shortName", "N/A"),
            "price": info.get("regularMarketPrice", None),
            "sector": info.get("sector", "N/A"),
        }
    except:
        return None

def display_stock_popup(ticker):
    info = get_stock_info(ticker)
    if info:
        with st.expander(f"📈 Investment Info: {info['symbol']}"):
            st.write(f"**Name:** {info['name']}")
            st.write(f"**Price:** ${info['price']:.2f}" if info['price'] else "**Price:** N/A")
            st.write(f"**Sector:** {info['sector']}")
            try:
                hist = yf.Ticker(ticker).history(period="6mo")
                if not hist.empty:
                    pct_change = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) * 100
                    st.write(f"**6-Month Change:** {pct_change:.2f}%")
                    st.line_chart(hist["Close"], use_container_width=True)
                else:
                    st.write("No historical data available.")
            except:
                st.write("Historical data could not be fetched.")

# Sidebar layout
def render_sidebar():
    with st.sidebar:
        st.header("📘 Learn the Basics")

        for sector in SECTOR_TICKERS:
            with st.expander(f"{get_sector_icon(sector)} {sector}"):
                if sector == "Tech":
                    st.markdown("Fast-growing companies like Apple (AAPL), Microsoft (MSFT), and Nvidia.")
                elif sector == "ETFs":
                    st.markdown("Bundles of stocks — safer for beginners (e.g., SPY, QQQ).")
                elif sector == "Banking":
                    st.markdown("Big banks like JPMorgan (JPM) and Bank of America (BAC).")
                elif sector == "Green Energy":
                    st.markdown("Clean energy companies (e.g., ICLN, TSLA, ENPH).")
                elif sector == "Crypto":
                    st.markdown("Digital assets like Bitcoin (BTC) and Ethereum (ETH). Highly volatile!")

                gainers = get_top_gainers(SECTOR_TICKERS[sector])
                st.markdown("**Top Gainers (Last 3 Months):**")
                for ticker, growth, price in gainers:
                    if st.button(f"{ticker}: {growth}% | ${price if price else 'N/A'}", key=f"{sector}_{ticker}"):
                        display_stock_popup(ticker)

        st.markdown("---")

        st.header("🔥 Trending Stocks")
        trending_tickers = fetch_trending_stocks()

        for symbol in trending_tickers:
            info = get_stock_info(symbol)
            if info:
                if info["price"]:
                    st.subheader(f"{info['symbol']} – ${info['price']:.2f}")
                else:
                    st.subheader(f"{info['symbol']}")
                st.caption(f"**{info['name']}** ({info['sector']})")
            else:
                st.error(f"{symbol} info not available.")
            st.markdown("---")

        try:
            finnhub_client = finnhub.Client(api_key="d1vsb5pr01qmbi8pt1cgd1vsb5pr01qmbi8pt1d0")
            news = finnhub_client.general_news('general', min_id=0)
            st.header("📰 Stock Market News")
            for article in news[:5]:
                st.markdown(f"**[{article['headline']}]({article['url']})**")
                st.caption(article['summary'][:100] + "...")
        except:
            st.warning("Could not fetch news right now.")

def get_sector_icon(sector):
    return {
        "Tech": "🧠",
        "ETFs": "💼",
        "Banking": "🏦",
        "Green Energy": "🌱",
        "Crypto": "🔥"
    }.get(sector, "📊")
