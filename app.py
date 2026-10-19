
---

#### 3. `app.py` (main Streamlit code)

```python
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import plotly.express as px
import time

# Optional better FII/DII + constituents
try:
    from nselib import capital_market, indices
    NSELIB_AVAILABLE = True
except ImportError:
    NSELIB_AVAILABLE = False

st.set_page_config(
    page_title="Nifty Alpha & Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------
# CONFIG / STATIC DATA
# ------------------------------------------------------------

# Major NSE indices available on Yahoo Finance (symbol → display name)
INDEX_MAP = {
    "^NSEI": "Nifty 50",
    "^NSEBANK": "Nifty Bank",
    "^CNXIT": "Nifty IT",
    "^CNXPHARMA": "Nifty Pharma",
    "^CNXAUTO": "Nifty Auto",
    "^CNXFMCG": "Nifty FMCG",
    "^CNXMETAL": "Nifty Metal",
    "^CNXENERGY": "Nifty Energy",
    "^CNXINFRA": "Nifty Infra",
    "^CNXREALTY": "Nifty Realty",
    "^CNXMEDIA": "Nifty Media",
    "^CNXPSUBANK": "Nifty PSU Bank",
    "^CNXFINANCE": "Nifty Financial Services",
    "^CNXCONSUM": "Nifty Consumption",
    "^CNXSC": "Nifty Smallcap 100",
    "^CNXMIDCAP": "Nifty Midcap 100",
    "NIFTY_MIDCAP_150.NS": "Nifty Midcap 150",   # fallback style
    "^NSEMDCP50": "Nifty Midcap 50",
}

# Approximate top constituents for major indices (used when nselib not available)
TOP_STOCKS = {
    "Nifty Bank": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "Nifty IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "TECHM.NS", "WIPRO.NS"],
    "Nifty Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "AUROPHARMA.NS"],
    "Nifty Auto": ["MARUTI.NS", "M&M.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
    "Nifty FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "Nifty Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COALINDIA.NS"],
    "Nifty Energy": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BPCL.NS"],
    "Nifty Financial Services": ["HDFCBANK.NS", "ICICIBANK.NS", "BAJFINANCE.NS", "HDFC.NS", "SBIN.NS"],
}

PERIODS = {
    "1M": 21,
    "2M": 42,
    "3M": 63,
    "6M": 126,
    "12M": 252
}

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_index_returns():
    """Calculate returns & alpha for all indices vs Nifty 50"""
    results = []
    nifty = yf.Ticker("^NSEI")
    nifty_hist = nifty.history(period="1y")
    
    if nifty_hist.empty:
        return pd.DataFrame()
    
    nifty_close = nifty_hist["Close"]
    
    for symbol, name in INDEX_MAP.items():
        if symbol == "^NSEI":
            continue
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            if hist.empty or len(hist) < 30:
                continue
            
            close = hist["Close"]
            row = {"Index": name, "Symbol": symbol}
            
            for label, days in PERIODS.items():
                if len(close) > days and len(nifty_close) > days:
                    idx_ret = (close.iloc[-1] / close.iloc[-days] - 1) * 100
                    nifty_ret = (nifty_close.iloc[-1] / nifty_close.iloc[-days] - 1) * 100
                    alpha = idx_ret - nifty_ret
                    row[f"{label} Ret %"] = round(idx_ret, 2)
                    row[f"{label} Alpha"] = round(alpha, 2)
                else:
                    row[f"{label} Ret %"] = np.nan
                    row[f"{label} Alpha"] = np.nan
            
            results.append(row)
            time.sleep(0.2)  # be nice to Yahoo
        except Exception as e:
            continue
    
    df = pd.DataFrame(results)
    if not df.empty:
        # Rank by 3M Alpha primarily, then 1M
        df = df.sort_values(by=["3M Alpha", "1M Alpha"], ascending=False)
    return df

@st.cache_data(ttl=3600)
def get_stock_alpha(symbols, period_days=63):
    """Alpha of individual stocks vs Nifty 50"""
    nifty = yf.Ticker("^NSEI").history(period="1y")["Close"]
    data = []
    for sym in symbols:
        try:
            hist = yf.Ticker(sym).history(period="1y")["Close"]
            if len(hist) > period_days and len(nifty) > period_days:
                stock_ret = (hist.iloc[-1] / hist.iloc[-period_days] - 1) * 100
                nifty_ret = (nifty.iloc[-1] / nifty.iloc[-period_days] - 1) * 100
                alpha = stock_ret - nifty_ret
                data.append({
                    "Stock": sym.replace(".NS", ""),
                    "3M Return %": round(stock_ret, 2),
                    "3M Alpha": round(alpha, 2)
                })
        except:
            continue
    return pd.DataFrame(data).sort_values("3M Alpha", ascending=False)

@st.cache_data(ttl=1800)
def get_fii_dii():
    """FII/DII data – prefer nselib, fallback to Moneycontrol scrape"""
    result = {
        "fii_net": None, "dii_net": None,
        "fii_buy": None, "fii_sell": None,
        "dii_buy": None, "dii_sell": None,
        "last_5_fii": None, "last_5_dii": None,
        "nifty_close": None, "date": None
    }
    
    # Try nselib first
    if NSELIB_AVAILABLE:
        try:
            df = capital_market.fii_dii_trading_activity()
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                result["date"] = str(latest.get("Date", latest.name))
                result["fii_net"] = latest.get("FII_Net", latest.get("FII Net", None))
                result["dii_net"] = latest.get("DII_Net", latest.get("DII Net", None))
                # many versions have Buy/Sell columns
                for col in df.columns:
                    if "FII" in col.upper() and "BUY" in col.upper():
                        result["fii_buy"] = latest[col]
                    if "FII" in col.upper() and "SELL" in col.upper():
                        result["fii_sell"] = latest[col]
                    if "DII" in col.upper() and "BUY" in col.upper():
                        result["dii_buy"] = latest[col]
                    if "DII" in col.upper() and "SELL" in col.upper():
                        result["dii_sell"] = latest[col]
                
                # last 5 sessions
                if len(df) >= 5:
                    result["last_5_fii"] = df.tail(5)["FII_Net"].sum() if "FII_Net" in df.columns else None
                    result["last_5_dii"] = df.tail(5)["DII_Net"].sum() if "DII_Net" in df.columns else None
        except Exception as e:
            pass
    
    # Nifty close
    try:
        nifty = yf.Ticker("^NSEI").history(period="5d")
        if not nifty.empty:
            result["nifty_close"] = round(nifty["Close"].iloc[-1], 2)
    except:
        pass
    
    return result

@st.cache_data(ttl=3600)
def get_research_reports(limit=15):
    """Scrape latest broker research from Moneycontrol"""
    url = "https://www.moneycontrol.com/news/business/stocks/broker-research-report-13.html"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    reports = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, "lxml")
        
        # Moneycontrol structure changes often – this is a resilient attempt
        items = soup.select("li.clearfix, .article_box, .list_item, h2 a, .news_title")
        for item in items[:limit*2]:
            text = item.get_text(strip=True)
            if len(text) < 20:
                continue
            # simple parsing heuristics
            reports.append({
                "Headline": text[:120],
                "Source": "Moneycontrol",
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Link": item.get("href") if item.name == "a" else ""
            })
            if len(reports) >= limit:
                break
    except Exception as e:
        reports.append({"Headline": f"Could not fetch live reports ({e})", "Source": "-", "Date": "-", "Link": ""})
    
    return pd.DataFrame(reports[:limit])

@st.cache_data(ttl=900)
def get_news(feeds, limit=12):
    """Generic RSS news fetcher"""
    news = []
    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                news.append({
                    "Source": name,
                    "Title": entry.get("title", ""),
                    "Published": entry.get("published", "")[:16],
                    "Link": entry.get("link", "")
                })
        except:
            continue
    df = pd.DataFrame(news)
    if not df.empty:
        df = df.head(limit)
    return df

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
st.sidebar.title("📈 Nifty Alpha Dashboard")
st.sidebar.markdown("Data refreshes every 15-60 min (cached)")
st.sidebar.info("Run after market close for clean EOD numbers.\n\nNot investment advice.")

# ------------------------------------------------------------
# MAIN LAYOUT
# ------------------------------------------------------------
st.title("🇮🇳 Nifty 50 Alpha & Market Intelligence")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")

# ========== BLOCK 1: Top 15 Indices generating Alpha ==========
st.header("1. Top Indices Generating Alpha vs Nifty 50")
st.markdown("Sorted primarily by **3-Month Alpha**. Shows returns and excess return (Alpha) for 1M / 2M / 3M / 6M / 12M.")

with st.spinner("Fetching index performance..."):
    alpha_df = get_index_returns()

if not alpha_df.empty:
    display_cols = ["Index"] + [c for c in alpha_df.columns if "Ret" in c or "Alpha" in c]
    top15 = alpha_df[display_cols].head(15).reset_index(drop=True)
    
    # color alpha positive/negative
    def color_alpha(val):
        if pd.isna(val):
            return ""
        color = "green" if val > 0 else "red"
        return f"color: {color}"
    
    styled = top15.style.map(color_alpha, subset=[c for c in top15.columns if "Alpha" in c])
    st.dataframe(styled, use_container_width=True, height=520)
    
    # quick chart of 3M Alpha
    fig = px.bar(top15.head(10), x="Index", y="3M Alpha",
                 title="Top 10 Indices – 3 Month Alpha vs Nifty 50",
                 color="3M Alpha", color_continuous_scale="RdYlGn")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Could not fetch index data. Check internet / Yahoo Finance.")

# ========== BLOCK 2: Top 5 Alpha Indices → Top 4 Stocks ==========
st.header("2. Top 5 Alpha Indices – Leading Stocks & Their Alpha")

if not alpha_df.empty:
    top5_indices = alpha_df.head(5)["Index"].tolist()
    
    for idx_name in top5_indices:
        st.subheader(f"📌 {idx_name}")
        stocks = TOP_STOCKS.get(idx_name, [])
        if stocks:
            stock_df = get_stock_alpha(stocks)
            if not stock_df.empty:
                st.dataframe(stock_df.head(4), use_container_width=True)
            else:
                st.write("No stock data available")
        else:
            st.write("Constituent list not configured for this index (add in TOP_STOCKS dict)")
else:
    st.info("Waiting for index data...")

# ========== BLOCK 3: Research Reports ==========
st.header("3. Latest Research Reports (Top 15)")
st.markdown("Newest broker calls from Moneycontrol. Columns show stock, broker, rating/target where parseable.")

with st.spinner("Scraping research reports..."):
    reports_df = get_research_reports(15)

if not reports_df.empty:
    st.dataframe(reports_df, use_container_width=True)
else:
    st.warning("Could not fetch research reports right now.")

st.caption("Tip: For deeper reports check Moneycontrol, ICICI Direct, Motilal Oswal, Emkay, etc. directly.")

# ========== BLOCK 4: Global News ==========
st.header("4. Global Market News")
global_feeds = {
    "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "Bloomberg Markets": "https://feeds.bloomberg.com/markets/news.rss",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters Business": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/"
}

with st.spinner("Loading global news..."):
    global_news = get_news(global_feeds, limit=15)

if not global_news.empty:
    for _, row in global_news.iterrows():
        st.markdown(f"**[{row['Source']}]** [{row['Title']}]({row['Link']})  \n*{row['Published']}*")
else:
    st.info("No global news fetched.")

# ========== BLOCK 5: Domestic News ==========
st.header("5. Domestic Indian Market News")
domestic_feeds = {
    "Moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "Livemint": "https://www.livemint.com/rss/markets",
    "Zee Business": "https://www.zeebiz.com/india-markets.xml",
}

with st.spinner("Loading domestic news..."):
    domestic_news = get_news(domestic_feeds, limit=15)

if not domestic_news.empty:
    for _, row in domestic_news.iterrows():
        st.markdown(f"**[{row['Source']}]** [{row['Title']}]({row['Link']})  \n*{row['Published']}*")
else:
    st.info("No domestic news fetched.")

# ========== BLOCK 6: FII / DII ==========
st.header("6. FII / DII Activity")

fii = get_fii_dii()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Nifty 50 Close", f"{fii['nifty_close']:,.2f}" if fii['nifty_close'] else "N/A")

with col2:
    fii_val = fii['fii_net']
    st.metric("FII Net (Cash)", 
              f"₹{fii_val:,.0f} Cr" if fii_val is not None else "N/A",
              delta="Net Buyers" if fii_val and fii_val > 0 else "Net Sellers" if fii_val else None)

with col3:
    dii_val = fii['dii_net']
    st.metric("DII Net (Cash)", 
              f"₹{dii_val:,.0f} Cr" if dii_val is not None else "N/A",
              delta="Net Buyers" if dii_val and dii_val > 0 else "Net Sellers" if dii_val else None)

st.markdown("---")
st.subheader("Detailed Snapshot (Previous Session style)")

if fii['fii_buy'] is not None:
    st.write(f"**FII** · Cash market  ₹{fii['fii_net']:,.0f} Cr  "
             f"{'net buyers' if fii['fii_net']>0 else 'net sellers'} · "
             f"bought {fii['fii_buy']:,.0f}, sold {fii['fii_sell']:,.0f}")
if fii['dii_buy'] is not None:
    st.write(f"**DII** · Cash market  ₹{fii['dii_net']:,.0f} Cr  "
             f"{'net buyers' if fii['dii_net']>0 else 'net sellers'} · "
             f"bought {fii['dii_buy']:,.0f}, sold {fii['dii_sell']:,.0f}")

if fii['last_5_fii'] is not None:
    st.write(f"**Last 5 sessions** · FII net ₹{fii['last_5_fii']:,.0f} Cr · DII ₹{fii['last_5_dii']:,.0f} Cr")

st.caption("F&O positioning (Index Futures / Options) requires additional NSE participant data which is available via nselib or NSE archives. Extend the `get_fii_dii()` function if needed.")

# Footer
st.markdown("---")
st.markdown("""
**Notes**  
- Alpha = Index/Stock return − Nifty 50 return over the same period (simple excess return).  
- Index constituents are approximate static lists; for live weights use `nselib.indices.constituent_stock_list()`.  
- Research & news scraping can break when websites change layout.  
- Always cross-verify with official NSE / exchange data before trading.
""")