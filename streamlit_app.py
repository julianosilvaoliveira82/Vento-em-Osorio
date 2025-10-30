import datetime as dt
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st

# ---------- Config da página ----------
st.set_page_config(page_title="Vento em Osório, RS", page_icon="💨", layout="wide")

# ---------- Estilos ----------
CARD_CSS = """
<style>
:root{
  --bg:#f7f9fc;
  --card:#ffffff;
  --muted:#94a3b8;
  --ok:#10b981;
  --warn:#ef4444;
  --primary:#1e3a5f;
}
.block-container{padding-top:1.2rem;}
.header{
  display:flex; align-items:center; gap:10px; margin-bottom:12px;
}
.badge{font-size:.75rem; color:var(--muted);}
.card{
  background:var(--card); border:1px solid #e5e7eb; border-radius:14px;
  padding:18px; box-shadow:0 1px 2px rgba(16,24,40,.06);
}
.kpi{display:flex; align-items:center; gap:12px;}
.kpi .icon{
  width:40px; height:40px; border-radius:10px; background:#eef2ff;
  display:flex; align-items:center; justify-content:center; font-size:18px;
}
.grid{display:grid; gap:12px;}
.grid.cols-2{grid-template-columns:1fr 1fr;}
.grid.cols-3{grid-template-columns:1fr 1fr 1fr;}
.meta{font-size:0.78rem; color:var(--muted);}
.table-card .header-row{
  display:grid; grid-template-columns:120px 1fr 1fr; padding:12px 16px; color:#64748b; font-size:.85rem;
  border-bottom:1px solid #e5e7eb;
}
.row{
  display:grid; grid-template-columns:120px 1fr 1fr; padding:12px 16px; align-items:center;
  border-bottom:1px solid #f1f5f9;
}
.dir{display:flex; align-items:center; gap:8px; color:#334155;}
.arrow{display:inline-block; transform: rotate(0deg);}
.status-grid{display:grid; grid-template-columns:1fr 1fr; gap:12px;}
.status-item{background:var(--card); border:1px solid #e5e7eb; border-radius:14px; padding:14px;}
.dot{width:8px; height:8px; border-radius:8px; display:inline-block; margin-right:6px;}
.dot.ok{background:var(--ok);} .dot.down{background:var(--warn);}
.btn{display:flex; justify-content:center; margin-top:12px;}
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

# ---------- Utilidades ----------
@st.cache_data(ttl=1800)
def fetch_forecast(lat: float, lon: float, days: int, vars: List[str]) -> pd.DataFrame:
    endpoint = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ",".join(vars),
        "timezone": "America/Sao_Paulo",
        "forecast_days": days,
    }
    r = requests.get(endpoint, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df

def wind_dir_text(deg: float) -> Tuple[str, str]:
    # Retorna (seta_html, descrição)
    dirs = [
        (0, "Norte – vento da terra/continente"),
        (45, "Nordeste – vento de quadrante oceânico"),
        (90, "Leste – vento do mar para o continente"),
        (135, "Sudeste – vento do mar para o continente"),
        (180, "Sul – vento de quadrante oceânico"),
        (225, "Sudoeste – vento do mar para o continente"),
        (270, "Oeste – vento da terra/continente"),
        (315, "Noroeste – vento da terra/continente"),
    ]
    # seta
    arrow = f'<span class="arrow">🧭</span>'
    # aproxima para descrição
    idx = int(((deg + 22.5) % 360) // 45)
    desc = dirs[idx][1]
    # seta rotacionada por CSS inline
    arrow = f'<span class="arrow" style="transform:rotate({deg}deg)">🡱</span>'
    return arrow, desc

def summarize(df: pd.DataFrame) -> Dict:
    now = pd.Timestamp.now(tz="America/Sao_Paulo")
    prox24 = df[(df["time"] >= now) & (df["time"] < now + pd.Timedelta(hours=24))].copy()
    ws = prox24["windspeed_10m"].mean() if "windspeed_10m" in prox24 else float("nan")
    gust = prox24["windgusts_10m"].max() if "windgusts_10m" in prox24 else float("nan")
    idx_max = prox24["windgusts_10m"].idxmax() if "windgusts_10m" in prox24 else None
    hora_pico = prox24.loc[idx_max, "time"].strftime("%H:%M") if idx_max is not None else "—"
    calmaria = prox24["windspeed_10m"].min() < 3 if "windspeed_10m" in prox24 else False
    return {"media": ws, "pico": gust, "hora_pico": hora_pico, "calmaria": calmaria}

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Configurações")
    dias = st.slider("Dias de previsão", 1, 7, 2)
    st.caption("Fonte: Open-Meteo • Sem chave • Cache 30 min")

# ---------- Dados ----------
LAT, LON = -29.885, -50.267
VARS = ["windspeed_10m", "windgusts_10m", "winddirection_10m"]

df = fetch_forecast(LAT, LON, dias=dias, vars=VARS)
df["hora"] = df["time"].dt.strftime("%H:%M")

# ---------- Header ----------
now_str = dt.datetime.now().strftime("%d/%m/%Y, %H:%M")
st.markdown(f"""
<div class="header">
  <h2 style="margin:0;">Vento em Osório, RS</h2>
  <span class="badge">Atualizado em: {now_str}</span>
