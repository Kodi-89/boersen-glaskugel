import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & Community Dashboard")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Gemini Space": "GEMI",
    "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_list = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                perf = ((curr / prev) - 1) * 100
            else:
                curr = t.fast_info.last_price or 0.0
                perf = 0.0
            
            results.append({"Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, "Performance %": round(perf, 2)})
            
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
    # Absicherung: Nur Zeilen mit Kurs > 0 nutzen
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        # Wir berechnen die Größe der Kacheln direkt im DataFrame
        df_plot['size'] = 1 
        fig = px.treemap(
            df_plot, path=['Aktie'], values='size',
            color='Performance %', color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0, text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Marktdaten werden geladen...")

# --- NEU: LIVE-DEPOT RECHNER ---
st.divider()
st.header("💰 Live-Depot Simulator")
c1, c2, c3 = st.columns(3)
with c1: sim_stock = st.selectbox("Aktie wählen:", live_df["Aktie"].tolist())
with c2: sim_qty = st.number_input("Anzahl", min_value=1, value=10)
with c3: sim_buy = st.number_input("Kaufkurs (€)", min_value=0.1, value=10.0)

# Kalkulation
current_price = live_df.loc[live_df["Aktie"] == sim_stock, "Kurs"].values[0]
if current_price > 0:
    win_loss = (current_price - sim_buy) * sim_qty
    win_pct = ((current_price / sim_buy) - 1) * 100
    st.metric(f"Status: {sim_stock}", f"{current_price * sim_qty:.2f} €", delta=f"{win_loss:.2f} € ({win_pct:.2f}%)")
else:
    st.warning("Keine aktuellen Kursdaten für die Berechnung verfügbar.")

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Voting")
    pick = st.selectbox("Dein Favorit?", list(tickers.keys()))
    if st.button("Senden"): st.session_state.v[pick] += 1
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
