# Sparesharing Landed Cost (DE, PRO) – Streamlit Cloud

## Deploy in 3 Minuten
1) Neues GitHub-Repo anlegen und diese drei Dateien hochladen:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml` (optional für Theme)
2) Gehe zu https://share.streamlit.io (Streamlit Community Cloud)
3) **Deploy anlegen**: Wähle dein Repo, `main`-Branch und `app.py` als Hauptdatei.
4) Fertig – du bekommst eine öffentliche URL.

## Optional: SimplyDuty API
Setze in Streamlit **Secrets** (App → Settings → Secrets):
```
SIMPLYDUTY_API_KEY="DEIN_KEY"
SIMPLYDUTY_ENDPOINT="https://.../duty"
```
Aktiviere in der App-Seitenleiste „SimplyDuty API nutzen“.

## Lokal testen (optional)
```
pip install -r requirements.txt
streamlit run app.py
```

## Hinweis
- HS-/Zollsätze und Frachtraten sind Beispielwerte – bitte pflegen/prüfen.
- Für verbindliche EU-Angaben: Access2Markets/TARIC.