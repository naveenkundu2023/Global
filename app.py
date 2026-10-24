"""
Nifty Pro Screener Dashboard v1.1
All sections in main area as TABS (no redundant sidebar).
1. ATH / Multi-Year Highs
2. Double Rounding Bottom
3. Broker Recommendations (with live price)
4. A/D + Resistance + Institutional + Options analytics + Trade ideas
Lighter dark theme, high contrast, no dataframe index columns.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy.signal import argrelextrema
import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# PAGE CONFIG + LIGHTER DARK THEME (better contrast)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nifty Pro Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #161b22; color: #e6edf3; }
    h1, h2, h3, h4 { color: #f0f6fc !important; }
    .stMetric { background-color: #21262d; border-radius: 8px; padding: 12px; border: 1px solid #30363d; }
    div[data-testid="stDataFrame"] { background-color: #21262d; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background-color: #0d1117; padding: 6px; border-radius: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #21262d; border-radius: 6px; color: #c9d1d9;
        padding: 10px 18px; font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f6feb !important; color: #ffffff !important;
    }
    .badge-green { background:#238636; color:#fff; padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.9rem; }
    .badge-red   { background:#da3633; color:#fff; padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.9rem; }
    .badge-amber { background:#d29922; color:#000; padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.9rem; }
    .badge-white { background:#8b949e; color:#000; padding:4px 12px; border-radius:12px; font-weight:600; font-size:0.9rem; }
    .stSelectbox label, .stRadio label { color: #e6edf3 !important; }
    p, span, label, .stMarkdown { color: #e6edf3; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# UNIVERSE – large Nifty-style list (practical for free hosting)
# ---------------------------------------------------------------------------
NIFTY_UNIVERSE = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","HINDUNILVR.NS","ITC.NS","SBIN.NS",
    "BHARTIARTL.NS","KOTAKBANK.NS","LT.NS","AXISBANK.NS","BAJFINANCE.NS","ASIANPAINT.NS","MARUTI.NS",
    "SUNPHARMA.NS","TITAN.NS","WIPRO.NS","ULTRACEMCO.NS","NESTLEIND.NS","POWERGRID.NS","NTPC.NS",
    "HCLTECH.NS","M&M.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","JSWSTEEL.NS","TATASTEEL.NS",
    "ONGC.NS","COALINDIA.NS","BAJAJFINSV.NS","TECHM.NS","INDUSINDBK.NS","GRASIM.NS","CIPLA.NS",
    "DRREDDY.NS","EICHERMOT.NS","HEROMOTOCO.NS","BRITANNIA.NS","DIVISLAB.NS","APOLLOHOSP.NS","BPCL.NS",
    "HINDALCO.NS","SHREECEM.NS","SBILIFE.NS","HDFCLIFE.NS","PIDILITIND.NS","DABUR.NS","GODREJCP.NS",
    "SIEMENS.NS","HAVELLS.NS","AMBUJACEM.NS","DLF.NS","VEDL.NS","TATACONSUM.NS","ICICIPRULI.NS",
    "BANKBARODA.NS","PNB.NS","CANBK.NS","IOC.NS","GAIL.NS","BERGEPAINT.NS","COLPAL.NS","MARICO.NS",
    "MCDOWELL-N.NS","UBL.NS","INDIGO.NS","ZOMATO.NS","PAYTM.NS","NYKAA.NS","POLICYBZR.NS","DMART.NS",
    "TRENT.NS","PAGEIND.NS","AUROPHARMA.NS","LUPIN.NS","BIOCON.NS","TORNTPHARM.NS","ALKEM.NS",
    "GLENMARK.NS","IPCALAB.NS","LAURUSLABS.NS","BALKRISIND.NS","MRF.NS","APOLLOTYRE.NS","CEATLTD.NS",
    "MOTHERSON.NS","BOSCHLTD.NS","TVSMOTOR.NS","BAJAJ-AUTO.NS","ASHOKLEY.NS","ESCORTS.NS",
    "EXIDEIND.NS","BEL.NS","HAL.NS","BHEL.NS","CONCOR.NS","IRCTC.NS","NHPC.NS","SJVN.NS",
    "RECLTD.NS","PFC.NS","HUDCO.NS","IRFC.NS","SAIL.NS","NMDC.NS","NATIONALUM.NS","HINDZINC.NS",
    "JINDALSTEL.NS","JSWENERGY.NS","TATAPOWER.NS","ADANIGREEN.NS","ADANIPOWER.NS","TORNTPOWER.NS",
    "IGL.NS","MGL.NS","PETRONET.NS","GSPL.NS","GUJGASLTD.NS","FEDERALBNK.NS","IDFCFIRSTB.NS",
    "BANDHANBNK.NS","RBLBANK.NS","AUBANK.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","LICHSGFIN.NS",
    "GODREJPROP.NS","OBEROIRLTY.NS","PRESTIGE.NS","BRIGADE.NS","ABB.NS","CGPOWER.NS","POLYCAB.NS",
    "KEI.NS","CROMPTON.NS","VOLTAS.NS","BLUESTARCO.NS","VBL.NS","PERSISTENT.NS","COFORGE.NS",
    "LTTS.NS","MPHASIS.NS","OFSS.NS","TATAELXSI.NS","KPITTECH.NS","CYIENT.NS","DIXON.NS",
    "AMBER.NS","KALYANKJIL.NS","JUBLFOOD.NS","NAUKRI.NS","PIIND.NS","SRF.NS","AARTIIND.NS",
    "DEEPAKNTR.NS","UPL.NS","COROMANDEL.NS","CUMMINSIND.NS","THERMAX.NS","METROPOLIS.NS",
    "LALPATHLAB.NS","MAXHEALTH.NS","FORTIS.NS","INDHOTEL.NS","DELHIVERY.NS","YESBANK.NS",
    "ABCAPITAL.NS","MANAPPURAM.NS","GMRINFRA.NS","IRB.NS","NCC.NS","APLAPOLLO.NS","DALBHARAT.NS",
    "RAMCOCEM.NS","JKCEMENT.NS","FLUOROCHEM.NS","SYNGENE.NS","GRANULES.NS","AFFLE.NS",
    "INDIAMART.NS","CDSL.NS","BSE.NS","MCX.NS","CAMS.NS","ANGELONE.NS","MOTILALOFS.NS",
    "PVRINOX.NS","SUNTV.NS","JSWINFRA.NS","IDEA.NS","UJJIVANSFB.NS","AAVAS.NS","LODHA.NS",
]

seen = set()
NIFTY_UNIVERSE = [x for x in NIFTY_UNIVERSE if not (x in seen or seen.add(x))]

SECTOR_MAP = {
    "RELIANCE.NS": "Energy/Conglomerate", "TCS.NS": "IT", "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking", "INFY.NS": "IT", "HINDUNILVR.NS": "FMCG", "ITC.NS": "FMCG",
    "SBIN.NS": "Banking", "BHARTIARTL.NS": "Telecom", "KOTAKBANK.NS": "Banking",
    "LT.NS": "Infra", "AXISBANK.NS": "Banking", "BAJFINANCE.NS": "NBFC",
    "ASIANPAINT.NS": "Paints", "MARUTI.NS": "Auto", "SUNPHARMA.NS": "Pharma",
    "TITAN.NS": "Consumer", "WIPRO.NS": "IT", "ULTRACEMCO.NS": "Cement",
    "NESTLEIND.NS": "FMCG", "POWERGRID.NS": "Power", "NTPC.NS": "Power",
    "HCLTECH.NS": "IT", "M&M.NS": "Auto", "TATAMOTORS.NS": "Auto",
    "ADANIENT.NS": "Conglomerate", "JSWSTEEL.NS": "Metals", "TATASTEEL.NS": "Metals",
    "ONGC.NS": "Oil&Gas", "COALINDIA.NS": "Mining", "INDIGO.NS": "Aviation",
}

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

def badge_html(color, text):
    return f'<span class="badge-{color}">{text}</span>'

@st.cache_data(ttl=3600, show_spinner=False)
def get_nifty_data(period="1y"):
    try:
        df = yf.download("^NSEI", period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def get_stock_data(ticker, period="2y"):
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 40:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def get_live_price(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        p = getattr(info, "last_price", None) or getattr(info, "lastPrice", None)
        if p:
            return float(p)
    except Exception:
        pass
    df = get_stock_data(ticker, "5d")
    if not df.empty:
        return float(df["Close"].iloc[-1])
    return np.nan

def compute_ad_line(df):
    if df.empty or "High" not in df.columns:
        return pd.Series(dtype=float)
    hl = (df["High"] - df["Low"]).replace(0, np.nan)
    clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / hl
    clv = clv.fillna(0)
    return (clv * df["Volume"]).cumsum()

def compute_pivots(df):
    if len(df) < 2:
        return {}
    prev = df.iloc[-2]
    h, l, c = float(prev["High"]), float(prev["Low"]), float(prev["Close"])
    pp = (h + l + c) / 3.0
    r1 = 2 * pp - l
    s1 = 2 * pp - h
    r2 = pp + (h - l)
    s2 = pp - (h - l)
    return {"PP": pp, "R1": r1, "R2": r2, "S1": s1, "S2": s2}

def detect_zones(df, lookback=120):
    if len(df) < lookback:
        return []
    data = df.iloc[-lookback:].copy()
    close = data["Close"]
    zones = []
    for w in range(18, 45, 5):
        for i in range(len(data) - w):
            window = close.iloc[i:i + w]
            rng = (window.max() - window.min()) / (window.mean() + 1e-9)
            if rng < 0.07:
                before = close.iloc[max(0, i - 20):i]
                if len(before) > 5 and before.iloc[-1] < before.iloc[0] * 0.97:
                    ztype = "Accumulation"
                elif i > 10 and window.mean() > close.iloc[:i].mean():
                    ztype = "Distribution"
                else:
                    ztype = "Consolidation"
                zones.append({
                    "start": data.index[i],
                    "end": data.index[i + w - 1],
                    "type": ztype,
                })
                break
    return zones[-2:] if zones else []

def compute_rs(stock_df, nifty_df, window=60):
    if stock_df.empty or nifty_df.empty or len(stock_df) < window:
        return 1.0
    try:
        s = stock_df["Close"].pct_change(window).iloc[-1]
        n = nifty_df["Close"].pct_change(window).iloc[-1]
        if n == 0 or np.isnan(n) or np.isnan(s):
            return 1.0
        return round(float(s / n), 2)
    except Exception:
        return 1.0

def detect_ath(ticker, df):
    if df.empty or len(df) < 100:
        return None
    close = df["Close"]
    current = float(close.iloc[-1])
    out = {
        "ticker": ticker.replace(".NS", ""),
        "price": round(current, 2),
        "ath": current >= float(close.max()) * 0.998,
        "ath_price": round(float(close.max()), 2),
        "3yr": False, "5yr": False, "10yr": False,
        "3yr_high": None, "5yr_high": None, "10yr_high": None,
    }
    for label, days in [("3yr", 756), ("5yr", 1260), ("10yr", 2520)]:
        window = close.iloc[-min(days, len(close)):]
        high = float(window.max())
        out[f"{label}_high"] = round(high, 2)
        if current >= high * 0.998 and len(window) > days * 0.6:
            out[label] = True
    return out

def detect_double_bottom(df, lookback=160):
    if df.empty or len(df) < lookback:
        return None
    data = df.iloc[-lookback:].copy()
    lows = data["Low"].values
    close = data["Close"].values
    min_idx = argrelextrema(lows, np.less_equal, order=7)[0]
    if len(min_idx) < 2:
        return None
    troughs = sorted(min_idx[-5:])
    if len(troughs) < 2:
        return None
    t1, t2 = troughs[-2], troughs[-1]
    p1, p2 = lows[t1], lows[t2]
    if p1 >= p2:
        return None
    neckline = float(np.max(close[t1:t2 + 1]))
    current = float(close[-1])
    broken = current > neckline * 1.004
    conf = 40
    if broken:
        conf += 25
    if p2 > p1 * 1.015:
        conf += 15
    if "Volume" in data.columns and data["Volume"].iloc[-1] > data["Volume"].iloc[-20:].mean() * 1.25:
        conf += 10
    days_between = t2 - t1
    if 15 <= days_between <= 100:
        conf += 10
    conf = min(conf, 95)
    return {
        "first_trough": round(float(p1), 2),
        "second_trough": round(float(p2), 2),
        "neckline": round(neckline, 2),
        "current": round(current, 2),
        "broken_out": broken,
        "confidence": conf,
        "days_between": int(days_between),
    }

def multi_factor_score(ticker, df, nifty_df, ath_info=None, pattern_info=None):
    if df.empty:
        return "white", "No Data", 0, "Insufficient data"
    score = 50
    reasons = []
    close = df["Close"]
    current = float(close.iloc[-1])
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else sma50

    if current > sma20 > sma50:
        score += 12
        reasons.append("Price>SMA20>SMA50")
    elif current < sma20 < sma50:
        score -= 12
        reasons.append("Price<SMA20<SMA50")
    if current > sma200:
        score += 8
        reasons.append("Above 200DMA")
    else:
        score -= 5
        reasons.append("Below 200DMA")

    rs = compute_rs(df, nifty_df)
    if rs > 1.15:
        score += 12
        reasons.append(f"Strong RS ({rs})")
    elif rs < 0.85:
        score -= 10
        reasons.append(f"Weak RS ({rs})")

    vol = df["Volume"]
    if vol.iloc[-1] > vol.iloc[-20:].mean() * 1.4:
        score += 8
        reasons.append("Volume spike")

    ad = compute_ad_line(df)
    if len(ad) > 20:
        slope = (ad.iloc[-1] - ad.iloc[-20]) / (abs(ad.iloc[-20]) + 1e-9)
        if slope > 0.05:
            score += 10
            reasons.append("Rising A/D")
        elif slope < -0.05:
            score -= 10
            reasons.append("Falling A/D")

    if ath_info:
        if ath_info.get("ath"):
            score += 10
            reasons.append("New ATH")
        elif ath_info.get("3yr") or ath_info.get("5yr"):
            score += 6
            reasons.append("Multi-year high")
    if pattern_info and pattern_info.get("broken_out"):
        score += 12
        reasons.append(f"DB breakout ({pattern_info['confidence']})")

    score = max(5, min(98, int(score)))
    if score >= 72:
        return "green", "BULLISH", score, " | ".join(reasons[:4])
    if score <= 35:
        return "red", "BEARISH", score, " | ".join(reasons[:4])
    if 45 <= score <= 55:
        return "white", "NEUTRAL", score, " | ".join(reasons[:4])
    return "amber", "WATCH", score, " | ".join(reasons[:4])

def volume_profile_hint(df, days=5):
    if len(df) < days + 2:
        return "Insufficient data", 0.0
    recent = df.iloc[-days:]
    chg = (recent["Close"].iloc[-1] / recent["Close"].iloc[0] - 1) * 100
    base = df["Volume"].iloc[-40:-days].mean() if len(df) > 40 else recent["Volume"].mean()
    vol_ratio = recent["Volume"].mean() / (base + 1e-9)
    if chg > 1.5 and vol_ratio > 1.2:
        return "Long Build-up (price up + vol up)", round(chg, 2)
    if chg < -1.5 and vol_ratio > 1.2:
        return "Short Build-up (price down + vol up)", round(chg, 2)
    if chg > 1.5 and vol_ratio < 0.9:
        return "Short Covering (price up + vol down)", round(chg, 2)
    if chg < -1.5 and vol_ratio < 0.9:
        return "Long Unwinding (price down + vol down)", round(chg, 2)
    return "Sideways / Mixed", round(chg, 2)

def trade_idea(score, label, rs, near_resist, ad_rising, pattern_broken):
    ideas = []
    if label == "BULLISH" and score >= 75 and ad_rising:
        ideas.append("**Primary:** Buy stock / Buy futures on dips toward support")
        ideas.append("**Options:** Bull Call Spread or Buy ATM/ITM CE")
        ideas.append("Avoid naked short puts unless strong conviction")
    elif label == "BULLISH" and pattern_broken:
        ideas.append("**Primary:** Buy on retest of neckline / broken resistance")
        ideas.append("**Options:** Buy CE or Bull Call Spread; stop below second trough")
    elif label == "BEARISH" and score <= 30:
        ideas.append("**Primary:** Sell / Short futures on bounce toward resistance")
        ideas.append("**Options:** Buy PE or Bear Put Spread")
        ideas.append("Covered Call only if you already hold and want to exit higher")
    elif label == "WATCH" and near_resist and not ad_rising:
        ideas.append("**Wait:** Near resistance + weak A/D — avoid fresh longs")
        ideas.append("**Options:** Short-term PE only on confirmation candle")
    else:
        ideas.append("**Neutral:** Wait for clearer A/D + price structure")
        ideas.append("Use defined-risk spreads only; avoid naked options")
    if rs > 1.2:
        ideas.append(f"RS strong ({rs}) — favour long bias on pullbacks")
    elif rs < 0.85:
        ideas.append(f"RS weak ({rs}) — favour short / underweight")
    return ideas

def get_options_oi_approx(ticker):
    try:
        t = yf.Ticker(ticker)
        exps = t.options
        if not exps:
            return None, None, "No options chain on free feed"
        use_exps = exps[:2]
        all_ce, all_pe = [], []
        for exp in use_exps:
            chain = t.option_chain(exp)
            calls = chain.calls.copy()
            puts = chain.puts.copy()
            calls["expiry"] = exp
            puts["expiry"] = exp
            all_ce.append(calls)
            all_pe.append(puts)
        ce = pd.concat(all_ce, ignore_index=True)
        pe = pd.concat(all_pe, ignore_index=True)
        ce = ce.nlargest(4, "openInterest")[["strike", "openInterest", "expiry", "lastPrice"]]
        pe = pe.nlargest(4, "openInterest")[["strike", "openInterest", "expiry", "lastPrice"]]
        return ce, pe, None
    except Exception as e:
        return None, None, str(e)[:90]

def get_news(ticker):
    try:
        t = yf.Ticker(ticker)
        news = getattr(t, "news", None) or []
        return [{"title": n.get("title", ""), "publisher": n.get("publisher", "")} for n in news[:4]]
    except Exception:
        return []

# ---------------------------------------------------------------------------
# HEADER + TABS (all sections in main area)
# ---------------------------------------------------------------------------
st.title("Nifty Pro Screener")
st.caption("ATH  |  Double Bottom  |  Broker Calls  |  A/D + Zones + Pivots + Options OI + Trade Ideas   •  v1.1 lighter dark")

tab1, tab2, tab3, tab4 = st.tabs([
    "ATH / Multi-Year Highs",
    "Double Bottom Breakouts",
    "Broker Recommendations",
    "A/D + Resistance + Analytics"
])

# ===========================================================================
# TAB 1 – ATH
# ===========================================================================
with tab1:
    st.subheader("All-Time & Multi-Year High Breakouts")
    st.markdown("Stocks at/near ATH, 3yr, 5yr or 10yr highs with multi-factor confidence.")

    max_scan = st.slider("Stocks to scan (higher = slower)", 40, min(220, len(NIFTY_UNIVERSE)), 80, key="ath_n")
    if st.button("Run ATH Scan", key="btn_ath"):
        nifty_df = get_nifty_data("2y")
        results = []
        bar = st.progress(0)
        universe = NIFTY_UNIVERSE[:max_scan]
        for i, t in enumerate(universe):
            df = get_stock_data(t, "max")
            if not df.empty:
                info = detect_ath(t, df)
                if info and (info["ath"] or info["3yr"] or info["5yr"] or info["10yr"]):
                    badge, label, score, reason = multi_factor_score(t, df, nifty_df, ath_info=info)
                    info.update({
                        "signal": label, "confidence": score, "reason": reason,
                        "rs": compute_rs(df, nifty_df),
                        "sector": SECTOR_MAP.get(t, "—")
                    })
                    results.append(info)
            bar.progress((i + 1) / len(universe))
        bar.empty()

        if not results:
            st.info("No fresh multi-year highs in this scan window.")
        else:
            df_res = pd.DataFrame(results).sort_values("confidence", ascending=False)
            st.success(f"Found {len(df_res)} stocks near/at highs")
            show = df_res[["ticker", "price", "ath", "3yr", "5yr", "10yr", "rs", "confidence", "signal", "sector", "reason"]]
            st.dataframe(show, use_container_width=True, height=400, hide_index=True)

            sel = st.selectbox("Inspect chart", df_res["ticker"].tolist(), key="ath_sel")
            if sel:
                full = sel + ".NS"
                df = get_stock_data(full, "2y")
                if not df.empty:
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index, open=df["Open"], high=df["High"],
                        low=df["Low"], close=df["Close"], name="Price",
                        increasing_line_color="#3fb950", decreasing_line_color="#f85149"
                    )])
                    fig.add_hline(y=float(df["Close"].max()), line_dash="dash",
                                  line_color="#3fb950", annotation_text="ATH")
                    fig.update_layout(
                        template="plotly_dark", height=460,
                        paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
                        xaxis_rangeslider_visible=False, font=dict(color="#e6edf3")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    row = df_res[df_res["ticker"] == sel].iloc[0]
                    color = "green" if row["signal"] == "BULLISH" else "red" if row["signal"] == "BEARISH" else "amber" if row["signal"] == "WATCH" else "white"
                    st.markdown(f"{badge_html(color, row['signal'])}  **Confidence {row['confidence']}/100**  |  RS {row['rs']}", unsafe_allow_html=True)
                    st.caption(row["reason"])
                    for n in get_news(full):
                        st.markdown(f"- {n['title']} _{n['publisher']}_")

# ===========================================================================
# TAB 2 – DOUBLE BOTTOM
# ===========================================================================
with tab2:
    st.subheader("Double Rounding Bottom + Breakout")
    st.markdown("First trough deeper, second higher → neckline breakout.")

    max_scan2 = st.slider("Stocks to scan", 40, min(180, len(NIFTY_UNIVERSE)), 70, key="db_n")
    if st.button("Run Double-Bottom Scan", key="btn_db"):
        nifty_df = get_nifty_data("1y")
        results = []
        bar = st.progress(0)
        universe = NIFTY_UNIVERSE[:max_scan2]
        for i, t in enumerate(universe):
            df = get_stock_data(t, "1y")
            if not df.empty:
                pat = detect_double_bottom(df)
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
                        "rs": compute_rs(df, nifty_df),
                        "sector": SECTOR_MAP.get(t, "—"),
                        "reason": reason,
                    })
            bar.progress((i + 1) / len(universe))
        bar.empty()

        if not results:
            st.info("No high-confidence double-bottom structures right now.")
        else:
            df_res = pd.DataFrame(results).sort_values("overall_conf", ascending=False)
            st.success(f"{len(df_res)} candidates")
            st.dataframe(df_res, use_container_width=True, height=360, hide_index=True)

            sel = st.selectbox("Chart candidate", df_res["ticker"].tolist(), key="db_sel")
            if sel:
                full = sel + ".NS"
                df = get_stock_data(full, "1y")
                pat = detect_double_bottom(df)
                if not df.empty and pat:
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index, open=df["Open"], high=df["High"],
                        low=df["Low"], close=df["Close"],
                        increasing_line_color="#3fb950", decreasing_line_color="#f85149"
                    )])
                    fig.add_hline(y=pat["neckline"], line_dash="dot", line_color="#d29922",
                                  annotation_text=f"Neckline {pat['neckline']}")
                    fig.add_hline(y=pat["first_trough"], line_dash="dash", line_color="#da3633",
                                  annotation_text="1st trough")
                    fig.add_hline(y=pat["second_trough"], line_dash="dash", line_color="#3fb950",
                                  annotation_text="2nd trough")
                    fig.update_layout(
                        template="plotly_dark", height=480,
                        paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
                        xaxis_rangeslider_visible=False, font=dict(color="#e6edf3")
                    )
                    st.plotly_chart(fig, use_container_width=True)

# ===========================================================================
# TAB 3 – BROKER RECS
# ===========================================================================
with tab3:
    st.subheader("Broker Recommendations (30 / 60 / 90 day)")
    st.caption("Sample data for demo — replace with live scraper later. Live price included.")

    recs = pd.DataFrame(SAMPLE_BROKER_RECS)
    recs["date"] = pd.to_datetime(recs["date"])
    today = pd.Timestamp(datetime.now().date())

    prices = {}
    for sym in recs["symbol"].unique():
        prices[sym] = get_live_price(sym)
    recs["current_price"] = recs["symbol"].map(prices)
    recs["upside_vs_live"] = np.where(
        recs["current_price"] > 0,
        (recs["target"] / recs["current_price"] - 1) * 100,
        recs["upside"]
    )

    t30, t60, t90, tall = st.tabs(["Last 30d", "Last 60d", "Last 90d", "All sample"])
    for tab, days in zip([t30, t60, t90, tall], [30, 60, 90, 9999]):
        with tab:
            sub = recs[recs["date"] >= today - timedelta(days=days)].copy()
            if sub.empty:
                st.write("No calls in this window.")
                continue
            buys = sub[sub["rating"].str.contains("Buy|Outperform|Overweight", case=False)]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Calls", len(sub))
            c2.metric("Positive", len(buys), f"{len(buys)/max(len(sub),1)*100:.0f}%")
            c3.metric("Avg Target Upside", f"{buys['upside_vs_live'].mean():.1f}%" if len(buys) else "—")
            c4.metric("Brokers", sub["broker"].nunique())

            st.dataframe(
                sub.sort_values("date", ascending=False)[
                    ["date", "broker", "symbol", "rating", "target", "current_price", "upside_vs_live"]
                ].rename(columns={"upside_vs_live": "upside_%_vs_live"}),
                use_container_width=True, height=340, hide_index=True
            )

# ===========================================================================
# TAB 4 – A/D + FULL ANALYTICS
# ===========================================================================
with tab4:
    st.subheader("A/D + Resistance + Zones + Options OI + Trade Ideas")
    st.markdown(
        "Select a stock → **Accumulation / Distribution zones** (like your sample), "
        "**R1 R2 S1 S2** pivots, A/D line, high-OI CE/PE strikes, buildup, PCR proxy, and trade recommendation."
    )

    with st.expander("High-probability filter table (optional scan)", expanded=False):
        max_ad = st.slider("Scan size", 30, 120, 50, key="ad_scan")
        if st.button("Build filter table", key="btn_ad_table"):
            nifty_df = get_nifty_data("1y")
            rows = []
            bar = st.progress(0)
            for i, t in enumerate(NIFTY_UNIVERSE[:max_ad]):
                df = get_stock_data(t, "1y")
                if not df.empty and len(df) >= 60:
                    badge, label, score, reason = multi_factor_score(t, df, nifty_df)
                    ad = compute_ad_line(df)
                    ad_rising = len(ad) > 20 and ad.iloc[-1] > ad.iloc[-20]
                    resist = float(df["High"].iloc[-60:].max())
                    current = float(df["Close"].iloc[-1])
                    dist = (resist - current) / current * 100
                    if (dist < 4 and ad_rising and score >= 55) or score >= 75 or score <= 30:
                        rows.append({
                            "ticker": t.replace(".NS", ""),
                            "price": round(current, 2),
                            "resistance": round(resist, 2),
                            "dist_%": round(dist, 2),
                            "ad_rising": ad_rising,
                            "rs": compute_rs(df, nifty_df),
                            "confidence": score,
                            "signal": label,
                            "sector": SECTOR_MAP.get(t, "—"),
                        })
                bar.progress((i + 1) / max_ad)
            bar.empty()
            if rows:
                st.dataframe(pd.DataFrame(rows).sort_values("confidence", ascending=False),
                             use_container_width=True, hide_index=True)
            else:
                st.info("No stocks met the strict filter.")

    st.markdown("---")
    choice = st.selectbox(
        "Select stock for full analytics",
        [t.replace(".NS", "") for t in NIFTY_UNIVERSE],
        index=0,
        key="ad_choice"
    )
    full_ticker = choice + ".NS"
    df = get_stock_data(full_ticker, "1y")
    nifty_df = get_nifty_data("1y")

    if df.empty:
        st.error("Could not load data for this ticker.")
    else:
        ad = compute_ad_line(df)
        pivots = compute_pivots(df)
        zones = detect_zones(df)
        badge, label, score, reason = multi_factor_score(full_ticker, df, nifty_df)
        rs = compute_rs(df, nifty_df)
        buildup, chg5 = volume_profile_hint(df, 5)
        current = float(df["Close"].iloc[-1])
        resist_60 = float(df["High"].iloc[-60:].max())
        support_60 = float(df["Low"].iloc[-60:].min())
        near_resist = (resist_60 - current) / current * 100 < 3.5
        ad_rising = len(ad) > 20 and ad.iloc[-1] > ad.iloc[-20]
        pat = detect_double_bottom(df)
        pattern_broken = bool(pat and pat.get("broken_out"))

        # CHART
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
            row_heights=[0.68, 0.32],
            subplot_titles=(f"{choice}  |  Price + Acc/Dist Zones + Pivots + OI", "Accumulation / Distribution Line")
        )

        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name="OHLC",
            increasing_line_color="#3fb950", decreasing_line_color="#f85149"
        ), row=1, col=1)

        for z in zones:
            color = "rgba(248,81,73,0.20)" if z["type"] == "Accumulation" else (
                "rgba(210,153,34,0.22)" if z["type"] == "Distribution" else "rgba(88,166,255,0.12)"
            )
            fig.add_vrect(
                x0=z["start"], x1=z["end"],
                fillcolor=color, line_width=0, row=1, col=1,
                annotation_text=z["type"], annotation_position="top left",
                annotation_font_size=11, annotation_font_color="#e6edf3"
            )

        for name, val, colr in [
            ("R2", pivots.get("R2"), "#f85149"),
            ("R1", pivots.get("R1"), "#ff7b72"),
            ("PP", pivots.get("PP"), "#8b949e"),
            ("S1", pivots.get("S1"), "#3fb950"),
            ("S2", pivots.get("S2"), "#56d364"),
        ]:
            if val:
                fig.add_hline(y=val, line_dash="dot", line_color=colr, line_width=1,
                              annotation_text=f"{name} {val:.1f}", annotation_position="right",
                              row=1, col=1)

        fig.add_hline(y=resist_60, line_dash="dash", line_color="#ff7b72",
                      annotation_text=f"60d High {resist_60:.1f}", row=1, col=1)
        fig.add_hline(y=support_60, line_dash="dash", line_color="#56d364",
                      annotation_text=f"60d Low {support_60:.1f}", row=1, col=1)

        ce_df, pe_df, oi_err = get_options_oi_approx(full_ticker)
        if ce_df is not None and not ce_df.empty:
            for _, r in ce_df.iterrows():
                fig.add_hline(y=float(r["strike"]), line_dash="dashdot", line_color="#58a6ff",
                              line_width=1, annotation_text=f"CE OI {int(r['openInterest'])}",
                              annotation_position="left", row=1, col=1)
        if pe_df is not None and not pe_df.empty:
            for _, r in pe_df.iterrows():
                fig.add_hline(y=float(r["strike"]), line_dash="dashdot", line_color="#d2a8ff",
                              line_width=1, annotation_text=f"PE OI {int(r['openInterest'])}",
                              annotation_position="left", row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index, y=ad, mode="lines", name="A/D",
            line=dict(color="#58a6ff", width=1.8),
            fill="tozeroy", fillcolor="rgba(88,166,255,0.12)"
        ), row=2, col=1)

        fig.update_layout(
            template="plotly_dark", height=700,
            paper_bgcolor="#161b22", plot_bgcolor="#0d1117",
            xaxis_rangeslider_visible=False, showlegend=False,
            font=dict(color="#e6edf3", size=12),
            margin=dict(l=40, r=40, t=40, b=20)
        )
        fig.update_xaxes(gridcolor="#21262d")
        fig.update_yaxes(gridcolor="#21262d")
        st.plotly_chart(fig, use_container_width=True)

        if oi_err and ce_df is None:
            st.caption(f"Options OI limited on free feed for this ticker. ({oi_err})")

        # ANALYTICS PANEL
        st.markdown("### Stock Analytics Panel")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Price", f"Rs {current:,.2f}")
        c2.metric("Signal", label)
        c3.metric("Confidence", f"{score}/100")
        c4.metric("RS vs Nifty", rs)
        c5.metric("5d Price Chg", f"{chg5}%")

        color = "green" if label == "BULLISH" else "red" if label == "BEARISH" else "amber" if label == "WATCH" else "white"
        st.markdown(f"{badge_html(color, label)}  **{reason}**", unsafe_allow_html=True)
        st.markdown(f"**Sector:** {SECTOR_MAP.get(full_ticker, '—')}  |  **Last 5 sessions:** {buildup}")

        if ce_df is not None and pe_df is not None and not ce_df.empty and not pe_df.empty:
            total_ce = ce_df["openInterest"].sum()
            total_pe = pe_df["openInterest"].sum()
            pcr = total_pe / total_ce if total_ce else np.nan
            if not np.isnan(pcr):
                st.markdown(f"**Approx PCR (top OI strikes, current+next expiry):** {pcr:.2f}")
            col_ce, col_pe = st.columns(2)
            with col_ce:
                st.markdown("**Top CE by OI**")
                st.dataframe(ce_df, use_container_width=True, hide_index=True)
            with col_pe:
                st.markdown("**Top PE by OI**")
                st.dataframe(pe_df, use_container_width=True, hide_index=True)

        st.markdown("#### Institutional / Flow cues (proxy)")
        st.info(
            "True daily FII/DII stock-level change is not free in real time. "
            "Proxies: volume-price buildup, A/D slope, high-volume sessions. "
            "Production: add NSE bulk/block deals + shareholding pattern."
        )
        if len(df) > 30:
            vol_ma = df["Volume"].rolling(20).mean()
            spikes = df[df["Volume"] > vol_ma * 2.2].tail(6)
            if not spikes.empty:
                spike_view = spikes[["Open", "High", "Low", "Close", "Volume"]].copy()
                spike_view["bias"] = np.where(spike_view["Close"] > spike_view["Open"], "Buy-side volume", "Sell-side volume")
                st.markdown("**Recent high-volume sessions (possible institutional activity)**")
                st.dataframe(spike_view, use_container_width=True, hide_index=True)

        st.markdown("#### Trade Recommendation (educational only)")
        for idea in trade_idea(score, label, rs, near_resist, ad_rising, pattern_broken):
            st.markdown(f"- {idea}")

        st.markdown("#### Headlines")
        news = get_news(full_ticker)
        if news:
            for n in news:
                st.markdown(f"- {n['title']}  _{n['publisher']}_")
        else:
            st.caption("No headlines from free feed.")

st.markdown("---")
st.caption("Nifty Pro Screener v1.1 • Educational only • Yahoo Finance data • Options/FII limited on free feeds")
