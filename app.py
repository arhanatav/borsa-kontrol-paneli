import re
import math
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


# ============================================================
# SAYFA AYARI
# ============================================================

st.set_page_config(
    page_title="Borsa & Kripto Kontrol Paneli",
    page_icon="📈",
    layout="wide",
)


st.markdown(
    """
    <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        .main-title {font-size: 2.1rem; font-weight: 850; margin-bottom: .1rem;}
        .subtle {color: #6b7280; font-size: .95rem; margin-bottom: 1rem;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.04);
        }
        .small-info {
            color: #6b7280;
            font-size: 0.88rem;
            line-height: 1.35;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HAZIR LİSTELER
# ============================================================

PRESETS = {
    "Popüler ABD Hisseleri": [
        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "GOOG",
        "AMD", "NFLX", "AVGO", "ORCL", "CRM", "ADBE", "INTC", "QCOM",
        "MU", "IBM", "NOW", "SHOP", "UBER", "ABNB", "PYPL", "SQ",
        "COIN", "PLTR", "SNOW", "NET", "CRWD", "PANW", "DDOG", "MDB",
        "ROKU", "RBLX", "HOOD", "SOFI", "RIVN", "LCID", "NIO", "BABA",
        "JD", "PDD", "DIS", "WBD", "PARA", "PEP", "KO", "MCD", "SBUX",
        "NKE", "COST", "WMT", "TGT", "HD", "LOW", "JPM", "BAC", "GS",
        "MS", "V", "MA", "AXP", "UNH", "LLY", "NVO", "JNJ", "PFE",
        "MRK", "XOM", "CVX", "OXY", "F", "GM", "GE", "CAT", "BA"
    ],
    "ABD Mega Cap": [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA",
        "BRK-B", "LLY", "AVGO", "JPM", "V", "MA", "UNH", "XOM", "COST",
        "WMT", "HD", "PG", "NFLX", "JNJ", "ORCL", "ABBV", "CRM", "BAC",
        "KO", "CVX", "MRK", "AMD", "PEP", "ADBE", "TMO", "LIN", "MCD"
    ],
    "Yapay Zeka & Çip": [
        "NVDA", "AMD", "AVGO", "TSM", "ASML", "ARM", "MU", "MRVL",
        "QCOM", "INTC", "AMAT", "LRCX", "KLAC", "TER", "ON", "NXPI",
        "SMCI", "DELL", "HPE", "ANET", "PLTR", "SNOW", "CRWD", "NET",
        "PANW", "DDOG", "MDB", "ORCL", "MSFT", "GOOGL", "META", "AMZN",
        "AI", "SOUN", "BBAI", "PATH"
    ],
    "ETF / Endeks": [
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "VEA", "VWO",
        "VGT", "XLK", "SMH", "SOXX", "ARKK", "ARKW", "XLF", "XLE",
        "XLV", "XLY", "XLP", "XLI", "XLU", "XLC", "XLB", "TLT",
        "IEF", "SHY", "HYG", "LQD", "GLD", "SLV", "USO", "UNG"
    ],
    "Kripto": [
        "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
        "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "DOT-USD",
        "TRX-USD", "TON11419-USD", "BCH-USD", "LTC-USD", "UNI-USD",
        "ATOM-USD", "ETC-USD", "APT21794-USD", "NEAR-USD", "ICP-USD",
        "FIL-USD", "HBAR-USD", "VET-USD", "AAVE-USD", "MKR-USD",
        "RNDR-USD", "INJ-USD", "OP-USD", "ARB11841-USD", "SUI20947-USD"
    ],
    "BIST Popüler": [
        "THYAO.IS", "ASELS.IS", "TUPRS.IS", "SISE.IS", "KCHOL.IS",
        "SAHOL.IS", "BIMAS.IS", "EREGL.IS", "FROTO.IS", "TOASO.IS",
        "GARAN.IS", "AKBNK.IS", "YKBNK.IS", "ISCTR.IS", "TCELL.IS",
        "ENKAI.IS", "KOZAL.IS", "PETKM.IS", "ARCLK.IS", "PGSUS.IS",
        "TAVHL.IS", "MGROS.IS", "SASA.IS", "HEKTS.IS", "ASTOR.IS",
        "KONTR.IS", "CWENE.IS", "MIATK.IS", "ODAS.IS", "ALARK.IS",
        "DOAS.IS", "EKGYO.IS", "KRDMD.IS", "VESTL.IS", "BRSAN.IS",
        "OYAKC.IS", "ULKER.IS", "CCOLA.IS", "AEFES.IS", "MAVI.IS",
        "ENJSA.IS", "AKSA.IS", "CIMSA.IS", "ISMEN.IS", "HALKB.IS",
        "VAKBN.IS", "GUBRF.IS", "KOZAA.IS", "IPEKE.IS", "DOHOL.IS"
    ],
}


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


MAX_SYMBOL_COUNT = 60
DOWNLOAD_CHUNK_SIZE = 20
FUNDAMENTAL_LIMIT = 40


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def clean_symbols(values: Iterable[str]) -> List[str]:
    cleaned: List[str] = []

    for value in values:
        if not value:
            continue

        parts = re.split(r"[\s,;]+", str(value))
        for part in parts:
            symbol = part.strip().upper()
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


def chunks(items: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def standardize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        return df

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


def extract_symbol_frame(raw: pd.DataFrame, symbols: List[str]) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}

    if raw is None or raw.empty:
        return result

    if isinstance(raw.columns, pd.MultiIndex):
        level0 = list(raw.columns.get_level_values(0).unique())
        level1 = list(raw.columns.get_level_values(1).unique())

        if any(sym in level0 for sym in symbols):
            for sym in symbols:
                if sym in level0:
                    df = raw[sym].copy()
                    df = standardize_ohlcv(df)
                    if not df.empty:
                        result[sym] = df

        elif any(sym in level1 for sym in symbols):
            for sym in symbols:
                if sym in level1:
                    df = raw.xs(sym, level=1, axis=1).copy()
                    df = standardize_ohlcv(df)
                    if not df.empty:
                        result[sym] = df
    else:
        if len(symbols) == 1:
            df = standardize_ohlcv(raw.copy())
            if not df.empty:
                result[symbols[0]] = df

    return result


# ============================================================
# VERİ FONKSİYONLARI
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def download_prices(symbols_tuple: Tuple[str, ...], period: str, interval: str) -> Dict[str, pd.DataFrame]:
    symbols = list(dict.fromkeys([s.strip().upper() for s in symbols_tuple if s.strip()]))
    final_result: Dict[str, pd.DataFrame] = {}

    if not symbols:
        return final_result

    for batch in chunks(symbols, DOWNLOAD_CHUNK_SIZE):
        try:
            raw = yf.download(
                tickers=batch,
                period=period,
                interval=interval,
                auto_adjust=True,
                group_by="ticker",
                progress=False,
                threads=True,
                actions=False,
                timeout=30,
            )
            batch_result = extract_symbol_frame(raw, batch)
            final_result.update(batch_result)
        except Exception:
            for sym in batch:
                try:
                    raw_single = yf.download(
                        tickers=sym,
                        period=period,
                        interval=interval,
                        auto_adjust=True,
                        group_by="ticker",
                        progress=False,
                        threads=False,
                        actions=False,
                        timeout=30,
                    )
                    single_result = extract_symbol_frame(raw_single, [sym])
                    final_result.update(single_result)
                except Exception:
                    pass

    return {
        symbol: df
        for symbol, df in final_result.items()
        if df is not None and not df.empty and "Close" in df.columns
    }


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals(symbols_tuple: Tuple[str, ...]) -> pd.DataFrame:
    rows = []

    for sym in list(symbols_tuple)[:FUNDAMENTAL_LIMIT]:
        try:
            info = yf.Ticker(sym).get_info() or {}
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

        rows.append(
            {
                "Sembol": sym,
                "İsim": info.get("shortName") or info.get("longName") or sym,
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
        )

    return pd.DataFrame(rows)


# ============================================================
# TEKNİK ANALİZ FONKSİYONLARI
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


def position_sizing(capital: float, risk_pct: float, entry: float, stop: float, target: float) -> Optional[Dict[str, float]]:
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
# GRAFİK FONKSİYONLARI
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
        vertical_spacing=0.035,
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
        height=720,
        margin=dict(l=12, r=12, t=48, b=20),
        title=f"{symbol} fiyat grafiği",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_rangeslider_visible=False,
    )

    fig.update_yaxes(title_text="Fiyat", row=1, col=1)

    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1A", step="month", stepmode="backward"),
                dict(count=3, label="3A", step="month", stepmode="backward"),
                dict(count=6, label="6A", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(step="all", label="Tümü"),
            ]
        ),
        row=1,
        col=1,
    )

    return fig


def make_compare_chart(price_dict: Dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()

    for symbol, df in price_dict.items():
        if df is None or df.empty or "Close" not in df.columns:
            continue

        close = df["Close"].dropna().astype(float)
        if close.empty or close.iloc[0] == 0:
            continue

        normalized = close / close.iloc[0] * 100

        fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized,
                mode="lines",
                name=symbol,
                line=dict(width=2.1),
            )
        )

    fig.add_hline(y=100, line_dash="dot", opacity=0.4)

    fig.update_layout(
        height=650,
        margin=dict(l=12, r=12, t=48, b=20),
        title="Karşılaştırmalı performans — her sembol kendi ilk verisinden 100 kabul edildi",
        yaxis_title="Normalize değer",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1A", step="month", stepmode="backward"),
                dict(count=3, label="3A", step="month", stepmode="backward"),
                dict(count=6, label="6A", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(step="all", label="Tümü"),
            ]
        )
    )

    return fig


def make_drawdown_chart(price_dict: Dict[str, pd.DataFrame]) -> go.Figure:
    fig = go.Figure()

    for symbol, df in price_dict.items():
        if df is None or df.empty or "Close" not in df.columns:
            continue

        close = df["Close"].dropna().astype(float)
        if close.empty:
            continue

        drawdown = (close / close.cummax() - 1) * 100

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode="lines",
                name=symbol,
                line=dict(width=1.8),
            )
        )

    fig.update_layout(
        height=520,
        margin=dict(l=12, r=12, t=48, b=20),
        title="Maksimum düşüş grafiği",
        yaxis_title="Düşüş %",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    return fig


# ============================================================
# ÜST BAŞLIK
# ============================================================

st.markdown('<div class="main-title">📊 Borsa & Kripto Kontrol Paneli</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">Eğitim ve kişisel takip amaçlıdır. Al-sat tavsiyesi değildir.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("Panel Ayarları")

    preset_name = st.selectbox("Hazır liste", list(PRESETS.keys()), index=0)
    preset_symbols = PRESETS[preset_name]

    default_count = min(6, len(preset_symbols))
    selected_symbols = st.multiselect(
        "Sembol seç",
        options=preset_symbols,
        default=preset_symbols[:default_count],
        help="Birden fazla sembol seçebilirsin.",
    )

    extra_symbols_text = st.text_area(
        "Ek sembol ekle",
        value="",
        placeholder="Örn: META, AMD, BTC-USD, THYAO.IS",
        help="Virgül, boşluk veya satır ile ayır.",
    )

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

    max_symbol_count = st.slider(
        "Aynı anda indirilecek maksimum sembol",
        min_value=5,
        max_value=MAX_SYMBOL_COUNT,
        value=30,
        step=5,
        help="Sayı arttıkça panel yavaşlayabilir. Streamlit Cloud için 20-30 daha sağlıklıdır.",
    )

    st.divider()
    st.subheader("Gösterge Ayarları")

    chart_type_option = st.radio("Tekli grafik tipi", ["Mum", "Çizgi"], index=0, horizontal=True)
    show_sma20 = st.checkbox("SMA20", value=True)
    show_sma50 = st.checkbox("SMA50", value=True)
    show_sma200 = st.checkbox("SMA200", value=True)
    show_ema21 = st.checkbox("EMA21", value=False)
    show_bb = st.checkbox("Bollinger", value=False)
    show_volume = st.checkbox("Hacim", value=True)
    show_rsi = st.checkbox("RSI", value=True)

    st.divider()
    st.markdown(
        f"""
        <div class="small-info">
        <b>Not:</b> Grafikteki <b>Tümü</b> butonu sadece indirilen verinin tamamını gösterir.
        Bu sürümde varsayılan veri aralığı <b>Tüm Zamanlar</b> yapıldı.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# VERİYİ HAZIRLA
# ============================================================

symbols = clean_symbols(selected_symbols + [extra_symbols_text])

if not symbols:
    st.warning("Başlamak için en az bir sembol seç veya ek sembol yaz.")
    st.stop()

if len(symbols) > max_symbol_count:
    st.warning(
        f"{len(symbols)} sembol seçildi. Performans için ilk {max_symbol_count} sembol indiriliyor."
    )
    symbols = symbols[:max_symbol_count]

period = PERIODS[period_label]
interval = INTERVALS[interval_label]

with st.spinner(f"Veriler alınıyor... ({len(symbols)} sembol, {period_label}, {interval_label})"):
    prices = download_prices(tuple(symbols), period, interval)

valid_symbols = list(prices.keys())
missing_symbols = [s for s in symbols if s not in valid_symbols]

if missing_symbols:
    st.warning("Veri alınamayan semboller: " + ", ".join(missing_symbols))

if not valid_symbols:
    st.error("Hiçbir sembol için veri alınamadı. Sembol formatını kontrol et.")
    st.stop()


# ============================================================
# ÖZET METRİKLER
# ============================================================

all_metrics = pd.DataFrame([metrics_for_symbol(sym, prices[sym]) for sym in valid_symbols])

score_rows = []
for sym in valid_symbols:
    score, label = technical_score(prices[sym])
    score_rows.append({"Sembol": sym, "Teknik Skor": score, "Teknik Yorum": label})

score_df = pd.DataFrame(score_rows)
summary_df = all_metrics.merge(score_df, on="Sembol", how="left")

selected_for_metrics = valid_symbols[0]
first_metrics = metrics_for_symbol(selected_for_metrics, prices[selected_for_metrics])

m1, m2, m3, m4 = st.columns(4)
m1.metric(f"{selected_for_metrics} Son Fiyat", human_number(first_metrics["Son Fiyat"]))
m2.metric("Günlük Değişim", pct_text(first_metrics["Günlük %"]))
m3.metric("Seçili Aralık Getiri", pct_text(first_metrics["Toplam Getiri %"]))
m4.metric("Maks. Düşüş", pct_text(first_metrics["Maks. Düşüş %"]))

st.caption(
    f"İndirilen sembol sayısı: {len(valid_symbols)} | "
    f"Veri aralığı: {period_label} | "
    f"Periyot: {interval_label}"
)


# ============================================================
# SEKMELER
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Grafikler", "Sembol Taraması", "Temel Veriler", "Risk Hesaplayıcı", "Veri Kontrol"]
)


