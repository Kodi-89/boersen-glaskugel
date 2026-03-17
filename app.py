import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from fpdf import FPDF
import base64
from datetime import datetime
import io

# --- KONFIGURATION ---
st.set_page_config(page_title="Börsen-Glaskugel", page_icon="🔮", layout="wide")

st.title("🔮 Die Börsen-Glaskugel")
st.subheader("Live-Performance & Community Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("🛠 Info & Regeln")
rules = [
    "1. Kein Mietgeld nutzen.",
    "2. Immer einen Stop-Loss setzen.",
    "3. Gewinne konsequent abschöpfen."
]
for rule in rules:
    st.sidebar.warning(rule)

# --- DATEN-ENGINE ---
tickers = {
    "SUSS MicroTec": "SUE.DE", "Delivery Hero": "DHER.DE", "Puma SE": "PUM.DE", 
    "TUI AG": "TUI1.DE", "Sable Offshore": "SOC", "Immunic Inc.": "IMUX",
    "Rheinmetall": "RHM.DE", "Gemini Space": "GEMI",
    "Tesla, Inc.": "TSLA", "AMD, Inc.": "AMD", "Microsoft": "MSFT"
}

@st.cache_data(ttl=60)
def load_data():
    results = []
    news_list = []
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                curr = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                perf = ((curr / prev) - 1) * 100
            else:
                curr = t.fast_info.last_price or 0.0
                perf = 0.0
            
            # WICHTIGER FIX: Wir stellen sicher, dass alle Werte sauber sind (float)
            if curr is None or perf is None:
                curr, perf = 0.0, 0.0
            else:
                curr, perf = float(curr), float(perf)

            results.append({"Aktie": name, "Kurs": round(curr, 2), "Symbol": sym, "Performance %": round(perf, 2)})
            
            n = t.news
            if n: news_list.append({"Aktie": name, "Headline": n[0]['title'], "Link": n[0]['link']})
        except:
            results.append({"Aktie": name, "Kurs": 0.0, "Symbol": sym, "Performance %": 0.0})
    return pd.DataFrame(results), news_list

live_df, live_news = load_data()

# --- LAYOUT ---
col_l, col_r = st.columns([1, 1.2])

with col_l:
    st.header("📈 Echtzeit-Kurse")
    st.dataframe(live_df.style.format({"Performance %": "{:.2f}%"}), use_container_width=True)
    st.write("---")
    st.subheader("🗞️ Top-Schlagzeilen")
    for n in live_news[:3]:
        st.markdown(f"**{n['Aktie']}**: [{n['Headline']}]({n['Link']})")

with col_r:
    st.header("🔥 24h Performance-Map")
    # ABSOLUTE ABSICHERUNG GEGEN TYPERRORS:
    # 1. Nur Aktien mit Kurs > 0
    # 2. Nur Aktien mit sauberen Float-Werten
    # 3. Wir berechnen die Größe direkt im DF
    df_plot = live_df[live_df["Kurs"] > 0].copy()
    
    # Sicherstellen, dass die Performance-Spalte numerisch ist und keine "None" enthält
    df_plot['Performance %'] = pd.to_numeric(df_plot['Performance %'], errors='coerce').fillna(0)
    df_plot['size'] = 1 
    
    if not df_plot.empty:
        fig = px.treemap(
            df_plot, path=['Aktie'], values='size',
            color='Performance %', color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0, text_auto='.2f'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Marktdaten werden geladen...")

# --- PDF REPORT DOWNLOADER ---
st.divider()
st.header("📄 Markt-Bericht")
st.write("Hier kannst du dir einen aktuellen Schnappschuss deiner Glaskugel-Daten als PDF herunterladen.")

def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    
    # Titel & Zeit
    pdf.cell(190, 10, 'Markt-Bericht: Die Börsen-Glaskugel', ln=True, align='C')
    pdf.set_font('Arial', '', 10)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.cell(190, 10, f'Stand: {now_str}', ln=True, align='C')
    pdf.ln(10)
    
    # Regeln
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, '💡 Die Glaskugel-Regeln:', ln=True)
    pdf.set_font('Arial', '', 10)
    for rule in rules:
        pdf.cell(190, 8, f'  - {rule}', ln=True)
    pdf.ln(10)
    
    # Tabelle: Kopfzeile
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 10, 'Aktie', border=1, fill=True)
    pdf.cell(40, 10, 'Symbol', border=1, fill=True)
    pdf.cell(40, 10, 'Kurs', border=1, fill=True, align='R')
    pdf.cell(40, 10, 'Performance %', border=1, fill=True, align='R')
    pdf.ln(10)
    
    # Tabelle: Daten
    pdf.set_font('Arial', '', 9)
    # Wir filtern die Tabelle für das PDF auf saubere Daten
    df_clean = df[df["Kurs"] > 0].copy()
    for _, row in df_clean.iterrows():
        pdf.cell(60, 10, str(row['Aktie']), border=1)
        pdf.cell(40, 10, str(row['Symbol']), border=1)
        pdf.cell(40, 10, f"{row['Kurs']:.2f} €", border=1, align='R')
        pdf.cell(40, 10, f"{row['Performance %']:.2f}%", border=1, align='R')
        pdf.ln(10)
    
    # PDF in Bytes umwandeln
    pdf_out = io.BytesIO(pdf.output(dest='S'))
    return pdf_out

# PDF Button
pdf_bytes = generate_pdf(live_df)
st.download_button(
    label="Marktbericht als PDF herunterladen",
    data=pdf_bytes,
    file_name=f"glaskugel_bericht_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
    mime="application/pdf",
)

# --- VOTING ---
st.divider()
if 'v' not in st.session_state: st.session_state.v = {k: 0 for k in tickers.keys()}
v1, v2 = st.columns([1, 2])
with v1:
    st.header("🗳️ Voting")
    pick = st.selectbox("Dein Favorit?", list(tickers.keys()))
    if st.button("Senden"): st.session_state.v[pick] += 1
with v2:
    st.bar_chart(pd.DataFrame(list(st.session_state.v.items()), columns=['Aktie', 'Votes']).set_index('Aktie'))
