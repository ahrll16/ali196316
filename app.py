import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Sayfa Yapılandırması
st.set_page_config(page_title="Ekonomi Terminali", layout="wide", page_icon="🏛️")

# 2. Kalıcı Dark Mode Kilidi, Menü Gizleme ve Profesyonel CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* ÜST MENÜYÜ VE AYARLARI GİZLE */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* KARANLIK MOD RENK KİLİDİ */
    :root {
        --primary-color: #58a6ff;
        --background-color: #0d1117;
        --secondary-background-color: #161b22;
        --text-color: #c9d1d9;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }

    /* Yazı Renklerini Sabitle */
    h1, h2, h3, h4, label, .stMarkdown, p, span { color: #c9d1d9 !important; }

    /* Metrik Kartları */
    [data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 20px;
        border-radius: 12px;
    }
    
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; font-weight: 600 !important; }

    /* Tab Tasarımı */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        color: #8b949e !important;
        padding: 8px 20px !important;
    }
    .stTabs [aria-selected="true"] { border-color: #58a6ff !important; color: #58a6ff !important; }

    /* Takvim Kartları */
    .calendar-card {
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #58a6ff;
        margin-bottom: 10px;
        background-color: #1c2128;
        border: 1px solid #30363d;
    }

    /* Yasal Uyarı Kutusu */
    .disclaimer-box {
        margin-top: 50px;
        padding: 20px;
        border-radius: 10px;
        background-color: rgba(255, 75, 75, 0.05);
        border: 1px solid rgba(255, 75, 75, 0.2);
        font-size: 12px;
        color: #8b949e;
        line-height: 1.6;
    }
    
    .unit-text { font-size: 11px; color: #58a6ff; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. VERİ SÖZLÜKLERİ
currencies = {
    "Dolar / TL": ["USDTRY=X", "₺"], "Euro / TL": ["EURTRY=X", "₺"],
    "Sterlin / TL": ["GBPTRY=X", "₺"], "İsviçre Frangı / TL": ["CHFTRY=X", "₺"],
    "EUR / USD (Parite)": ["EURUSD=X", "Oran"], "Dolar Endeksi (DXY)": ["DX-Y.NYB", "Endeks"]
}

stock_exchanges = {
    "🌎 Amerika": {
        "ABD (S&P 500)": "^GSPC", "ABD (Nasdaq)": "^IXIC", "ABD (Dow Jones)": "^DJI",
        "Kanada (TSX)": "^GSPTSE", "Brezilya (Bovespa)": "^BVSP", "Meksika (IPC)": "^MXX"
    },
    "🇪🇺 Avrupa & 🇹🇷 TR": {
        "Türkiye (BIST 100)": "XU100.IS", "Almanya (DAX 40)": "^GDAXI", 
        "İngiltere (FTSE 100)": "^FTSE", "Fransa (CAC 40)": "^FCHI", 
        "İtalya (FTSE MIB)": "FTSEMIB.MI", "Rusya (MOEX)": "IMOEX.ME"
    },
    "🌏 Asya & Pasifik": {
        "Japonya (Nikkei 225)": "^N225", "Çin (Shanghai)": "000001.SS", "Çin (Shenzhen)": "399001.SZ",
        "Hindistan (NIFTY 50)": "^NSEI", "G. Kore (KOSPI)": "^KS11", "Avustralya (ASX 200)": "^AXJO"
    },
    "🕌 MEA": {
        "S. Arabistan (TASI)": "^TASI.SR", "G. Afrika (JSE)": "^J203.JO", "Katar (QE)": "^QSI"
    }
}

commodities = {
    "💎 Değerli Madenler": {
        "Altın (Ons)": ["GC=F", 1, "USD/Ons"], "Gümüş (Ons)": ["SI=F", 1, "USD/Ons"],
        "Platin": ["PL=F", 1, "USD/Ons"], "Paladyum": ["PA=F", 1, "USD/Ons"]
    },
    "🛢️ Enerji & Sanayi": {
        "Brent Petrol": ["BZ=F", 1, "USD/Varil"],
        "WTI Petrol": ["CL=F", 1, "USD/Varil"],
        "Doğalgaz": ["NG=F", 1, "USD/MMBtu"],
        "Dizel (Gasoil)": ["HO=F", 1, "USD/Galon"],
        "Bakır (Ton)": ["HG=F", 2204.62, "USD/Ton"],
        "Alüminyum (Ton)": ["ALI=F", 1, "USD/Ton"],
        "Çinko (Ton)": ["ZN=F", 1, "USD/Ton"],
        "Nikel (Ton)": ["NIL=F", 1, "USD/Ton"]
    },
    "🌾 Tarım Ürünleri": {
        "Pamuk": ["CT=F", 1, "USD/Lbs"], "Buğday": ["W=F", 1, "USD/Bushel"], 
        "Mısır": ["ZC=F", 1, "USD/Bushel"], "Kahve": ["KC=F", 1, "USD/Lbs"], "Kakao": ["CC=F", 1, "USD/Ton"]
    }
}

company_data = {
    "🇺🇸 ABD Devleri": {"Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA", "Tesla": "TSLA", "Amazon": "AMZN", "Meta": "META"},
    "🇹🇷 Türkiye Devleri": {"THY": "THYAO.IS", "Koç Holding": "KCHOL.IS", "Tüpraş": "TUPRS.IS", "Aselsan": "ASELS.IS", "Ereğli": "EREGL.IS"},
    "🇪🇺 Avrupa & Asya": {"ASML": "ASML", "SAP": "SAP", "Samsung": "005930.KS", "Toyota": "7203.T"}
}

crypto = {
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", "XRP": "XRP-USD",
    "BNB": "BNB-USD", "Cardano": "ADA-USD", "Avalanche": "AVAX-USD", "Dogecoin": "DOGE-USD"
}

economic_calendar = [
    {"Tarih": "2026-05-21", "Ülke": "🇹🇷 Türkiye", "Olay": "TCMB Faiz Kararı", "Etki": "Yüksek"},
    {"Tarih": "2026-06-10", "Ülke": "🇺🇸 ABD", "Olay": "FED Faiz Kararı & Projeksiyonlar", "Etki": "Kritik"},
    {"Tarih": "2026-06-11", "Ülke": "🇪🇺 Euro Bölgesi", "Olay": "ECB Para Politikası Toplantısı", "Etki": "Yüksek"},
    {"Tarih": "2026-06-18", "Ülke": "🇹🇷 Türkiye", "Olay": "TCMB PPK Toplantısı", "Etki": "Yüksek"},
    {"Tarih": "2026-07-29", "Ülke": "🇺🇸 ABD", "Olay": "FED Faiz Kararı", "Etki": "Yüksek"},
    {"Tarih": "2026-09-17", "Ülke": "🇹🇷 Türkiye", "Olay": "TCMB Faiz Kararı", "Etki": "Yüksek"},
    {"Tarih": "2026-11-03", "Ülke": "🇺🇸 ABD", "Olay": "ABD Ara Seçimleri (Midterm)", "Etki": "Kritik"},
    {"Tarih": "2026-12-16", "Ülke": "🇺🇸 ABD", "Olay": "Yılın Son FED Faiz Kararı", "Etki": "Yüksek"}
]

# 4. YARDIMCI FONKSİYONLAR
def fetch_data(ticker, multiplier=1):
    try:
        t = yf.Ticker(ticker)
        d = t.history(period="1mo", interval="1d")
        if d.empty or len(d) < 2:
            # Yedek deneme (5 günlük)
            d = t.history(period="5d")
        
        if not d.empty and len(d) >= 2:
            curr = d['Close'].iloc[-1] * multiplier
            diff = curr - (d['Close'].iloc[-2] * multiplier)
            pct = (diff / (d['Close'].iloc[-2] * multiplier)) * 100
            return curr, diff, pct
    except Exception:
        return None, None, None
    return None, None, None

def render_pro_chart(assets_dict, category_name):
    st.markdown(f"### 📈 {category_name} Analiz Paneli")
    c_sel, c_per = st.columns([2, 1])
    flat_list = {}
    if any(isinstance(v, dict) for v in assets_dict.values()):
        for sub in assets_dict.values(): flat_list.update(sub)
    else: flat_list = assets_dict

    with c_sel:
        name = st.selectbox(f"Varlık Seç ({category_name}):", list(flat_list.keys()), key=f"s_{category_name}")
        val = flat_list[name]
        ticker = val[0] if isinstance(val, list) else val
        mult = val[1] if isinstance(val, list) and isinstance(val[1], (int, float)) else 1

    with c_per:
        per_map = {"1 Ay": "1mo", "1 Yıl": "1y", "5 Yıl": "5y"}
        sel_p = st.select_slider(f"Zaman ({category_name}):", options=list(per_map.keys()), value="1 Yıl", key=f"p_{category_name}")
    
    hist = yf.Ticker(ticker).history(period=per_map[sel_p])
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'] * mult, fill='tozeroy', line=dict(color='#58a6ff', width=2), fillcolor='rgba(88, 166, 255, 0.1)', name=name))
        fig.update_layout(template="plotly_dark", margin=dict(l=0, r=0, t=20, b=0), height=350, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#30363d'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

# 5. ANA ARAYÜZ
st.title("🏛️ Ekonomi Terminali")

tabs = st.tabs(["💱 Döviz", "📉 Borsalar", "🏗️ Emtia", "🏢 Şirketler", "₿ Kripto", "📅 Takvim", "💼 Simülatör"])

with tabs[0]:
    cols = st.columns(4)
    for idx, (n, v) in enumerate(currencies.items()):
        p, d, pct = fetch_data(v[0])
        if p: cols[idx%4].metric(n, f"{p:,.4f}", f"{d:,.4f} (%{pct:+.2f}%)")
    render_pro_chart(currencies, "Döviz")

with tabs[1]:
    region = st.radio("Bölge Seç:", list(stock_exchanges.keys()), horizontal=True)
    cols = st.columns(3)
    for idx, (n, t) in enumerate(stock_exchanges[region].items()):
        p, d, pct = fetch_data(t)
        if p: cols[idx%3].metric(n, f"{p:,.2f}", f"{d:,.2f} (%{pct:+.2f}%)")
    render_pro_chart(stock_exchanges, "Borsalar")

with tabs[2]:
    for cat, items in commodities.items():
        st.markdown(f"#### {cat}")
        cols = st.columns(4)
        for idx, (n, v) in enumerate(items.items()):
            p, d, pct = fetch_data(v[0], v[1])
            if p is not None: 
                cols[idx % 4].metric(n, f"{p:,.2f}", f"{d:,.2f} (%{pct:+.2f}%)")
                cols[idx % 4].markdown(f'<p class="unit-text">Birim: {v[2]}</p>', unsafe_allow_html=True)
            else:
                cols[idx % 4].metric(n, "Yükleniyor...", "—")
    render_pro_chart(commodities, "Emtia")

with tabs[3]:
    c_reg = st.radio("Şirket Bölgesi:", list(company_data.keys()), horizontal=True)
    cols = st.columns(3)
    for idx, (n, t) in enumerate(company_data[c_reg].items()):
        p, d, pct = fetch_data(t)
        if p: cols[idx%3].metric(n, f"{p:,.2f}", f"{d:,.2f} (%{pct:+.2f}%)")
    render_pro_chart(company_data, "Şirketler")

with tabs[4]:
    cols = st.columns(4)
    for idx, (n, t) in enumerate(crypto.items()):
        p, d, pct = fetch_data(t)
        if p: 
            # DÜZELTİLDİ: 3 argüman kuralı (İsim, Fiyat, Değişim)
            cols[idx%4].metric(n, f"{p:,.2f}", f"{d:,.2f} (%{pct:+.2f}%)")
    render_pro_chart(crypto, "Kripto")

with tabs[5]:
    st.subheader("📅 Stratejik Ekonomik Takvim (2026)")
    for event in economic_calendar:
        st.markdown(f'<div class="calendar-card"><b>{event["Tarih"]}</b> | {event["Ülke"]} - <b>{event["Olay"]}</b><br><small style="color: #8b949e">Önem Derecesi: {event["Etki"]}</small></div>', unsafe_allow_html=True)

with tabs[6]:
    st.subheader("💼 Akıllı Yatırım Simülatörü")
    s1, s2, s3, s4 = st.columns(4)
    all_flat = {**{k: v[0] for k, v in currencies.items()}, **crypto}
    for sub in stock_exchanges.values(): all_flat.update(sub)
    for sub in commodities.values(): 
        for k, v in sub.items(): all_flat[k] = v[0]
    for sub in company_data.values(): all_flat.update(sub)

    asset_key = s1.selectbox("Simülasyon Varlığı:", list(all_flat.keys()))
    inv_curr = s2.selectbox("Yatırım Para Birimi:", ["TL", "USD", "EUR"])
    amt = s3.number_input("Yatırım Tutarı:", min_value=1.0, value=1000.0)
    dt = s4.date_input("Yatırım Başlangıç Tarihi:", value=datetime.now() - timedelta(days=365))

    if st.button("Simülasyonu Çalıştır"):
        asset_h = yf.Ticker(all_flat[asset_key]).history(start=dt)
        usd_h = yf.Ticker("USDTRY=X").history(start=dt)
        if not asset_h.empty and not usd_h.empty:
            growth = asset_h['Close'].iloc[-1] / asset_h['Close'].iloc[0]
            is_try = ".IS" in all_flat[asset_key] or "TRY" in all_flat[asset_key]
            final_val = amt * growth
            if inv_curr == "TL" and not is_try:
                final_val = amt * growth * (usd_h['Close'].iloc[-1] / usd_h['Close'].iloc[0])
            st.success(f"Portföyün Bugünkü Değeri: **{final_val:,.2f} {inv_curr}**")
            st.info(f"Net Getiri: **% {((final_val/amt)-1)*100:+.2f}**")

# --- YASAL UYARI ---
st.markdown("""
<div class="disclaimer-box">
    <strong>⚠️ Yasal Uyarı / Disclaimer:</strong><br>
    Bu terminalde sunulan veriler, grafikler ve simülasyon sonuçları yalnızca bilgilendirme amaçlıdır. Verilerin doğruluğu, güncelliği veya eksiksizliği garanti edilmemektedir. 
    Burada yer alan hiçbir ifade yatırım danışmanlığı kapsamında değildir. Yatırım kararlarınızı vermeden önce mutlaka profesyonel bir finans danışmanına danışmalı ve kendi risk analizlerinizi yapmalısınız. 
    Bu verilerdeki olası hatalardan veya bu verilere dayanılarak yapılan işlemlerden doğabilecek zararlardan yazılım sorumlu tutulamaz.<br><br>
    <em>The data, charts, and simulation results presented in this terminal are for informational purposes only. Accuracy, timeliness, or completeness of the data is not guaranteed. 
    Nothing contained herein constitutes financial or investment advice. You should always consult with a professional financial advisor and perform your own risk analysis before making investment decisions. 
    The software cannot be held liable for any potential errors in the data or losses arising from transactions based on this information.</em>
</div>
""", unsafe_allow_html=True)
