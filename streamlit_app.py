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
def fetch_forecast() -> pd.DataFrame:
    # URL completa da API Open-Meteo, conforme solicitado
    url = "https://api.open-meteo.com/v1/forecast?latitude=-29.8889&longitude=-50.2667&timezone=America%2FSao_Paulo&forecast_days=3&windspeed_unit=kmh&precipitation_unit=mm&hourly=temperature_2m,wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_speed_180m,wind_direction_10m,wind_direction_80m,wind_direction_120m,wind_direction_180m,wind_gusts_10m,precipitation_probability,precipitation,rain&daily=sunrise,sunset,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant"
    
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()

        # Validação básica da resposta
        if "hourly" not in data or "time" not in data["hourly"]:
            st.error("Resposta da API inválida. Não foi possível encontrar dados horários.")
            return pd.DataFrame()

        df = pd.DataFrame(data["hourly"])
        
        # Renomear colunas para corresponder ao resto do script
        df.rename(columns={
            "time": "time",
            "wind_speed_10m": "windspeed_10m",
            "wind_gusts_10m": "windgusts_10m",
            "wind_direction_10m": "winddirection_10m"
        }, inplace=True)

        # Certificar que a coluna 'time' é do tipo datetime
        df["time"] = pd.to_datetime(df["time"])
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar dados da API: {e}")
        return pd.DataFrame()
    except (KeyError, ValueError) as e:
        st.error(f"Erro ao processar os dados recebidos da API: {e}")
        return pd.DataFrame()

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
# Removido para simplificar a interface, conforme a imagem de referência
# with st.sidebar:
#     st.header("Configurações")
#     dias = st.slider("Dias de previsão", 1, 7, 2)
#     st.caption("Fonte: Open-Meteo • Sem chave • Cache 30 min")

# ---------- Dados ----------
df = fetch_forecast()

# Adicionar verificação para DataFrame vazio
if not df.empty:
    df["hora"] = df["time"].dt.strftime("%H:%M")
else:
    st.warning("Não foi possível carregar os dados da previsão. Tente novamente mais tarde.")
    st.stop()

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
with st.container():
    st.markdown('<div class="card kpi-card">', unsafe_allow_html=True)
    # SVG para o ícone de velocidade
    icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-wind"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path></svg>'
    st.markdown(f"""
    <div class="kpi">
      <div class="icon">{icon_svg}</div>
      <div>
        <div class="meta">Velocidade média (próx. 24h)</div>
        <div style="font-size:2rem; font-weight:700;">{s['media']:.0f} <span style="font-size:1.2rem;font-weight:500;">km/h</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### Destaques das Próximas 24h")
colA, colB = st.columns(2)
with colA:
    st.markdown('<div class="card highlight-card">', unsafe_allow_html=True)
    icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-up-circle"><circle cx="12" cy="12" r="10"></circle><polyline points="16 12 12 8 8 12"></polyline><line x1="12" y1="16" x2="12" y2="8"></line></svg>'
    st.markdown(f"""
    <div class="kpi">
      <div class="icon" style="background:#fee2e2;">{icon_svg}</div>
      <div>
        <div class="meta">Pico de Vento</div>
        <div style="font-size:1.5rem;font-weight:700;">{s['pico']:.0f} <span style="font-size:1rem;font-weight:500;">km/h</span></div>
        <div class="meta">previsto para ~ {s['hora_pico']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with colB:
    st.markdown('<div class="card highlight-card">', unsafe_allow_html=True)
    icon_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-arrow-down-circle"><circle cx="12" cy="12" r="10"></circle><polyline points="8 12 12 16 16 12"></polyline><line x1="12" y1="8" x2="12" y2="16"></line></svg>'
    calm_text = "Sem previsão de calmaria." if not s['calmaria'] else "Calmaria prevista."
    st.markdown(f"""
    <div class="kpi">
      <div class="icon" style="background:#dbeafe;">{icon_svg}</div>
      <div>
        <div class="meta">Período de Calmaria</div>
        <div style="font-size:1.1rem;font-weight:500;height:48px;display:flex;align-items:center;">{calm_text}</div>
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
st.markdown("### Status da Fonte de Dados")
# A verificação 'df.empty' nos informa indiretamente o status da API
status_ok = not df.empty
st.markdown(
    f"""
    <div class="card">
        <div class="status-item">
            <span class="dot {'ok' if status_ok else 'down'}"></span>
            Open-Meteo — {'Online' if status_ok else 'Offline'}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("Protótipo não oficial. Dados: Open-Meteo. Layout inspirado no painel solicitado.")
