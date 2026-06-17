import re
import math
from io import StringIO
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


# ============================================================
# SAYFA AYARI
# ============================================================

st.set_page_config(
    page_title="S&P 500 Tek Hisse Grafik Paneli",
    page_icon="📊",
    layout="wide",
)


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2.4rem;
        }

        .main-title {
            font-size: 2.1rem;
            font-weight: 850;
            margin-bottom: .15rem;
        }

        .subtle {
            color: #6b7280;
            font-size: .95rem;
            margin-bottom: 1rem;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stPlotlyChart"] {
            margin-top: 1rem;
            margin-bottom: 2.4rem;
        }

        h3 {
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
        }

        .small-info {
            color: #6b7280;
            font-size: 0.88rem;
            line-height: 1.35;
        }

        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# AYARLAR
# ============================================================

PERIODS = {
    "5 Gün": "5d",
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "6 Ay": "6mo",
    "Yılbaşından Beri": "ytd",
    "1 Yıl": "1y",
    "2 Yıl": "2y",
    "5 Yıl": "5y",
    "10 Yıl": "10y",
    "Tüm Zamanlar": "max",
}

INTERVALS = {
    "Günlük": "1d",
    "Haftalık": "1wk",
    "Aylık": "1mo",
}


LOCAL_SP500_FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK-B",
    "LLY", "AVGO", "JPM", "V", "MA", "UNH", "XOM", "COST", "WMT", "HD", "PG",
    "NFLX", "JNJ", "ORCL", "ABBV", "BAC", "KO", "CVX", "MRK", "AMD", "PEP",
    "ADBE", "CRM", "TMO", "MCD", "CSCO", "ABT", "WFC", "ACN", "DHR", "LIN",
    "INTU", "TXN", "QCOM", "IBM", "GE", "AMGN", "CAT", "PM", "NOW", "ISRG",
    "VZ", "NEE", "DIS", "RTX", "UBER", "PFE", "AMAT", "GS", "AXP", "SPGI",
    "PGR", "UNP", "LOW", "BKNG", "HON", "T", "ETN", "BLK", "MS", "TJX",
    "SYK", "LMT", "VRTX", "ELV", "C", "MDT", "ADI", "BSX", "CB", "MMC",
    "ADP", "PANW", "GILD", "REGN", "MU", "PLD", "DE", "SBUX", "KLAC", "UPS",
    "AMT", "CI", "MDLZ", "BMY", "SO", "FI", "NKE", "SCHW", "DUK", "ICE",
    "MO", "INTC", "ZTS", "SHW", "EQIX", "CL", "TT", "WM", "APH", "MCK",
    "CVS", "CME", "PH", "CDNS", "TDG", "CMG", "EOG", "AON", "GD", "MSI",
    "WELL", "MMM", "ITW", "USB", "PNC", "TGT", "MCO", "HCA", "SNPS", "ORLY",
    "APD", "BDX", "MAR", "AJG", "NOC", "EMR", "FDX", "CSX", "ROP", "ECL",
    "FCX", "NXPI", "COF", "ADSK", "PSX", "SLB", "GM", "HLT", "AFL", "TRV",
    "TFC", "NSC", "OKE", "PCAR", "CARR", "AZO", "O", "SRE", "SPG", "DHI",
    "JCI", "MET", "BK", "AEP", "ROST", "KMB", "DLR", "F", "PSA", "NEM",
    "ALL", "CPRT", "GWW", "VLO", "AMP", "PAYX", "URI", "CMI", "MNST", "LHX",
    "MPC", "KMI", "AIG", "PWR", "COR", "MSCI", "FIS", "FICO", "FAST", "OXY",
    "RSG", "LEN", "KDP", "TEL", "A", "KVUE", "PCG", "CTAS", "PRU", "HUM",
    "CCI", "EW", "HES", "AME", "IDXX", "D", "STZ", "YUM", "IQV", "EXC",
    "VRSK", "OTIS", "GEV", "IR", "CTSH", "ODFL", "SYY", "VMC", "ACGL",
    "BKR", "KR", "GIS", "EA", "IT", "XEL", "LULU", "DFS", "DD", "EXR",
    "MLM", "RCL", "CTVA", "ED", "DAL", "NUE", "HPQ", "WAB", "EFX", "HIG",
    "ON", "EIX", "XYL", "VICI", "MTD", "GLW", "TSCO", "EBAY", "AVB", "PPG",
    "ROK", "CDW", "WEC", "MPWR", "GRMN", "ANSS", "FITB", "WTW", "KEYS",
    "BIIB", "CAH", "FTV", "EQR", "FANG", "RMD", "WBD", "DOV", "GPN", "AWK",
    "MTB", "LYB", "CHTR", "PHM", "BR", "WST", "HPE", "TTWO", "STT", "DTE",
    "NTAP", "SBAC", "TROW", "IFF", "ZBH", "CHD", "WAT", "APTV", "VLTO",
    "STE", "PPL", "WY", "ETR", "HBAN", "TRGP", "NVR", "FE", "BRO", "ES",
    "DECK", "CBOE", "HUBB", "BALL", "TYL", "BLDR", "AEE", "TER", "PTC",
    "CINF", "MKC", "LDOS", "RF", "STX", "INVH", "CMS", "PODD", "ARE",
    "GDDY", "ATO", "CLX", "TDY", "DRI", "COO", "CNP", "EQT", "HOLX", "WDC",
    "MOH", "UAL", "LUV", "SYF", "EXPE", "OMC", "BAX", "PKG", "CFG", "K",
    "J", "MAA", "LH", "ESS", "TXT", "FSLR", "MAS", "VTR", "IEX", "AVY",
    "ALGN", "DGX", "BBY", "NRG", "NDAQ", "TSN", "WRB", "LVS", "SWKS",
    "EXPD", "FDS", "AMCR", "CF", "GEN", "MRO", "CAG", "LNT", "IP", "AKAM",
    "SWK", "POOL", "KEY", "KIM", "DOC", "ROL", "TRMB", "SNA", "PNR", "DPZ",
    "JBHT", "EVRG", "VRSN", "UDR", "EG", "ZBRA", "HST", "NI", "JKHY", "AES",
    "LKQ", "KMX", "EMN", "JNPR", "NDSN", "IPG", "ALLE", "INCY", "UHS",
    "CRL", "REG", "AIZ", "EPAM", "FFIV", "TECH", "CTRA", "BXP", "TAP",
    "TFX", "TPR", "HRL", "CHRW", "PAYC", "AOS", "CPB", "FOXA", "FOX",
    "CPT", "NWSA", "NWS", "QRVO", "MOS", "MKTX", "PNW", "APA", "HSIC",
    "FRT", "BWA", "WYNN", "HAS", "MTCH", "GL", "DAY", "RVTY", "GNRC",
    "BF-B", "MGM", "LW", "DVA", "AAL", "IVZ", "CZR", "PARA"
]


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def normalize_symbol(symbol: str) -> str:
    if not symbol:
        return ""
    return symbol.strip().upper().replace(".", "-")


