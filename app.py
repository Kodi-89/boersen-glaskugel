import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel Ultra", page_icon="🔮", layout="wide")

# AUTO-REFRESH: Alle 30 Sekunden (Wichtig: streamlit-autorefresh in requirements.txt!)
st_autorefresh(interval=30 * 1000, key="data_refresh")

st.title("🔮 Die Börsen-Glaskugel Ultra")
st.subheader("Live-Terminal | Fear & Greed | Kauf-Signale")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=25)
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
            
            # SIGNAL LOGIK
            signal = "💎 HOLD"
            if curr > 0 and curr >= (high * 0.985): signal = "🚀 BUY"
            elif perf < -4: signal = "⚠️ DISKONT"

            results.append({
                "Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, 
                "Performance %": round(perf, 2), "Signal": signal
            })
            n = t.news
            if n: news_list.append({"Aktie": name, "Title": n[0]['title'], "Link": n[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0, "Signal": "N/A"})
    return pd.DataFrame(results), news_list

live_df, all_news = load_data()

# --- TOP SEKTION: MEDAILLEN & TACHO ---
head_l, head_r = st.columns([2, 1])

with head_l:
    top_3 = live_df[live_df["Performance %"] > 0].sort_values(by="Performance %", ascending=False).head(3)
    if not top_3.empty:
        m_cols = st.columns(3)
        medals = ["🥇 Gold", "🥈 Silber", "🥉 Bronze"]
        for i, (idx, row) in enumerate(top_3.iterrows()):
            m_cols[i].metric(label=f"{medals[i]}: {row['Aktie']}", value=f"{row['Kurs']} €", delta=f"{row['Performance %']}%")

with head_r:
    # FEAR & GREED TACHO
    avg_perf = live_df["Performance %"].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = avg_perf,
        title = {'text': "Markt-Stimmung (Fear vs Greed)"},
        gauge = {
            'axis': {'range': [-5, 5]},
            'bar': {'color': "black"},
            'steps': [
                {'range': [-5, -1.5], 'color': "red"},
                {'range': [-1.5, 1.5], 'color': "yellow"},
                {'range': 1.5, 5, 'color': "green"}],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': avg_perf}
        }
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# --- MAIN LAYOUT ---
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.header("📈 Echtzeit-Monitor")
    st.dataframe(live_df.style.applymap(
        lambda x: 'color: #00ff00; font-weight: bold' if 'BUY' in str(x) else '', subset=['Signal']
    ).format({"Performance %": "{:.2f}%"}), use_container_width=True)
    
    st.write("---")
    st.header("🤖 Orakel & News")
    oracle_list = sorted(list(set(live_df["Aktie"].tolist())))
    sel = st.selectbox("Wähle dein Asset:", oracle_list)
    
    if st.button("Orakel befragen"):
        row = live_df[live_df["Aktie"] == sel].iloc[0]
        if row["Performance %"] > 5: st.balloons()
        st.info(f"Analyse für {sel}: Performance liegt bei {row['Performance %']}%. Signal: {row['Signal']}")
        
        spec_news = next((item for item in all_news if item["Aktie"] == sel), None)
        if spec_news: st.markdown(f"🔗 [Direkt zur News]({spec_news['Link']})")

with col_r:
    st.header("🔥 Performance-Map")
    df_plot = live_df[(live_df["Kurs"] > 0) & (live_df["Performance %"] != 0)].copy()
    if not df_plot.empty:
        df_plot['size'] = 1
        fig = px.treemap(df_plot, path=['Aktie'], values='size', color='Performance %', 
                         color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🗞️ Letzte Meldungen")
    for n in all_news[:4]:
        st.markdown(f"**{n['Aktie']}**: [{n['Title']}]({n['Link']})")

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v_c1, v_c2 = st.columns([1, 2])
with v_c1:
    pick = st.selectbox("Welche Aktie pumpt als Nächstes?", oracle_list, key="v_final")
    if st.button("Vote abgeben"): st.session_state.v[pick] += 1
with v_c2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
