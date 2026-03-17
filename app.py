import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel Pro Export", page_icon="📈", layout="wide")

# AUTO-REFRESH: Alle 30 Sekunden
st_autorefresh(interval=30 * 1000, key="data_refresh")

st.title("🔮 Börsen-Glaskugel Pro")
st.caption("Live-Daten & CSV-Export-Funktion")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=15)
def load_market_data():
    data_rows = []
    news_items = []
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            f = t.fast_info
            price = float(f.last_price) if f.last_price else 0.0
            p_close = float(f.previous_close) if f.previous_close else 0.0
            day_high = float(f.day_high) if f.day_high else price
            change = ((price / p_close) - 1) * 100 if p_close > 0 else 0.0
            
            status = "⚪ HOLD"
            if price > 0 and price >= (day_high * 0.99): status = "🟢 BUY"
            elif change < -8: status = "🔴 CRASH"
            elif change > 4: status = "🚀 MOON"

            data_rows.append({"Asset": name, "Symbol": symbol, "Preis (€)": round(price, 2), "Performance %": round(change, 2), "Status": status})
            raw_news = t.news
            if raw_news: news_items.append({"Asset": name, "Title": raw_news[0]['title'], "URL": raw_news[0]['link']})
        except: continue
    return pd.DataFrame(data_rows).drop_duplicates(subset=['Asset']), news_items

df, news = load_market_data()

# --- SIDEBAR: EXPORT & TOOLS ---
st.sidebar.header("📂 Daten-Export")
csv = df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Watchlist als CSV laden",
    data=csv,
    file_name='boersen_glaskugel_export.csv',
    mime='text/csv',
)

st.sidebar.markdown("---")
if st.sidebar.button("🎲 Zufalls-Check"):
    st.sidebar.info(f"Fokus heute auf: **{random.choice(df['Asset'].tolist())}**")

# --- HAUPTBEREICH ---
col_stats = st.columns(3)
top = df.sort_values(by="Performance %", ascending=False).iloc[0]
avg = df["Performance %"].mean()
col_stats[0].metric("Top Mover", top['Asset'], f"{top['Performance %']}%")
col_stats[1].metric("Markt-Schnitt", "Watchlist", f"{round(avg, 2)}%")
col_stats[2].metric("Assets", "Aktiv", len(df))

st.divider()

left, right = st.columns([1, 1.5])
with left:
    st.subheader("🔥 Heatmap")
    fig = px.treemap(df, path=['Asset'], values='Preis (€)', color='Performance %', color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📊 Live-Monitor")
    st.dataframe(df.style.applymap(lambda x: f"color: {'#00ff00' if x > 0 else '#ff4b4b'}", subset=['Performance %']), use_container_width=True, hide_index=True)

st.divider()
st.subheader("🗞️ News-Ticker")
for item in news[:5]:
    st.markdown(f"**{item['Asset']}**: [{item['Title']}]({item['URL']})")
