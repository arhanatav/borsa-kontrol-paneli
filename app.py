import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np


st.set_page_config(
    page_title="Borsa Kontrol Paneli",
    layout="wide"
)


st.title("Borsa Kontrol Paneli")
st.caption("Eğitim ve kişisel takip amaçlıdır. Al-sat tavsiyesi değildir.")


def para_format(x):
    try:
        if x is None or pd.isna(x):
            return "-"
        x = float(x)
        if abs(x) >= 1_000_000_000_000:
            return f"{x / 1_000_000_000_000:.2f} T"
        elif abs(x) >= 1_000_000_000:
            return f"{x / 1_000_000_000:.2f} B"
        elif abs(x) >= 1_000_000:
            return f"{x / 1_000_000:.2f} M"
        else:
            return f"{x:.2f}"
    except:
        return "-"


def oran_format(x):
    try:
        if x is None or pd.isna(x):
            return "-"
        return f"{float(x):.2f}"
    except:
        return "-"


def yuzde_format(x):
    try:
        if x is None or pd.isna(x):
            return "-"
        return f"{float(x) * 100:.2f}%"
    except:
        return "-"


@st.cache_data(ttl=900)
def fiyat_verisi_al(symbol, period="1y"):
    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data


@st.cache_data(ttl=3600)
def temel_bilgi_al(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.get_info()
    except:
        return {}


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def teknik_analiz(symbol, period="1y"):
    data = fiyat_verisi_al(symbol, period)

    if data.empty:
        return data, None

    data["SMA20"] = data["Close"].rolling(20).mean()
    data["SMA50"] = data["Close"].rolling(50).mean()
    data["SMA200"] = data["Close"].rolling(200).mean()
    data["RSI"] = rsi(data["Close"])

    data["EMA12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA12"] - data["EMA26"]
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()

    if "Volume" in data.columns:
        data["VOL20"] = data["Volume"].rolling(20).mean()
    else:
        data["Volume"] = 0
        data["VOL20"] = 0

    temiz = data.dropna()

    if temiz.empty:
        return data, None

    son = temiz.iloc[-1]

    skor = 0

    if son["Close"] > son["SMA20"]:
        skor += 15

    if son["SMA20"] > son["SMA50"]:
        skor += 15

    if son["Close"] > son["SMA200"]:
        skor += 15

    if 40 <= son["RSI"] <= 70:
        skor += 20

    if son["MACD"] > son["MACD_SIGNAL"]:
        skor += 20

    if son["Volume"] > son["VOL20"]:
        skor += 15

    if skor >= 70:
        yorum = "Pozitif teknik görünüm"
    elif skor >= 40:
        yorum = "Nötr / izleme"
    else:
        yorum = "Zayıf teknik görünüm"

    rapor = {
        "Sembol": symbol,
        "Son Fiyat": round(float(son["Close"]), 2),
        "SMA20": round(float(son["SMA20"]), 2),
        "SMA50": round(float(son["SMA50"]), 2),
        "SMA200": round(float(son["SMA200"]), 2),
        "RSI": round(float(son["RSI"]), 2),
        "MACD": round(float(son["MACD"]), 4),
        "MACD Sinyal": round(float(son["MACD_SIGNAL"]), 4),
        "Teknik Skor": skor,
        "Teknik Yorum": yorum
    }

    return data, rapor


def peg_yorumla(peg):
    try:
        if peg is None or pd.isna(peg):
            return "PEG verisi yok"

        peg = float(peg)

        if peg < 0:
            return "Negatif PEG, büyüme zayıf olabilir"
        elif peg < 1:
            return "Büyümeye göre ucuz olabilir"
        elif peg < 2:
            return "Makul / izlenebilir"
        elif peg < 3:
            return "Pahalılaşmış olabilir"
        else:
            return "Büyümeye göre pahalı olabilir"
    except:
        return "PEG hesaplanamadı"


def temel_analiz(symbol):
    info = temel_bilgi_al(symbol)

    if not info:
        return None

    fk = info.get("trailingPE")
    ileri_fk = info.get("forwardPE")
    pd_dd = info.get("priceToBook")

    peg = info.get("trailingPegRatio") or info.get("pegRatio")
    kar_buyumesi = info.get("earningsGrowth")
    gelir_buyumesi = info.get("revenueGrowth")

    if peg is None and fk is not None and kar_buyumesi is not None:
        if kar_buyumesi > 0:
            peg = fk / (kar_buyumesi * 100)

    piyasa_degeri = info.get("marketCap")
    firma_degeri = info.get("enterpriseValue")
    gelir = info.get("totalRevenue")
    brut_marj = info.get("grossMargins")
    faaliyet_marj = info.get("operatingMargins")
    net_marj = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    borc = info.get("totalDebt")
    nakit = info.get("totalCash")
    borc_ozkaynak = info.get("debtToEquity")
    beta = info.get("beta")

    skor = 0

    if net_marj is not None and net_marj > 0:
        skor += 15

    if brut_marj is not None and brut_marj > 0.20:
        skor += 15

    if gelir_buyumesi is not None and gelir_buyumesi > 0:
        skor += 15

    if kar_buyumesi is not None and kar_buyumesi > 0:
        skor += 15

    if roe is not None and roe > 0:
        skor += 15

    if nakit is not None and borc is not None and nakit >= borc:
        skor += 10

    if borc_ozkaynak is not None and borc_ozkaynak < 100:
        skor += 10

    if peg is not None and peg > 0 and peg < 2:
        skor += 10

    if skor >= 70:
        yorum = "Temel görünüm güçlü"
    elif skor >= 40:
        yorum = "Temel görünüm orta / izleme"
    else:
        yorum = "Temel görünüm zayıf veya veri eksik"

    rapor = {
        "Sembol": symbol,
        "Şirket": info.get("longName", symbol),
        "Sektör": info.get("sector", "-"),
        "Endüstri": info.get("industry", "-"),
        "Piyasa Değeri": para_format(piyasa_degeri),
        "Firma Değeri": para_format(firma_degeri),
        "Gelir": para_format(gelir),
        "F/K": oran_format(fk),
        "İleri F/K": oran_format(ileri_fk),
        "PD/DD": oran_format(pd_dd),
        "PEG Ratio": oran_format(peg),
        "PEG Yorumu": peg_yorumla(peg),
        "Gelir Büyümesi": yuzde_format(gelir_buyumesi),
        "Kâr Büyümesi": yuzde_format(kar_buyumesi),
        "Brüt Kâr Marjı": yuzde_format(brut_marj),
        "Faaliyet Marjı": yuzde_format(faaliyet_marj),
        "Net Kâr Marjı": yuzde_format(net_marj),
        "ROE": yuzde_format(roe),
        "Toplam Borç": para_format(borc),
        "Toplam Nakit": para_format(nakit),
        "Borç / Özkaynak": oran_format(borc_ozkaynak),
        "Beta": oran_format(beta),
        "Temel Skor": skor,
        "Temel Yorum": yorum
    }

    return rapor


def risk_hesapla(sermaye, risk_yuzdesi, giris, stop, hedef):
    risk_tutari = sermaye * risk_yuzdesi / 100
    birim_risk = abs(giris - stop)

    if birim_risk == 0:
        return None

    adet = risk_tutari / birim_risk
    pozisyon = adet * giris
    zarar = abs(giris - stop) * adet
    kar = abs(hedef - giris) * adet

    if zarar == 0:
        rr = None
    else:
        rr = kar / zarar

    return {
        "Sermaye": round(sermaye, 2),
        "İşlem Başı Risk %": risk_yuzdesi,
        "Maksimum Zarar": round(risk_tutari, 2),
        "Giriş": giris,
        "Stop": stop,
        "Hedef": hedef,
        "Alınabilecek Adet": round(adet, 4),
        "Pozisyon Büyüklüğü": round(pozisyon, 2),
        "Stop Olursa Zarar": round(zarar, 2),
        "Hedef Olursa Kâr": round(kar, 2),
        "Risk / Getiri": round(rr, 2) if rr is not None else "-"
    }


tab1, tab2, tab3 = st.tabs([
    "Kontrol Paneli",
    "Risk Hesaplayıcı",
    "Takip Listesi"
])


with tab1:
    st.subheader("Teknik + Temel Analiz")

    col1, col2 = st.columns([2, 1])

    with col1:
        symbol = st.text_input(
            "Sembol gir",
            value="ASELS.IS",
            help="Örnek: ASELS.IS, THYAO.IS, TSLA, NVDA, BTC-USD, XAGUSD=X"
        )

    with col2:
        period = st.selectbox(
            "Veri aralığı",
            ["6mo", "1y", "2y", "5y"],
            index=1
        )

    if st.button("Analiz Et"):
        data, teknik = teknik_analiz(symbol, period)
        temel = temel_analiz(symbol)

        if data.empty:
            st.error("Veri alınamadı. Sembolü kontrol et.")
        else:
            st.markdown("### Fiyat Grafiği")

            grafik_kolonlari = ["Close"]

            if "SMA20" in data.columns:
                grafik_kolonlari.append("SMA20")

            if "SMA50" in data.columns:
                grafik_kolonlari.append("SMA50")

            st.line_chart(data[grafik_kolonlari].dropna())

            if teknik:
                st.markdown("### Teknik Analiz")
                st.dataframe(pd.DataFrame([teknik]), use_container_width=True)

            if temel:
                st.markdown("### Temel Analiz")
                st.dataframe(pd.DataFrame([temel]), use_container_width=True)
            else:
                st.warning("Temel analiz verisi alınamadı.")


with tab2:
    st.subheader("Risk Hesaplayıcı")

    col1, col2, col3 = st.columns(3)

    with col1:
        sermaye = st.number_input("Toplam Sermaye", min_value=0.0, value=100000.0, step=1000.0)
        risk_yuzdesi = st.number_input("İşlem Başı Risk %", min_value=0.1, value=2.0, step=0.1)

    with col2:
        giris = st.number_input("Giriş Fiyatı", min_value=0.0, value=100.0, step=1.0)
        stop = st.number_input("Stop Fiyatı", min_value=0.0, value=95.0, step=1.0)

    with col3:
        hedef = st.number_input("Hedef Fiyat", min_value=0.0, value=115.0, step=1.0)

    sonuc = risk_hesapla(sermaye, risk_yuzdesi, giris, stop, hedef)

    if sonuc:
        st.markdown("### Risk Sonucu")
        st.dataframe(pd.DataFrame([sonuc]), use_container_width=True)

        rr = sonuc["Risk / Getiri"]

        if rr != "-" and rr < 1.5:
            st.warning("Risk / getiri oranı düşük görünüyor.")
        elif rr != "-":
            st.success("Risk / getiri oranı daha sağlıklı görünüyor.")
    else:
        st.error("Stop fiyatı giriş fiyatına eşit olamaz.")


with tab3:
    st.subheader("Takip Listesi")

    sembol_metni = st.text_area(
        "Sembolleri alt alta yaz",
        value="ASELS.IS\nTHYAO.IS\nTSLA\nNVDA\nBTC-USD\nXAGUSD=X"
    )

    semboller = [s.strip() for s in sembol_metni.split("\n") if s.strip()]

    if st.button("Listeyi Tara"):
        rows = []

        for s in semboller:
            data, teknik = teknik_analiz(s, "1y")
            temel = temel_analiz(s)

            row = {
                "Sembol": s
            }

            if teknik:
                row["Son Fiyat"] = teknik.get("Son Fiyat")
                row["RSI"] = teknik.get("RSI")
                row["Teknik Skor"] = teknik.get("Teknik Skor")
                row["Teknik Yorum"] = teknik.get("Teknik Yorum")

            if temel:
                row["F/K"] = temel.get("F/K")
                row["PD/DD"] = temel.get("PD/DD")
                row["PEG Ratio"] = temel.get("PEG Ratio")
                row["PEG Yorumu"] = temel.get("PEG Yorumu")
                row["Temel Skor"] = temel.get("Temel Skor")
                row["Temel Yorum"] = temel.get("Temel Yorum")

            rows.append(row)

        st.dataframe(pd.DataFrame(rows), use_container_width=True)
