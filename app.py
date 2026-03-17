import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel: Gemini Edition Pro", page_icon="💎", layout="wide")

# AUTO-REFRESH: Alle 30 Sekunden
st_autorefresh(interval=30 * 1000, key="data_refresh")

st.title("🔮 Börsen-Glaskugel: Gemini Edition Pro")
st.caption("Live-Kurse | CSV-Export | Stabiles Voting-System")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "Gemini (Google)": "GOOGL",
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=20)
def load_market_data():
    results = []
    news_items = []
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            f = t.fast_info
            curr = float(f.last_price) if f.last_price is not None else 0.0
            p_close = float(f.previous_close) if f.previous_close is not None else 0.0
            d_high = float(f.day_high) if f.day_high is not None else curr
            perf = ((curr / p_close) - 1) * 100 if p_close > 0 else 0.0
            
            sig = "⚪ HOLD"
            if curr > 0 and curr >= (d_high * 0.99): sig = "🟢 BUY"
            elif perf < -9: sig = "🔴 CRASH"
            elif perf > 3: sig = "🚀 MOON"

            results.append({"Asset": name, "Symbol": symbol, "Preis (€/$)": round(curr, 2), "Perf %": round(perf, 2), "Signal": sig})
            raw_news = t.news
            if raw_news: news_items.append({"Asset": name, "Title": raw_news[0]['title'], "URL": raw_news[0]['link']})
        except: continue
    return pd.DataFrame(results).drop_duplicates(subset=['Asset']), news_items

live_df, current_news = load_market_data()

# --- SIDEBAR: PREMIUM TOOLS & NEUER TACHO ---
st.sidebar.header("💎 Gemini Premium Tools")

# 1. Stimmungstacho in der Sidebar
avg_perf = live_df["Perf %"].mean()
fig_sidebar = go.Figure(go.Indicator(
    mode = "gauge+number", value = avg_perf,
    gauge = {'axis': {'range': [-5, 5]}, 'bar': {'color': "white"},
             'steps': [{'range': [-5, -1.5], 'color': "#ff4b4b"},
                       {'range': [-1.5, 1.5], 'color': "#f63366"},
                       {'range': [1.5, 5], 'color': "#00ff00"}]}
))
fig_sidebar.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
st.sidebar.plotly_chart(fig_sidebar, use_container_width=True)

if st.sidebar.button("🎲 Zufälliger Moonshot-Tipp"):
    st.sidebar.info(f"Orakel meint: Schau dir mal **{random.choice(live_df['Asset'].tolist())}** an!")

st.sidebar.markdown("---")
csv_data = live_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(label="📥 CSV Export", data=csv_data, file_name='gemini_pro_export.csv', mime='text/csv')

# --- TOP SEKTION ---
top_3 = live_df[live_df["Perf %"] > 0].sort_values(by="Perf %", ascending=False).head(3)
if not top_3.empty:
    m_cols = st.columns(3)
    medals = ["🥇 Gold", "🥈 Silber", "🥉 Bronze"]
    for i, (idx, row) in enumerate(top_3.iterrows()):
        m_cols[i].metric(label=f"{medals[i]}: {row['Asset']}", value=f"{row['Preis (€/$)']} €/$", delta=f"{row['Perf %']}%")

st.divider()

# --- MAIN LAYOUT ---
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.header("📈 Echtzeit-Monitor Pro")
    def spotlight_gemini(row):
        return ['border: 3px solid #ffaa00' if row['Asset'] == 'Gemini (Google)' else '' for _ in row.index]

    st.dataframe(
        live_df.style.applymap(lambda x: f"color: {'#00ff00' if x > 0 else '#ff4b4b'}", subset=['Perf %'])
        .apply(spotlight_gemini, axis=1),
        use_container_width=True, hide_index=True
    )

with col_r:
    st.header("🔥 Performance-Map")
    df_plot = live_df[(live_df["Preis (€/$)"] > 0) & (live_df["Perf %"] != 0)].copy()
    if not df_plot.empty:
        df_plot['count'] = 1
        fig = px.treemap(df_plot, path=['Asset'], values='count', color='Perf %', color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- STABILES VOTING SYSTEM ---
st.subheader("🗳️ Community Moonshot Voting")
# Initialisierung oder Update der Stimmen-Liste
if 'v' not in st.session_state:
    st.session_state.v = {k: 0 for k in tickers.keys()}
else:
    # Falls neue Aktien dazugekommen sind (wie Gemini), füge sie dem Speicher hinzu
    for k in tickers.keys():
        if k not in st.session_state.v:
            st.session_state.v[k] = 0

v1, v2 = st.columns([1, 2])
with v1:
    pick = st.selectbox("Wer zündet als Nächstes?", sorted(live_df["Asset"].tolist()))
    if st.button("Stimme abgeben"):
        st.session_state.v[pick] += 1
        st.toast(f"Stimme für {pick} gezählt!", icon='🔥')

with v2:
    v_df = pd.DataFrame(list(st.session_state.v.items()), columns=['Asset', 'Votes']).set_index('Asset')
    # Nur Assets anzeigen, die auch in der aktuellen Ticker-Liste sind
    v_df = v_df.loc[v_df.index.isin(live_df["Asset"])]
    st.bar_chart(v_df)

st.subheader("🗞️ News-Ticker")
for item in current_news[:4]:
    st.markdown(f"**{item['Asset']}**: [{item['Title']}]({item['URL']})")