def clean_symbols(values: Iterable[str]) -> List[str]:
    cleaned = []

    for value in values:
        if not value:
            continue

        parts = re.split(r"[\s,;]+", str(value))

        for part in parts:
            symbol = normalize_symbol(part)
            if symbol:
                cleaned.append(symbol)

    return list(dict.fromkeys(cleaned))


def human_number(x) -> str:
    try:
        if x is None or pd.isna(x):
            return "-"

        x = float(x)
        sign = "-" if x < 0 else ""
        x = abs(x)

        for limit, suffix in [
            (1_000_000_000_000, "T"),
            (1_000_000_000, "B"),
            (1_000_000, "M"),
            (1_000, "K"),
        ]:
            if x >= limit:
                return f"{sign}{x / limit:.2f} {suffix}"

        return f"{sign}{x:.2f}"
    except Exception:
        return "-"


def pct_text(x) -> str:
    try:
        if x is None or pd.isna(x):
            return "-"
        return f"{float(x):.2f}%"
    except Exception:
        return "-"


def safe_float(x) -> float:
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.get_level_values(-1)
        except Exception:
            pass

    rename_map = {}

    for col in df.columns:
        col_str = str(col).strip()
        lower = col_str.lower()

        if lower == "open":
            rename_map[col] = "Open"
        elif lower == "high":
            rename_map[col] = "High"
        elif lower == "low":
            rename_map[col] = "Low"
        elif lower == "close":
            rename_map[col] = "Close"
        elif lower == "adj close":
            rename_map[col] = "Adj Close"
        elif lower == "volume":
            rename_map[col] = "Volume"

    df = df.rename(columns=rename_map)

    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            df[col] = np.nan

    for col in ["Open", "High", "Low"]:
        df[col] = df[col].fillna(df["Close"])

    df = df.dropna(subset=["Close"]).sort_index()

    try:
        df.index = pd.to_datetime(df.index)
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
    except Exception:
        pass

    return df


