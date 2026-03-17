import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from fpdf import FPDF
import base64
from datetime import datetime

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & Community Dashboard")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_list = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            # Nutze fast_info für stabilere Daten nach Börsenschluss
            info = t.fast_info
            curr = info.last_price
            prev = info.previous_close
            
            # Falls curr None ist (z.B. bei Fehlern), setzen wir 0.0
            curr = float(curr) if curr is not None else 0.0
            prev = float(prev) if prev is not None else 0.0
            
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            
            results.append({
                "Aktie": name, 
                "Kurs": round(curr, 2), 
                "Symbol": sym, 
                "Performance %": round(perf, 2)
            })
            
            # News laden
            n = t.news
            if n: news_list.append({"Aktie": name, "Headline": n[0]['title'], "Link": n[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_list

live_df, live_news = load_data()

# --- LAYOUT ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    st.write("---")
    st.subheader("🗞️ Top-Schlagzeilen")
    for n in live_news[:3]:
        st.markdown(f"**{n['Aktie']}**: [{n['Headline']}]({n['Link']})")

with col_r:
    st.header("🔥 24h Performance-Map")
    # Nur Aktien mit echtem Kurs anzeigen
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        df_plot['size'] = 1 
        fig = px.treemap(
            df_plot, path=['Aktie'], values='size',
            color='Performance %', color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0, text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Warte auf Marktdaten (Börsenpause)...")

# --- PDF & VOTING BLEIBEN GLEICH ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Voting")
    pick = st.selectbox("Favorit?", list(tickers.keys()))
    if st.button("Senden"): st.session_state.v[pick] += 1
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
