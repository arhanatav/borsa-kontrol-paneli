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
    page_title="S&P 500 Hisse Grafiği",
    page_icon="📈",
    layout="wide",
)


st.markdown(
    """
    <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2.2rem;}
        .main-title {font-size: 2.1rem; font-weight: 850; margin-bottom: .15rem;}
        .subtle {color: #6b7280; font-size: .95rem; margin-bottom: 1rem;}

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stPlotlyChart"] {
            margin-top: 1.1rem;
            margin-bottom: 2.2rem;
        }

        .small-info {
            color: #6b7280;
            font-size: 0.88rem;
            line-height: 1.35;
        }

        h3 {
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
        }

        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SABİTLER
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


FUNDAMENTAL_LIMIT = 1


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


# ============================================================
# S&P 500 LİSTESİ
# ============================================================

@st.cache_data(ttl=21600, show_spinner=False)
def load_sp500_table() -> Tuple[pd.DataFrame, bool]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    try:
        tables = pd.read_html(url, attrs={"id": "constituents"})

        if not tables:
            tables = pd.read_html(url)

        df = tables[0].copy()

        needed_cols = ["Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]
        for col in needed_cols:
            if col not in df.columns:
                df[col] = "-"

        df = df[needed_cols].copy()

        # Wikipedia sembolü BRK.B gibi gelebilir.
        # Yahoo Finance/yfinance tarafında BRK-B formatı kullanılır.
        df["Yahoo Symbol"] = (
            df["Symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(".", "-", regex=False)
        )

        df["Security"] = df["Security"].astype(str)
        df["GICS Sector"] = df["GICS Sector"].astype(str)
        df["GICS Sub-Industry"] = df["GICS Sub-Industry"].astype(str)

        df = df.sort_values("Yahoo Symbol").reset_index(drop=True)

        return df, True

    except Exception:
        fallback = pd.DataFrame(
            [
                {"Symbol": "AAPL", "Security": "Apple Inc.", "GICS Sector": "Information Technology", "GICS Sub-Industry": "-"},
                {"Symbol": "MSFT", "Security": "Microsoft Corp.", "GICS Sector": "Information Technology", "GICS Sub-Industry": "-"},
                {"Symbol": "NVDA", "Security": "NVIDIA Corp.", "GICS Sector": "Information Technology", "GICS Sub-Industry": "-"},
                {"Symbol": "AMZN", "Security": "Amazon.com Inc.", "GICS Sector": "Consumer Discretionary", "GICS Sub-Industry": "-"},
                {"Symbol": "GOOGL", "Security": "Alphabet Inc. Class A", "GICS Sector": "Communication Services", "GICS Sub-Industry": "-"},
                {"Symbol": "META", "Security": "Meta Platforms Inc.", "GICS Sector": "Communication Services", "GICS Sub-Industry": "-"},
                {"Symbol": "TSLA", "Security": "Tesla Inc.", "GICS Sector": "Consumer Discretionary", "GICS Sub-Industry": "-"},
                {"Symbol": "BRK-B", "Security": "Berkshire Hathaway Inc.", "GICS Sector": "Financials", "GICS Sub-Industry": "-"},
                {"Symbol": "JPM", "Security": "JPMorgan Chase & Co.", "GICS Sector": "Financials", "GICS Sub-Industry": "-"},
                {"Symbol": "LLY", "Security": "Eli Lilly and Co.", "GICS Sector": "Health Care", "GICS Sub-Industry": "-"},
            ]
        )

        fallback["Yahoo Symbol"] = fallback["Symbol"]

        return fallback, False


# ============================================================
# VERİ FONKSİYONLARI
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def download_price(symbol: str, period: str, interval: str) -> pd.DataFrame:
    symbol = symbol.strip().upper()

    if not symbol:
        return pd.DataFrame()

    try:
        raw = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=True,
            group_by="ticker",
            progress=False,
            threads=False,
            actions=False,
            timeout=30,
        )
    except Exception:
        return pd.DataFrame()

    if raw is None or raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        level0 = list(raw.columns.get_level_values(0).unique())
        level1 = list(raw.columns.get_level_values(1).unique())

        if symbol in level0:
            df = raw[symbol].copy()
        elif symbol in level1:
            df = raw.xs(symbol, level=1, axis=1).copy()
        else:
            try:
                df = raw.droplevel(0, axis=1).copy()
            except Exception:
                df = raw.copy()
    else:
        df = raw.copy()

    return standardize_ohlcv(df)


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals(symbol: str) -> pd.DataFrame:
    symbol = symbol.strip().upper()

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
# GRAFİK FONKSİYONU
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

st.markdown('<div class="main-title">📊 S&P 500 Tek Hisse Grafik Paneli</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">Sembol yaz, sadece o hissenin grafiği çıksın. Eğitim ve kişisel takip amaçlıdır; al-sat tavsiyesi değildir.</div>',
    unsafe_allow_html=True,
)


# ============================================================
# S&P 500 VERİSİ
# ============================================================

sp500_df, sp500_ok = load_sp500_table()

if not sp500_ok:
    st.warning(
        "S&P 500 listesi internetten alınamadı. Geçici olarak sınırlı yedek liste kullanılıyor. "
        "requirements.txt içinde lxml olduğundan emin ol."
    )

sp500_symbols = set(sp500_df["Yahoo Symbol"].astype(str).str.upper().tolist())


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
            help="S&P 500 sembolü yaz. BRK.B yerine BRK-B yaz.",
        )

        cleaned = clean_symbols([symbol_text])
        symbol = cleaned[0] if cleaned else ""

    else:
        options = []
        symbol_lookup = {}

        for _, row in sp500_df.iterrows():
            yahoo_symbol = str(row["Yahoo Symbol"]).upper()
            label = f"{yahoo_symbol} — {row['Security']}"
            options.append(label)
            symbol_lookup[label] = yahoo_symbol

        default_label = next((x for x in options if x.startswith("AAPL")), options[0])

        selected_label = st.selectbox(
            "S&P 500 hissesi",
            options=options,
            index=options.index(default_label),
        )

        symbol = symbol_lookup[selected_label]

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

    chart_type_option = st.radio("Grafik tipi", ["Mum", "Çizgi"], index=0, horizontal=True)
    show_sma20 = st.checkbox("SMA20", value=True)
    show_sma50 = st.checkbox("SMA50", value=True)
    show_sma200 = st.checkbox("SMA200", value=True)
    show_ema21 = st.checkbox("EMA21", value=False)
    show_bb = st.checkbox("Bollinger", value=False)
    show_volume = st.checkbox("Hacim", value=True)
    show_rsi = st.checkbox("RSI", value=True)

    st.divider()
    st.markdown(
        """
        <div class="small-info">
        Bu sürümde karşılaştırmalı grafik kaldırıldı.  
        Sadece yazdığın veya seçtiğin tek sembol indirilir.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SEMBOL KONTROLÜ
# ============================================================

if not symbol:
    st.warning("Başlamak için bir sembol yaz.")
    st.stop()

symbol = symbol.upper().replace(".", "-")

if symbol not in sp500_symbols:
    st.info(
        f"{symbol} mevcut S&P 500 listesinde görünmüyor. "
        "Yine de yfinance üzerinden veri deneniyor. S&P 500 için örnek: AAPL, MSFT, NVDA, BRK-B."
    )


period = PERIODS[period_label]
interval = INTERVALS[interval_label]


# ============================================================
# FİYAT VERİSİ
# ============================================================

with st.spinner(f"{symbol} verisi alınıyor... ({period_label}, {interval_label})"):
    price_df = download_price(symbol, period, interval)


if price_df.empty:
    st.error(
        f"{symbol} için veri alınamadı. Sembolü kontrol et. "
        "Örnek: BRK.B yerine BRK-B yazmalısın."
    )
    st.stop()


# ============================================================
# ÖZET METRİKLER
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
            symbol,
            price_df,
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
        "Teknik skor basit bir takip filtresidir: Close>SMA20, SMA20>SMA50, RSI dengesi, Close>EMA21 ve Close>SMA200 koşullarından puan toplar."
    )


