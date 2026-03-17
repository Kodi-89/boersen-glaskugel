iimport streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & News Dashboard")
st.markdown("---")

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_list = [] 
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            curr = info.last_price or 0.0
            prev = info.previous_close or 0.0
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            
            results.append({"Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, "Performance %": round(perf, 2)})
            
            # Alle News sammeln
            n = t.news
            if n:
                news_list.append({"Aktie": name, "Title": n[0]['title'], "Link": n[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_list

live_df, all_news = load_data()

# --- LAYOUT ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    
    st.write("---")
    st.header("🤖 Das Glaskugel-Orakel")
    oracle_list = sorted(list(set(live_df["Aktie"].tolist())))
    selected_oracle = st.selectbox("Wähle eine Aktie:", oracle_list)
    
    if st.button("Orakel befragen"):
        row = live_df[live_df["Aktie"] == selected_oracle].iloc[0]
        perf = row["Performance %"]
        # Finde News für diese spezielle Aktie
        specific_news = next((item for item in all_news if item["Aktie"] == selected_oracle), None)
        
        st.write(f"**Analyse für {selected_oracle}:**")
        if specific_news:
            st.markdown(f"🔗 [AKTUELL: {specific_news['Title']}]({specific_news['Link']})")
        
        if perf > 5:
            st.balloons()
            st.success(f"🚀 RAKETE! {perf}% Plus. Das Orakel sagt: Anschnallen!")
        elif perf > 0:
            st.info(f"✅ Stabil. {perf}% Plus. Gewinne laufen lassen.")
        else:
            st.warning(f"📉 {perf}%. Das Orakel rät zur Vorsicht.")

with col_r:
    st.header("🔥 24h Performance-Map")
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        df_plot['size'] = 1 
        fig = px.treemap(df_plot, path=['Aktie'], values='size', color='Performance %', color_continuous_scale='RdYlGn', color_continuous_midpoint=0, text_auto='.2f')
        st.plotly_chart(fig, use_container_width=True)
    
    # --- NEU: NEWS ZENTRALE DIREKT SICHTBAR ---
    st.write("---")
    st.subheader("🗞️ Aktuelle Schlagzeilen (Live)")
    if all_news:
        for n in all_news[:5]: # Die 5 neuesten News anzeigen
            st.markdown(f"**{n['Aktie']}**: [{n['Title']}]({n['Link']})")
    else:
        st.write("Keine News gefunden (Börse schläft).")

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Voting")
    pick = st.selectbox("Favorit?", oracle_list)
    if st.button("Senden"): st.session_state.v[pick] += 1
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