# ============================================================
# S&P 500 LİSTESİ
# ============================================================

@st.cache_data(ttl=21600, show_spinner=False)
def load_sp500_table() -> Tuple[pd.DataFrame, str]:
    sources = [
        "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv",
        "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv",
    ]

    for url in sources:
        try:
            df = pd.read_csv(url)

            symbol_col = None
            name_col = None
            sector_col = None

            for col in df.columns:
                c = str(col).lower()
                if c in ["symbol", "ticker"]:
                    symbol_col = col
                elif c in ["name", "security"]:
                    name_col = col
                elif "sector" in c:
                    sector_col = col

            if symbol_col is None:
                continue

            out = pd.DataFrame()
            out["Symbol"] = df[symbol_col].astype(str).map(normalize_symbol)
            out["Security"] = df[name_col].astype(str) if name_col else out["Symbol"]
            out["Sector"] = df[sector_col].astype(str) if sector_col else "-"
            out["Sub Industry"] = "-"

            out = out.dropna(subset=["Symbol"])
            out = out[out["Symbol"] != ""]
            out = out.drop_duplicates(subset=["Symbol"])
            out = out.sort_values("Symbol").reset_index(drop=True)

            if len(out) > 400:
                return out, "online_csv"

        except Exception:
            pass

    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        tables = pd.read_html(StringIO(response.text), match="Symbol")

        df = tables[0].copy()

        needed_cols = ["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]

        for col in needed_cols:
            if col not in df.columns:
                df[col] = "-"

        out = pd.DataFrame()
        out["Symbol"] = df["Symbol"].astype(str).map(normalize_symbol)
        out["Security"] = df["Security"].astype(str)
        out["Sector"] = df["GICS Sector"].astype(str)
        out["Sub Industry"] = df["GICS Sub-Industry"].astype(str)

        out = out.dropna(subset=["Symbol"])
        out = out[out["Symbol"] != ""]
        out = out.drop_duplicates(subset=["Symbol"])
        out = out.sort_values("Symbol").reset_index(drop=True)

        if len(out) > 400:
            return out, "wikipedia"

    except Exception:
        pass

    fallback_df = pd.DataFrame(
        {
            "Symbol": LOCAL_SP500_FALLBACK,
            "Security": LOCAL_SP500_FALLBACK,
            "Sector": "-",
            "Sub Industry": "-",
        }
    )

    fallback_df = fallback_df.drop_duplicates(subset=["Symbol"])
    fallback_df = fallback_df.sort_values("Symbol").reset_index(drop=True)

    return fallback_df, "local_fallback"


# ============================================================
# FİYAT VERİSİ
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def download_price(symbol: str, period: str, interval: str) -> pd.DataFrame:
    symbol = normalize_symbol(symbol)

    if not symbol:
        return pd.DataFrame()

    attempts = []

    try:
        raw = yf.Ticker(symbol).history(
            period=period,
            interval=interval,
            auto_adjust=True,
            actions=False,
        )
        attempts.append(raw)
    except Exception:
        pass

    try:
        raw = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
            actions=False,
            timeout=30,
        )
        attempts.append(raw)
    except Exception:
        pass

    if period == "max":
        try:
            raw = yf.download(
                tickers=symbol,
                start="1900-01-01",
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False,
                actions=False,
                timeout=30,
            )
            attempts.append(raw)
        except Exception:
            pass

    try:
        raw = yf.download(
            tickers=symbol,
            period="10y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            actions=False,
            timeout=30,
        )
        attempts.append(raw)
    except Exception:
        pass

    for raw in attempts:
        if raw is None or raw.empty:
            continue

        df = standardize_ohlcv(raw)

        if not df.empty and "Close" in df.columns:
            return df

    return pd.DataFrame()


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals(symbol: str) -> pd.DataFrame:
    symbol = normalize_symbol(symbol)

    try:
        info = yf.Ticker(symbol).get_info() or {}
    except Exception:
        info = {}

    trailing_pe = safe_float(info.get("trailingPE"))
    forward_pe = safe_float(info.get("forwardPE"))
    price_to_book = safe_float(info.get("priceToBook"))
    peg = safe_float(info.get("pegRatio") or info.get("trailingPegRatio"))
    profit_margins = safe_float(info.get("profitMargins"))
    roe = safe_float(info.get("returnOnEquity"))
    debt_to_equity = safe_float(info.get("debtToEquity"))
    revenue_growth = safe_float(info.get("revenueGrowth"))

    row = {
        "Sembol": symbol,
        "İsim": info.get("shortName") or info.get("longName") or symbol,
        "Sektör": info.get("sector", "-"),
        "Endüstri": info.get("industry", "-"),
        "Piyasa Değeri": human_number(info.get("marketCap")),
        "F/K": round(trailing_pe, 2) if not math.isnan(trailing_pe) else "-",
        "İleri F/K": round(forward_pe, 2) if not math.isnan(forward_pe) else "-",
        "PD/DD": round(price_to_book, 2) if not math.isnan(price_to_book) else "-",
        "PEG": round(peg, 2) if not math.isnan(peg) else "-",
        "Net Marj": pct_text(profit_margins * 100),
        "ROE": pct_text(roe * 100),
        "Borç/Özkaynak": round(debt_to_equity, 2) if not math.isnan(debt_to_equity) else "-",
        "Gelir Büyümesi": pct_text(revenue_growth * 100),
    }

    return pd.DataFrame([row])


