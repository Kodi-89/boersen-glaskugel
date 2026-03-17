import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel Zocker-Edition", page_icon="🎲", layout="wide")

# AUTO-REFRESH: Alle 30 Sekunden
st_autorefresh(interval=30 * 1000, key="data_refresh")

st.title("🔮 Die Börsen-Glaskugel: Zocker-Edition")
st.subheader("Live-Kurse | Depot-Check | Moonshot-Generator")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=20) # TTL etwas kürzer für frische Daten
def load_data():
    results = []
    news_list = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            curr = float(info.last_price) if info.last_price else 0.0
            prev = float(info.previous_close) if info.previous_close else 0.0
            high = float(info.day_high) if info.day_high else curr
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            
            signal = "💎 HOLD"
            if curr > 0 and curr >= (high * 0.985): signal = "🚀 BUY"
            elif perf < -10: signal = "🚨 CRASH"

            results.append({
                "Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, 
                "Performance %": round(perf, 2), "Signal": signal
            })
            n = t.news
            if n: news_list.append({"Aktie": name, "Title": n[0]['title'], "Link": n[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0, "Signal": "N/A"})
    
    # DOPPEL-CHECK: Hier löschen wir alle Duplikate, falls yfinance doppelt liefert
    df = pd.DataFrame(results).drop_duplicates(subset=['Aktie'], keep='first')
    return df, news_list

live_df, all_news = load_data()

# --- SIDEBAR: ZOCKER-TOOLS ---
st.sidebar.header("🕹️ Zocker-Tools")
if st.sidebar.button("🎲 Zufälliger Moonshot-Tipp"):
    tipp = random.choice(live_df["Aktie"].tolist())
    st.sidebar.info(f"Das System empfiehlt: **{tipp}**!")

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Depot-Live-Check")
selected_stock = st.sidebar.selectbox("Welche Aktie hältst du?", live_df["Aktie"].unique())
amount = st.sidebar.number_input("Anzahl der Anteile:", min_value=0, value=0)

if amount > 0:
    row = live_df[live_df["Aktie"] == selected_stock].iloc[0]
    total_val = amount * row["Kurs"]
    daily_gain = total_val * (row['Performance %'] / 100)
    st.sidebar.metric("Gesamtwert", f"{total_val:,.2f} €")
    st.sidebar.metric("Tages-GuV", f"{daily_gain:,.2f} €", delta=f"{row['Performance %']}%")

# --- TOP SEKTION ---
col_stats, col_gauge = st.columns([2, 1])

with col_stats:
    top_3 = live_df[live_df["Performance %"] > 0].sort_values(by="Performance %", ascending=False).head(3)
    if not top_3.empty:
        m_cols = st.columns(3)
        medals = ["🥇 Gold", "🥈 Silber", "🥉 Bronze"]
        for i, (idx, row) in enumerate(top_3.iterrows()):
            m_cols[i].metric(label=f"{medals[i]}: {row['Aktie']}", value=f"{row['Kurs']} €", delta=f"{row['Performance %']}%")

with col_gauge:
    avg_perf = live_df["Performance %"].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = avg_perf,
        gauge = {'axis': {'range': [-5, 5]}, 'bar': {'color': "black"},
                 'steps': [{'range': [-5, -1.5], 'color': "red"},
                           {'range': [-1.5, 1.5], 'color': "yellow"},
                           {'range': [1.5, 5], 'color': "green"}]}
    ))
    fig_gauge.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# --- MAIN LAYOUT ---
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.header("📈 Echtzeit-Monitor")
    # Reset_index sorgt für saubere Zeilen ohne doppelte IDs
    display_df = live_df.reset_index(drop=True)
    st.dataframe(display_df.style.applymap(
        lambda x: 'color: #00ff00; font-weight: bold' if 'BUY' in str(x) else ('color: #ff4b4b' if 'CRASH' in str(x) else ''), 
        subset=['Signal']
    ).format({"Performance %": "{:.2f}%"}), use_container_width=True)

with col_r:
    st.header("🔥 Performance-Map")
    df_plot = live_df[(live_df["Kurs"] > 0) & (live_df["Performance %"] != 0)].copy()
    if not df_plot.empty:
        df_plot['size'] = 1
        fig = px.treemap(df_plot, path=['Aktie'], values='size', color='Performance %', 
                         color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🗞️ News-Ticker")
    for n in all_news[:4]:
        st.markdown(f"**{n['Aktie']}**: [{n['Title']}]({n['Link']})")

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
vc1, vc2 = st.columns([1, 2])
with vc1:
    pick = st.selectbox("Favorit?", sorted(live_df["Aktie"].tolist()), key="v_final")
    if st.button("Stimme senden"): st.session_state.v[pick] += 1
with vc2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
