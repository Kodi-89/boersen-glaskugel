import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import random

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel: Gemini Edition Pro", page_icon="💎", layout="wide")

# AUTO-REFRESH: Alle 30 Sekunden (WICHTIG: streamlit-autorefresh in requirements.txt!)
st_autorefresh(interval=30 * 1000, key="data_refresh")

st.title("🔮 Börsen-Glaskugel: Gemini Edition Pro")
st.caption("Live-Kurse | CSV-Export | Golden Gemini Spotlight")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "Gemini (Google)": "GOOGL",  # 💎 Das Mutterschiff!
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=20) # TTL für frische Daten
def load_market_data():
    results = []
    news_items = []
    
    for name, symbol in tickers.items():
        try:
            t = yf.Ticker(symbol)
            f = t.fast_info
            
            # Absolute Absicherung: Nur echte Float-Werte
            curr = float(f.last_price) if f.last_price is not None else 0.0
            p_close = float(f.previous_close) if f.previous_close is not None else 0.0
            d_high = float(f.day_high) if f.day_high is not None else curr
            d_low = float(f.day_low) if f.day_low is not None else curr
            
            perf = ((curr / p_close) - 1) * 100 if p_close > 0 else 0.0
            
            # Clear Status & Signal Logik
            sig = "⚪ HOLD"
            if curr > 0 and curr >= (d_high * 0.99): sig = "🟢 BUY"
            elif perf < -9: sig = "🔴 CRASH"
            elif perf > 4: sig = "🚀 MOON"

            results.append({
                "Asset": name, "Symbol": symbol, "Preis (€/$)": round(curr, 2), 
                "Perf %": round(perf, 2), "Signal": sig
            })
            
            # News einsammeln
            raw_news = t.news
            if raw_news:
                news_items.append({"Asset": name, "Title": raw_news[0]['title'], "URL": raw_news[0]['link']})
        except:
            continue
            
    # DUPLICATE-CHECK: Wir löschen Dubletten basierend auf dem Namen
    df_clean = pd.DataFrame(results).drop_duplicates(subset=['Asset'])
    return df_clean, news_items

live_df, current_news = load_market_data()

# --- SIDEBAR: GÖNN-DIR PREMIUM TOOLS ---
st.sidebar.header("💎 Gemini Premium Tools")
if st.sidebar.button("🎲 Zufälliger Moonshot-Tipp"):
    st.sidebar.info(f"Orakel meint: Schau dir mal **{random.choice(live_df['Asset'].tolist())}** an!")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Daten-Sicherung")
csv_data = live_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="📥 Watchlist als CSV laden",
    data=csv_data,
    file_name='boersen_glaskugel_premium_export.csv',
    mime='text/csv',
)

# --- TOP SEKTION ---
col_moves, col_gauge = st.columns([2, 1])

with col_moves:
    # Top 3 Performer
    top_3 = live_df[live_df["Perf %"] > 0].sort_values(by="Perf %", ascending=False).head(3)
    if not top_3.empty:
        m_cols = st.columns(3)
        medals = ["🥇 Gold", "🥈 Silber", "🥉 Bronze"]
        for i, (idx, row) in enumerate(top_3.iterrows()):
            m_cols[i].metric(label=f"{medals[i]}: {row['Asset']}", value=f"{row['Preis (€/$)']} €/$", delta=f"{row['Perf %']}%")
    else:
        st.info("Aktuell keine Assets im Plus (Bärenmarkt).")

with col_gauge:
    # FEAR & GREED TACHO (Endgültig BUG-FREE)
    v_perf = live_df["Perf %"].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = v_perf,
        gauge = {'axis': {'range': [-5, 5]}, 'bar': {'color': "black"},
                 'steps': [
                    {'range': [-5, -1.5], 'color': "red"},
                    {'range': [-1.5, 1.5], 'color': "yellow"},
                    {'range': [1.5, 5], 'color': "green"}] # FIX HIER: [1.5, 5] statt 1.5, 5
        }
    ))
    fig_gauge.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# --- MAIN LAYOUT ---
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.header("📈 Echtzeit-Monitor Pro")
    
    # 💎 GOLDEN SPOTLIGHT LOGIK
    def spotlight_gemini(row):
        is_gem = row['Asset'] == 'Gemini (Google)'
        # Goldene Umrandung für Gemini
        border = '4px solid #ff9900' if is_gem else ''
        return [f'border: {border}' for _ in row.index]

    # STYLING & CLEAN LAYOUT (ohne Index-Zahlen)
    st.dataframe(
        live_df.style.applymap(
            lambda x: f"color: {'#00ff00' if x > 0 else '#ff4b4b'}", subset=['Perf %']
        )
        .apply(spotlight_gemini, axis=1), # Gemini Spotlight
        use_container_width=True, hide_index=True
    )

with col_r:
    st.header("🔥 Performance-Map")
    # Sicherheits-Check für Map-Daten
    df_plot = live_df[(live_df["Preis (€/$)"] > 0) & (live_df["Perf %"] != 0)].copy()
    if not df_plot.empty:
        df_plot['count'] = 1 
        try:
            fig = px.treemap(df_plot, path=['Asset'], values='count', color='Perf %', 
                             color_continuous_scale='RdYlGn', color_continuous_midpoint=0)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Börsenpause – Map macht Nickerchen.")
    
    st.subheader("🗞️ News-Ticker")
    for item in current_news[:4]:
        st.markdown(f"**{item['Asset']}**: [{item['Title']}]({item['URL']})")

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
vc1, vc2 = st.columns([1, 2])
with vc1:
    pick = st.selectbox("Nächster Moonshot?", live_df["Asset"].tolist(), key="v_final")
    if st.button("Vote abgeben"): st.session_state.v[pick] += 1
with vc2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Asset', 'Votes']).set_index('Asset'))
