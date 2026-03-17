import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel | Community Edition", page_icon="🔮", layout="wide")

# --- BRANDING & PHILOSOPHIE ---
st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance Monitor & Community Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("🛠 Navigation & Info")
st.sidebar.info("Diese App nutzt Live-Daten von Yahoo Finance zur Analyse von Markttrends.")
st.sidebar.warning("⚠️ **Regeln:** 1. Kein Mietgeld. 2. Stop-Loss nutzen. 3. Gewinne abschöpfen.")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", 
    "Delivery Hero": "DHER.DE", 
    "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", 
    "Sable Offshore": "SOC", 
    "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE",
    "Gemini Space Station": "GEMI",
    "Tesla, Inc.": "TSLA",
    "AMD, Inc.": "AMD",
    "Microsoft Corp.": "MSFT"
}

@st.cache_data(ttl=300)
def load_data():
    results = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            current_price = info.last_price
            prev_close = info.previous_close
            
            # Berechnung der echten 24h Performance
            perf = ((current_price / prev_close) - 1) * 100 if prev_close else 0
            
            results.append({
                "Aktie": name, 
                "Kurs": round(current_price, 2), 
                "Symbol": sym,
                "Performance %": round(perf, 2)
            })
        except: 
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results)

live_df = load_data()

# --- LAYOUT: LIVE-MONITOR & HEATMAP ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.header("📈 Echtzeit-Kurse")
    # Styling für die Tabelle (Grün bei Plus, Rot bei Minus)
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)

with col_right:
    st.header("🔥 24h Performance-Map")
    
    fig = px.treemap(
        live_df, 
        path=['Aktie'], 
        values=[1]*len(live_df), # Alle Kacheln gleich groß
        color='Performance %', 
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        text_auto='.2f'
    )
    st.plotly_chart(fig, use_container_width=True)

# --- STOP-LOSS RECHNER ---
st.divider()
st.header("📉 Risiko-Management")
c1, c2, c3 = st.columns(3)
with c1: entry = st.number_input("Einstieg (€)", value=10.0)
with c2: risk = st.slider("Risiko (%)", 1, 25, 10)
with c3:
    sl = entry * (1 - risk/100)
    st.metric("Stop-Loss Marke", f"{sl:.2f} €", delta=f"-{risk}%", delta_color="inverse")

# --- VOTING & WÜNSCHE ---
st.divider()
col_v1, col_v2 = st.columns(2)
with col_v1:
    st.header("🗳️ Community-Voting")
    if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
    for k in tickers.keys():
        if k not in st.session_state.v: st.session_state.v[k] = 0
        
    pick = st.selectbox("Welcher Wert hat das größte Potenzial?", list(tickers.keys()))
    if st.button("Stimme abgeben"): 
        st.session_state.v[pick] += 1
        st.success(f"Votum für {pick} registriert!")
        
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))

with col_v2:
    st.header("💡 Wunschliste")
    wish = st.text_input("Welchen Ticker sollen wir hinzufügen?")
    if st.button("Vorschlagen"): st.balloons(); st.success(f"'{wish}' wurde vorgemerkt!")

# --- FOOTER ---
st.divider()
st.caption("🤝 Open Source Community-Projekt. Keine Anlageberatung.")
