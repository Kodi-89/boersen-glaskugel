import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel | Community Edition", page_icon="🔮", layout="wide")

# --- BRANDING ---
st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance Monitor & Community Dashboard")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Gemini Space Station": "GEMI",
    "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft Corp.": "MSFT"
}

@st.cache_data(ttl=300)
def load_data():
    results = []
    news_list = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            curr = info.last_price if info.last_price else 0.0
            prev = info.previous_close if info.previous_close else curr
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            
            results.append({"Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, "Performance %": round(perf, 2)})
            
            tn = t.news
            if tn: news_list.append({"Aktie": name, "Headline": tn[0]['title'], "Link": tn[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_list

live_df, live_news = load_data()

# --- LAYOUT: MONITOR & HEATMAP ---
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    st.write("---")
    st.subheader("🗞️ Top-Schlagzeilen")
    for n in live_news[:3]:
        st.markdown(f"**{n['Aktie']}**: [{n['Headline']}]({n['Link']})")

with col_right:
    st.header("🔥 24h Performance-Map")
    # Der Fix: Wir filtern Werte ohne Kurs aus der Grafik aus, um TypeErrors zu vermeiden
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        fig = px.treemap(
            df_plot, path=['Aktie'], values=[1]*len(df_plot),
            color='Performance %', color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0, text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Warte auf Marktdaten...")

# --- NEU: LIVE-DEPOT RECHNER ---
st.divider()
st.header("💰 Live-Depot Simulator")
st.info("Simuliere hier deine Positionen und sieh, wie sie sich jetzt gerade schlagen.")
d_c1, d_c2, d_c3 = st.columns(3)
with d_c1:
    sim_stock = st.selectbox("Wähle eine Aktie:", list(tickers.keys()))
with d_c2:
    sim_qty = st.number_input("Anzahl Aktien", min_value=1, value=10)
with d_c3:
    sim_buy_price = st.number_input("Dein Kaufkurs (€)", min_value=0.1, value=15.0)

# Kalkulation
current_val = live_df.loc[live_df["Aktie"] == sim_stock, "Kurs"].values[0]
total_cost = sim_qty * sim_buy_price
total_now = sim_qty * current_val
profit_abs = total_now - total_cost
profit_pct = (profit_abs / total_cost) * 100 if total_cost > 0 else 0

st.metric(f"Ergebnis für {sim_stock}", f"{total_now:.2f} €", 
          delta=f"{profit_abs:.2f} € ({profit_pct:.2f}%)")

# --- VOTING ---
st.divider()
st.header("🗳️ Community-Voting")
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
for k in tickers.keys():
    if k not in st.session_state.v: st.session_state.v[k] = 0

cv1, cv2 = st.columns([1, 2])
with cv1:
    pick = st.selectbox("Favorit?", list(tickers.keys()), key="vote_box")
    if st.button("Abstimmen"): st.session_state.v[pick] += 1
with cv2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
