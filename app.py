"""
Nifty Professional Screener Dashboard
Dark-themed multi-section Streamlit app
Sections:
1. All-Time / Multi-Year High Breakouts
2. Double Rounding Bottom + Breakout
3. Broker Recommendations (30/60/90d rolling)
4. Accumulation/Distribution + Resistance (Nifty 100)
Extra intelligence: RS vs Nifty, multi-factor confidence, badges, news hooks
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# Optional: pandas_ta for indicators
try:
    import pandas_ta as ta
    HAS_TA = True
except ImportError:
    HAS_TA = False

# ---------------------------------------------------------------------------
# PAGE CONFIG & DARK THEME
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nifty Pro Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom dark CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stSidebar {
        background-color: #1a1d24;
    }
    h1, h2, h3, h4 {
        color: #f0f2f6 !important;
    }
    .stMetric {
        background-color: #1e222d;
        border-radius: 8px;
        padding: 10px;
    }
    .badge-green {
        background-color: #00c853;
        color: #000;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-red {
        background-color: #ff1744;
        color: #fff;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-white {
        background-color: #e0e0e0;
        color: #000;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-amber {
        background-color: #ffab00;
        color: #000;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    div[data-testid="stDataFrame"] {
        background-color: #1e222d;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e222d;
        border-radius: 6px;
        color: #aaa;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2962ff !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# CONSTANTS & HELPERS
# ---------------------------------------------------------------------------
NIFTY100_SAMPLE = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "POWERGRID.NS", "NTPC.NS", "HCLTECH.NS", "M&M.NS", "TATAMOTORS.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "ONGC.NS",
    "COALINDIA.NS", "BAJAJFINSV.NS", "TECHM.NS", "INDUSINDBK.NS", "GRASIM.NS",
    "CIPLA.NS", "DRREDDY.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BRITANNIA.NS",
    "DIVISLAB.NS", "APOLLOHOSP.NS", "BPCL.NS", "HINDALCO.NS", "SHREECEM.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "PIDILITIND.NS", "DABUR.NS", "GODREJCP.NS",
    "SIEMENS.NS", "HAVELLS.NS", "AMBUJACEM.NS", "DLF.NS", "VEDL.NS",
    "TATACONSUM.NS", "ICICIPRULI.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS"
]

SECTOR_MAP = {
    "RELIANCE.NS": "Energy / Conglomerate",
    "TCS.NS": "IT Services",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "INFY.NS": "IT Services",
    "HINDUNILVR.NS": "FMCG",
    "ITC.NS": "FMCG",
    "SBIN.NS": "Banking",
    "BHARTIARTL.NS": "Telecom",
    "KOTAKBANK.NS": "Banking",
    "LT.NS": "Infrastructure / Engineering",
    "AXISBANK.NS": "Banking",
    "BAJFINANCE.NS": "NBFC",
    "ASIANPAINT.NS": "Paints",
    "MARUTI.NS": "Auto",
    "SUNPHARMA.NS": "Pharma",
    "TITAN.NS": "Consumer / Jewellery",
    "WIPRO.NS": "IT Services",
    "ULTRACEMCO.NS": "Cement",
    "NESTLEIND.NS": "FMCG",
    "POWERGRID.NS": "Power",
    "NTPC.NS": "Power",
    "HCLTECH.NS": "IT Services",
    "M&M.NS": "Auto",
    "TATAMOTORS.NS": "Auto",
    "ADANIENT.NS": "Conglomerate",
    "ADANIPORTS.NS": "Infrastructure",
    "JSWSTEEL.NS": "Metals",
    "TATASTEEL.NS": "Metals",
    "ONGC.NS": "Oil & Gas",
}

# Sample broker recommendations (replace with real scraper later)
SAMPLE_BROKER_RECS = [
    {"date": "2026-10-20", "broker": "Motilal Oswal", "symbol": "HDFCBANK.NS", "rating": "Buy", "target": 925, "upside": 18.2},
    {"date": "2026-10-19", "broker": "Nuvama", "symbol": "ICICIBANK.NS", "rating": "Buy", "target": 1850, "upside": 17.0},
    {"date": "2026-10-19", "broker": "Jefferies", "symbol": "ULTRACEMCO.NS", "rating": "Buy", "target": 14380, "upside": 35.0},
    {"date": "2026-10-19", "broker": "HSBC", "symbol": "ULTRACEMCO.NS", "rating": "Buy", "target": 14200, "upside": 33.3},
    {"date": "2026-10-19", "broker": "CLSA", "symbol": "ULTRACEMCO.NS", "rating": "Outperform", "target": 13000, "upside": 22.1},
    {"date": "2026-10-19", "broker": "JP Morgan", "symbol": "ULTRACEMCO.NS", "rating": "Overweight", "target": 12900, "upside": 21.1},
    {"date": "2026-10-19", "broker": "Kotak", "symbol": "ULTRACEMCO.NS", "rating": "Sell", "target": 8900, "upside": -16.4},
    {"date": "2026-10-18", "broker": "Goldman Sachs", "symbol": "ICICIBANK.NS", "rating": "Buy", "target": 2025, "upside": 45.0},
    {"date": "2026-10-18", "broker": "UBS", "symbol": "ICICIBANK.NS", "rating": "Buy", "target": 1800, "upside": 28.8},
    {"date": "2026-10-17", "broker": "Citi", "symbol": "HDFCBANK.NS", "rating": "Buy", "target": 880, "upside": 12.5},
    {"date": "2026-10-15", "broker": "Motilal Oswal", "symbol": "SBIN.NS", "rating": "Buy", "target": 1300, "upside": 36.0},
    {"date": "2026-10-12", "broker": "Jefferies", "symbol": "AXISBANK.NS", "rating": "Buy", "target": 1700, "upside": 22.0},
    {"date": "2026-10-10", "broker": "CLSA", "symbol": "TCS.NS", "rating": "Outperform", "target": 4800, "upside": 15.0},
    {"date": "2026-10-08", "broker": "HSBC", "symbol": "INFY.NS", "rating": "Buy", "target": 2100, "upside": 18.0},
    {"date": "2026-09-28", "broker": "JP Morgan", "symbol": "RELIANCE.NS", "rating": "Overweight", "target": 3200, "upside": 12.0},
    {"date": "2026-09-20", "broker": "Nuvama", "symbol": "BAJFINANCE.NS", "rating": "Buy", "target": 8500, "upside": 20.0},
    {"date": "2026-09-15", "broker": "Motilal Oswal", "symbol": "TITAN.NS", "rating": "Buy", "target": 4200, "upside": 16.0},
    {"date": "2026-09-10", "broker": "UBS", "symbol": "SUNPHARMA.NS", "rating": "Buy", "target": 1900, "upside": 14.0},
    {"date": "2026-08-25", "broker": "Kotak", "symbol": "LT.NS", "rating": "Buy", "target": 4200, "upside": 19.0},
    {"date": "2026-08-10", "broker": "Citi", "symbol": "MARUTI.NS", "rating": "Buy", "target": 14000, "upside": 21.0},
]

@st.cache_data(ttl=3600)
def get_nifty_data(period="1y"):
    """Fetch Nifty 50 for relative strength baseline."""
    try:
        nifty = yf.download("^NSEI", period=period, progress=False, auto_adjust=True)
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)
        return nifty
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_stock_data(ticker, period="2y"):
    """Download OHLCV for a single ticker."""
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 50:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()

def compute_ad_line(df):
    """Chaikin Accumulation/Distribution Line."""
    if df.empty or "High" not in df.columns:
        return pd.Series(dtype=float)
    clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    clv = clv.fillna(0)
    ad = (clv * df["Volume"]).cumsum()
    return ad

def compute_relative_strength(stock_df, nifty_df):
    """RS = Stock % change / Nifty % change over same window (last 60 trading days)."""
    if stock_df.empty or nifty_df.empty:
        return 1.0
    try:
        s = stock_df["Close"].pct_change(60).iloc[-1]
        n = nifty_df["Close"].pct_change(60).iloc[-1]
        if n == 0 or np.isnan(n) or np.isnan(s):
            return 1.0
        return round(float(s / n), 2)
    except Exception:
        return 1.0

def detect_ath_breakouts(ticker, df):
    """Detect new highs across multiple lookbacks."""
    if df.empty or len(df) < 100:
        return None
    close = df["Close"]
    current = float(close.iloc[-1])
    results = {
        "ticker": ticker.replace(".NS", ""),
        "price": round(current, 2),
        "ath": False,
        "3yr": False,
        "5yr": False,
        "10yr": False,
        "ath_price": round(float(close.max()), 2),
        "3yr_high": None,
        "5yr_high": None,
        "10yr_high": None,
    }
    # All-time
    if current >= float(close.max()) * 0.998:  # slight tolerance
        results["ath"] = True
    # Rolling windows (approx trading days)
    for label, days in [("3yr", 756), ("5yr", 1260), ("10yr", 2520)]:
        window = close.iloc[-min(days, len(close)):]
        high = float(window.max())
        results[f"{label}_high"] = round(high, 2)
        if current >= high * 0.998 and len(window) > days * 0.7:
            results[label] = True
    return results

def detect_double_rounding_bottom(df, lookback=180):
    """
    Simplified double bottom detector.
    Looks for two troughs where first is deeper, second higher, then breakout above neckline.
    Returns dict with confidence or None.
    """
    if df.empty or len(df) < lookback:
        return None
    data = df.iloc[-lookback:].copy()
    close = data["Close"].values
    lows = data["Low"].values
    dates = data.index

    # Find local minima (troughs)
    from scipy.signal import argrelextrema
    min_idx = argrelextrema(lows, np.less_equal, order=8)[0]
    if len(min_idx) < 2:
        return None

    # Take the two most recent significant troughs
    troughs = sorted(min_idx[-4:])  # last few
    if len(troughs) < 2:
        return None

    t1, t2 = troughs[-2], troughs[-1]
    price1, price2 = lows[t1], lows[t2]

    # First bigger (deeper), second smaller (higher low)
    if price1 >= price2:
        return None  # not the pattern we want

    # Neckline = highest high between the two troughs
    neckline = float(np.max(close[t1:t2+1]))
    current = float(close[-1])

    # Breakout condition
    broken = current > neckline * 1.005

    # Rounding approximation: check curvature roughly via mid-points
    depth1 = neckline - price1
    depth2 = neckline - price2
    if depth1 <= 0 or depth2 <= 0:
        return None

    # Confidence scoring
    conf = 40
    if broken:
        conf += 25
    if price2 > price1 * 1.02:  # clear higher low
        conf += 15
    # Volume confirmation on breakout day
    if "Volume" in data.columns and data["Volume"].iloc[-1] > data["Volume"].iloc[-20:].mean() * 1.3:
        conf += 10
    # Distance between troughs reasonable (20-90 days)
    days_between = t2 - t1
    if 20 <= days_between <= 90:
        conf += 10

    conf = min(conf, 95)

    return {
        "pattern": "Double Rounding Bottom",
        "first_trough": round(float(price1), 2),
        "second_trough": round(float(price2), 2),
        "neckline": round(neckline, 2),
        "current": round(current, 2),
        "broken_out": broken,
        "confidence": conf,
        "days_between": int(days_between),
    }

def multi_factor_score(ticker, df, nifty_df, ath_info=None, pattern_info=None):
    """
    Composite confidence & signal.
    Factors: trend, RS, volume, A/D direction, pattern, ATH status.
    Returns badge color, label, score 0-100, short reasoning.
    """
    if df.empty:
        return "white", "No Data", 0, "Insufficient data"

    score = 50  # neutral base
    reasons = []

    close = df["Close"]
    current = float(close.iloc[-1])
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) > 200 else sma50

    # Trend
    if current > sma20 > sma50:
        score += 12
        reasons.append("Price > SMA20 > SMA50")
    elif current < sma20 < sma50:
        score -= 12
        reasons.append("Price < SMA20 < SMA50")

    if current > sma200:
        score += 8
        reasons.append("Above 200DMA")
    else:
        score -= 5
        reasons.append("Below 200DMA")

    # Relative Strength
    rs = compute_relative_strength(df, nifty_df)
    if rs > 1.15:
        score += 12
        reasons.append(f"Strong RS vs Nifty ({rs})")
    elif rs < 0.85:
        score -= 10
        reasons.append(f"Weak RS vs Nifty ({rs})")

    # Volume
    vol = df["Volume"]
    if vol.iloc[-1] > vol.iloc[-20:].mean() * 1.4:
        score += 8
        reasons.append("Volume spike")

    # A/D Line slope (last 20 days)
    ad = compute_ad_line(df)
    if len(ad) > 20:
        ad_slope = (ad.iloc[-1] - ad.iloc[-20]) / abs(ad.iloc[-20] + 1e-9)
        if ad_slope > 0.05:
            score += 10
            reasons.append("Rising A/D (Accumulation)")
        elif ad_slope < -0.05:
            score -= 10
            reasons.append("Falling A/D (Distribution)")

    # ATH / pattern boost
    if ath_info:
        if ath_info.get("ath"):
            score += 10
            reasons.append("New All-Time High")
        elif ath_info.get("3yr") or ath_info.get("5yr"):
            score += 6
            reasons.append("Multi-year high")

    if pattern_info and pattern_info.get("broken_out"):
        score += 12
        reasons.append(f"Double bottom breakout (conf {pattern_info['confidence']})")

    score = max(5, min(98, int(score)))

    if score >= 72:
        badge, label = "green", "BULLISH"
    elif score <= 35:
        badge, label = "red", "BEARISH"
    elif 45 <= score <= 55:
        badge, label = "white", "NEUTRAL"
    else:
        badge, label = "amber", "WATCH"

    return badge, label, score, " | ".join(reasons[:4])

def get_simple_news(ticker):
    """Try to pull recent news headlines via yfinance."""
    try:
        t = yf.Ticker(ticker)
        news = t.news[:4] if hasattr(t, "news") and t.news else []
        return [{"title": n.get("title", ""), "publisher": n.get("publisher", "")} for n in news]
    except Exception:
        return []

def badge_html(color, text):
    return f'<span class="badge-{color}">{text}</span>'

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.title("📈 Nifty Pro Screener")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Dashboard Home",
        "🚀 ATH / Multi-Year Highs",
        "🔄 Double Bottom Breakouts",
        "🏦 Broker Recommendations",
        "📊 A/D + Resistance (Nifty 100)",
        "ℹ️ About & Roadmap"
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("Dark theme • Data via Yahoo Finance • Educational use only")
st.sidebar.caption(f"Last refresh logic: cached 30-60 min")

# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
if page == "🏠 Dashboard Home":
    st.title("Nifty Professional Screener")
    st.markdown("### Multi-factor Indian equity dashboard with confidence scoring")
    st.markdown("""
    This dashboard combines classic technical screeners with extra intelligence layers:
    - **Relative Strength** vs Nifty 50
    - **Accumulation / Distribution** flow
    - **Multi-factor confidence** (trend + volume + RS + pattern + A/D)
    - Colour-coded badges (Green = Bullish, Red = Bearish, Amber = Watch, White = Neutral)
    - Broker recommendation summary (sample + extensible)
    - News hooks & sector context
    """)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Universe", "Nifty 100 sample", "60 stocks")
    col2.metric("Data Source", "Yahoo Finance", "Live")
    col3.metric("Theme", "Dark", "Professional")
    col4.metric("Status", "v0.9 MVP", "Sharpen iteratively")

    st.info("Use the sidebar to jump into each screener. Start with **ATH / Multi-Year Highs** or **A/D + Resistance**.")

# ---------------------------------------------------------------------------
# 1. ATH / MULTI-YEAR HIGHS
# ---------------------------------------------------------------------------
elif page == "🚀 ATH / Multi-Year Highs":
    st.title("🚀 All-Time & Multi-Year High Breakouts")
    st.markdown("Stocks making new highs across different timeframes with multi-factor confidence.")

    with st.spinner("Scanning Nifty sample for new highs..."):
        nifty_df = get_nifty_data("2y")
        results = []
        progress = st.progress(0)
        for i, t in enumerate(NIFTY100_SAMPLE):
            df = get_stock_data(t, period="max")  # need long history
            if df.empty:
                progress.progress((i + 1) / len(NIFTY100_SAMPLE))
                continue
            info = detect_ath_breakouts(t, df)
            if info and (info["ath"] or info["3yr"] or info["5yr"] or info["10yr"]):
                badge, label, score, reason = multi_factor_score(t, df, nifty_df, ath_info=info)
                info["badge"] = badge
                info["signal"] = label
                info["confidence"] = score
                info["reason"] = reason
                info["rs"] = compute_relative_strength(df, nifty_df)
                info["sector"] = SECTOR_MAP.get(t, "—")
                results.append(info)
            progress.progress((i + 1) / len(NIFTY100_SAMPLE))
        progress.empty()

    if not results:
        st.warning("No fresh multi-year highs found in the current sample. Markets may be consolidating.")
    else:
        df_res = pd.DataFrame(results)
        # Sort by confidence
        df_res = df_res.sort_values("confidence", ascending=False)

        st.subheader(f"Found {len(df_res)} stocks near/at highs")
        # Display table with badges
        display_cols = ["ticker", "price", "ath", "3yr", "5yr", "10yr", "rs", "confidence", "signal", "sector", "reason"]
        st.dataframe(
            df_res[display_cols].style.apply(
                lambda row: ["background-color: #1b5e20" if row["signal"] == "BULLISH"
                             else "background-color: #b71c1c" if row["signal"] == "BEARISH"
                             else "background-color: #e65100" if row["signal"] == "WATCH"
                             else "" for _ in row],
                axis=1
            ),
            use_container_width=True,
            height=420
        )

        # Detail view
        st.markdown("---")
        selected = st.selectbox("Inspect a stock", df_res["ticker"].tolist())
        if selected:
            full_ticker = selected + ".NS"
            df = get_stock_data(full_ticker, "2y")
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="Price"
                ))
                # ATH line
                ath_val = df["Close"].max()
                fig.add_hline(y=ath_val, line_dash="dash", line_color="#00e676",
                              annotation_text=f"ATH {ath_val:.1f}")
                fig.update_layout(
                    template="plotly_dark",
                    title=f"{selected} — Price & All-Time High",
                    height=480,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)

                # News & commentary placeholder
                st.markdown("#### Recent News / Context")
                news = get_simple_news(full_ticker)
                if news:
                    for n in news:
                        st.markdown(f"- **{n['title']}** _{n['publisher']}_")
                else:
                    st.caption("No recent headlines pulled. Add your preferred news API later.")

                row = df_res[df_res["ticker"] == selected].iloc[0]
                st.markdown(f"**Signal:** {badge_html(row['badge'], row['signal'])}  "
                            f"**Confidence:** {row['confidence']}/100  "
                            f"**RS vs Nifty:** {row['rs']}", unsafe_allow_html=True)
                st.caption(row["reason"])

# ---------------------------------------------------------------------------
# 2. DOUBLE ROUNDING BOTTOM
# ---------------------------------------------------------------------------
elif page == "🔄 Double Bottom Breakouts":
    st.title("🔄 Double Rounding Bottom + Breakout")
    st.markdown("First trough deeper, second higher (rounding style), price breaking neckline.")

    with st.spinner("Scanning for double-bottom structures..."):
        nifty_df = get_nifty_data("1y")
        results = []
        progress = st.progress(0)
        for i, t in enumerate(NIFTY100_SAMPLE):
            df = get_stock_data(t, period="1y")
            if df.empty:
                progress.progress((i + 1) / len(NIFTY100_SAMPLE))
                continue
            pat = detect_double_rounding_bottom(df)
            if pat and pat["confidence"] >= 55:
                badge, label, score, reason = multi_factor_score(t, df, nifty_df, pattern_info=pat)
                results.append({
                    "ticker": t.replace(".NS", ""),
                    "price": pat["current"],
                    "first_low": pat["first_trough"],
                    "second_low": pat["second_trough"],
                    "neckline": pat["neckline"],
                    "broken": pat["broken_out"],
                    "pattern_conf": pat["confidence"],
                    "overall_conf": score,
                    "signal": label,
                    "badge": badge,
                    "rs": compute_relative_strength(df, nifty_df),
                    "reason": reason,
                    "sector": SECTOR_MAP.get(t, "—")
                })
            progress.progress((i + 1) / len(NIFTY100_SAMPLE))
        progress.empty()

    if not results:
        st.info("No high-confidence double-bottom breakouts detected in the current window. Try again after a few sessions of consolidation.")
    else:
        df_res = pd.DataFrame(results).sort_values("overall_conf", ascending=False)
        st.subheader(f"{len(df_res)} candidates")
        st.dataframe(df_res.drop(columns=["badge"]), use_container_width=True, height=380)

        selected = st.selectbox("Chart a candidate", df_res["ticker"].tolist())
        if selected:
            full = selected + ".NS"
            df = get_stock_data(full, "1y")
            pat = detect_double_rounding_bottom(df)
            if not df.empty and pat:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="Price"
                ))
                fig.add_hline(y=pat["neckline"], line_dash="dot", line_color="#ffab00",
                              annotation_text=f"Neckline {pat['neckline']}")
                fig.add_hline(y=pat["first_trough"], line_dash="dash", line_color="#ff1744",
                              annotation_text="1st trough")
                fig.add_hline(y=pat["second_trough"], line_dash="dash", line_color="#00e676",
                              annotation_text="2nd trough")
                fig.update_layout(template="plotly_dark", height=500,
                                  title=f"{selected} Double Bottom", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                row = df_res[df_res["ticker"] == selected].iloc[0]
                st.markdown(f"{badge_html(row['badge'], row['signal'])}  "
                            f"Overall Confidence **{row['overall_conf']}** | Pattern Conf **{row['pattern_conf']}**",
                            unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3. BROKER RECOMMENDATIONS
# ---------------------------------------------------------------------------
elif page == "🏦 Broker Recommendations":
    st.title("🏦 Broker Recommendations Summary")
    st.markdown("Rolling 30 / 60 / 90 day view (sample data — replace with live scraper).")

    recs = pd.DataFrame(SAMPLE_BROKER_RECS)
    recs["date"] = pd.to_datetime(recs["date"])
    today = pd.Timestamp("2026-10-24")  # fixed for reproducibility; change to datetime.now() in live

    def filter_days(days):
        cutoff = today - timedelta(days=days)
        return recs[recs["date"] >= cutoff].copy()

    tab30, tab60, tab90, taball = st.tabs(["Last 30 Days", "Last 60 Days", "Last 90 Days", "All Sample"])

    for tab, days in zip([tab30, tab60, tab90, taball], [30, 60, 90, 9999]):
        with tab:
            sub = filter_days(days)
            if sub.empty:
                st.write("No recommendations in this window.")
                continue

            # Summary metrics
            c1, c2, c3, c4 = st.columns(4)
            buys = sub[sub["rating"].str.contains("Buy|Outperform|Overweight", case=False)]
            sells = sub[sub["rating"].str.contains("Sell|Underperform|Reduce", case=False)]
            c1.metric("Total Calls", len(sub))
            c2.metric("Buy / Positive", len(buys), f"{len(buys)/len(sub)*100:.0f}%")
            c3.metric("Sell / Negative", len(sells))
            c4.metric("Avg Upside (Buys)", f"{buys['upside'].mean():.1f}%" if not buys.empty else "—")

            # By broker
            st.markdown("#### By Broker")
            broker_summary = sub.groupby("broker").agg(
                calls=("rating", "count"),
                avg_upside=("upside", "mean"),
                buy_count=("rating", lambda x: x.str.contains("Buy|Outperform|Overweight", case=False).sum())
            ).reset_index().sort_values("calls", ascending=False)
            st.dataframe(broker_summary, use_container_width=True)

            # Full table
            st.markdown("#### Detailed Calls")
            st.dataframe(
                sub.sort_values("date", ascending=False)[["date", "broker", "symbol", "rating", "target", "upside"]],
                use_container_width=True,
                height=320
            )

    st.markdown("---")
    st.info("""
    **Next sharpening steps for this section**
    - Scrape Moneycontrol / Trendlyne / Business Upturn daily
    - Store in SQLite with unique (broker, symbol, date)
    - Add consensus rating & target change tracking
    - Link each symbol back to the technical screens above
    """)

# ---------------------------------------------------------------------------
# 4. A/D + RESISTANCE (NIFTY 100)
# ---------------------------------------------------------------------------
elif page == "📊 A/D + Resistance (Nifty 100)":
    st.title("📊 Accumulation / Distribution + Resistance")
    st.markdown("Select any stock → view A/D line (green = accumulation, red = distribution) + key resistance. Table shows only high-probability setups.")

    # Pre-compute qualifying stocks
    with st.spinner("Computing A/D & multi-factor scores for Nifty sample..."):
        nifty_df = get_nifty_data("1y")
        table_rows = []
        progress = st.progress(0)
        for i, t in enumerate(NIFTY100_SAMPLE):
            df = get_stock_data(t, "1y")
            if df.empty or len(df) < 60:
                progress.progress((i + 1) / len(NIFTY100_SAMPLE))
                continue
            badge, label, score, reason = multi_factor_score(t, df, nifty_df)
            ad = compute_ad_line(df)
            ad_rising = False
            if len(ad) > 20:
                ad_rising = ad.iloc[-1] > ad.iloc[-20]

            # Simple resistance = recent 60-day high
            resist = float(df["High"].iloc[-60:].max())
            current = float(df["Close"].iloc[-1])
            dist_to_resist = (resist - current) / current * 100

            # Qualify: near resistance (<4%) + rising A/D  OR  strong overall score
            near_resist = dist_to_resist < 4.0
            qualify = (near_resist and ad_rising and score >= 55) or score >= 75 or score <= 30

            if qualify:
                table_rows.append({
                    "ticker": t.replace(".NS", ""),
                    "price": round(current, 2),
                    "resistance": round(resist, 2),
                    "dist_%": round(dist_to_resist, 2),
                    "ad_rising": ad_rising,
                    "rs": compute_relative_strength(df, nifty_df),
                    "confidence": score,
                    "signal": label,
                    "badge": badge,
                    "reason": reason,
                    "sector": SECTOR_MAP.get(t, "—")
                })
            progress.progress((i + 1) / len(NIFTY100_SAMPLE))
        progress.empty()

    if table_rows:
        df_tab = pd.DataFrame(table_rows).sort_values("confidence", ascending=False)
        st.subheader("High-Probability Setups (filtered)")
        st.dataframe(df_tab.drop(columns=["badge"]), use_container_width=True, height=300)
    else:
        st.warning("No stocks currently meet the strict near-resistance + accumulation filter. Showing all for inspection.")
        df_tab = pd.DataFrame()

    st.markdown("---")
    # Dropdown for any stock
    choice = st.selectbox(
        "Select stock for detailed chart",
        [t.replace(".NS", "") for t in NIFTY100_SAMPLE],
        index=0
    )
    full_ticker = choice + ".NS"
    df = get_stock_data(full_ticker, "1y")

    if not df.empty:
        ad = compute_ad_line(df)
        resist = float(df["High"].iloc[-60:].max())
        support = float(df["Low"].iloc[-60:].min())
        badge, label, score, reason = multi_factor_score(full_ticker, df, nifty_df)

        # Dual-axis chart: Price + A/D
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.65, 0.35],
            subplot_titles=(f"{choice} Price + Resistance", "Accumulation / Distribution Line")
        )

        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="OHLC"
        ), row=1, col=1)

        fig.add_hline(y=resist, line_dash="dash", line_color="#ff1744",
                      annotation_text=f"Res {resist:.1f}", row=1, col=1)
        fig.add_hline(y=support, line_dash="dash", line_color="#00e676",
                      annotation_text=f"Sup {support:.1f}", row=1, col=1)

        # A/D with color segments
        ad_colors = ["#00c853" if ad.iloc[i] >= ad.iloc[max(0, i-1)] else "#ff1744"
                     for i in range(len(ad))]
        fig.add_trace(go.Scatter(
            x=df.index, y=ad, mode="lines",
            line=dict(color="#2962ff", width=1.5),
            name="A/D Line",
            fill="tozeroy",
            fillcolor="rgba(41,98,255,0.15)"
        ), row=2, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=620,
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Badges & intelligence
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Signal**  {badge_html(badge, label)}", unsafe_allow_html=True)
        with col2:
            st.metric("Confidence", f"{score}/100")
        with col3:
            st.metric("RS vs Nifty (60d)", compute_relative_strength(df, nifty_df))

        st.caption(f"Reasoning: {reason}")
        st.markdown(f"**Sector context:** {SECTOR_MAP.get(full_ticker, 'General')}")

        # News
        st.markdown("#### Latest Headlines")
        news = get_simple_news(full_ticker)
        if news:
            for n in news:
                st.markdown(f"- {n['title']}  _{n['publisher']}_")
        else:
            st.caption("No headlines available via free feed. Wire a news API (NewsAPI, Finnhub, etc.) for production.")

# ---------------------------------------------------------------------------
# ABOUT
# ---------------------------------------------------------------------------
else:
    st.title("ℹ️ About & Roadmap")
    st.markdown("""
    ### What this dashboard does
    - **ATH / Multi-year highs** — flags stocks at or near all-time, 3yr, 5yr, 10yr highs with confidence.
    - **Double Rounding Bottom** — simplified geometric + volume confirmation pattern.
    - **Broker Recommendations** — rolling 30/60/90 day summary (currently sample data).
    - **A/D + Resistance** — Chaikin A/D line, key resistance, filtered high-probability table, interactive chart.
    - **Extra intelligence** on every decision:
      - Relative Strength vs Nifty 50
      - Multi-factor score (trend, volume, A/D slope, pattern, RS)
      - Colour badges + confidence 0-100
      - Sector tag + news headlines hook

    ### How to run locally
    ```bash
    pip install -r requirements.txt
    streamlit run app.py
    ```

    ### Deploy on Streamlit Cloud
    1. Push this folder to a public GitHub repo
    2. Go to share.streamlit.io → New app → select repo & `app.py`
    3. Done (free tier is enough for personal use)

    ### Sharpening roadmap (your iterative plan)
    | Priority | Item | Status |
    |----------|------|--------|
    | P0 | Live broker scraper (Moneycontrol / Trendlyne) | To do |
    | P0 | Expand to full Nifty 100 / 200 | Easy |
    | P1 | Better double-bottom (ML or stricter geometry) | Research |
    | P1 | SQLite persistence for daily scans | Easy |
    | P2 | Management commentary / earnings transcript sentiment | Advanced |
    | P2 | Sector tailwind score (auto from news + flows) | Advanced |
    | P3 | Telegram / email alerts on new high-confidence signals | Medium |

    ### Disclaimer
    This is an educational / research tool. Not investment advice. Always do your own due diligence.
    Data comes from Yahoo Finance (free, delayed). Pattern detection is heuristic.
    """)

# Footer
st.markdown("---")
st.caption("Nifty Pro Screener • Dark theme • Built for iterative sharpening • v0.9")
