import os
import json
from datetime import datetime
from typing import Dict, Any

import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sparesharing Landed Cost (DE, PRO)", page_icon="📦", layout="wide")

import streamlit as st

st.set_page_config(page_title="Landing Cost Calculator – Sparesharing")

col1, col2 = st.columns([1,5])
with col1:
    st.image("logo.png", width=120)  # Logo einfügen
with col2:
    st.title("Landing Cost Calculator")
    st.caption("Sparesharing – Dein Partner für transparente Beschaffungskosten")


# -----------------------------
# Defaults / Settings
# -----------------------------

DEFAULT_VAT = {
    "Österreich": 0.20,
    "Deutschland": 0.19,
    "Italien": 0.22,
    "Tschechien": 0.21,
    "Polen": 0.23,
    "Slowakei": 0.20,
}

AIR_RATE_PER_KG = {
    "Österreich": 4.2,
    "Deutschland": 4.0,
    "Italien": 4.5,
    "Tschechien": 4.4,
    "Polen": 4.6,
    "Slowakei": 4.3,
}

HS_DUTY_LOOKUP = {
    "8501.10": 0.025,
    "8414.59": 0.03,
    "8504.40": 0.02,
    "8536.50": 0.03,
    "8414.51": 0.03,
}

VOLUMETRIC_FACTOR = 167.0  # kg/m³
BASE_FEE_EUR = 80.0
SEA_RATE_EUR_PER_M3 = 65.0
RAIL_RATE_EUR_PER_M3 = 120.0
EXPRESS_RATE_EUR_PER_KG = 5.2

def fmt_eur(x: float) -> str:
    return f"€ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def call_simplyduty(api_key: str, base_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        resp = requests.post(base_url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.warning(f"SimplyDuty API HTTP {resp.status_code}: {resp.text[:200]}")
            return {}
    except Exception as e:
        st.warning(f"SimplyDuty API Fehler: {e}")
        return {}

# Sidebar for API + lead
with st.sidebar:
    st.markdown("### 📧 Lead (optional)")
    lead_email = st.text_input("E-Mail", value="", placeholder="name@firma.com")
    lead_company = st.text_input("Firma", value="", placeholder="Ihre Firma")
    consent = st.checkbox("Ich stimme zu, dass meine Daten gespeichert werden.", value=True)
    st.markdown("---")
    st.markdown("**API-Integration (optional)**")
    use_api = st.checkbox("SimplyDuty API nutzen", value=False)
    api_key = st.text_input("SIMPLYDUTY_API_KEY (oder in secrets setzen)", type="password", value=st.secrets.get("SIMPLYDUTY_API_KEY", ""))
    api_url = st.text_input("SIMPLYDUTY_ENDPOINT", value=st.secrets.get("SIMPLYDUTY_ENDPOINT", ""),
                            help="Endpoint laut offizieller Doku, z. B. https://.../duty")
    st.markdown("---")
    st.caption("Hinweis: HS-/Zollsätze und Frachtraten sind Beispielwerte. Für verbindliche Berechnungen offizielle Quellen prüfen (EU Access2Markets/TARIC).")

st.title("📦 Sparesharing – Landed Cost Rechner (DE, PRO)")
st.write("Berechne deine **Gesamtkosten bis zum Zielort** (inkl. CIF, Zoll, MwSt., Gebühren).")

# Inputs
colA, colB, colC = st.columns([1,1,1])

with colA:
    incoterm = st.selectbox("Incoterm", ["EXW", "FOB", "CIF"], index=1)
    dest_country = st.selectbox("Zielland (MwSt./Luftfracht)", list(DEFAULT_VAT.keys()), index=0)
    currency = st.selectbox("Währung (Lieferant)", ["USD", "EUR", "CNY", "GBP", "JPY", "CHF"], index=0)
    fx_to_eur = st.number_input("FX Kurs → EUR (1 Währung = EUR)", min_value=0.0001, value=0.92, step=0.01, format="%.4f")

with colB:
    unit_price = st.number_input("Stückpreis (Lieferant, in Währung)", min_value=0.0, value=10.0, step=0.01, format="%.4f")
    qty = st.number_input("Menge (Stück)", min_value=1, value=1000, step=1)
    weight_kg = st.number_input("Bruttogewicht (kg)", min_value=0.0, value=200.0, step=0.1)
    volume_m3 = st.number_input("Volumen (m³)", min_value=0.0, value=1.5, step=0.01, format="%.2f")

with colC:
    hs_code = st.text_input("HS-Code (optional)", value="8414.59")
    ship_mode = st.selectbox("Transportmodus", ["See", "Luft", "Schiene", "Express"], index=0)
    freight_mode = st.selectbox("Fracht – Eingabeart", ["Automatisch", "Manuell"], index=0)
    manual_freight = st.number_input("Fracht (manuell, EUR)", min_value=0.0, value=1500.0, step=10.0)
    insurance_rate = st.number_input("Versicherungsrate", min_value=0.0, value=0.003, step=0.001, format="%.3f")
    local_broker = st.number_input("Brokerage & Hafen-/Zollgebühren (EUR)", min_value=0.0, value=250.0, step=10.0)
    local_other = st.number_input("Sonstige Gebühren (EUR)", min_value=0.0, value=50.0, step=10.0)

# Core calculation
unit_eur = unit_price * fx_to_eur
goods_value = unit_eur * qty

volumetric_kg = volume_m3 * VOLUMETRIC_FACTOR
if freight_mode == "Manuell":
    freight_eur = manual_freight
