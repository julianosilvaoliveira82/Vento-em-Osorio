import datetime as dt
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Vento em Osório", page_icon="💨", layout="wide")

st.title("💨 Vento em Osório — RS")
st.caption("Demo em Streamlit usando dados da Open-Meteo (gratuita)")

# Coordenadas aproximadas de Osório/RS
LAT, LON = -29.885, -50.267

with st.sidebar:
    st.header("Configurações")
    dias = st.slider("Dias de previsão", min_value=1, max_value=7, value=3)
    metricas = st.multiselect(
        "Variáveis",
        ["windspeed_10m", "windgusts_10m", "winddirection_10m"],
        default=["windspeed_10m", "windgusts_10m"],
    )
    st.info("Fonte: open-meteo.com • Sem chave de API", icon="ℹ️")

# Monta a chamada de API
endpoint = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": LAT,
    "longitude": LON,
    "hourly": ",".join(metricas),
    "timezone": "America/Sao_Paulo",
    "forecast_days": dias,
}

r = requests.get(endpoint, params=params, timeout=20)
r.raise_for_status()
data = r.json()

if "hourly" not in data:
    st.error("Sem dados recebidos. Tente ajustar as variáveis.")
    st.stop()

df = pd.DataFrame(data["hourly"])
df["time"] = pd.to_datetime(df["time"])
df = df.set_index("time")

st.subheader("Séries horárias")
st.line_chart(df)

st.subheader("Tabela")
st.dataframe(df.tail(48))

st.caption(
    "Observação: valores são previsões modelo Open-Meteo. "
    "Este app é uma prova de conceito."
)
