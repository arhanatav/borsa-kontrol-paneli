import re
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Borsa & Kripto Kontrol Paneli",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
        .main-title {font-size: 2.1rem; font-weight: 800; margin-bottom: .1rem;}
        .subtle {color: #6b7280; font-size: .95rem;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 1px 8px rgba(15, 23, 42, 0.04);
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 18px 18px 8px 18px;
            margin-top: 8px;
            box-shadow: 0 1px 10px rgba(15, 23, 42, 0.04);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

PRESETS = {
    "Popüler ABD Hisseleri": ["TSLA", "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL", "AMD", "NFLX"],
    "BIST Örnekleri": ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "SISE.IS", "GARAN.IS", "EREGL.IS", "BIMAS.IS", "TUPRS.IS"],
    "Kripto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "ETF / Emtia": ["SPY", "QQQ", "VOO", "IWM", "GLD", "SLV", "XLE", "XLK"],
}

PERIODS = {
    "1 Ay": "1mo",
    "3 Ay": "3mo",
    "6 Ay": "6mo",
    "1 Yıl": "1y",
    "2 Yıl": "2y",
    "5 Yıl": "5y",
    "Maksimum": "max",
}

INTERVALS = {
    "Günlük": "1d",
    "Haftalık": "1wk",
    "Aylık": "1mo",
}


def clean_symbols(values):
    cleaned = []
    for value in values:
        if not value:
            continue
        parts = re.split(r"[\s,;]+", str(value))
        for part in parts:
            part = part.strip().upper()
            if part:
                cleaned.append(part)
    return list(dict.fromkeys(cleaned))


def human_number(x):
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


def pct_text(x):
    try:
        if x is None or pd.isna(x):
            return "-"
        return f"{float(x):.2f}%"
    except Exception:
        return "-"


def safe_float(x):
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


@st.cache_data(ttl=900, show_spinner=False)
def download_prices(symbols_tuple, period, interval):
    symbols = list(symbols_tuple)
    raw = yf.download(
        tickers=symbols,
        period=period,
        interval=interval,
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )

    result = {}
    if raw is None or raw.empty:
        return result

    if isinstance(raw.columns, pd.MultiIndex):
        level0 = list(raw.columns.get_level_values(0).unique())
        level1 = list(raw.columns.get_level_values(1).unique())

        if any(sym in level0 for sym in symbols):
            for sym in symbols:
                if sym in level0:
                    df = raw[sym].copy()
                    if not df.empty:
                        result[sym] = standardize_ohlcv(df)
        elif any(sym in level1 for sym in symbols):
            for sym in symbols:
                if sym in level1:
                    df = raw.xs(sym, level=1, axis=1).copy()
                    if not df.empty:
                        result[sym] = standardize_ohlcv(df)
    else:
        result[symbols[0]] = standardize_ohlcv(raw.copy())

    return {k: v for k, v in result.items() if v is not None and not v.empty}


def standardize_ohlcv(df):
    df = df.copy()
    df.columns = [str(c).strip().title().replace("Adj Close", "Adj Close") for c in df.columns]

    if "Close" not in df.columns and "Adj Close" in df.columns:
        df["Close"] = df["Adj Close"]

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in df.columns:
            df[col] = np.nan

    df = df.dropna(subset=["Close"])
    df = df.sort_index()
    return df


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals(symbols_tuple):
    rows = []
    for sym in list(symbols_tuple)[:20]:
        info = {}
        try:
            info = yf.Ticker(sym).get_info() or {}
        except Exception:
            info = {}

        rows.append(
            {
                "Sembol": sym,
                "İsim": info.get("shortName") or info.get("longName") or sym,
                "Sektör": info.get("sector", "-"),
                "Piyasa Değeri": human_number(info.get("marketCap")),
                "F/K": round(safe_float(info.get("trailingPE")), 2) if not math.isnan(safe_float(info.get("trailingPE"))) else "-",
                "İleri F/K": round(safe_float(info.get("forwardPE")), 2) if not math.isnan(safe_float(info.get("forwardPE"))) else "-",
                "PD/DD": round(safe_float(info.get("priceToBook")), 2) if not math.isnan(safe_float(info.get("priceToBook"))) else "-",
                "PEG": round(safe_float(info.get("pegRatio") or info.get("trailingPegRatio")), 2)
                if not math.isnan(safe_float(info.get("pegRatio") or info.get("trailingPegRatio")))
                else "-",
                "Net Marj": pct_text(safe_float(info.get("profitMargins")) * 100),
                "ROE": pct_text(safe_float(info.get("returnOnEquity")) * 100),
                "Borç/Özkaynak": round(safe_float(info.get("debtToEquity")), 2)
                if not math.isnan(safe_float(info.get("debtToEquity")))
                else "-",
                "Gelir Büyümesi": pct_text(safe_float(info.get("revenueGrowth")) * 100),
            }
        )
    return pd.DataFrame(rows)