else:
    if ship_mode == "See":
        freight_eur = volume_m3 * SEA_RATE_EUR_PER_M3 + BASE_FEE_EUR
    elif ship_mode == "Schiene":
        freight_eur = volume_m3 * RAIL_RATE_EUR_PER_M3 + BASE_FEE_EUR
    elif ship_mode == "Luft":
        perkg = AIR_RATE_PER_KG.get(dest_country, 4.2)
        freight_eur = max(weight_kg, volumetric_kg) * perkg + BASE_FEE_EUR
    else:  # Express
        freight_eur = max(weight_kg, volumetric_kg) * EXPRESS_RATE_EUR_PER_KG + BASE_FEE_EUR

insurance_eur = insurance_rate * goods_value
if incoterm == "CIF":
    customs_base = goods_value
else:
    customs_base = goods_value + freight_eur + insurance_eur

# Duty rate: API > HS-Table > default 5%
duty_rate = HS_DUTY_LOOKUP.get(hs_code.strip(), 0.05)

api_data = {}
if use_api and api_key and api_url:
    payload = {
        "destination_country": dest_country,
        "hs_code": hs_code.strip(),
        "customs_value_eur": customs_base,
        "goods_value_eur": goods_value,
        "freight_eur": freight_eur,
        "insurance_eur": insurance_eur,
    }
    api_data = call_simplyduty(api_key, api_url, payload)
    for key in ("duty_rate", "dutyRate", "duty_percent"):
        if key in api_data and isinstance(api_data[key], (int, float)):
            duty_rate = float(api_data[key])
            break

duty_amount = customs_base * duty_rate
vat_rate = DEFAULT_VAT.get(dest_country, 0.20)
vat_amount = (customs_base + duty_amount) * vat_rate
local_fees = local_broker + local_other
total_landed = customs_base + duty_amount + vat_amount + local_fees
unit_landed = total_landed / qty if qty else 0.0
freight_share = (freight_eur / total_landed) if total_landed else 0.0

# Results
st.subheader("Ergebnisse")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Warenwert", fmt_eur(goods_value))
m2.metric("CIF / Zollwert-Basis", fmt_eur(customs_base))
m3.metric("Zollabgaben", fmt_eur(duty_amount))
m4.metric("MwSt.", fmt_eur(vat_amount))

m5, m6, m7 = st.columns(3)
m5.metric("Lokale Gebühren gesamt", fmt_eur(local_fees))
m6.metric("Gesamtkosten (Landed Cost)", fmt_eur(total_landed))
m7.metric("Kosten pro Stück", fmt_eur(unit_landed))

st.progress(min(1.0, freight_share), text=f"Frachtanteil ~ {freight_share*100:.1f}%")

st.markdown("#### Detailtabelle")
df = pd.DataFrame([{
    "Incoterm": incoterm,
    "Zielland": dest_country,
    "Währung": currency,
    "FX→EUR": fx_to_eur,
    "Stückpreis EUR": unit_eur,
    "Menge": qty,
    "Warenwert EUR": goods_value,
    "Gewicht kg": weight_kg,
    "Volumen m³": volume_m3,
    "Volumengewicht kg": volumetric_kg,
    "Fracht EUR": freight_eur,
    "Versicherung EUR": insurance_eur,
    "Zollwert (CIF-Basis) EUR": customs_base,
    "HS-Code": hs_code,
    "Zollsatz %": duty_rate,
    "Zoll EUR": duty_amount,
    "MwSt.-Satz %": vat_rate,
    "MwSt. EUR": vat_amount,
    "Gebühren EUR": local_fees,
    "Total Landed EUR": total_landed,
    "€/Stück": unit_landed,
}])
st.dataframe(df, use_container_width=True)

st.download_button("⬇️ Ergebnisse als CSV", data=df.to_csv(index=False).encode("utf-8"),
                   file_name="landed_cost_result.csv", mime="text/csv")

st.download_button("⬇️ Ergebnisse als JSON", data=df.to_json(orient="records", indent=2).encode("utf-8"),
                   file_name="landed_cost_result.json", mime="application/json")

st.markdown("##### Offizieller EU-Link (Access2Markets)")
if hs_code.strip():
    url = f"https://trade.ec.europa.eu/access-to-markets/en/results?text={hs_code.strip()}"
    st.markdown(f"[HS-Code in Access2Markets öffnen]({url})")

# Optional: lead capture (local JSON)
if consent and lead_email:
    row = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "email": lead_email,
        "company": lead_company,
        "input": {
            "incoterm": incoterm, "dest": dest_country, "currency": currency, "fx": fx_to_eur,
            "unit_price": unit_price, "qty": qty, "weight": weight_kg, "volume": volume_m3,
            "hs_code": hs_code, "ship_mode": ship_mode
        },
        "result": {"total_landed": total_landed, "unit_landed": unit_landed}
    }
    try:
        existing = []
        leads_path = "leads.json"
        if os.path.exists(leads_path):
            with open(leads_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.append(row)
        with open(leads_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        st.success("Lead gespeichert (lokal in leads.json).")
    except Exception as e:
        st.warning(f"Lead konnte nicht gespeichert werden: {e}")

st.markdown("---")
st.caption("⚠️ Haftungsausschluss: Diese App liefert Schätzungen. Zollsätze/MwSt. ändern sich. Prüfen Sie verbindliche Angaben in offiziellen Quellen (EU Access2Markets/TARIC).")
