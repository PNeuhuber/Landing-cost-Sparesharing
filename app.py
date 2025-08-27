import streamlit as st
import pandas as pd

# --------------------------------------------------
# Grundkonfiguration
# --------------------------------------------------
st.set_page_config(
    page_title="Landing Cost Calculator – Sparesharing",
    page_icon="💼",
    layout="wide"
)

# --------------------------------------------------
# Branding: Logo + Titel
# --------------------------------------------------
col1, col2 = st.columns([1,5])
with col1:
    st.image("logo.png", width=120)   # Logo einfügen
with col2:
    st.title("Landing Cost Calculator")
    st.caption("Sparesharing – Dein Partner für transparente Beschaffungskosten")

st.markdown("---")

# --------------------------------------------------
# Eingabebereich
# --------------------------------------------------
col1, col2, col3, col4 = st.columns([1.2,1,1,1])

with col1:
    product_name = st.text_input("Produkt", placeholder="z. B. Alu-Profil 2020")

with col2:
    price_cn = st.number_input("Warenwert (CNY)", min_value=0.0, format="%.2f", step=100.0)

with col3:
    freight = st.number_input("Fracht (CNY)", min_value=0.0, format="%.2f", step=50.0)

with col4:
    insurance = st.number_input("Versicherung (CNY)", min_value=0.0, format="%.2f", step=10.0)

colA, colB, colC = st.columns([1,1,1])
with colA:
    fx_rate = st.number_input("Wechselkurs CNY→EUR", value=0.1250, step=0.0001, format="%.4f")
with colB:
    duty_rate = st.number_input("Zollsatz (%)", value=2.7, step=0.1, format="%.1f")
with colC:
    vat_rate = st.number_input("USt Österreich (%)", value=20.0, step=1.0, format="%.0f")

# --------------------------------------------------
# Berechnung
# --------------------------------------------------
cif_cny = price_cn + freight + insurance
duty_cny = cif_cny * (duty_rate/100)
vat_cny  = (cif_cny + duty_cny) * (vat_rate/100)
total_cny = cif_cny + duty_cny + vat_cny

# Umrechnung in EUR
cif_eur    = cif_cny * fx_rate
duty_eur   = duty_cny * fx_rate
vat_eur    = vat_cny * fx_rate
total_eur  = total_cny * fx_rate

# --------------------------------------------------
# Tabelle vorbereiten
# --------------------------------------------------
df = pd.DataFrame({
    "Position": ["Warenwert+Fracht+Versicherung (CIF)", "Zoll", "USt", "Gesamt"],
    "CNY": [cif_cny, duty_cny, vat_cny, total_cny],
    "EUR": [cif_eur, duty_eur, vat_eur, total_eur],
})

# Formatierung (DE-Zahlenformat)
fmt = { 
    "CNY": lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ¥",
    "EUR": lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
}

# --------------------------------------------------
# Ausgabe
# --------------------------------------------------
st.subheader("Kostenübersicht")
st.dataframe(
    df.style.format(fmt),
    use_container_width=True,
    hide_index=True
)

st.metric("Gesamtkosten (EUR)", f"{total_eur:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €")

# --------------------------------------------------
# Fußzeile mit kleinem Logo
# --------------------------------------------------
st.markdown(
    """
    <div style="text-align:center; margin-top:2rem; color: #64748B;">
        <img src="logo.png" width="100"><br>
        © 2025 Sparesharing – Global Sourcing & Smart Maintenance
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("---")
st.caption("⚠️ Haftungsausschluss: Diese App liefert Schätzungen. Zollsätze/MwSt. ändern sich. Prüfen Sie verbindliche Angaben in offiziellen Quellen (EU Access2Markets/TARIC).")