def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def add_indicators(df):
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["RSI"] = calc_rsi(df["Close"])

    middle = df["Close"].rolling(20).mean()
    std = df["Close"].rolling(20).std()
    df["BB_UPPER"] = middle + (2 * std)
    df["BB_LOWER"] = middle - (2 * std)
    return df


def metrics_for_symbol(symbol, df):
    close = df["Close"].dropna()
    if close.empty:
        return {
            "Sembol": symbol,
            "Son Fiyat": np.nan,
            "Günlük %": np.nan,
            "Toplam Getiri %": np.nan,
            "Volatilite %": np.nan,
            "Maks. Düşüş %": np.nan,
        }

    last = close.iloc[-1]
    previous = close.iloc[-2] if len(close) > 1 else np.nan
    daily = ((last / previous) - 1) * 100 if previous and not pd.isna(previous) else np.nan
    total_return = ((last / close.iloc[0]) - 1) * 100 if len(close) > 1 else np.nan

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
    }


def make_single_chart(symbol, df, chart_type, show_sma20, show_sma50, show_sma200, show_ema21, show_bb, show_volume, show_rsi):
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
                name=f"{symbol} Close",
                line=dict(width=2.4),
            ),
            row=1,
            col=1,
        )

    overlays = [
        ("SMA20", show_sma20, 1.4),
        ("SMA50", show_sma50, 1.6),
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
        volume_colors = np.where(df["Close"] >= df["Open"], "rgba(22,163,74,.35)", "rgba(220,38,38,.35)")
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
        height=690,
        margin=dict(l=12, r=12, t=45, b=20),
        title=f"{symbol} fiyat grafiği",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis_rangeslider_visible=False,
    )
    fig.update_yaxes(title_text="Fiyat", row=1, col=1)
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1A", step="month", stepmode="backward"),
                    dict(count=3, label="3A", step="month", stepmode="backward"),
                    dict(count=6, label="6A", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="Tümü"),
                ]
            )
        ),
        row=1,
        col=1,
    )
    return fig