with tab1:
    if len(valid_symbols) > 1:
        st.markdown("### Çoklu Sembol Karşılaştırması")
        st.plotly_chart(make_compare_chart(prices), use_container_width=True, theme="streamlit")

        with st.expander("Maksimum düşüş grafiğini göster"):
            st.plotly_chart(make_drawdown_chart(prices), use_container_width=True, theme="streamlit")

    st.markdown("### Tekli Detaylı Grafik")
    chart_symbol = st.selectbox("Grafikte gösterilecek sembol", valid_symbols, index=0)

    st.plotly_chart(
        make_single_chart(
            chart_symbol,
            prices[chart_symbol],
            chart_type_option,
            show_sma20,
            show_sma50,
            show_sma200,
            show_ema21,
            show_bb,
            show_volume,
            show_rsi,
        ),
        use_container_width=True,
        theme="streamlit",
    )


with tab2:
    st.markdown("### Teknik Özet ve Performans")

    display_df = summary_df.copy()
    numeric_cols = ["Son Fiyat", "Günlük %", "Toplam Getiri %", "Volatilite %", "Maks. Düşüş %"]

    sort_col = st.selectbox(
        "Sıralama ölçütü",
        ["Toplam Getiri %", "Günlük %", "Volatilite %", "Maks. Düşüş %", "Teknik Skor", "Bar Sayısı"],
        index=0,
    )

    ascending = st.checkbox("Küçükten büyüğe sırala", value=False)

    sorted_df = display_df.sort_values(sort_col, ascending=ascending, na_position="last")

    for col in numeric_cols:
        sorted_df[col] = sorted_df[col].map(lambda x: round(x, 2) if not pd.isna(x) else "-")

    st.dataframe(
        sorted_df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Teknik skor basit bir takip filtresidir: Close>SMA20, SMA20>SMA50, RSI dengesi, Close>EMA21 ve Close>SMA200 koşullarından puan toplar."
    )