</div>
""", unsafe_allow_html=True)

# ---------- Cards superiores ----------
s = summarize(df)
col1 = st.container()
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="kpi">
      <div class="icon">📈</div>
      <div>
        <div class="meta">Velocidade média (próx. 24h)</div>
        <div style="font-size:2rem; font-weight:700;">{:.0f} km/h</div>
      </div>
    </div>
    """.format(s["media"] if pd.notna(s["media"]) else 0), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

colA, colB = st.columns(2)
with colA:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="kpi">
      <div class="icon">🡱</div>
      <div>
        <div class="meta">Pico de Vento</div>
        <div style="font-size:1.6rem; font-weight:700;">{int(s["pico"]) if pd.notna(s["pico"]) else 0} km/h</div>
        <div class="meta">previsto para ~ {s["hora_pico"]}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with colB:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    calm = "Sem previsão de calmaria." if not s["calmaria"] else "Calmaria prevista nas próximas 24h."
    st.markdown(f"""
    <div class="kpi">
      <div class="icon">⤵️</div>
      <div>
        <div class="meta">Período de Calmaria</div>
        <div>{calm}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Tabela detalhada ----------
st.markdown("### Previsão Detalhada por Hora")
st.markdown('<div class="card table-card">', unsafe_allow_html=True)
st.markdown('<div class="header-row"><div>HORA</div><div>VENTO (KM/H)</div><div>DIREÇÃO</div></div>', unsafe_allow_html=True)

# paginação "Carregar mais"
if "rows" not in st.session_state:
    st.session_state.rows = 8

def render_rows(_df: pd.DataFrame, limit: int):
    show = _df.head(limit).copy()
    for _, r in show.iterrows():
        gust = int(r["windgusts_10m"]) if pd.notna(r["windgusts_10m"]) else 0
        ws = int(r["windspeed_10m"]) if pd.notna(r["windspeed_10m"]) else 0
        arrow, desc = wind_dir_text(float(r["winddirection_10m"]) if pd.notna(r["winddirection_10m"]) else 0.0)
        html = f"""
        <div class="row">
          <div>{r['hora']}</div>
          <div>{ws} <span class="meta">Raj {gust}</span></div>
          <div class="dir">{arrow} {desc}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

render_rows(df, st.session_state.rows)
st.markdown('</div>', unsafe_allow_html=True)

c = st.container()
with c:
    if st.session_state.rows < len(df):
        if st.button("Carregar mais"):
            st.session_state.rows += 8
            st.experimental_rerun()

# ---------- Status das fontes ----------
st.markdown("### Status das Fontes de Dados")
st.markdown('<div class="status-grid">', unsafe_allow_html=True)

def status_card(titulo: str, itens: List[Tuple[str, bool]]):
    st.markdown('<div class="status-item">', unsafe_allow_html=True)
    st.markdown(f"**{titulo}**", unsafe_allow_html=True)
    for nome, ok in itens:
        dot = '<span class="dot ok"></span>' if ok else '<span class="dot down"></span>'
        st.markdown(f"{dot} {nome} — {'Online' if ok else 'Offline'}", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

colL, colR = st.columns(2)
with colL:
    status_card("Lagoa dos Barros", [("Windguru", True)])
with colR:
    status_card("Osório", [("Windy", True), ("Windguru", True), ("Windfinder", True)])

st.markdown('</div>', unsafe_allow_html=True)

st.caption("Protótipo não oficial. Dados: Open-Meteo. Layout inspirado no painel solicitado.")