def make_compare_chart(price_dict):
    closes = pd.concat(
        {symbol: df["Close"] for symbol, df in price_dict.items() if "Close" in df.columns and not df.empty},
        axis=1,
    ).sort_index()

    normalized = pd.DataFrame(index=closes.index)
    for col in closes.columns:
        s = closes[col].dropna()
        if not s.empty:
            normalized[col] = closes[col] / s.iloc[0] * 100

    fig = go.Figure()
    for col in normalized.columns:
        fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized[col],
                mode="lines",
                name=col,
                line=dict(width=2.2),
            )
        )

    fig.add_hline(y=100, line_dash="dot", opacity=0.4)
    fig.update_layout(
        height=620,
        margin=dict(l=12, r=12, t=45, b=20),
        title="Karşılaştırmalı performans — başlangıç 100 kabul edildi",
        yaxis_title="Normalize değer",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(
        rangeselector=dict(
            buttons=list(
                [
                    dict(count=1, label="1A", step="month", stepmode="backward"),
                    dict(count=3, label="3A", step="month", stepmode="backward"),
                    dict(count=6, label="6A", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="Tümü"),
                ]
            )
        )
    )
    return fig


def technical_score(df):
    df = add_indicators(df).dropna(subset=["Close"])
    usable = df.dropna(subset=["SMA20", "SMA50", "RSI"])
    if usable.empty:
        return 0, "Veri az"

    last = usable.iloc[-1]
    score = 0
    score += 20 if last["Close"] > last["SMA20"] else 0
    score += 20 if last["SMA20"] > last["SMA50"] else 0
    score += 20 if 40 <= last["RSI"] <= 70 else 0
    score += 20 if last["Close"] > last["EMA21"] else 0
    score += 20 if last["Close"] > last["SMA200"] else 0

    if score >= 75:
        label = "Güçlü"
    elif score >= 45:
        label = "Nötr / izleme"
    else:
        label = "Zayıf"

    return score, label


def position_sizing(capital, risk_pct, entry, stop, target):
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


st.markdown('<div class="main-title">📊 Borsa & Kripto Kontrol Paneli</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">Eğitim ve kişisel takip amaçlıdır. Al-sat tavsiyesi değildir.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Panel Ayarları")

    preset_name = st.selectbox("Hazır liste", list(PRESETS.keys()), index=0)
    selected_symbols = st.multiselect(
        "Sembol seç",
        PRESETS[preset_name],
        default=PRESETS[preset_name][:4],
        help="Birden fazla sembol seçebilirsin.",
    )

    extra_symbols_text = st.text_area(
        "Ek sembol ekle",
        value="",
        placeholder="Örn: META, AMD, BTC-USD, THYAO.IS",
        help="Virgül, boşluk veya satır ile ayır.",
    )

    period_label = st.selectbox("Veri aralığı", list(PERIODS.keys()), index=3)
    interval_label = st.selectbox("Mum / veri periyodu", list(INTERVALS.keys()), index=0)

    st.divider()
    st.subheader("Gösterge Ayarları")
    chart_type_option = st.radio("Tekli grafik tipi", ["Mum", "Çizgi"], index=0, horizontal=True)
    show_sma20 = st.checkbox("SMA20", value=True)
    show_sma50 = st.checkbox("SMA50", value=True)
    show_sma200 = st.checkbox("SMA200", value=False)
    show_ema21 = st.checkbox("EMA21", value=False)
    show_bb = st.checkbox("Bollinger", value=False)
    show_volume = st.checkbox("Hacim", value=True)
    show_rsi = st.checkbox("RSI", value=True)

symbols = clean_symbols(selected_symbols + [extra_symbols_text])
period = PERIODS[period_label]
interval = INTERVALS[interval_label]

if not symbols:
    st.warning("Başlamak için en az bir sembol seç veya ek sembol yaz.")
    st.stop()

with st.spinner("Veriler alınıyor..."):
    prices = download_prices(tuple(symbols), period, interval)

valid_symbols = list(prices.keys())
missing_symbols = [s for s in symbols if s not in valid_symbols]

if missing_symbols:
    st.warning("Veri alınamayan semboller: " + ", ".join(missing_symbols))

if not valid_symbols:
    st.error("Hiçbir sembol için veri alınamadı. Sembol formatını kontrol et.")
    st.stop()

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

tab1, tab2, tab3, tab4 = st.tabs(["Grafikler", "Sembol Taraması", "Temel Veriler", "Risk Hesaplayıcı"])

with tab1:
    if len(valid_symbols) > 1:
        st.markdown("### Çoklu Sembol Karşılaştırması")
        st.plotly_chart(make_compare_chart(prices), use_container_width=True, theme="streamlit")

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
    for col in numeric_cols:
        display_df[col] = display_df[col].map(lambda x: round(x, 2) if not pd.isna(x) else "-")

    st.dataframe(
        display_df.sort_values("Toplam Getiri %", ascending=False, key=lambda s: pd.to_numeric(s, errors="coerce")),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Teknik skor basit bir takip filtresidir: Close>SMA20, SMA20>SMA50, RSI dengesi, Close>EMA21 ve Close>SMA200 koşullarından puan toplar."
    )

with tab3:
    st.markdown("### Temel Analiz Tablosu")
    with st.spinner("Temel veriler alınıyor..."):
        fundamentals = fetch_fundamentals(tuple(valid_symbols))
    st.dataframe(fundamentals, use_container_width=True, hide_index=True)
    st.caption("Kripto ve bazı BIST sembollerinde temel veri eksik gelebilir. Bu, veri sağlayıcısından kaynaklanır.")

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
            show_result[col] = show_result[col].map(lambda x: round(x, 4) if isinstance(x, (int, float, np.floating)) else x)

        st.dataframe(show_result, use_container_width=True, hide_index=True)

        rr = result["Risk/Getiri"]
        if rr < 1.5:
            st.warning("Risk/getiri oranı düşük görünüyor.")
        else:
            st.success("Risk/getiri oranı daha sağlıklı görünüyor.")
