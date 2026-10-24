"""Nifty Pro Screener v1.2 - progressive scan, visible UI, sectoral indices tab."""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy.signal import argrelextrema
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Nifty Pro Screener", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.stApp{background:#1c2128;color:#e6edf3;}
h1,h2,h3,h4{color:#f0f6fc!important;}
.stMetric{background:#2d333b;border-radius:8px;padding:10px;border:1px solid #444c56;}
.stTabs [data-baseweb="tab-list"]{gap:8px;background:#0d1117;padding:8px;border-radius:10px;flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{background:#2d333b!important;color:#e6edf3!important;border:1px solid #444c56!important;border-radius:8px!important;padding:12px 18px!important;font-weight:600!important;}
.stTabs [aria-selected="true"]{background:#1f6feb!important;color:#fff!important;}
.stButton>button{background:#1f6feb!important;color:#fff!important;border:none!important;border-radius:8px!important;font-weight:600!important;padding:0.55rem 1.25rem!important;}
.stButton>button:hover{background:#388bfd!important;}
.badge-green{background:#238636;color:#fff;padding:4px 12px;border-radius:12px;font-weight:600;}
.badge-red{background:#da3633;color:#fff;padding:4px 12px;border-radius:12px;font-weight:600;}
.badge-amber{background:#d29922;color:#000;padding:4px 12px;border-radius:12px;font-weight:600;}
.badge-white{background:#8b949e;color:#000;padding:4px 12px;border-radius:12px;font-weight:600;}
[data-testid="stSidebar"]{display:none;}
label,p{color:#e6edf3!important;}
</style>
""", unsafe_allow_html=True)

def badge_html(c,t): return f'<span class="badge-{c}">{t}</span>'

NIFTY_UNIVERSE = [
"RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","HINDUNILVR.NS","ITC.NS","SBIN.NS",
"BHARTIARTL.NS","KOTAKBANK.NS","LT.NS","AXISBANK.NS","BAJFINANCE.NS","ASIANPAINT.NS","MARUTI.NS",
"SUNPHARMA.NS","TITAN.NS","WIPRO.NS","ULTRACEMCO.NS","NESTLEIND.NS","POWERGRID.NS","NTPC.NS",
"HCLTECH.NS","M&M.NS","TATAMOTORS.NS","ADANIENT.NS","ADANIPORTS.NS","JSWSTEEL.NS","TATASTEEL.NS",
"ONGC.NS","COALINDIA.NS","BAJAJFINSV.NS","TECHM.NS","INDUSINDBK.NS","GRASIM.NS","CIPLA.NS",
"DRREDDY.NS","EICHERMOT.NS","HEROMOTOCO.NS","BRITANNIA.NS","DIVISLAB.NS","APOLLOHOSP.NS","BPCL.NS",
"HINDALCO.NS","SHREECEM.NS","SBILIFE.NS","HDFCLIFE.NS","PIDILITIND.NS","DABUR.NS","GODREJCP.NS",
"SIEMENS.NS","HAVELLS.NS","AMBUJACEM.NS","DLF.NS","VEDL.NS","TATACONSUM.NS","ICICIPRULI.NS",
"BANKBARODA.NS","PNB.NS","CANBK.NS","IOC.NS","GAIL.NS","INDIGO.NS","ZOMATO.NS","DMART.NS",
"AUROPHARMA.NS","LUPIN.NS","BIOCON.NS","TORNTPHARM.NS","ALKEM.NS","BEL.NS","HAL.NS","BHEL.NS",
"IRCTC.NS","NHPC.NS","RECLTD.NS","PFC.NS","IRFC.NS","SAIL.NS","NMDC.NS","JINDALSTEL.NS",
"TATAPOWER.NS","ADANIGREEN.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","AUBANK.NS","CHOLAFIN.NS",
"GODREJPROP.NS","OBEROIRLTY.NS","PRESTIGE.NS","ABB.NS","POLYCAB.NS","VOLTAS.NS","VBL.NS",
"PERSISTENT.NS","COFORGE.NS","LTTS.NS","MPHASIS.NS","DIXON.NS","JUBLFOOD.NS","NAUKRI.NS",
"PIIND.NS","SRF.NS","UPL.NS","MAXHEALTH.NS","FORTIS.NS","INDHOTEL.NS","YESBANK.NS",
"APLAPOLLO.NS","DALBHARAT.NS","RAMCOCEM.NS","JKCEMENT.NS","CDSL.NS","BSE.NS","MCX.NS",
"CAMS.NS","ANGELONE.NS","MOTILALOFS.NS","MAZDOCK.NS","BDL.NS","SOLARINDS.NS","LODHA.NS",
"LTIM.NS","PAGEIND.NS","TVSMOTOR.NS","BAJAJ-AUTO.NS","ASHOKLEY.NS","MOTHERSON.NS",
"PETRONET.NS","IGL.NS","BANDHANBNK.NS","MUTHOOTFIN.NS","LICHSGFIN.NS","KEI.NS","CROMPTON.NS",
"OFSS.NS","KPITTECH.NS","SYNGENE.NS","GRANULES.NS","AFFLE.NS","INDIAMART.NS","UNIONBANK.NS",
"BANKINDIA.NS","CUB.NS","BRIGADE.NS","PHOENIXLTD.NS","CONCOR.NS","GMRINFRA.NS","IRB.NS",
]
seen=set(); NIFTY_UNIVERSE=[x for x in NIFTY_UNIVERSE if not (x in seen or seen.add(x))]

INDEX_CONSTITUENTS = {
"NIFTY METAL":["JSWSTEEL.NS","TATASTEEL.NS","HINDALCO.NS","VEDL.NS","NMDC.NS","SAIL.NS","JINDALSTEL.NS"],
"NIFTY INDIA DEFENCE":["HAL.NS","BEL.NS","BHEL.NS","MAZDOCK.NS","BDL.NS","SOLARINDS.NS"],
"NIFTY CAPITAL MARKETS":["BSE.NS","CDSL.NS","MCX.NS","CAMS.NS","ANGELONE.NS","MOTILALOFS.NS"],
"NIFTY PSU BANK":["SBIN.NS","BANKBARODA.NS","PNB.NS","CANBK.NS","UNIONBANK.NS","BANKINDIA.NS"],
"NIFTY PHARMA":["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","AUROPHARMA.NS","LUPIN.NS","TORNTPHARM.NS"],
"NIFTY ENERGY":["RELIANCE.NS","NTPC.NS","POWERGRID.NS","ONGC.NS","COALINDIA.NS","BPCL.NS","IOC.NS"],
"NIFTY AUTO":["MARUTI.NS","M&M.NS","TATAMOTORS.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS","EICHERMOT.NS","TVSMOTOR.NS"],
"NIFTY IT":["TCS.NS","INFY.NS","HCLTECH.NS","WIPRO.NS","TECHM.NS","LTIM.NS","PERSISTENT.NS","COFORGE.NS"],
"NIFTY FMCG":["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS","DABUR.NS","GODREJCP.NS"],
"NIFTY BANK":["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS","INDUSINDBK.NS"],
"NIFTY FINANCIAL SERVICES":["HDFCBANK.NS","ICICIBANK.NS","BAJFINANCE.NS","BAJAJFINSV.NS","HDFCLIFE.NS","SBILIFE.NS"],
"NIFTY REALTY":["DLF.NS","GODREJPROP.NS","OBEROIRLTY.NS","PRESTIGE.NS","LODHA.NS","BRIGADE.NS"],
"NIFTY INFRASTRUCTURE":["LT.NS","ADANIPORTS.NS","POWERGRID.NS","NTPC.NS","SIEMENS.NS","ABB.NS","IRB.NS"],
"NIFTY HEALTHCARE INDEX":["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","APOLLOHOSP.NS","MAXHEALTH.NS","FORTIS.NS"],
"NIFTY COMMODITIES":["RELIANCE.NS","ULTRACEMCO.NS","JSWSTEEL.NS","TATASTEEL.NS","HINDALCO.NS","COALINDIA.NS"],
"NIFTY INDIA MANUFACTURING":["RELIANCE.NS","TATAMOTORS.NS","M&M.NS","SUNPHARMA.NS","ULTRACEMCO.NS","BEL.NS"],
"NIFTY NEXT 50":["ADANIENT.NS","ADANIPORTS.NS","DLF.NS","VEDL.NS","PIDILITIND.NS","HAVELLS.NS"],
"NIFTY PSE":["NTPC.NS","POWERGRID.NS","ONGC.NS","COALINDIA.NS","BPCL.NS","BEL.NS"],
"NIFTY OIL & GAS":["RELIANCE.NS","ONGC.NS","BPCL.NS","IOC.NS","GAIL.NS","PETRONET.NS"],
"NIFTY CONSUMER DURABLES":["TITAN.NS","HAVELLS.NS","VOLTAS.NS","CROMPTON.NS","VBL.NS"],
}
SECTOR_MAP={"RELIANCE.NS":"Energy","TCS.NS":"IT","HDFCBANK.NS":"Banking","HAL.NS":"Defence","JSWSTEEL.NS":"Metals","SUNPHARMA.NS":"Pharma"}
SAMPLE_BROKER_RECS=[
{"date":"2026-10-20","broker":"Motilal Oswal","symbol":"HDFCBANK.NS","rating":"Buy","target":925},
{"date":"2026-10-19","broker":"Nuvama","symbol":"ICICIBANK.NS","rating":"Buy","target":1850},
{"date":"2026-10-19","broker":"Jefferies","symbol":"ULTRACEMCO.NS","rating":"Buy","target":14380},
{"date":"2026-10-19","broker":"HSBC","symbol":"ULTRACEMCO.NS","rating":"Buy","target":14200},
{"date":"2026-10-19","broker":"CLSA","symbol":"ULTRACEMCO.NS","rating":"Outperform","target":13000},
{"date":"2026-10-19","broker":"JP Morgan","symbol":"ULTRACEMCO.NS","rating":"Overweight","target":12900},
{"date":"2026-10-19","broker":"Kotak","symbol":"ULTRACEMCO.NS","rating":"Sell","target":8900},
{"date":"2026-10-18","broker":"Goldman Sachs","symbol":"ICICIBANK.NS","rating":"Buy","target":2025},
{"date":"2026-10-15","broker":"Motilal Oswal","symbol":"SBIN.NS","rating":"Buy","target":1300},
{"date":"2026-10-12","broker":"Jefferies","symbol":"AXISBANK.NS","rating":"Buy","target":1700},
{"date":"2026-10-10","broker":"CLSA","symbol":"TCS.NS","rating":"Outperform","target":4800},
{"date":"2026-09-28","broker":"JP Morgan","symbol":"RELIANCE.NS","rating":"Overweight","target":3200},
{"date":"2026-09-20","broker":"Nuvama","symbol":"BAJFINANCE.NS","rating":"Buy","target":8500},
{"date":"2026-08-25","broker":"Kotak","symbol":"LT.NS","rating":"Buy","target":4200},
]

@st.cache_data(ttl=3600,show_spinner=False)
def get_nifty_data(period="1y"):
    try:
        df=yf.download("^NSEI",period=period,progress=False,auto_adjust=True)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        return df
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=1800,show_spinner=False)
def get_stock_data(ticker,period="2y"):
    try:
        df=yf.download(ticker,period=period,progress=False,auto_adjust=True)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        if df.empty or len(df)<40: return pd.DataFrame()
        return df
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=600,show_spinner=False)
def get_live_price(ticker):
    try:
        t=yf.Ticker(ticker); info=t.fast_info
        p=getattr(info,"last_price",None) or getattr(info,"lastPrice",None)
        if p: return float(p)
    except Exception: pass
    df=get_stock_data(ticker,"5d")
    return float(df["Close"].iloc[-1]) if not df.empty else np.nan

def compute_ad_line(df):
    if df.empty: return pd.Series(dtype=float)
    hl=(df["High"]-df["Low"]).replace(0,np.nan)
    clv=((df["Close"]-df["Low"])-(df["High"]-df["Close"]))/hl
    return (clv.fillna(0)*df["Volume"]).cumsum()

def compute_pivots(df):
    if len(df)<2: return {}
    prev=df.iloc[-2]; h,l,c=float(prev["High"]),float(prev["Low"]),float(prev["Close"]); pp=(h+l+c)/3
    return {"PP":pp,"R1":2*pp-l,"R2":pp+(h-l),"S1":2*pp-h,"S2":pp-(h-l)}

def detect_zones(df,lookback=120):
    if len(df)<lookback: return []
    data=df.iloc[-lookback:]; close=data["Close"]; zones=[]
    for w in range(18,45,5):
        for i in range(len(data)-w):
            window=close.iloc[i:i+w]
            if (window.max()-window.min())/(window.mean()+1e-9)<0.07:
                before=close.iloc[max(0,i-20):i]
                if len(before)>5 and before.iloc[-1]<before.iloc[0]*0.97: ztype="Accumulation"
                elif i>10 and window.mean()>close.iloc[:i].mean(): ztype="Distribution"
                else: ztype="Consolidation"
                zones.append({"start":data.index[i],"end":data.index[i+w-1],"type":ztype}); break
    return zones[-2:]

def compute_rs(stock_df,nifty_df,window=60):
    try:
        if stock_df.empty or nifty_df.empty or len(stock_df)<window: return 1.0
        s=stock_df["Close"].pct_change(window).iloc[-1]; n=nifty_df["Close"].pct_change(window).iloc[-1]
        if n==0 or np.isnan(n) or np.isnan(s): return 1.0
        return round(float(s/n),2)
    except Exception: return 1.0

def detect_ath(ticker,df):
    if df.empty or len(df)<100: return None
    close=df["Close"]; current=float(close.iloc[-1])
    out={"ticker":ticker.replace(".NS",""),"price":round(current,2),"ath":current>=float(close.max())*0.998,"ath_price":round(float(close.max()),2),"3yr":False,"5yr":False,"10yr":False}
    for label,days in [("3yr",756),("5yr",1260),("10yr",2520)]:
        window=close.iloc[-min(days,len(close)):]; high=float(window.max()); out[f"{label}_high"]=round(high,2)
        if current>=high*0.998 and len(window)>days*0.55: out[label]=True
    return out

def detect_double_bottom(df,lookback=160):
    if df.empty or len(df)<lookback: return None
    data=df.iloc[-lookback:]; lows=data["Low"].values; close=data["Close"].values
    min_idx=argrelextrema(lows,np.less_equal,order=7)[0]
    if len(min_idx)<2: return None
    troughs=sorted(min_idx[-5:])
    if len(troughs)<2: return None
    t1,t2=troughs[-2],troughs[-1]; p1,p2=lows[t1],lows[t2]
    if p1>=p2: return None
    neckline=float(np.max(close[t1:t2+1])); current=float(close[-1]); broken=current>neckline*1.004
    conf=40+(25 if broken else 0)+(15 if p2>p1*1.015 else 0)
    if "Volume" in data.columns and data["Volume"].iloc[-1]>data["Volume"].iloc[-20:].mean()*1.25: conf+=10
    if 15<=(t2-t1)<=100: conf+=10
    return {"first_trough":round(float(p1),2),"second_trough":round(float(p2),2),"neckline":round(neckline,2),"current":round(current,2),"broken_out":broken,"confidence":min(conf,95),"days_between":int(t2-t1)}

def multi_factor_score(ticker,df,nifty_df,ath_info=None,pattern_info=None):
    if df.empty: return "white","No Data",0,"Insufficient data"
    score,reasons=50,[]
    close=df["Close"]; current=float(close.iloc[-1])
    sma20=close.rolling(20).mean().iloc[-1]; sma50=close.rolling(50).mean().iloc[-1]
    sma200=close.rolling(200).mean().iloc[-1] if len(close)>=200 else sma50
    if current>sma20>sma50: score+=12; reasons.append("Price>SMA20>SMA50")
    elif current<sma20<sma50: score-=12; reasons.append("Price<SMA20<SMA50")
    if current>sma200: score+=8; reasons.append("Above 200DMA")
    else: score-=5; reasons.append("Below 200DMA")
    rs=compute_rs(df,nifty_df)
    if rs>1.15: score+=12; reasons.append(f"Strong RS ({rs})")
    elif rs<0.85: score-=10; reasons.append(f"Weak RS ({rs})")
    if df["Volume"].iloc[-1]>df["Volume"].iloc[-20:].mean()*1.4: score+=8; reasons.append("Volume spike")
    ad=compute_ad_line(df)
    if len(ad)>20:
        slope=(ad.iloc[-1]-ad.iloc[-20])/(abs(ad.iloc[-20])+1e-9)
        if slope>0.05: score+=10; reasons.append("Rising A/D")
        elif slope<-0.05: score-=10; reasons.append("Falling A/D")
    if ath_info and ath_info.get("ath"): score+=10; reasons.append("New ATH")
    if pattern_info and pattern_info.get("broken_out"): score+=12; reasons.append("DB breakout")
    score=max(5,min(98,int(score)))
    if score>=72: return "green","BULLISH",score," | ".join(reasons[:4])
    if score<=35: return "red","BEARISH",score," | ".join(reasons[:4])
    if 45<=score<=55: return "white","NEUTRAL",score," | ".join(reasons[:4])
    return "amber","WATCH",score," | ".join(reasons[:4])

def volume_profile_hint(df,days=5):
    if len(df)<days+2: return "Insufficient",0.0
    recent=df.iloc[-days:]; chg=(recent["Close"].iloc[-1]/recent["Close"].iloc[0]-1)*100
    base=df["Volume"].iloc[-40:-days].mean() if len(df)>40 else recent["Volume"].mean()
    vr=recent["Volume"].mean()/(base+1e-9)
    if chg>1.5 and vr>1.2: return "Long Build-up",round(chg,2)
    if chg<-1.5 and vr>1.2: return "Short Build-up",round(chg,2)
    if chg>1.5 and vr<0.9: return "Short Covering",round(chg,2)
    if chg<-1.5 and vr<0.9: return "Long Unwinding",round(chg,2)
    return "Sideways/Mixed",round(chg,2)

def trade_idea(score,label,rs,near_resist,ad_rising,pattern_broken):
    ideas=[]
    if label=="BULLISH" and score>=75 and ad_rising: ideas+=["**Primary:** Buy stock/futures on dips","**Options:** Bull Call Spread or ITM CE"]
    elif label=="BULLISH" and pattern_broken: ideas+=["**Primary:** Buy on neckline retest","**Options:** CE / Bull Call Spread"]
    elif label=="BEARISH" and score<=30: ideas+=["**Primary:** Short futures on bounce","**Options:** PE / Bear Put Spread"]
    elif near_resist and not ad_rising: ideas+=["**Wait:** Near resistance + weak A/D"]
    else: ideas+=["**Neutral:** Wait for clearer structure"]
    if rs>1.2: ideas.append(f"RS strong ({rs})")
    elif rs<0.85: ideas.append(f"RS weak ({rs})")
    return ideas

def get_options_oi_approx(ticker):
    try:
        t=yf.Ticker(ticker)
        if not t.options: return None,None,"No chain"
        all_ce,all_pe=[],[]
        for exp in t.options[:2]:
            ch=t.option_chain(exp); c,p=ch.calls.copy(),ch.puts.copy(); c["expiry"]=exp; p["expiry"]=exp
            all_ce.append(c); all_pe.append(p)
        ce=pd.concat(all_ce).nlargest(4,"openInterest")[["strike","openInterest","expiry","lastPrice"]]
        pe=pd.concat(all_pe).nlargest(4,"openInterest")[["strike","openInterest","expiry","lastPrice"]]
        return ce,pe,None
    except Exception as e: return None,None,str(e)[:80]

def get_news(ticker):
    try:
        news=getattr(yf.Ticker(ticker),"news",None) or []
        return [{"title":n.get("title",""),"publisher":n.get("publisher","")} for n in news[:3]]
    except Exception: return []

@st.cache_data(ttl=3600)
def load_indices_table():
    path=Path(__file__).parent/"nifty_indices_clean.csv"
    if path.exists(): return pd.read_csv(path)
    return pd.DataFrame([{"INDEX":"NIFTY METAL","CURRENT":13133.6,"%CHANGE":-0.18,"30 D %CHNG":1.7,"365 D %CHNG":35.73},{"INDEX":"NIFTY INDIA DEFENCE","CURRENT":9700.1,"%CHANGE":0.82,"30 D %CHNG":2.78,"365 D %CHNG":26.34},{"INDEX":"NIFTY PSU BANK","CURRENT":8614.5,"%CHANGE":1.21,"30 D %CHNG":1.51,"365 D %CHNG":24.47},{"INDEX":"NIFTY PHARMA","CURRENT":26646.5,"%CHANGE":-0.5,"30 D %CHNG":-0.06,"365 D %CHNG":21.34},{"INDEX":"NIFTY 50","CURRENT":23925.95,"%CHANGE":0.05,"30 D %CHNG":-3.42,"365 D %CHNG":-3.19}])

for k,v in [("ath_offset",0),("ath_results",[]),("db_offset",0),("db_results",[]),("db_selected",None)]:
    if k not in st.session_state: st.session_state[k]=v

st.title("Nifty Pro Screener v1.2")
st.caption(f"Universe: {len(NIFTY_UNIVERSE)} | Progressive scan | Boxed tabs | Blue buttons | 5 tabs")
tab1,tab2,tab3,tab4,tab5=st.tabs(["ATH / Multi-Year Highs","Double Bottom","Broker Recommendations","A/D + Analytics","Sectoral Indices (NSE)"])

with tab1:
    st.subheader("All-Time & Multi-Year High Breakouts")
    batch=st.slider("Batch size per run",20,80,40,key="ath_batch")
    c1,c2,c3=st.columns(3)
    with c1: run=st.button("Run next batch (ATH)",key="btn_ath")
    with c2:
        if st.button("Reset ATH scan",key="btn_ath_reset"):
            st.session_state.ath_offset=0; st.session_state.ath_results=[]; st.rerun()
    with c3: st.write(f"Progress: **{st.session_state.ath_offset}** / {len(NIFTY_UNIVERSE)}")
    if run:
        nifty_df=get_nifty_data("2y"); start=st.session_state.ath_offset; end=min(start+batch,len(NIFTY_UNIVERSE))
        universe=NIFTY_UNIVERSE[start:end]; bar=st.progress(0); new=[]
        for i,t in enumerate(universe):
            df=get_stock_data(t,"max")
            if not df.empty:
                info=detect_ath(t,df)
                if info and (info["ath"] or info["3yr"] or info["5yr"] or info["10yr"]):
                    _,label,score,reason=multi_factor_score(t,df,nifty_df,ath_info=info)
                    info.update({"signal":label,"confidence":score,"reason":reason,"rs":compute_rs(df,nifty_df),"sector":SECTOR_MAP.get(t,"—")}); new.append(info)
            bar.progress((i+1)/max(len(universe),1))
        bar.empty(); st.session_state.ath_results.extend(new); st.session_state.ath_offset=end
        st.success(f"Scanned {start}->{end}. New: {len(new)}. Total: {len(st.session_state.ath_results)}")
    if st.session_state.ath_results:
        df_res=pd.DataFrame(st.session_state.ath_results).drop_duplicates("ticker").sort_values("confidence",ascending=False)
        st.dataframe(df_res[["ticker","price","ath","3yr","5yr","10yr","rs","confidence","signal","sector","reason"]],use_container_width=True,height=380,hide_index=True)
        sel=st.selectbox("Chart",df_res["ticker"].tolist(),key="ath_sel_stable")
        if sel:
            df=get_stock_data(sel+".NS","2y")
            if not df.empty:
                fig=go.Figure(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],increasing_line_color="#3fb950",decreasing_line_color="#f85149"))
                fig.add_hline(y=float(df["Close"].max()),line_dash="dash",line_color="#3fb950",annotation_text="ATH")
                fig.update_layout(template="plotly_dark",height=420,paper_bgcolor="#1c2128",plot_bgcolor="#0d1117",xaxis_rangeslider_visible=False,font=dict(color="#e6edf3"))
                st.plotly_chart(fig,use_container_width=True)

with tab2:
    st.subheader("Double Rounding Bottom + Breakout")
    batch2=st.slider("Batch size",20,60,30,key="db_batch")
    c1,c2,c3=st.columns(3)
    with c1: run2=st.button("Run next batch (DB)",key="btn_db")
    with c2:
        if st.button("Reset DB scan",key="btn_db_reset"):
            st.session_state.db_offset=0; st.session_state.db_results=[]; st.session_state.db_selected=None; st.rerun()
    with c3: st.write(f"Progress: **{st.session_state.db_offset}** / {len(NIFTY_UNIVERSE)}")
    if run2:
        nifty_df=get_nifty_data("1y"); start=st.session_state.db_offset; end=min(start+batch2,len(NIFTY_UNIVERSE))
        universe=NIFTY_UNIVERSE[start:end]; bar=st.progress(0); new=[]
        for i,t in enumerate(universe):
            df=get_stock_data(t,"1y")
            if not df.empty:
                pat=detect_double_bottom(df)
                if pat and pat["confidence"]>=55:
                    _,label,score,reason=multi_factor_score(t,df,nifty_df,pattern_info=pat)
                    new.append({"ticker":t.replace(".NS",""),"price":pat["current"],"first_low":pat["first_trough"],"second_low":pat["second_trough"],"neckline":pat["neckline"],"broken":pat["broken_out"],"pattern_conf":pat["confidence"],"overall_conf":score,"signal":label,"rs":compute_rs(df,nifty_df),"sector":SECTOR_MAP.get(t,"—"),"reason":reason})
            bar.progress((i+1)/max(len(universe),1))
        bar.empty(); st.session_state.db_results.extend(new); st.session_state.db_offset=end
        st.success(f"Scanned {start}->{end}. New: {len(new)}. Total: {len(st.session_state.db_results)}")
    if st.session_state.db_results:
        df_res=pd.DataFrame(st.session_state.db_results).drop_duplicates("ticker").sort_values("overall_conf",ascending=False)
        st.dataframe(df_res,use_container_width=True,height=340,hide_index=True)
        options=df_res["ticker"].tolist()
        ix=options.index(st.session_state.db_selected) if st.session_state.db_selected in options else 0
        sel=st.selectbox("Chart candidate (does NOT re-scan)",options,index=ix,key="db_sel_stable")
        st.session_state.db_selected=sel
        if sel:
            df=get_stock_data(sel+".NS","1y"); pat=detect_double_bottom(df)
            if not df.empty and pat:
                fig=go.Figure(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],increasing_line_color="#3fb950",decreasing_line_color="#f85149"))
                fig.add_hline(y=pat["neckline"],line_dash="dot",line_color="#d29922",annotation_text=f"Neckline {pat['neckline']}")
                fig.add_hline(y=pat["first_trough"],line_dash="dash",line_color="#da3633",annotation_text="1st trough")
                fig.add_hline(y=pat["second_trough"],line_dash="dash",line_color="#3fb950",annotation_text="2nd trough")
                fig.update_layout(template="plotly_dark",height=460,paper_bgcolor="#1c2128",plot_bgcolor="#0d1117",xaxis_rangeslider_visible=False,font=dict(color="#e6edf3"))
                st.plotly_chart(fig,use_container_width=True)

with tab3:
    st.subheader("Broker Recommendations")
    recs=pd.DataFrame(SAMPLE_BROKER_RECS); recs["date"]=pd.to_datetime(recs["date"])
    prices={s:get_live_price(s) for s in recs["symbol"].unique()}
    recs["current_price"]=recs["symbol"].map(prices)
    recs["upside_%"]=np.where(recs["current_price"]>0,(recs["target"]/recs["current_price"]-1)*100,np.nan)
    today=pd.Timestamp(datetime.now().date())
    for label,days in [("30d",30),("60d",60),("90d",90),("All",9999)]:
        with st.expander(f"Last {label}",expanded=(label=="30d")):
            sub=recs[recs["date"]>=today-timedelta(days=days)]
            if sub.empty: st.write("No data")
            else: st.dataframe(sub[["date","broker","symbol","rating","target","current_price","upside_%"]].sort_values("date",ascending=False),use_container_width=True,hide_index=True)

with tab4:
    st.subheader("A/D + Zones + Pivots + Options + Trade Ideas")
    choice=st.selectbox("Stock",[t.replace(".NS","") for t in NIFTY_UNIVERSE],key="ad_choice")
    full=choice+".NS"; df=get_stock_data(full,"1y"); nifty_df=get_nifty_data("1y")
    if df.empty: st.error("No data")
    else:
        ad=compute_ad_line(df); pivots=compute_pivots(df); zones=detect_zones(df)
        color,label,score,reason=multi_factor_score(full,df,nifty_df); rs=compute_rs(df,nifty_df)
        buildup,chg5=volume_profile_hint(df); current=float(df["Close"].iloc[-1])
        resist_60=float(df["High"].iloc[-60:].max()); support_60=float(df["Low"].iloc[-60:].min())
        near_resist=(resist_60-current)/current*100<3.5; ad_rising=len(ad)>20 and ad.iloc[-1]>ad.iloc[-20]
        pat=detect_double_bottom(df); pattern_broken=bool(pat and pat.get("broken_out"))
        fig=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.68,0.32],vertical_spacing=0.04,subplot_titles=(f"{choice} Price + Zones + Pivots","A/D Line"))
        fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],increasing_line_color="#3fb950",decreasing_line_color="#f85149"),row=1,col=1)
        for z in zones:
            fill="rgba(248,81,73,0.2)" if z["type"]=="Accumulation" else ("rgba(210,153,34,0.22)" if z["type"]=="Distribution" else "rgba(88,166,255,0.12)")
            fig.add_vrect(x0=z["start"],x1=z["end"],fillcolor=fill,line_width=0,row=1,col=1,annotation_text=z["type"],annotation_font_color="#e6edf3")
        for name,val,colr in [("R2",pivots.get("R2"),"#f85149"),("R1",pivots.get("R1"),"#ff7b72"),("PP",pivots.get("PP"),"#8b949e"),("S1",pivots.get("S1"),"#3fb950"),("S2",pivots.get("S2"),"#56d364")]:
            if val: fig.add_hline(y=val,line_dash="dot",line_color=colr,annotation_text=f"{name} {val:.1f}",row=1,col=1)
        fig.add_hline(y=resist_60,line_dash="dash",line_color="#ff7b72",annotation_text="60d High",row=1,col=1)
        fig.add_hline(y=support_60,line_dash="dash",line_color="#56d364",annotation_text="60d Low",row=1,col=1)
        ce_df,pe_df,_=get_options_oi_approx(full)
        if ce_df is not None:
            for _,r in ce_df.iterrows(): fig.add_hline(y=float(r["strike"]),line_dash="dashdot",line_color="#58a6ff",annotation_text=f"CE {int(r['openInterest'])}",row=1,col=1)
        if pe_df is not None:
            for _,r in pe_df.iterrows(): fig.add_hline(y=float(r["strike"]),line_dash="dashdot",line_color="#d2a8ff",annotation_text=f"PE {int(r['openInterest'])}",row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=ad,mode="lines",line=dict(color="#58a6ff",width=1.8),fill="tozeroy",fillcolor="rgba(88,166,255,0.12)"),row=2,col=1)
        fig.update_layout(template="plotly_dark",height=680,paper_bgcolor="#1c2128",plot_bgcolor="#0d1117",xaxis_rangeslider_visible=False,showlegend=False,font=dict(color="#e6edf3"))
        st.plotly_chart(fig,use_container_width=True)
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("Price",f"Rs {current:,.2f}"); c2.metric("Signal",label); c3.metric("Confidence",f"{score}/100"); c4.metric("RS vs Nifty",rs); c5.metric("5d Chg",f"{chg5}%")
        st.markdown(f"{badge_html(color,label)} **{reason}** | {buildup}",unsafe_allow_html=True)
        if ce_df is not None and pe_df is not None:
            pcr=pe_df["openInterest"].sum()/max(ce_df["openInterest"].sum(),1)
            st.markdown(f"**Approx PCR:** {pcr:.2f}")
            a,b=st.columns(2)
            with a: st.markdown("**Top CE OI**"); st.dataframe(ce_df,hide_index=True,use_container_width=True)
            with b: st.markdown("**Top PE OI**"); st.dataframe(pe_df,hide_index=True,use_container_width=True)
        st.markdown("#### Trade ideas (educational)")
        for idea in trade_idea(score,label,rs,near_resist,ad_rising,pattern_broken): st.markdown(f"- {idea}")

with tab5:
    st.subheader("NSE Sectoral / Strategy Indices vs Nifty")
    idx_df=load_indices_table()
    for c in list(idx_df.columns):
        if "365" in str(c): idx_df=idx_df.rename(columns={c:"365 D %CHNG"})
        if "30 D" in str(c): idx_df=idx_df.rename(columns={c:"30 D %CHNG"})
        if str(c).strip().upper().startswith("%CHANGE") or str(c).strip()=="%CHANGE": idx_df=idx_df.rename(columns={c:"%CHANGE"})
        if "CURRENT" in str(c).upper(): idx_df=idx_df.rename(columns={c:"CURRENT"})
        if str(c).strip().upper().startswith("INDEX"): idx_df=idx_df.rename(columns={c:"INDEX"})
    for c in ["CURRENT","%CHANGE","30 D %CHNG","365 D %CHNG"]:
        if c in idx_df.columns: idx_df[c]=pd.to_numeric(idx_df[c],errors="coerce")
    top30=idx_df.dropna(subset=["365 D %CHNG"]).sort_values("365 D %CHNG",ascending=False).head(30)
    st.markdown("#### Top 30 indices by 1-year % change")
    show=[c for c in ["INDEX","CURRENT","%CHANGE","30 D %CHNG","365 D %CHNG"] if c in top30.columns]
    st.dataframe(top30[show],use_container_width=True,height=360,hide_index=True)
    nifty_rows=idx_df[idx_df["INDEX"].astype(str).str.contains("NIFTY 50",case=False,na=False)]
    nifty_1y=float(nifty_rows["365 D %CHNG"].iloc[0]) if len(nifty_rows) else -3.19
    st.info(f"Nifty 50 1Y ≈ **{nifty_1y:.2f}%**. Indices above this are outperforming.")
    sel_idx=st.selectbox("Select index",top30["INDEX"].tolist(),key="idx_sel")
    constituents=[]
    for k,v in INDEX_CONSTITUENTS.items():
        if k.upper() in sel_idx.upper() or sel_idx.upper() in k.upper(): constituents=v; break
    if not constituents:
        for k,v in INDEX_CONSTITUENTS.items():
            key=k.replace("NIFTY ","")
            if key in sel_idx.upper() or any(w in sel_idx.upper() for w in key.split() if len(w)>3): constituents=v; break
    st.markdown(f"#### Top stocks for **{sel_idx}**")
    if not constituents: st.warning("No mapped constituents for this index yet.")
    else:
        rows=[]; nifty_df=get_nifty_data("1y")
        for t in constituents[:8]:
            px=get_live_price(t); df=get_stock_data(t,"1y"); rs=compute_rs(df,nifty_df) if not df.empty else 1.0
            _,label,score,reason=multi_factor_score(t,df,nifty_df) if not df.empty else ("white","—",0,"")
            rows.append({"ticker":t.replace(".NS",""),"price":round(px,2) if not np.isnan(px) else None,"rs_vs_nifty":rs,"confidence":score,"signal":label,"reason":reason})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.markdown("---"); st.markdown("#### RS leaders from indices beating Nifty")
    strong=top30[top30["365 D %CHNG"]>nifty_1y]["INDEX"].tolist(); cands=[]
    for name in strong:
        for k,v in INDEX_CONSTITUENTS.items():
            if k.upper() in name.upper() or name.upper() in k.upper() or any(w in name.upper() for w in k.replace("NIFTY ","").split() if len(w)>3): cands.extend(v)
    cands=list(dict.fromkeys(cands))[:35]
    if st.button("Score top stocks from outperforming indices",key="btn_strong"):
        nifty_df=get_nifty_data("1y"); scored=[]; bar=st.progress(0)
        for i,t in enumerate(cands):
            df=get_stock_data(t,"1y")
            if not df.empty:
                rs=compute_rs(df,nifty_df); _,label,score,reason=multi_factor_score(t,df,nifty_df)
                scored.append({"ticker":t.replace(".NS",""),"price":round(float(df["Close"].iloc[-1]),2),"rs_vs_nifty":rs,"confidence":score,"signal":label,"reason":reason})
            bar.progress((i+1)/max(len(cands),1))
        bar.empty()
        if scored:
            out=pd.DataFrame(scored).sort_values(["rs_vs_nifty","confidence"],ascending=False).head(20)
            st.success("Top 20 by RS vs Nifty"); st.dataframe(out,use_container_width=True,hide_index=True)
            bulls=out[out["signal"]=="BULLISH"].head(5)
            if not bulls.empty:
                st.markdown("##### Recommendations")
                for _,r in bulls.iterrows():
                    st.markdown(f"- **{r['ticker']}** @ {r['price']} — {badge_html('green','BULLISH')} conf {r['confidence']} | RS {r['rs_vs_nifty']}",unsafe_allow_html=True)

st.markdown("---"); st.caption("v1.2 • Progressive scan • Educational only")