# ============================================================
# TEKNİK ANALİZ
# ============================================================

def calc_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    close = close.astype(float)

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["RSI"] = calc_rsi(df["Close"])

    middle = df["Close"].rolling(20).mean()
    std = df["Close"].rolling(20).std()

    df["BB_MIDDLE"] = middle
    df["BB_UPPER"] = middle + (2 * std)
    df["BB_LOWER"] = middle - (2 * std)

    return df


def metrics_for_symbol(symbol: str, df: pd.DataFrame) -> Dict[str, float]:
    close = df["Close"].dropna().astype(float)

    if close.empty:
        return {
            "Sembol": symbol,
            "Son Fiyat": np.nan,
            "Günlük %": np.nan,
            "Toplam Getiri %": np.nan,
            "Volatilite %": np.nan,
            "Maks. Düşüş %": np.nan,
            "Veri Başlangıcı": "-",
            "Veri Bitişi": "-",
            "Bar Sayısı": 0,
        }

    last = close.iloc[-1]
    previous = close.iloc[-2] if len(close) > 1 else np.nan

    daily = ((last / previous) - 1) * 100 if not pd.isna(previous) and previous != 0 else np.nan
    total_return = ((last / close.iloc[0]) - 1) * 100 if len(close) > 1 and close.iloc[0] != 0 else np.nan

    returns = close.pct_change().dropna()
    volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 2 else np.nan
    drawdown = ((close / close.cummax()) - 1).min() * 100 if len(close) > 2 else np.nan

    return {
        "Sembol": symbol,
        "Son Fiyat": float(last),
        "Günlük %": float(daily) if not pd.isna(daily) else np.nan,
        "Toplam Getiri %": float(total_return) if not pd.isna(total_return) else np.nan,
        "Volatilite %": float(volatility) if not pd.isna(volatility) else np.nan,
        "Maks. Düşüş %": float(drawdown) if not pd.isna(drawdown) else np.nan,
        "Veri Başlangıcı": close.index.min().strftime("%Y-%m-%d"),
        "Veri Bitişi": close.index.max().strftime("%Y-%m-%d"),
        "Bar Sayısı": int(len(close)),
    }