with tab3:
    st.markdown("### Temel Analiz Tablosu")

    with st.spinner("Temel veriler alınıyor..."):
        fundamentals = fetch_fundamentals(symbol)

    st.dataframe(fundamentals, use_container_width=True, hide_index=True)

    st.caption(
        "Bazı sembollerde temel veri eksik gelebilir. Bu durum veri sağlayıcısından kaynaklanır."
    )


with tab4:
    st.markdown("### Pozisyon ve Risk Hesaplayıcı")

    last_price = float(price_df["Close"].dropna().iloc[-1])

    c1, c2, c3 = st.columns(3)

    with c1:
        capital = st.number_input("Toplam Sermaye", min_value=0.0, value=100000.0, step=1000.0)
        risk_pct = st.number_input("İşlem Başı Risk %", min_value=0.1, max_value=100.0, value=2.0, step=0.1)

    with c2:
        entry = st.number_input("Giriş Fiyatı", min_value=0.0, value=round(last_price, 2), step=1.0)
        stop = st.number_input("Stop Fiyatı", min_value=0.0, value=round(last_price * 0.95, 2), step=1.0)

    with c3:
        target = st.number_input("Hedef Fiyat", min_value=0.0, value=round(last_price * 1.15, 2), step=1.0)
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
            list_df["Yahoo Symbol"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["Security"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["GICS Sector"].astype(str).str.lower().str.contains(q, na=False)
            | list_df["GICS Sub-Industry"].astype(str).str.lower().str.contains(q, na=False)
        )

        list_df = list_df[mask].copy()

    show_sp500 = list_df[
        ["Yahoo Symbol", "Security", "GICS Sector", "GICS Sub-Industry"]
    ].rename(
        columns={
            "Yahoo Symbol": "Yahoo Sembol",
            "Security": "Şirket",
            "GICS Sector": "Sektör",
            "GICS Sub-Industry": "Alt Sektör",
        }
    )

    st.dataframe(show_sp500, use_container_width=True, hide_index=True)

    st.info(
        "Sembol yazarken Yahoo Finance formatı kullanılır. "
        "Örneğin Berkshire Hathaway için BRK.B değil BRK-B yaz."
    )
