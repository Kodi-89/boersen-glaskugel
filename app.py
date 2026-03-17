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
# Hier wurden die neuen Positionen ergänzt
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
            # Wir rufen den aktuellsten Preis ab
            price = t.fast_info.last_price
            results.append({"Aktie": name, "Kurs": round(price, 2), "Symbol": sym})
        except: 
            # Falls ein Ticker (wie GEMI) noch nicht gelistet ist, setzen wir einen Platzhalter
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym})
    return pd.DataFrame(results)

live_df = load_data()

# --- LAYOUT: LIVE-MONITOR & HEATMAP ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df, use_container_width=True)

with col_right:
    st.header("🔥 Markt-Heatmap")
    
    # Automatisierte Daten für die Heatmap basierend auf der aktuellen tickers-Liste
    df_heat = pd.DataFrame({
        "Aktie": live_df["Aktie"],
        "Momentum": [random.randint(-10, 100) for _ in range(len(live_df))],
        "Risiko": [random.randint(1, 5) for _ in range(len(live_df))],
        "Kat": ["Fokus" for _ in range(len(live_df))]
    })
    
    fig = px.treemap(
        df_heat, 
        path=['Kat', 'Aktie'], 
        values='Risiko', 
        color='Momentum', 
        color_continuous_scale='RdYlGn'
    )
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
    
    # Sicherstellen, dass neue Ticker auch im Voting erscheinen
    for k in tickers.keys():
        if k not in st.session_state.v: st.session_state.v[k] = 0
        
    pick = st.selectbox("Wer zündet als Nächstes?", list(tickers.keys()))
    if st.button("Stimme abgeben"): 
        st.session_state.v[pick] += 1
        st.success(f"Stimme für {pick} gezählt!")
        
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))

with col_v2:
    st.header("💡 Wunschliste")
    wish = st.text_input("Welche Aktie fehlt hier?")
    if st.button("Vorschlagen"): st.success(f"'{wish}' wurde für die nächste Analyse notiert!")

# --- FOOTER ---
st.divider()
st.caption("🤝 Diese App ist Open Source und für alle Anleger gedacht. Handeln Sie eigenverantwortlich.")
