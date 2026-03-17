import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & News Dashboard")
st.markdown("---")

# --- DATEN-ENGINE (Optimiert für Stabilität) ---
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
            
            # ABSOLUTE ABSICHERUNG: Wenn Daten fehlen, setzen wir 0.0
            curr = info.last_price if info.last_price is not None else 0.0
            prev = info.previous_close if info.previous_close is not None else 0.0
            perf = ((curr / prev) - 1) * 100 if (prev and prev > 0) else 0.0
            
            results.append({
                "Aktie": name, 
                "Kurs": round(float(curr), 2), 
                "Symbol": sym, 
                "Performance %": round(float(perf), 2)
            })
            
            # News sammeln (mit Link)
            n = t.news
            if n:
                news_list.append({"Aktie": name, "Title": n[0]['title'], "Link": n[0]['link']})
        except:
            # Fallback bei komplettem Fehler
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_list

live_df, all_news = load_data()

# --- NEU: GOLDENE MEDAILLEN (Ganz Oben) ---
# Wir sortieren und holen die Top 3, aber nur wenn sie eine Performance > 0 haben
top_performers = live_df[live_df["Performance %"] > 0].sort_values(by="Performance %", ascending=False).head(3)

if not top_performers.empty:
    st.subheader("🏆 Die Top-Aktien des Tages")
    t_c1, t_c2, t_c3 = st.columns(3)
    cols = [t_c1, t_c2, t_c3]
    medals = ["🥇 Gold", "🥈 Silber", "🥉 Bronze"]
    colors = ["#ff9900", "#acacac", "#cd7f32"] # Gold, Silber, Bronze Farben

    for i, (idx, row) in enumerate(top_performers.iterrows()):
        cols[i].markdown(f"**{medals[i]}**")
        cols[i].metric(
            label=f"{row['Aktie']} ({row['Symbol']})",
            value=f"{row['Kurs']} €",
            delta=f"{row['Performance %']}%",
            delta_color="normal"
        )
else:
    st.write("Warte auf frische Gewinner (Börse evtl. geschlossen).")

st.markdown("---")

# --- LAYOUT: MAP & ORACLE ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    
    st.write("---")
    st.header("🤖 Das Glaskugel-Orakel")
    # FIX: Liste bereinigen und sortieren
    oracle_list = sorted(list(set(live_df["Aktie"].tolist())))
    selected_oracle = st.selectbox("Wähle eine Aktie:", oracle_list)
    
    if st.button("Orakel befragen"):
        row = live_df[live_df["Aktie"] == selected_oracle].iloc[0]
        perf = row["Performance %"]
        
        # News-Link für diese Aktie suchen
        specific_news = next((item for item in all_news if item["Aktie"] == selected_oracle), None)
        
        st.write(f"**Analyse für {selected_oracle}:**")
        if perf > 5:
            st.balloons() # Raketen-Effekt bei Gewinnern
            st.success(f"🚀 **RAKETEN-MODUS!** {perf}% Plus. Das Orakel sagt: Halt dich fest, wir fliegen!")
        elif perf > 0:
            st.info(f"✅ **SOLIDE.** {perf}% sind grüner Bereich. Das Orakel rät: Entspannt zurücklehnen.")
        elif perf < -5:
            st.error(f"💀 **AUTSCH.** {perf}% im Keller. Zeit für starke Nerven.")
        else:
            st.write("💤 **STILLSTAND.** Das Orakel gähnt.")
        
        # Link anzeigen
        if specific_news:
            st.markdown(f"🔗 [Hier geht's zur News: {specific_news['Title']}]({specific_news['Link']})")

with col_r:
    st.header("🔥 24h Performance-Map")
    # ABSOLUTER FIX FÜR DEN FEHLER: Nur Aktien mit Kurs > 0 in die Map, damit Plotly nicht abstürzt
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        df_plot['size'] = 1 
        fig = px.treemap(
            df_plot, 
            path=['Aktie'], 
            values='size', 
            color='Performance %', 
            color_continuous_scale='RdYlGn', 
            color_continuous_midpoint=0, 
            text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Warte auf frische Marktdaten...")
    
    # --- NEWS-ZENTRALE ---
    st.write("---")
    st.subheader("🗞️ Aktuelle Schlagzeilen (Live)")
    if all_news:
        for n in all_news[:5]: # Die 5 neuesten News anzeigen
            st.markdown(f"**{n['Aktie']}**: [{n['Title']}]({n['Link']})")
    else:
        st.write("Keine News gefunden (Börse macht Pause).")

# --- COMMUNITY VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Community-Voting")
    pick = st.selectbox("Wer zündet als Nächstes?", oracle_list) # Auch hier die saubere Liste
    if st.button("Stimme abgeben"): 
        st.session_state.v[pick] += 1
        st.toast(f"Stimme für {pick} gezählt!", icon='🔥')
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
