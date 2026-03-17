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
st.subheader("Ein Gemeinschaftsprojekt für transparente Hochspekulation")
st.markdown("---")

# Sidebar
st.sidebar.header("🛠 Navigation & Info")
st.sidebar.info("Diese App gehört der Gemeinschaft. Sie dient der Aufklärung über Risiken und Chancen im März 2026.")
st.sidebar.warning("⚠️ **Regeln:** 1. Kein Mietgeld. 2. Stop-Loss nutzen. 3. Gewinne abschöpfen.")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", 
    "Puma SE": "PUM.DE", "TUI AG": "TUI1.DE", 
    "Sable Offshore": "SOC", "Immunic Inc.": "IMUX"
    "Rheinmetall": "RHM.DE
}

@st.cache_data(ttl=300)
def load_data():
    results = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            results.append({"Aktie": name, "Kurs": round(t.fast_info.last_price, 2), "Symbol": sym})
        except: pass
    return pd.DataFrame(results)

live_df = load_data()

# --- LAYOUT: LIVE-MONITOR & HEATMAP ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df, use_container_width=True)

with col_right:
    st.header("🔥 Markt-Heatmap")
    df_heat = pd.DataFrame({
        "Aktie": list(tickers.keys()),
        "Momentum": [15, -5, 10, 25, 100, 71],
        "Risiko": [3, 5, 3, 4, 4, 5],
        "Kat": ["Squeeze", "Squeeze", "Squeeze", "Insider", "US-Mom", "Biotech"]
    })
    fig = px.treemap(df_heat, path=['Kat', 'Aktie'], values='Risiko', color='Momentum', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

# --- STOP-LOSS RECHNER ---
st.divider()
st.header("📉 Risiko-Management")
c1, c2, c3 = st.columns(3)
with c1: entry = st.number_input("Einstieg (€)", value=10.0)
with c2: risk = st.slider("Risiko (%)", 1, 20, 10)
with c3:
    sl = entry * (1 - risk/100)
    st.metric("Stop-Loss Marke", f"{sl:.2f} €", delta=f"-{risk}%", delta_color="inverse")

# --- VOTING & WÜNSCHE ---
st.divider()
col_v1, col_v2 = st.columns(2)
with col_v1:
    st.header("🗳️ Community-Voting")
    if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
    pick = st.selectbox("Wer zündet als Nächstes?", list(tickers.keys()))
    if st.button("Stimme abgeben"): st.session_state.v[pick] += 1
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))

with col_v2:
    st.header("💡 Wunschliste")
    wish = st.text_input("Welche Aktie fehlt hier?")
    if st.button("Vorschlagen"): st.success(f"'{wish}' wurde für April notiert!")

# --- FOOTER ---
st.divider()
st.caption("🤝 Diese App ist Open Source und für alle Anleger gedacht. Handeln Sie eigenverantwortlich.")