def technical_score(df: pd.DataFrame) -> Tuple[int, str]:
    df = add_indicators(df).dropna(subset=["Close"])

    if df.empty:
        return 0, "Veri yok"

    last = df.iloc[-1]
    score = 0

    if not pd.isna(last.get("SMA20")) and last["Close"] > last["SMA20"]:
        score += 20

    if not pd.isna(last.get("SMA20")) and not pd.isna(last.get("SMA50")) and last["SMA20"] > last["SMA50"]:
        score += 20

    if not pd.isna(last.get("RSI")) and 40 <= last["RSI"] <= 70:
        score += 20

    if not pd.isna(last.get("EMA21")) and last["Close"] > last["EMA21"]:
        score += 20

    if not pd.isna(last.get("SMA200")) and last["Close"] > last["SMA200"]:
        score += 20

    if score >= 75:
        label = "Güçlü"
    elif score >= 45:
        label = "Nötr / izleme"
    else:
        label = "Zayıf"

    return score, label


def position_sizing(
    capital: float,
    risk_pct: float,
    entry: float,
    stop: float,
    target: float,
) -> Optional[Dict[str, float]]:
    risk_amount = capital * risk_pct / 100
    unit_risk = abs(entry - stop)

    if unit_risk <= 0:
        return None

    qty = risk_amount / unit_risk
    position = qty * entry
    loss = abs(entry - stop) * qty
    profit = abs(target - entry) * qty
    rr = profit / loss if loss else np.nan

    return {
        "Sermaye": capital,
        "İşlem Başı Risk %": risk_pct,
        "Maksimum Zarar": risk_amount,
        "Giriş": entry,
        "Stop": stop,
        "Hedef": target,
        "Adet": qty,
        "Pozisyon Büyüklüğü": position,
        "Stop Zarar": loss,
        "Hedef Kâr": profit,
        "Risk/Getiri": rr,
    }


# ============================================================
# GRAFİK
# ============================================================

