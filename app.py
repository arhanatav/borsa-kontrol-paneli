import re
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Borsa & Kripto Pro Panel",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e1a; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; max-width: 100% !important; }
.main-header { background: linear-gradient(135deg, #0d1117 0%, #161b27 50%, #0d1117 100%); border: 1px solid #1e2d40; border-radius: 16px; padding: 20px 28px; margin-bottom: 20px; }
.main-title { font-size: 1.9rem; font-weight: 800; background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; letter-spacing: -0.5px; }
.main-subtitle { color: #4b5563; font-size: 0.82rem; margin-top: 4px; font-weight: 400; }
div[data-testid="stMetric"] { background: linear-gradient(135deg, #111827 0%, #1a2235 100%); border: 1px solid #1e2d40; border-radius: 14px; padding: 16px 18px; box-shadow: 0 4px 24px rgba(0,0,0,0.3); }
div[data-testid="stMetric"]:hover { border-color: #38bdf8; }
div[data-testid="stMetric"] label { color: #6b7280 !important; font-size: 0.78rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.5px; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 1.5rem !important; font-weight: 700 !important; font-family: 'JetBrains Mono', monospace !important; }
section[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e2d40 !important; }
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #cbd5e1 !important; }
.stTabs [data-baseweb="tab-list"] { background: #111827; border-radius: 12px; padding: 4px; border: 1px solid #1e2d40; gap: 2px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #6b7280; font-weight: 500; font-size: 0.85rem; padding: 8px 18px; border: none; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #1e3a5f, #1e2d5f) !important; color: #38bdf8 !important; border: 1px solid #2563eb44 !important; }
.stSelectbox > div > div, .stMultiSelect > div > div { background: #111827 !important; border-color: #1e2d40 !important; color: #f1f5f9 !important; border-radius: 10px !important; }
.stTextArea textarea { background: #111827 !important; border-color: #1e2d40 !important; color: #f1f5f9 !important; border-radius: 10px !important; }
hr { border-color: #1e2d40 !important; }
</style>
""", unsafe_allow_html=True)

# ── S&P 500 listesini Wikipedia'dan çek ────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def get_sp500_tickers():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        return sorted(tickers)
    except Exception:
        # Fallback: hardcoded S&P 500 subset if Wikipedia fails
        return [
            "MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","ABNB","AKAM","ALB","ARE",
            "ALGN","ALLE","LNT","ALL","GOOGL","GOOG","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG",
            "AMT","AWK","AMP","AME","AMGN","APH","ADI","ANSS","AON","APA","AAPL","AMAT","APTV","ACGL",
            "ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC",
            "BK","BBWI","BAX","BDX","WRB","BBY","BIO","TECH","BIIB","BLK","BX","BA","BCH","BMY","AVGO",
            "BR","BRO","BF-B","BLDR","BXP","CHRW","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR",
            "CTLT","CAT","CBOE","CBRE","CDW","CE","CNC","CNX","CDAY","CF","CRL","SCHW","CHTR","CVX","CMG",
            "CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA",
            "CMA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CPAY","CTVA","CSGP","COST","CTRA","CCI",
            "CSX","CMI","CVS","DHR","DHI","DRI","DVA","DAY","DECK","DE","DELL","DAL","DVN","DXCM","FANG",
            "DLR","DFS","DG","DLTR","D","DPZ","DOV","DOW","DHR","DTE","DUK","DD","EMN","ETN","EBAY","ECL",
            "EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS",
            "EL","ETSY","EG","EVRST","ES","EXC","EXPD","EXPE","EXR","XOM","FFIV","FDS","FICO","FAST","FRT",
            "FDX","FIS","FITB","FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN",
            "IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL",
            "HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM",
            "HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF",
            "IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM",
            "JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KLAC","KHC","KR","LHX","LH","LRCX",
            "LW","LVS","LDOS","LEN","LII","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX",
            "MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD","MGM",
            "MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI",
            "MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH",
            "NRG","NUE","NVR","NVDA","NWL","OKTA","ODFL","OMC","ON","OKE","ORCL","OTIS","OXY","ORLY","OGN",
            "PCAR","PKG","PLTR","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PNC",
            "POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM",
            "RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI",
            "CRM","SBAC","SLB","STX","SEE","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV",
            "SWK","SBUX","STT","STLD","STE","SYK","SMCI","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP",
            "TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC",
            "TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN",
            "VRSK","VZ","VRTX","VTRS","VICI","V","VST","VMC","WRK","WAB","WBA","WMT","DIS","WBD","WM","WAT",
            "WEC","WFC","WELL","WST","WDC","WHR","WMB","WTW","GWW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZTS",
        ]

@st.cache_data(ttl=86400, show_spinner=False)
def get_sp500_with_names():
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
        df = tables[0]
        df["Symbol"] = df["Symbol"].str.replace(".", "-", regex=False)
        return dict(zip(df["Symbol"], df["Security"]))
    except Exception:
        return {}

SP500_TICKERS = get_sp500_tickers()

PRESETS = {
    "📊 S&P 500 — Tümü": SP500_TICKERS,
    "🇺🇸 S&P 500 — İlk 50 (Piyasa Değeri)": [
        "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","V",
        "JPM","UNH","XOM","MA","JNJ","AVGO","PG","HD","MRK","COST",
        "ABBV","CVX","KO","PEP","WMT","BAC","CSCO","ACN","MCD","CRM",
        "ABT","LIN","TMO","NKE","ORCL","DHR","TXN","PM","NEE","RTX",
        "HON","SPGI","UPS","AMGN","QCOM","IBM","GS","CAT","INTU","ISRG",
    ],
    "🤖 Yapay Zeka & Yarı İletken": [
        "NVDA","AMD","INTC","AVGO","QCOM","ARM","SMCI","MRVL","AMAT","KLAC",
        "LRCX","MU","MSFT","GOOGL","META","PLTR","AI","SNOW","NET","CRWD",
        "PANW","ZS","DDOG","DELL","HPE","ADI","ON","MCHP","ANET","VRT",
    ],
    "🏦 Finans & Bankacılık": [
        "JPM","BAC","WFC","GS","MS","C","BLK","AXP","V","MA",
        "PYPL","COF","USB","PNC","TFC","SCHW","IBKR","CME","ICE",
        "MCO","SPGI","FIS","FITB","ALLY","SYF","DFS","AIG","BK","STT",
    ],
    "💊 Sağlık & Biyoteknoloji": [
        "JNJ","UNH","PFE","MRK","ABBV","LLY","BMY","AMGN","GILD","CVS",
        "HUM","CI","ABT","TMO","DHR","ISRG","REGN","VRTX","BIIB","MRNA",
        "ILMN","IQV","SYK","MDT","EW","BSX","HOLX","ZBH","BAX","BDX",
    ],
    "⚡ Enerji & Petrol": [
        "XOM","CVX","COP","SLB","EOG","MPC","PSX","VLO","OXY","HES",
        "DVN","FANG","BKR","HAL","APA","MRO","CTRA","LNG","KMI","WMB",
        "OKE","ET","TRGP","NRG","EIX","PCG","D","DUK","NEE","AEE",
    ],
    "🏭 Sanayi & Savunma": [
        "CAT","DE","HON","UPS","FDX","RTX","LMT","NOC","BA","GE",
        "MMM","EMR","ITW","PH","ROK","ETN","AME","TDG","HII","AXON",
        "HWM","TXT","LDOS","BAH","SAIC","FAST","PCAR","CMI","OTIS","CARR",
    ],
    "🛒 Tüketici & Perakende": [
        "WMT","COST","TGT","HD","LOW","NKE","SBUX","MCD","CMG","YUM",
        "DG","DLTR","KR","ETSY","EBAY","PTON","RH","WSM","BBY","ORLY",
        "AZO","TSCO","ROST","TJX","LULU","TPR","RL","PVH","HBI","ANF",
    ],
    "🏠 Gayrimenkul & REIT": [
        "O","AMT","PLD","EQIX","CCI","SPG","PSA","DLR","EXR","VICI",
        "WELL","VTR","NNN","WPC","STAG","FR","EGP","REXR","MAA","ESS",
    ],
    "🌐 İletişim & Medya": [
        "META","GOOGL","NFLX","DIS","CMCSA","T","VZ","CHTR","TMUS",
        "WBD","PARA","FOXA","NYT","ZM","TWLO","LUMN","NWSA","IPG","OMC",
    ],
    "🇹🇷 BIST 100": [
        "AEFES.IS","AGHOL.IS","AKBNK.IS","AKSA.IS","AKSEN.IS","ARCLK.IS","ASELS.IS","ASTOR.IS",
        "BIMAS.IS","BRSAN.IS","CCOLA.IS","CIMSA.IS","DOAS.IS","DOHOL.IS","ECILC.IS","EKGYO.IS",
        "ENKAI.IS","EREGL.IS","FROTO.IS","GARAN.IS","GUBRF.IS","HALKB.IS","HEKTS.IS","ISCTR.IS",
        "KCHOL.IS","KONTR.IS","KRDMD.IS","MAVI.IS","MGROS.IS","ODAS.IS","OTKAR.IS","OYAKC.IS",
        "PETKM.IS","PGSUS.IS","SAHOL.IS","SARKY.IS","SASA.IS","SISE.IS","SKBNK.IS","SOKM.IS",
        "TAVHL.IS","TCELL.IS","THYAO.IS","TKFEN.IS","TOASO.IS","TSKB.IS","TTKOM.IS","TUPRS.IS",
        "ULKER.IS","VAKBN.IS","VESTL.IS","YKBNK.IS","ZOREN.IS","AKBNK.IS","ENJSA.IS","TTRAK.IS",
    ],
    "🇹🇷 BIST Seçkinler": [
        "THYAO.IS","ASELS.IS","KCHOL.IS","GARAN.IS","EREGL.IS","BIMAS.IS","TUPRS.IS","SISE.IS",
        "SAHOL.IS","TOASO.IS","ARCLK.IS","FROTO.IS","VESTL.IS","AKBNK.IS","YKBNK.IS","ISCTR.IS",
        "HALKB.IS","VAKBN.IS","TCELL.IS","TTKOM.IS","PETKM.IS","TKFEN.IS","OTKAR.IS","ENKAI.IS",
    ],
    "₿ Kripto Büyük": [
        "BTC-USD","ETH-USD","BNB-USD","SOL-USD","XRP-USD","ADA-USD","AVAX-USD","DOT-USD",
        "MATIC-USD","LINK-USD","LTC-USD","BCH-USD","TON-USD","NEAR-USD","APT-USD","ETC-USD",
    ],
    "₿ Kripto DeFi": [
        "UNI-USD","AAVE-USD","CRV-USD","MKR-USD","SNX-USD","COMP-USD","SUSHI-USD",
        "DOGE-USD","SHIB-USD","TRX-USD","ATOM-USD","ICP-USD","FIL-USD","XLM-USD",
    ],
    "📦 ETF Geniş Piyasa": ["SPY","QQQ","VOO","IWM","DIA","VTI","SCHB","RSP","MDY","IJR","VXF","ITOT"],
    "🌍 ETF Global": ["EFA","EEM","VWO","GXC","EWJ","EWG","EWU","INDA","EWZ","FXI","VEA","IEMG"],
    "🏗️ ETF Sektör": ["XLK","XLF","XLE","XLV","XLI","XLY","XLP","XLU","XLB","XLRE","XLC","XBI"],
    "🥇 Emtia & Altın": ["GLD","SLV","GDX","GDXJ","USO","UNG","PDBC","DJP","CPER","PALL"],
    "📊 Yüksek Temettü": ["O","MAIN","ARCC","T","VZ","MO","PM","KO","PEP","JNJ","PG","MMM","IBM","CVX","XOM","ABBV","MRK","BMY"],
    "🚀 Büyüme & Momentum": ["SHOP","SQ","ROKU","COIN","HOOD","RBLX","U","LYFT","UBER","ABNB","DASH","RIVN","PLTR","AFRM","OPEN"],
}

# Veri aralığı — "Tümü/Max" = start=1900 ile yfinance elindeki en eski veriye gider
PERIODS = {
    "1 Ay":    {"days": 31,   "label": "1mo"},
    "3 Ay":    {"days": 93,   "label": "3mo"},
    "6 Ay":    {"days": 186,  "label": "6mo"},
    "1 Yıl":   {"days": 366,  "label": "1y"},
    "2 Yıl":   {"days": 731,  "label": "2y"},
    "5 Yıl":   {"days": 1827, "label": "5y"},
    "10 Yıl":  {"days": 3653, "label": "10y"},
    "Tümü (IPO'dan beri)": {"days": None, "label": "max"},
}
INTERVALS = {"Günlük": "1d", "Haftalık": "1wk", "Aylık": "1mo"}

PLOTLY_BASE = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font=dict(family="Inter, monospace", color="#94a3b8", size=11),
    margin=dict(l=70, r=20, t=60, b=20),
    hoverlabel=dict(bgcolor="#111827", bordercolor="#1e2d40", font=dict(color="#f1f5f9", size=12)),
)
LEGEND_STYLE = dict(bgcolor="#111827", bordercolor="#1e2d40", borderwidth=1, font=dict(size=10))
COLORS = {
    "blue":"#38bdf8","purple":"#818cf8","green":"#4ade80","red":"#f87171",
    "yellow":"#fbbf24","orange":"#fb923c","cyan":"#22d3ee","pink":"#f472b6",
    "teal":"#2dd4bf","gray":"#4b5563","white":"#f1f5f9",
}
MULTI_COLORS = ["#38bdf8","#818cf8","#4ade80","#fbbf24","#f472b6","#fb923c","#22d3ee","#a78bfa","#2dd4bf","#f87171","#e2e8f0","#84cc16"]

# ── UTILS ──────────────────────────────────────────────────────────────────
def clean_symbols(values):
    cleaned = []
    for value in values:
        if not value: continue
        for part in re.split(r"[\s,;|\n]+", str(value)):
            part = part.strip().upper()
            if part: cleaned.append(part)
    return list(dict.fromkeys(cleaned))

def human_number(x):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)): return "-"
        x = float(x); sign = "-" if x < 0 else ""; ax = abs(x)
        for limit, suffix in [(1e12,"T"),(1e9,"B"),(1e6,"M"),(1e3,"K")]:
            if ax >= limit: return f"{sign}{ax/limit:.2f}{suffix}"
        return f"{sign}{ax:.2f}"
    except Exception: return "-"

def pct_text(x, decimals=2):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)): return "-"
        return f"{float(x):.{decimals}f}%"
    except Exception: return "-"

def safe_float(x):
    try:
        if x is None: return np.nan
        v = float(x); return np.nan if math.isnan(v) else v
    except Exception: return np.nan

def fmt(x, decimals=2, suffix=""):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)): return "-"
        return f"{float(x):.{decimals}f}{suffix}"
    except Exception: return "-"

# ── DATA ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def download_prices(symbols_tuple, period_label, interval):
    symbols = list(symbols_tuple)
    period_info = PERIODS[period_label]

    def _download(**kwargs):
        try:
            return yf.download(
                tickers=symbols, auto_adjust=False, group_by="ticker",
                progress=False, threads=True, **kwargs,
            )
        except Exception:
            return None

    if period_info["days"] is None:
        # "Tümü" — 1900'den bugüne = yfinance'in elindeki tüm tarih
        end = datetime.utcnow() + timedelta(days=1)
        raw = _download(start="1900-01-01", end=end.strftime("%Y-%m-%d"), interval=interval)
    else:
        end = datetime.utcnow() + timedelta(days=1)
        start = end - timedelta(days=period_info["days"])
        raw = _download(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval=interval)
        if raw is None or raw.empty:
            raw = _download(period=period_info["label"], interval=interval)

    result = {}
    if raw is None or raw.empty: return result

    if isinstance(raw.columns, pd.MultiIndex):
        level0 = list(raw.columns.get_level_values(0).unique())
        level1 = list(raw.columns.get_level_values(1).unique())
        if any(s in level0 for s in symbols):
            for sym in symbols:
                if sym in level0:
                    df = raw[sym].copy()
                    if not df.empty:
                        r = standardize_ohlcv(df)
                        if r is not None: result[sym] = r
        elif any(s in level1 for s in symbols):
            for sym in symbols:
                if sym in level1:
                    try:
                        df = raw.xs(sym, level=1, axis=1).copy()
                        if not df.empty:
                            r = standardize_ohlcv(df)
                            if r is not None: result[sym] = r
                    except Exception: pass
    else:
        r = standardize_ohlcv(raw.copy())
        if r is not None: result[symbols[0]] = r
    return result

def standardize_ohlcv(df):
    df = df.copy()
    df.columns = [str(c).strip().title() for c in df.columns]
    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]
    for col in ["Open","High","Low","Close","Volume"]:
        if col not in df.columns: df[col] = np.nan
    df = df.dropna(subset=["Close"])
    if df.empty: return None
    return df.sort_index()

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals(symbols_tuple):
    rows = []
    for sym in list(symbols_tuple)[:25]:
        try: info = yf.Ticker(sym).get_info() or {}
        except Exception: info = {}
        def g(key): return info.get(key)
        def sf(key): return safe_float(g(key))
        def pct(key):
            v = sf(key); return pct_text(v*100) if not math.isnan(v) else "-"
        def r2(key):
            v = sf(key); return round(v,2) if not math.isnan(v) else "-"
        rows.append({
            "Sembol":sym, "Şirket":g("shortName") or g("longName") or sym,
            "Sektör":g("sector") or "-", "Endüstri":g("industry") or "-",
            "Borsa":g("exchange") or "-", "Para Birimi":g("currency") or "-",
            "Ülke":g("country") or "-", "Çalışan":human_number(g("fullTimeEmployees")),
            "Piyasa Değeri":human_number(g("marketCap")),
            "Fiyat":fmt(g("currentPrice") or g("regularMarketPrice")),
            "52H Yüksek":fmt(g("fiftyTwoWeekHigh")), "52H Düşük":fmt(g("fiftyTwoWeekLow")),
            "Hedef Fiyat":fmt(g("targetMeanPrice")), "Analist":g("recommendationKey") or "-",
            "Beta":r2("beta"), "F/K (İz)":r2("trailingPE"), "F/K (İleri)":r2("forwardPE"),
            "PD/DD":r2("priceToBook"), "PEG":r2("pegRatio"),
            "FD/FAVÖK":r2("enterpriseToEbitda"), "FD/Satış":r2("enterpriseToRevenue"),
            "Fiy/Satış":r2("priceToSalesTrailing12Months"),
            "EPS (İz)":fmt(g("trailingEps")), "EPS (İleri)":fmt(g("forwardEps")),
            "EPS Büyüme":pct("earningsGrowth"), "Gelir Büyümesi":pct("revenueGrowth"),
            "Brüt Marj":pct("grossMargins"), "FAVÖK Marj":pct("ebitdaMargins"),
            "Net Marj":pct("profitMargins"), "ROE":pct("returnOnEquity"),
            "ROA":pct("returnOnAssets"), "Borç/Özkaynak":r2("debtToEquity"),
            "Cari Oran":r2("currentRatio"), "Hızlı Oran":r2("quickRatio"),
            "Temettü %":pct("dividendYield"), "Ödeme Oranı":pct("payoutRatio"),
            "Gelir":human_number(g("totalRevenue")), "FAVÖK":human_number(g("ebitda")),
            "Net Kâr":human_number(g("netIncomeToCommon")), "Nakit":human_number(g("totalCash")),
            "Toplam Borç":human_number(g("totalDebt")),
            "Serbest NK":human_number(g("freeCashflow")),
        })
    return pd.DataFrame(rows)

# ── INDICATORS ─────────────────────────────────────────────────────────────
def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow; sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig

def calc_stoch_rsi(close, rsi_period=14, stoch_period=14, k=3, d=3):
    rsi = calc_rsi(close, rsi_period)
    rsi_min = rsi.rolling(stoch_period).min(); rsi_max = rsi.rolling(stoch_period).max()
    stoch = 100*(rsi-rsi_min)/(rsi_max-rsi_min).replace(0, np.nan)
    return stoch.rolling(k).mean(), stoch.rolling(k).mean().rolling(d).mean()

def calc_atr(df, period=14):
    h=df["High"]; l=df["Low"]; c=df["Close"]; pc=c.shift(1)
    tr = pd.concat([(h-l),(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def add_indicators(df):
    df = df.copy(); c = df["Close"]
    df["SMA20"]=c.rolling(20).mean(); df["SMA50"]=c.rolling(50).mean()
    df["SMA100"]=c.rolling(100).mean(); df["SMA200"]=c.rolling(200).mean()
    df["EMA9"]=c.ewm(span=9,adjust=False).mean(); df["EMA21"]=c.ewm(span=21,adjust=False).mean()
    df["EMA55"]=c.ewm(span=55,adjust=False).mean()
    df["RSI"]=calc_rsi(c); df["RSI9"]=calc_rsi(c,9)
    mid=c.rolling(20).mean(); std=c.rolling(20).std()
    df["BB_MID"]=mid; df["BB_UPPER"]=mid+2*std; df["BB_LOWER"]=mid-2*std
    df["BB_WIDTH"]=(df["BB_UPPER"]-df["BB_LOWER"])/mid*100
    df["MACD"],df["MACD_SIGNAL"],df["MACD_HIST"]=calc_macd(c)
    df["STOCH_K"],df["STOCH_D"]=calc_stoch_rsi(c)
    df["ATR"]=calc_atr(df); df["ATR_PCT"]=df["ATR"]/c*100
    df["OBV"]=(np.sign(c.diff().fillna(0))*df["Volume"].fillna(0)).cumsum()
    df["VWAP"]=(df["Volume"]*(df["High"]+df["Low"]+df["Close"])/3).cumsum()/df["Volume"].cumsum()
    df["ROC10"]=c.pct_change(10)*100; df["ROC20"]=c.pct_change(20)*100
    df["WILLR"]=-100*(df["High"].rolling(14).max()-c)/(df["High"].rolling(14).max()-df["Low"].rolling(14).min()).replace(0,np.nan)
    df["CCI"]=(c-c.rolling(20).mean())/(0.015*c.rolling(20).apply(lambda x: np.mean(np.abs(x-np.mean(x)))))
    return df

def metrics_for_symbol(symbol, df):
    close = df["Close"].dropna()
    empty = {"Sembol":symbol,"Son Fiyat":np.nan,"Günlük %":np.nan,"Toplam Getiri %":np.nan,
             "Volatilite %":np.nan,"Maks. Düşüş %":np.nan,"Sharpe":np.nan,"Sortino":np.nan}
    if close.empty: return empty
    last=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else np.nan
    daily=((last/prev)-1)*100 if prev and not math.isnan(prev) else np.nan
    total=((last/float(close.iloc[0]))-1)*100 if len(close)>1 else np.nan
    rets=close.pct_change().dropna()
    vol=float(rets.std()*np.sqrt(252)*100) if len(rets)>2 else np.nan
    dd=float(((close/close.cummax())-1).min()*100) if len(close)>2 else np.nan
    mean_r=rets.mean(); std_r=rets.std()
    sharpe=float(mean_r/std_r*np.sqrt(252)) if std_r else np.nan
    neg=rets[rets<0]; sortino=float(mean_r/neg.std()*np.sqrt(252)) if len(neg)>2 else np.nan
    return {"Sembol":symbol,"Son Fiyat":last,"Günlük %":daily,"Toplam Getiri %":total,
            "Volatilite %":vol,"Maks. Düşüş %":dd,"Sharpe":sharpe,"Sortino":sortino}

def technical_score(df):
    df2=add_indicators(df).dropna(subset=["Close"])
    usable=df2.dropna(subset=["SMA20","SMA50","RSI","MACD","MACD_SIGNAL","STOCH_K"])
    if usable.empty: return 0,"Yetersiz Veri",[]
    L=usable.iloc[-1]; score=0; signals=[]
    checks=[
        (L["Close"]>L["SMA20"],10,"↑SMA20","↓SMA20"),
        (L["Close"]>L["SMA50"],10,"↑SMA50","↓SMA50"),
        (L["Close"]>L["SMA200"],15,"↑SMA200","↓SMA200"),
        (L["SMA20"]>L["SMA50"],10,"✦Altın","✦Ölüm"),
        (L["MACD"]>L["MACD_SIGNAL"],15,"MACD↑","MACD↓"),
        (L["MACD_HIST"]>0,10,"Hist↑",None),
        (40<=L["RSI"]<=65,10,"RSI✓",None),
        (L["RSI"]<35,5,"Aşırı-sat",None),
        (L["Close"]>L["EMA21"],10,"↑EMA21",None),
        (L["STOCH_K"]>L["STOCH_D"] and L["STOCH_K"]<80,10,"Stoch↑",None),
    ]
    for cond,pts,pos,neg in checks:
        if cond: score+=pts; signals.append(pos)
        elif neg: signals.append(neg)
    label="🟢 Güçlü Al" if score>=70 else "🟡 Nötr" if score>=50 else "🟠 Dikkatli" if score>=30 else "🔴 Zayıf"
    return score, label, signals

# ── CHARTS ─────────────────────────────────────────────────────────────────
def make_single_chart(symbol, df, chart_type, opts):
    df=add_indicators(df)
    show_vol=opts.get("vol",True); show_rsi=opts.get("rsi",True)
    show_macd=opts.get("macd",False); show_stoch=opts.get("stoch",False)
    show_sma20=opts.get("sma20",True); show_sma50=opts.get("sma50",True)
    show_sma100=opts.get("sma100",False); show_sma200=opts.get("sma200",False)
    show_ema9=opts.get("ema9",False); show_ema21=opts.get("ema21",False)
    show_ema55=opts.get("ema55",False); show_bb=opts.get("bb",False)
    show_vwap=opts.get("vwap",False); show_obv=opts.get("obv",False)

    sub_count=1+int(show_vol)+int(show_rsi)+int(show_macd)+int(show_stoch)+int(show_obv)
    heights=[0.52]
    if show_vol: heights.append(0.12)
    if show_rsi: heights.append(0.12)
    if show_macd: heights.append(0.12)
    if show_stoch: heights.append(0.12)
    if show_obv: heights.append(0.12)
    total=sum(heights); heights=[h/total for h in heights]

    fig=make_subplots(rows=sub_count,cols=1,shared_xaxes=True,vertical_spacing=0.025,row_heights=heights)

    if chart_type=="Mum":
        fig.add_trace(go.Candlestick(
            x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],name=symbol,
            increasing_line_color=COLORS["green"],decreasing_line_color=COLORS["red"],
            increasing_fillcolor="rgba(74,222,128,0.4)",decreasing_fillcolor="rgba(248,113,113,0.4)",
        ),row=1,col=1)
    else:
        fig.add_trace(go.Scatter(x=df.index,y=df["Close"],mode="lines",name=symbol,
            line=dict(color=COLORS["blue"],width=2),
            fill="tozeroy",fillcolor="rgba(56,189,248,0.08)"),row=1,col=1)

    for col_name,enabled,color,width,dash in [
        ("SMA20",show_sma20,COLORS["yellow"],1.4,"dot"),
        ("SMA50",show_sma50,COLORS["orange"],1.6,"solid"),
        ("SMA100",show_sma100,COLORS["pink"],1.4,"dash"),
        ("SMA200",show_sma200,COLORS["purple"],1.8,"solid"),
        ("EMA9",show_ema9,COLORS["cyan"],1.2,"dot"),
        ("EMA21",show_ema21,COLORS["teal"],1.4,"solid"),
        ("EMA55",show_ema55,COLORS["blue"],1.6,"dash"),
    ]:
        if enabled and col_name in df.columns:
            fig.add_trace(go.Scatter(x=df.index,y=df[col_name],mode="lines",
                name=col_name,line=dict(color=color,width=width,dash=dash)),row=1,col=1)

    if show_bb:
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_UPPER"],mode="lines",
            name="BB Üst",line=dict(color=COLORS["gray"],width=1,dash="dot"),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_LOWER"],mode="lines",name="Bollinger",
            line=dict(color=COLORS["gray"],width=1,dash="dot"),
            fill="tonexty",fillcolor="rgba(75,85,99,0.1)"),row=1,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["BB_MID"],mode="lines",
            name="BB Mid",line=dict(color=COLORS["gray"],width=0.8,dash="dash"),showlegend=False),row=1,col=1)

    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(go.Scatter(x=df.index,y=df["VWAP"],mode="lines",
            name="VWAP",line=dict(color=COLORS["pink"],width=1.4,dash="dashdot")),row=1,col=1)

    cur=2
    if show_vol:
        vol_colors=["rgba(74,222,128,0.5)" if c>=o else "rgba(248,113,113,0.5)"
                    for c,o in zip(df["Close"],df["Open"])]
        fig.add_trace(go.Bar(x=df.index,y=df["Volume"].fillna(0),name="Hacim",
            marker_color=vol_colors,showlegend=False),row=cur,col=1)
        fig.update_yaxes(title_text="Hacim",title_font=dict(size=9),row=cur,col=1); cur+=1

    if show_rsi:
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI"],mode="lines",name="RSI(14)",
            line=dict(color=COLORS["blue"],width=1.6)),row=cur,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["RSI9"],mode="lines",name="RSI(9)",
            line=dict(color=COLORS["cyan"],width=1,dash="dot")),row=cur,col=1)
        for lvl,col in [(70,"rgba(248,113,113,0.5)"),(30,"rgba(74,222,128,0.5)"),(50,"rgba(75,85,99,0.4)")]:
            fig.add_hline(y=lvl,line_dash="dot",line_color=col,row=cur,col=1)
        fig.update_yaxes(range=[0,100],title_text="RSI",title_font=dict(size=9),row=cur,col=1); cur+=1

    if show_macd:
        hist_colors=["rgba(74,222,128,0.6)" if v>=0 else "rgba(248,113,113,0.6)"
                     for v in df["MACD_HIST"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index,y=df["MACD_HIST"],name="Hist",
            marker_color=hist_colors,showlegend=False),row=cur,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD"],mode="lines",name="MACD",
            line=dict(color=COLORS["blue"],width=1.5)),row=cur,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["MACD_SIGNAL"],mode="lines",name="Signal",
            line=dict(color=COLORS["orange"],width=1.5)),row=cur,col=1)
        fig.add_hline(y=0,line_dash="dot",line_color="rgba(75,85,99,0.5)",row=cur,col=1)
        fig.update_yaxes(title_text="MACD",title_font=dict(size=9),row=cur,col=1); cur+=1

    if show_stoch:
        fig.add_trace(go.Scatter(x=df.index,y=df["STOCH_K"],mode="lines",name="Stoch K",
            line=dict(color=COLORS["blue"],width=1.5)),row=cur,col=1)
        fig.add_trace(go.Scatter(x=df.index,y=df["STOCH_D"],mode="lines",name="Stoch D",
            line=dict(color=COLORS["orange"],width=1.5,dash="dot")),row=cur,col=1)
        for lvl,col in [(80,"rgba(248,113,113,0.5)"),(20,"rgba(74,222,128,0.5)")]:
            fig.add_hline(y=lvl,line_dash="dot",line_color=col,row=cur,col=1)
        fig.update_yaxes(range=[0,100],title_text="Stoch",title_font=dict(size=9),row=cur,col=1); cur+=1

    if show_obv:
        fig.add_trace(go.Scatter(x=df.index,y=df["OBV"],mode="lines",name="OBV",
            line=dict(color=COLORS["purple"],width=1.5),
            fill="tozeroy",fillcolor="rgba(129,140,248,0.1)"),row=cur,col=1)
        fig.update_yaxes(title_text="OBV",title_font=dict(size=9),row=cur,col=1)

    # Legend sağ altta, rangeselector sol üstte — çakışmıyor
    fig.update_layout(
        height=840, xaxis_rangeslider_visible=False, hovermode="x unified",
        title=dict(text=f"<b>{symbol}</b>",font=dict(size=16,color="#f1f5f9"),x=0.5,xanchor="center"),
        legend=dict(orientation="h",yanchor="bottom",y=-0.06,xanchor="center",x=0.5,**LEGEND_STYLE),
        **PLOTLY_BASE,
    )
    fig.update_yaxes(title_text="Fiyat",title_font=dict(size=9),row=1,col=1)
    for i in range(1,sub_count+1):
        fig.update_xaxes(gridcolor="#1e2d40",linecolor="#1e2d40",row=i,col=1)
        fig.update_yaxes(gridcolor="#1e2d40",linecolor="#1e2d40",tickfont=dict(size=10),row=i,col=1)
    # Sadece 4 buton — taşma yok
    fig.update_xaxes(rangeselector=dict(
        bgcolor="#0d1117",activecolor="#1e3a5f",bordercolor="#1e2d40",borderwidth=1,
        font=dict(color="#94a3b8",size=11),
        buttons=[
            dict(count=1, label="1Y",  step="year",  stepmode="backward"),
            dict(count=5, label="5Y",  step="year",  stepmode="backward"),
            dict(count=10,label="10Y", step="year",  stepmode="backward"),
            dict(step="all",label="Tümü"),
        ]
    ),row=1,col=1)
    return fig

def make_correlation_heatmap(price_dict):
    closes=pd.concat({sym:df["Close"] for sym,df in price_dict.items() if not df.empty},axis=1).dropna()
    if closes.shape[1]<2: return None
    corr=closes.pct_change().dropna().corr(); syms=list(corr.columns); vals=corr.values
    colorscale=[[0.0,"#b91c1c"],[0.25,"#ef4444"],[0.5,"#111827"],[0.75,"#22c55e"],[1.0,"#15803d"]]
    text=[[f"{vals[i][j]:.2f}" for j in range(len(syms))] for i in range(len(syms))]
    fig=go.Figure(go.Heatmap(z=vals,x=syms,y=syms,text=text,texttemplate="%{text}",
        colorscale=colorscale,zmin=-1,zmax=1,
        colorbar=dict(tickfont=dict(color="#94a3b8"),outlinecolor="#1e2d40")))
    fig.update_layout(
        height=max(350,60*len(syms)),
        title=dict(text="<b>Korelasyon Matrisi</b>",font=dict(size=14,color="#f1f5f9")),
        xaxis=dict(gridcolor="#1e2d40",tickfont=dict(color="#94a3b8")),
        yaxis=dict(gridcolor="#1e2d40",tickfont=dict(color="#94a3b8")),
        **PLOTLY_BASE,
    )
    return fig

def make_risk_return_scatter(df):
    df=df.dropna(subset=["Volatilite %","Toplam Getiri %"])
    if df.empty: return None
    colors=[COLORS["green"] if r>0 else COLORS["red"] for r in df["Toplam Getiri %"]]
    fig=go.Figure(go.Scatter(
        x=df["Volatilite %"],y=df["Toplam Getiri %"],mode="markers+text",
        text=df["Sembol"],textposition="top center",textfont=dict(size=10,color="#94a3b8"),
        marker=dict(size=12,color=colors,line=dict(color="#0d1117",width=1.5)),
        hovertemplate="<b>%{text}</b><br>Volatilite: %{x:.1f}%<br>Getiri: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=0,line_dash="dot",line_color="rgba(75,85,99,0.5)")
    fig.update_layout(
        height=420,
        title=dict(text="<b>Risk / Getiri Dağılımı</b>",font=dict(size=14,color="#f1f5f9")),
        xaxis=dict(title="Volatilite (yıllık %)",gridcolor="#1e2d40",linecolor="#1e2d40"),
        yaxis=dict(title="Toplam Getiri %",gridcolor="#1e2d40",linecolor="#1e2d40"),
        **PLOTLY_BASE,
    )
    return fig

def position_sizing(capital,risk_pct,entry,stop,target):
    unit_risk=abs(entry-stop)
    if unit_risk<=0: return None
    risk_amount=capital*risk_pct/100; qty=risk_amount/unit_risk; pos_size=qty*entry
    loss=unit_risk*qty; profit=abs(target-entry)*qty; rr=profit/loss if loss else np.nan
    kelly=(rr*0.5-0.5)/rr if rr and rr>1 else 0
    return {"Toplam Sermaye":capital,"Risk %":risk_pct,"Max Zarar":round(risk_amount,2),
            "Giriş":entry,"Stop":stop,"Hedef":target,"Adet/Lot":round(qty,4),
            "Pozisyon Büyüklüğü":round(pos_size,2),"Pozisyon %":round(pos_size/capital*100,2),
            "Stop Zarar":round(loss,2),"Hedef Kâr":round(profit,2),
            "R:R Oranı":round(rr,2),"Kelly %":round(kelly*100,2)}

# ════════════════════════════════════════
# UI
# ════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <div class="main-title">📊 Borsa & Kripto Pro Panel</div>
  <div class="main-subtitle">S&P 500 · BIST 100 · Kripto · ETF · Teknik & Temel Analiz — Eğitim amaçlıdır, al-sat tavsiyesi değildir.</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Panel Ayarları")
    preset_name = st.selectbox("Hazır Liste", list(PRESETS.keys()), index=0)
    preset_list = PRESETS[preset_name]

    # S&P 500 listesinde default 10 hisse, diğerlerinde 20
    default_count = min(10 if preset_name == "📊 S&P 500 — Tümü" else 20, len(preset_list))
    selected_symbols = st.multiselect("Sembol Seç", preset_list,
        default=preset_list[:default_count])
    extra_text = st.text_area("Ek Sembol Ekle", value="",
        placeholder="Örn: META, AMD, BTC-USD, THYAO.IS")
    period_label   = st.selectbox("Veri Aralığı", list(PERIODS.keys()), index=5)
    interval_label = st.selectbox("Periyot", list(INTERVALS.keys()), index=0)

    # "Tümü" seçilince haftalık daha stabil
    if period_label == "Tümü (IPO'dan beri)" and interval_label == "Günlük":
        st.info("📌 'Tümü' için haftalık periyot önerilir — daha hızlı ve eksiksiz veri.")

    st.divider()
    st.markdown("### 📉 Teknik Göstergeler")
    chart_type = st.radio("Grafik Tipi", ["Mum","Çizgi"], horizontal=True)
    st.markdown("**Hareketli Ortalamalar**")
    c1,c2 = st.columns(2)
    with c1:
        sma20=st.checkbox("SMA20",value=True); sma50=st.checkbox("SMA50",value=True)
        sma100=st.checkbox("SMA100"); sma200=st.checkbox("SMA200")
    with c2:
        ema9=st.checkbox("EMA9"); ema21=st.checkbox("EMA21")
        ema55=st.checkbox("EMA55"); bb=st.checkbox("Bollinger")
    st.markdown("**Alt Paneller**")
    c3,c4=st.columns(2)
    with c3:
        vol=st.checkbox("Hacim",value=True); rsi=st.checkbox("RSI",value=True); macd=st.checkbox("MACD")
    with c4:
        stoch=st.checkbox("Stoch RSI"); obv=st.checkbox("OBV"); vwap=st.checkbox("VWAP")

indicator_opts=dict(sma20=sma20,sma50=sma50,sma100=sma100,sma200=sma200,
    ema9=ema9,ema21=ema21,ema55=ema55,bb=bb,vol=vol,rsi=rsi,macd=macd,stoch=stoch,obv=obv,vwap=vwap)

symbols = clean_symbols(selected_symbols + [extra_text])
interval = INTERVALS[interval_label]

if not symbols:
    st.warning("Lütfen en az bir sembol seç."); st.stop()

with st.spinner("📡 Veriler alınıyor…"):
    prices = download_prices(tuple(symbols), period_label, interval)

valid_symbols=list(prices.keys())
missing=[s for s in symbols if s not in valid_symbols]
if missing: st.warning(f"Veri alınamadı: {', '.join(missing)}")
if not valid_symbols: st.error("Hiçbir sembol için veri alınamadı."); st.stop()

# Veri başlangıç tarihini göster
if valid_symbols:
    first_sym = valid_symbols[0]
    first_date = prices[first_sym].index[0]
    last_date  = prices[first_sym].index[-1]
    st.caption(f"📅 {first_sym}: {first_date.strftime('%d.%m.%Y')} — {last_date.strftime('%d.%m.%Y')} · {len(prices[first_sym])} bar")

all_metrics=pd.DataFrame([metrics_for_symbol(s,prices[s]) for s in valid_symbols])
score_rows=[]
for sym in valid_symbols:
    try:
        score,label,signals=technical_score(prices[sym])
        score_rows.append({"Sembol":sym,"Teknik Skor":score,"Sinyal":label,"Detay":" | ".join(signals[:6])})
    except Exception:
        score_rows.append({"Sembol":sym,"Teknik Skor":0,"Sinyal":"-","Detay":"-"})
score_df=pd.DataFrame(score_rows)
summary_df=all_metrics.merge(score_df,on="Sembol",how="left")

first=valid_symbols[0]; fm=metrics_for_symbol(first,prices[first])
c1,c2,c3,c4,c5,c6=st.columns(6)
c1.metric(f"💹 {first}",human_number(fm["Son Fiyat"]))
c2.metric("Günlük Değişim",pct_text(fm["Günlük %"]))
c3.metric("Dönem Getirisi",pct_text(fm["Toplam Getiri %"]))
c4.metric("Maks. Düşüş",pct_text(fm["Maks. Düşüş %"]))
c5.metric("Yıllık Vol.",pct_text(fm["Volatilite %"]))
c6.metric("Sharpe",fmt(fm["Sharpe"]))

tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "📈 Grafikler","🔍 Teknik Tarama","📊 Temel Analiz","🔗 Korelasyon","⚖️ Risk/Getiri","💰 Pozisyon"
])

with tab1:
    chart_sym=st.selectbox("Sembol Seç",valid_symbols,index=0,key="csym")
    st.plotly_chart(make_single_chart(chart_sym,prices[chart_sym],chart_type,indicator_opts),
        use_container_width=True,theme=None)
    dfi=add_indicators(prices[chart_sym]).dropna(subset=["Close"])
    if not dfi.empty:
        L=dfi.iloc[-1]
        ic1,ic2,ic3,ic4,ic5,ic6=st.columns(6)
        ic1.metric("ATR(14)",fmt(L.get("ATR")))
        ic2.metric("ATR %",fmt(L.get("ATR_PCT"),2,"%"))
        ic3.metric("BB Genişliği",fmt(L.get("BB_WIDTH"),2,"%"))
        ic4.metric("ROC(10d)",fmt(L.get("ROC10"),2,"%"))
        ic5.metric("Williams %R",fmt(L.get("WILLR"),1))
        ic6.metric("CCI(20)",fmt(L.get("CCI"),1))

with tab2:
    st.markdown("### 🔍 Teknik Özet")
    disp=summary_df.copy()
    for col in ["Son Fiyat","Günlük %","Toplam Getiri %","Volatilite %","Maks. Düşüş %","Sharpe","Sortino"]:
        disp[col]=disp[col].map(lambda x: round(x,2) if isinstance(x,float) and not math.isnan(x) else "-")
    st.dataframe(disp.sort_values("Teknik Skor",ascending=False),use_container_width=True,hide_index=True)
    st.divider()
    st.markdown("### 📐 Detaylı Gösterge Tablosu")
    tech_rows=[]
    for sym in valid_symbols:
        try:
            dft=add_indicators(prices[sym]).dropna(subset=["Close"])
            if dft.empty: continue
            L=dft.iloc[-1]
            tech_rows.append({
                "Sembol":sym,"Fiyat":fmt(L["Close"]),"RSI(14)":fmt(L.get("RSI")),
                "RSI(9)":fmt(L.get("RSI9")),"MACD":fmt(L.get("MACD")),
                "MACD Sig":fmt(L.get("MACD_SIGNAL")),"MACD Hist":fmt(L.get("MACD_HIST")),
                "Stoch K":fmt(L.get("STOCH_K")),"Stoch D":fmt(L.get("STOCH_D")),
                "ATR":fmt(L.get("ATR")),"ATR%":fmt(L.get("ATR_PCT"),2),
                "Williams%R":fmt(L.get("WILLR")),"CCI":fmt(L.get("CCI"),1),
                "ROC10%":fmt(L.get("ROC10"),2),"SMA20":fmt(L.get("SMA20")),
                "SMA50":fmt(L.get("SMA50")),"SMA200":fmt(L.get("SMA200")),
                "EMA9":fmt(L.get("EMA9")),"EMA21":fmt(L.get("EMA21")),
                "BB Üst":fmt(L.get("BB_UPPER")),"BB Alt":fmt(L.get("BB_LOWER")),
                "BB W%":fmt(L.get("BB_WIDTH"),2),"VWAP":fmt(L.get("VWAP")),
            })
        except Exception: pass
    if tech_rows:
        st.dataframe(pd.DataFrame(tech_rows),use_container_width=True,hide_index=True)

with tab3:
    st.markdown("### 📊 Temel Analiz")
    with st.spinner("Temel veriler çekiliyor…"):
        fundamentals=fetch_fundamentals(tuple(valid_symbols))
    if not fundamentals.empty:
        sub1,sub2,sub3,sub4,sub5=st.tabs(["🏢 Şirket","📌 Fiyat","📐 Değerleme","📈 Karlılık","💵 Finansallar"])
        cat1=["Sembol","Şirket","Sektör","Endüstri","Borsa","Para Birimi","Ülke","Çalışan"]
        cat2=["Sembol","Fiyat","52H Yüksek","52H Düşük","Hedef Fiyat","Analist","Beta","Piyasa Değeri"]
        cat3=["Sembol","F/K (İz)","F/K (İleri)","PD/DD","PEG","FD/FAVÖK","FD/Satış","Fiy/Satış","EPS (İz)","EPS (İleri)","EPS Büyüme"]
        cat4=["Sembol","Brüt Marj","FAVÖK Marj","Net Marj","ROE","ROA","Borç/Özkaynak","Cari Oran","Hızlı Oran","Ödeme Oranı"]
        cat5=["Sembol","Gelir","FAVÖK","Net Kâr","Nakit","Toplam Borç","Serbest NK","Gelir Büyümesi","Temettü %"]
        def sc(df,cols): return df[[c for c in cols if c in df.columns]]
        with sub1: st.dataframe(sc(fundamentals,cat1),use_container_width=True,hide_index=True)
        with sub2: st.dataframe(sc(fundamentals,cat2),use_container_width=True,hide_index=True)
        with sub3: st.dataframe(sc(fundamentals,cat3),use_container_width=True,hide_index=True)
        with sub4: st.dataframe(sc(fundamentals,cat4),use_container_width=True,hide_index=True)
        with sub5: st.dataframe(sc(fundamentals,cat5),use_container_width=True,hide_index=True)
    st.caption("Kripto ve bazı BIST hisselerinde temel veri eksik olabilir.")

with tab4:
    st.markdown("### 🔗 Korelasyon Matrisi")
    if len(valid_symbols)>=2:
        fig_corr=make_correlation_heatmap(prices)
        if fig_corr:
            st.plotly_chart(fig_corr,use_container_width=True,theme=None)
            st.caption("1 = tam pozitif · -1 = tam negatif. Günlük getiri bazlı.")
    else:
        st.info("Korelasyon için en az 2 sembol seç.")

with tab5:
    st.markdown("### ⚖️ Risk / Getiri Dağılımı")
    fig_rr=make_risk_return_scatter(all_metrics)
    if fig_rr: st.plotly_chart(fig_rr,use_container_width=True,theme=None)
    st.divider()
    st.markdown("### 📊 Getiri Dağılımı (Histogram)")
    hist_sym=st.selectbox("Sembol",valid_symbols,key="hist_sym")
    ret_series=prices[hist_sym]["Close"].pct_change().dropna()*100
    fig_hist=go.Figure(go.Histogram(x=ret_series,nbinsx=80,
        marker_color="rgba(56,189,248,0.6)",marker_line=dict(color=COLORS["blue"],width=0.5)))
    fig_hist.add_vline(x=float(ret_series.mean()),line_dash="dash",line_color=COLORS["green"],
        annotation_text=f"Ort: {ret_series.mean():.2f}%",annotation_font_color=COLORS["green"])
    fig_hist.update_layout(height=380,
        title=dict(text=f"<b>{hist_sym}</b> — Günlük Getiri Dağılımı",font=dict(color="#f1f5f9",size=14)),
        xaxis=dict(title="Günlük Getiri %",gridcolor="#1e2d40",linecolor="#1e2d40"),
        yaxis=dict(title="Frekans",gridcolor="#1e2d40",linecolor="#1e2d40"),**PLOTLY_BASE)
    st.plotly_chart(fig_hist,use_container_width=True,theme=None)

with tab6:
    st.markdown("### 💰 Pozisyon & Risk Hesaplayıcı")
    c1,c2,c3=st.columns(3)
    with c1:
        capital=st.number_input("Toplam Sermaye",min_value=0.0,value=100000.0,step=1000.0)
        risk_pct=st.number_input("İşlem Başı Risk %",min_value=0.1,max_value=100.0,value=2.0,step=0.1)
    with c2:
        entry=st.number_input("Giriş Fiyatı",min_value=0.0,value=100.0,step=0.5)
        stop=st.number_input("Stop Fiyatı",min_value=0.0,value=95.0,step=0.5)
    with c3:
        target=st.number_input("Hedef Fiyat",min_value=0.0,value=115.0,step=0.5)
        commission_pct=st.number_input("Komisyon %",min_value=0.0,value=0.1,step=0.01)
    result=position_sizing(capital,risk_pct,entry,stop,target)
    if result is None:
        st.error("Stop fiyatı giriş fiyatına eşit olamaz.")
    else:
        commission=result["Pozisyon Büyüklüğü"]*commission_pct/100*2
        result["Komisyon (2 yön)"]=round(commission,2)
        result["Net Kâr (kom.)"]=round(result["Hedef Kâr"]-commission,2)
        st.dataframe(pd.DataFrame([result]).T.rename(columns={0:"Değer"}),use_container_width=True)
        rr=result["R:R Oranı"]
        if rr>=2.0: st.success(f"✅ R:R = {rr:.2f} — Sağlıklı.")
        elif rr>=1.5: st.warning(f"⚠️ R:R = {rr:.2f} — Kabul edilebilir.")
        else: st.error(f"❌ R:R = {rr:.2f} — Düşük.")
        st.info(f"💡 Kelly Kriteri: Sermayenin **{result['Kelly %']:.1f}%**'ini kullan.")
