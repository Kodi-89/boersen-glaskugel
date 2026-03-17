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
    "Rheinmetall": "RHM.DE", "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_dict = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            info = t.fast_info
            curr = float(info.last_price) if info.last_price else 0.0
            prev = float(info.previous_close) if info.previous_close else 0.0
            perf = ((curr / prev) - 1) * 100 if prev > 0 else 0.0
            results.append({"Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, "Performance %": round(perf, 2)})
            n = t.news
            if n: news_dict[name] = n[0]['title']
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_dict

live_df, live_news_dict = load_data()

# --- LAYOUT ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    
    st.write("---")
    st.header("🤖 Das Glaskugel-Orakel")
    # FIX: Eindeutige Liste für das Menü
    oracle_list = sorted(list(set(live_df["Aktie"].tolist())))
    selected_oracle = st.selectbox("Wähle eine Aktie für eine Prognose:", oracle_list)
    
    if st.button("Orakel befragen"):
        row = live_df[live_df["Aktie"] == selected_oracle].iloc[0]
        perf = row["Performance %"]
        headline = live_news_dict.get(selected_oracle, "keine frischen Schlagzeilen")
        
        st.write(f"**Analyse für {selected_oracle}:**")
        st.write(f"*Aktuelle News: {headline}*")
        
        if perf > 5:
            st.balloons() # RAKETEN-EFFEKT!
            st.success(f"🚀 **RAKETEN-MODUS!** {perf}% Plus. Die News '{headline}' zündet! Wer jetzt nicht drin ist, guckt in die Röhre.")
        elif perf > 0:
            st.info(f"✅ **SOLIDE.** {perf}% sind grüner Bereich. Die News '{headline}' stützt den Kurs.")
        elif perf < -5:
            st.error(f"💀 **ALARM!** {perf}% Crash. '{headline}' zieht den Kurs runter. Das Orakel rät: Nerven aus Stahl oder wegrennen.")
        elif perf < 0:
            st.warning(f"📉 **MÜDE BULLEN.** {perf}% Minus. Trotz der News fehlt der Pfeffer.")
        else:
            st.write("💤 **STILLSTAND.** Das Orakel gähnt bei diesen News.")

with col_r:
    st.header("🔥 24h Performance-Map")
    # ABSOLUTER FIX FÜR DEN ERROR: Nur plotten, wenn Daten da sind!
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
        st.warning("⚠️ Die Börsen machen gerade Pause. Sobald Kurse fließen, glüht hier die Heatmap!")

# --- COMMUNITY VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Community-Voting")
    pick = st.selectbox("Wer zündet als Nächstes?", oracle_list)
    if st.button("Stimme abgeben"): 
        st.session_state.v[pick] += 1
        st.toast(f"Stimme für {pick} gezählt!", icon='🔥')
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