def make_single_chart(
    symbol: str,
    df: pd.DataFrame,
    chart_type: str,
    show_sma20: bool,
    show_sma50: bool,
    show_sma200: bool,
    show_ema21: bool,
    show_bb: bool,
    show_volume: bool,
    show_rsi: bool,
) -> go.Figure:
    df = add_indicators(df)

    rows = 1 + int(show_volume) + int(show_rsi)

    row_heights = [0.68]

    if show_volume:
        row_heights.append(0.16)

    if show_rsi:
        row_heights.append(0.16)

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.045,
        row_heights=row_heights,
    )

    if chart_type == "Mum":
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name=symbol,
            ),
            row=1,
            col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name=f"{symbol} Fiyat",
                line=dict(width=2.4),
            ),
            row=1,
            col=1,
        )

    overlays = [
        ("SMA20", show_sma20, 1.3),
        ("SMA50", show_sma50, 1.5),
        ("SMA200", show_sma200, 1.8),
        ("EMA21", show_ema21, 1.4),
    ]

    for col_name, enabled, width in overlays:
        if enabled and col_name in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col_name],
                    mode="lines",
                    name=col_name,
                    line=dict(width=width),
                ),
                row=1,
                col=1,
            )

    if show_bb:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_UPPER"],
                mode="lines",
                name="Bollinger Üst",
                line=dict(width=1, dash="dot"),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_LOWER"],
                mode="lines",
                name="Bollinger Alt",
                fill="tonexty",
                line=dict(width=1, dash="dot"),
                opacity=0.22,
            ),
            row=1,
            col=1,
        )

    current_row = 2

    if show_volume:
        volume_colors = np.where(
            df["Close"] >= df["Open"],
            "rgba(22,163,74,.35)",
            "rgba(220,38,38,.35)",
        )

        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"].fillna(0),
                name="Hacim",
                marker_color=volume_colors,
            ),
            row=current_row,
            col=1,
        )

        fig.update_yaxes(title_text="Hacim", row=current_row, col=1)
        current_row += 1

    if show_rsi:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                mode="lines",
                name="RSI",
                line=dict(width=1.8),
            ),
            row=current_row,
            col=1,
        )

        fig.add_hline(y=70, line_dash="dot", opacity=0.45, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dot", opacity=0.45, row=current_row, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=current_row, col=1)

    fig.update_layout(
        height=780,
        margin=dict(l=18, r=18, t=115, b=105),
        title=dict(
            text=f"{symbol} fiyat grafiği",
            x=0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            font=dict(size=18),
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
            itemwidth=70,
        ),
        xaxis_rangeslider_visible=False,
    )

    fig.update_yaxes(title_text="Fiyat", row=1, col=1)

    fig.update_xaxes(
        rangeselector=dict(
            x=0,
            y=1.13,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(245,247,250,0.95)",
            activecolor="rgba(220,38,38,0.18)",
            buttons=[
                dict(count=1, label="1A", step="month", stepmode="backward"),
                dict(count=3, label="3A", step="month", stepmode="backward"),
                dict(count=6, label="6A", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(step="all", label="Tümü"),
            ],
        ),
        row=1,
        col=1,
    )

    return fig


# ============================================================
# BAŞLIK
# ============================================================

st.markdown(
    '<div class="main-title">📊 S&P 500 Tek Hisse Grafik Paneli</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtle">Sembol yaz veya S&P 500 listesinden seç. Sadece tek hissenin grafiği gösterilir. Eğitim amaçlıdır; al-sat tavsiyesi değildir.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# S&P 500 LİSTESİ
# ============================================================

sp500_df, sp500_source = load_sp500_table()
sp500_symbols = set(sp500_df["Symbol"].astype(str).map(normalize_symbol).tolist())


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Panel Ayarları")

    input_mode = st.radio(
        "Hisse seçimi",
        ["Sembol yaz", "S&P 500 listesinden seç"],
        index=0,
    )

    if input_mode == "Sembol yaz":
        symbol_text = st.text_input(
            "Sembol",
            value="AAPL",
            placeholder="Örn: AAPL, MSFT, NVDA, TSLA, BRK-B",
            help="Berkshire için BRK.B değil BRK-B yaz.",
        )

        cleaned = clean_symbols([symbol_text])
        symbol = cleaned[0] if cleaned else ""

    else:
        option_labels = []
        option_to_symbol = {}

        for _, row in sp500_df.iterrows():
            symbol_item = normalize_symbol(row["Symbol"])
            company = str(row["Security"])
            sector = str(row["Sector"])

            label = f"{symbol_item} — {company} — {sector}"
            option_labels.append(label)
            option_to_symbol[label] = symbol_item

        default_label = next(
            (label for label in option_labels if label.startswith("AAPL")),
            option_labels[0],
        )

        selected_label = st.selectbox(
            "S&P 500 hissesi",
            options=option_labels,
            index=option_labels.index(default_label),
        )

        symbol = option_to_symbol[selected_label]

    period_label = st.selectbox(
        "Veri aralığı",
        list(PERIODS.keys()),
        index=list(PERIODS.keys()).index("Tüm Zamanlar"),
    )

    interval_label = st.selectbox(
        "Mum / veri periyodu",
        list(INTERVALS.keys()),
        index=0,
    )

    st.divider()
    st.subheader("Gösterge Ayarları")

    chart_type_option = st.radio(
        "Grafik tipi",
        ["Mum", "Çizgi"],
        index=0,
        horizontal=True,
    )

    show_sma20 = st.checkbox("SMA20", value=True)
    show_sma50 = st.checkbox("SMA50", value=True)
    show_sma200 = st.checkbox("SMA200", value=True)
    show_ema21 = st.checkbox("EMA21", value=False)
    show_bb = st.checkbox("Bollinger", value=False)
    show_volume = st.checkbox("Hacim", value=True)
    show_rsi = st.checkbox("RSI", value=True)

    st.divider()

    if st.button("Veriyi yenile / cache temizle"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f"""
        <div class="small-info">
        S&P 500 liste kaynağı: <b>{sp500_source}</b><br>
        Yüklenen sembol sayısı: <b>{len(sp500_df)}</b><br><br>
        Bu sürümde karşılaştırmalı grafik yoktur. Sadece seçilen tek sembol indirilir.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SEMBOL KONTROL
# ============================================================

symbol = normalize_symbol(symbol)

if not symbol:
    st.warning("Başlamak için bir sembol yaz.")
    st.stop()

if symbol not in sp500_symbols:
    st.info(
        f"{symbol} mevcut S&P 500 listesinde görünmüyor. "
        "Yine de yfinance üzerinden veri deneniyor. Örnek semboller: AAPL, MSFT, NVDA, TSLA, BRK-B."
    )

period = PERIODS[period_label]
interval = INTERVALS[interval_label]


# ============================================================
# VERİ ÇEK
# ============================================================

with st.spinner(f"{symbol} verisi alınıyor..."):
    price_df = download_price(symbol, period, interval)

if price_df.empty:
    st.error(
        f"{symbol} için veri alınamadı. Sembolü kontrol et. "
        "Berkshire için BRK.B değil BRK-B yaz. Sorun devam ederse Veriyi yenile / cache temizle butonuna bas."
    )
    st.stop()


# ============================================================
# METRİKLER
# ============================================================

metrics = metrics_for_symbol(symbol, price_df)
score, score_label = technical_score(price_df)

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(f"{symbol} Son Fiyat", human_number(metrics["Son Fiyat"]))
m2.metric("Günlük Değişim", pct_text(metrics["Günlük %"]))
m3.metric("Seçili Aralık Getiri", pct_text(metrics["Toplam Getiri %"]))
m4.metric("Maks. Düşüş", pct_text(metrics["Maks. Düşüş %"]))
m5.metric("Teknik Skor", f"{score}/100", score_label)

st.caption(
    f"Sembol: {symbol} | "
    f"Veri aralığı: {period_label} | "
    f"Periyot: {interval_label} | "
    f"İlk veri: {metrics['Veri Başlangıcı']} | "
    f"Son veri: {metrics['Veri Bitişi']} | "
    f"Bar sayısı: {metrics['Bar Sayısı']}"
)


# ============================================================
# SEKMELER
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Grafik", "Teknik Özet", "Temel Veriler", "Risk Hesaplayıcı", "S&P 500 Listesi"]
)


with tab1:
    st.markdown(f"### {symbol} Tekli Grafik")

    st.plotly_chart(
        make_single_chart(
            symbol=symbol,
            df=price_df,
            chart_type=chart_type_option,
            show_sma20=show_sma20,
            show_sma50=show_sma50,
            show_sma200=show_sma200,
            show_ema21=show_ema21,
            show_bb=show_bb,
            show_volume=show_volume,
            show_rsi=show_rsi,
        ),
        use_container_width=True,
        theme="streamlit",
    )


with tab2:
    st.markdown("### Teknik Özet")

    summary_df = pd.DataFrame(
        [
            {
                "Sembol": symbol,
                "Son Fiyat": round(metrics["Son Fiyat"], 4) if not pd.isna(metrics["Son Fiyat"]) else "-",
                "Günlük %": round(metrics["Günlük %"], 2) if not pd.isna(metrics["Günlük %"]) else "-",
                "Toplam Getiri %": round(metrics["Toplam Getiri %"], 2) if not pd.isna(metrics["Toplam Getiri %"]) else "-",
                "Volatilite %": round(metrics["Volatilite %"], 2) if not pd.isna(metrics["Volatilite %"]) else "-",
                "Maks. Düşüş %": round(metrics["Maks. Düşüş %"], 2) if not pd.isna(metrics["Maks. Düşüş %"]) else "-",
                "Teknik Skor": score,
                "Teknik Yorum": score_label,
                "Veri Başlangıcı": metrics["Veri Başlangıcı"],
                "Veri Bitişi": metrics["Veri Bitişi"],
                "Bar Sayısı": metrics["Bar Sayısı"],
            }
        ]
    )

    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.caption(
        "Teknik skor basit bir filtredir: Close>SMA20, SMA20>SMA50, RSI dengesi, Close>EMA21 ve Close>SMA200 koşullarından puan toplar."
    )


with tab3:
    st.markdown("### Temel Analiz Tablosu")

    with st.spinner("Temel veriler alınıyor..."):
        fundamentals_df = fetch_fundamentals(symbol)

    st.dataframe(fundamentals_df, use_container_width=True, hide_index=True)

    st.caption(
        "Bazı sembollerde temel veri eksik gelebilir. Bu veri sağlayıcıdan kaynaklanır."
    )


with tab4:
    st.markdown("### Pozisyon ve Risk Hesaplayıcı")

    last_price = float(price_df["Close"].dropna().iloc[-1])

    c1, c2, c3 = st.columns(3)

    with c1:
        capital = st.number_input(
            "Toplam Sermaye",
            min_value=0.0,
            value=100000.0,
            step=1000.0,
        )

        risk_pct = st.number_input(
            "İşlem Başı Risk %",
            min_value=0.1,
            max_value=100.0,
            value=2.0,
            step=0.1,
        )

    with c2:
        entry = st.number_input(
            "Giriş Fiyatı",
            min_value=0.0,
            value=round(last_price, 2),
            step=1.0,
        )

        stop = st.number_input(
            "Stop Fiyatı",
            min_value=0.0,
            value=round(last_price * 0.95, 2),
            step=1.0,
        )

    with c3:
        target = st.number_input(
            "Hedef Fiyat",
            min_value=0.0,
            value=round(last_price * 1.15, 2),
            step=1.0,
        )

        st.write("")

    result = position_sizing(
        capital=capital,
        risk_pct=risk_pct,
        entry=entry,
        stop=stop,
        target=target,
    )

    if result is None:
        st.error("Stop fiyatı giriş fiyatına eşit olamaz.")
    else:
        result_df = pd.DataFrame([result])
        show_result = result_df.copy()

        for col in show_result.columns:
            show_result[col] = show_result[col].map(
                lambda x: round(x, 4) if isinstance(x, (int, float, np.floating)) else x
            )

        st.dataframe(show_result, use_container_width=True, hide_index=True)

        rr = result["Risk/Getiri"]

        if rr < 1.5:
            st.warning("Risk/getiri oranı düşük görünüyor.")
        else:
            st.success("Risk/getiri oranı daha sağlıklı görünüyor.")


with tab5:
    st.markdown("### S&P 500 Hisse Listesi")

    search_text = st.text_input(
        "Listede ara",
        value="",
        placeholder="Örn: Apple, NVIDIA, Financials, AAPL",
    )

    list_df = sp500_df.copy()

    if search_text.strip():
        q = search_text.strip().lower()

        mask = (
            list_df["Symbol"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["Security"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["Sector"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["Sub Industry"].astype(str).str.lower().str.contains(q, na=False)
        )

        list_df = list_df[mask].copy()

    show_df = list_df.rename(
        columns={
            "Symbol": "Sembol",
            "Security": "Şirket",
            "Sector": "Sektör",
            "Sub Industry": "Alt Sektör",
        }
    )

    st.dataframe(show_df, use_container_width=True, hide_index=True)

    st.info(
        "Sembol yazarken Yahoo Finance formatı kullanılır. "
        "Örneğin Berkshire Hathaway için BRK.B değil BRK-B yaz."
    )