with tab3:
    st.markdown("### Temel Analiz Tablosu")

    st.caption(
        f"Temel veriler en fazla ilk {FUNDAMENTAL_LIMIT} sembol için çekilir. "
        "Kripto ve bazı BIST sembollerinde temel veri eksik gelebilir."
    )

    with st.spinner("Temel veriler alınıyor..."):
        fundamentals = fetch_fundamentals(tuple(valid_symbols))

    st.dataframe(fundamentals, use_container_width=True, hide_index=True)


with tab4:
    st.markdown("### Pozisyon ve Risk Hesaplayıcı")

    c1, c2, c3 = st.columns(3)

    with c1:
        capital = st.number_input("Toplam Sermaye", min_value=0.0, value=100000.0, step=1000.0)
        risk_pct = st.number_input("İşlem Başı Risk %", min_value=0.1, max_value=100.0, value=2.0, step=0.1)

    with c2:
        entry = st.number_input("Giriş Fiyatı", min_value=0.0, value=100.0, step=1.0)
        stop = st.number_input("Stop Fiyatı", min_value=0.0, value=95.0, step=1.0)

    with c3:
        target = st.number_input("Hedef Fiyat", min_value=0.0, value=115.0, step=1.0)
        st.write("")

    result = position_sizing(capital, risk_pct, entry, stop, target)

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
    st.markdown("### Veri Kontrol")

    data_quality_rows = []
    for sym in valid_symbols:
        df = prices[sym]
        data_quality_rows.append(
            {
                "Sembol": sym,
                "İlk Tarih": df.index.min().strftime("%Y-%m-%d") if not df.empty else "-",
                "Son Tarih": df.index.max().strftime("%Y-%m-%d") if not df.empty else "-",
                "Satır Sayısı": len(df),
                "Son Kapanış": round(float(df["Close"].dropna().iloc[-1]), 4) if not df["Close"].dropna().empty else "-",
            }
        )

    st.dataframe(pd.DataFrame(data_quality_rows), use_container_width=True, hide_index=True)

    with st.expander("Seçili semboller"):
        st.write(", ".join(valid_symbols))

    st.info(
        "Tüm zamanlar seçiliyken veri başlangıcı her sembole göre değişir. "
        "Örneğin yeni halka arz edilen veya yeni listelenen varlıkların geçmişi doğal olarak daha kısa olur."
    )
