import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & Community Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("🛠 Info & Regeln")
rules = ["1. Kein Mietgeld nutzen.", "2. Stop-Loss setzen.", "3. Gewinne abschöpfen."]
for rule in rules:
    st.sidebar.warning(rule)

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_dict = {} # News pro Aktie speichern
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            curr = info.last_price
            prev = info.previous_close
            curr = float(curr) if curr is not None else 0.0
            prev = float(prev) if prev is not None else 0.0
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            
            results.append({
                "Aktie": name, 
                "Kurs": round(curr, 2), 
                "Symbol": sym, 
                "Performance %": round(perf, 2)
            })
            
            # News laden
            n = t.news
            if n:
                # Wir speichern Headline und Link als Tuple
                news_dict[name] = (n[0]['title'], n[0]['link'])
                
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_dict

live_df, live_news_dict = load_data()

# --- LAYOUT ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    
    # --- DAS VERBESSERTE KI-ORAKEL ---
    st.write("---")
    st.header("🤖 Das Glaskugel-Orakel")
    
    # FIX: Wir nutzen set() um Duplikate zu entfernen und sorted() für A-Z
    oracle_list = sorted(list(set(live_df["Aktie"].tolist())))
    
    selected_oracle = st.selectbox("Wähle eine Aktie für eine Prognose:", oracle_list)
    
    if st.button("Orakel befragen"):
        row = live_df[live_df["Aktie"] == selected_oracle].iloc[0]
        perf = row["Performance %"]
        news_data = live_news_dict.get(selected_oracle)
        
        # News auswerten
        if news_data:
            headline, link = news_data
            news_text = f"News-Kontext: '{headline}'"
            news_link_md = f"[Zum Artikel springen →]({link})"
        else:
            news_text = "News-Kontext: Keine frischen Schlagzeilen."
            news_link_md = ""
            headline = "Stille"

        st.write(f"**Analyse für {selected_oracle}:**")
        st.write(f"*{news_text}*")
        if news_link_md: st.markdown(news_link_md)

        if perf > 5:
            st.balloons() # Raketen-Effekt bei Gewinnern
            st.success(f"🚀 **RAKETEN-MODUS!** {perf}% Plus. Die Schlagzeile '{headline}' zündet! Das Orakel sagt: Anschnallen!")
        elif perf > 0:
            st.info(f"✅ **SOLID.** {perf}% sind grüner Bereich. '{headline}' stützt. Das Orakel rät: Gewinne laufen lassen.")
        elif perf < -5:
            st.error(f"💀 **ALARM!** {perf}% Crash. '{headline}' zieht runter. Das Orakel sieht Blut auf den Straßen.")
        elif perf < 0:
            st.warning(f"📉 **MÜDE BULLEN.** {perf}% Minus. Trotz '{headline}' fehlt der Schwung.")
        else:
            st.write("💤 **STILLSTAND.** Das Orakel gähnt bei diesem Kurs.")

with col_r:
    st.header("🔥 24h Performance-Map")
    # Nur Aktien mit Kurs > 0 in die Map, damit Plotly nicht meckert
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    if not df_plot.empty:
        df_plot['size'] = 1 
        fig = px.treemap(
            df_plot, path=['Aktie'], values='size',
            color='Performance %', color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0, text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Warte auf Marktdaten (Börsenpause)...")

# --- VOTING ---
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
