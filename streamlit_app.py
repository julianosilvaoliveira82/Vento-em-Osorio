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

        # Converter para datetime e localizar para o fuso horário correto
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize("America/Sao_Paulo")
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

    if prox24.empty:
        return {"media": 0, "pico": 0, "hora_pico": "—", "calmaria": True}

    ws = prox24["windspeed_10m"].mean()
    gust = prox24["windgusts_10m"].max()

    # Adicionar verificação para evitar erro com idxmax em séries vazias ou com NaNs
    if not prox24["windgusts_10m"].empty and prox24["windgusts_10m"].notna().any():
        idx_max = prox24["windgusts_10m"].idxmax()
        hora_pico = prox24.loc[idx_max, "time"].strftime("%H:%M")
    else:
        hora_pico = "—"

    calmaria = prox24["windspeed_10m"].min() < 3

    return {
        "media": ws if pd.notna(ws) else 0,
        "pico": gust if pd.notna(gust) else 0,
        "hora_pico": hora_pico,
        "calmaria": calmaria
    }

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
icon_wind = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-wind"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path></svg>'
icon_refresh = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-refresh-cw"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L20.49 2M3.51 22a9 9 0 0 1-2.85-11.88"></path></svg>'

st.markdown(f"""
<div class="header">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="color:#2563eb;">{icon_wind}</div>
        <div>
            <h1 style="font-size:1.25rem; font-weight:700; color:#1e293b; margin:0;">Vento em Osório, RS</h1>
            <p style="font-size:0.75rem; color:#64748b; margin:0;">Atualizado em: {now_str}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Cards superiores ----------
s = summarize(df)
icon_trending_up = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trending-up"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
icon_chevrons_up = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevrons-up"><polyline points="17 11 12 6 7 11"></polyline><polyline points="17 18 12 13 7 18"></polyline></svg>'
icon_chevrons_down = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevrons-down"><polyline points="7 13 12 18 17 13"></polyline><polyline points="7 6 12 11 17 6"></polyline></svg>'

# Card de Velocidade Média
st.markdown(f"""
<div class="card">
    <div class="kpi">
        <div class="icon" style="background:#dbeafe; color:#2563eb;">{icon_trending_up}</div>
        <div>
            <div class="meta">Velocidade média (próx. 24h)</div>
            <div style="font-size:1.875rem; font-weight:700; color:#1e293b;">
                {s['media']:.0f} <span style="font-size:1rem; font-weight:500; color:#64748b;">km/h</span>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<h2 class="section-header">Destaques das Próximas 24h</h2>', unsafe_allow_html=True)
colA, colB = st.columns(2)
with colA:
    st.markdown(f"""
    <div class="card">
        <div class="kpi">
            <div class="icon" style="background:#fee2e2; color:#dc2626;">{icon_chevrons_up}</div>
            <div>
                <div class="meta">Pico de Vento</div>
                <div style="font-size:1.5rem; font-weight:700; color:#1e293b;">
                    {s['pico']:.0f} <span style="font-size:0.875rem; font-weight:500; color:#64748b;">km/h</span>
                </div>
                <div class="meta">previsto para ~ {s['hora_pico']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with colB:
    calm_text = "Sem previsão de calmaria." if not s['calmaria'] else "Calmaria prevista."
    st.markdown(f"""
    <div class="card">
        <div class="kpi">
            <div class="icon" style="background:#d1fae5; color:#059669;">{icon_chevrons_down}</div>
            <div>
                <div class="meta">Período de Calmaria</div>
                <div style="font-size:1rem; font-weight:600; color:#1e293b; height: 52px; display:flex; align-items:center;">{calm_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Tabela detalhada ----------
st.markdown('<h2 class="section-header">Previsão Detalhada por Hora</h2>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)

icon_nav = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-navigation"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>'

# Cabeçalho da tabela
st.markdown("""
<div class="table-header">
    <div class="col">HORA</div>
    <div class="col">VENTO (KM/H)</div>
    <div class="col">DIREÇÃO</div>
</div>
""", unsafe_allow_html=True)

# Paginação
if "rows" not in st.session_state:
    st.session_state.rows = 8

# Renderizar linhas da tabela
now = pd.Timestamp.now(tz="America/Sao_Paulo").floor('h')
future_df = df[df["time"] >= now]

for _, r in future_df.head(st.session_state.rows).iterrows():
    gust = int(r["windgusts_10m"])
    ws = int(r["windspeed_10m"])
    arrow_style = f"transform:rotate({int(r['winddirection_10m'])}deg);"
    _, desc = wind_dir_text(float(r["winddirection_10m"]))

    st.markdown(f"""
    <div class="table-row">
        <div class="col font-semibold">{r['hora']}</div>
        <div class="col">
            <div class="wind-speed">{ws}</div>
            <div class="gust-speed">Raj {gust}</div>
        </div>
        <div class="col direction">
            <div class="direction-icon" style="{arrow_style}">{icon_nav}</div>
            <span class="direction-text">{desc}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Botão Carregar Mais
if st.session_state.rows < len(future_df):
    st.markdown('<div style="text-align:center; margin-top:16px;">', unsafe_allow_html=True)
    if st.button("Carregar mais"):
        st.session_state.rows += 8
        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ---------- Status das fontes ----------
if 'show_sources' not in st.session_state:
    st.session_state.show_sources = False

def toggle_sources():
    st.session_state.show_sources = not st.session_state.show_sources

icon_chevron = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevron-down"><polyline points="6 9 12 15 18 9"></polyline></svg>'
rotation_style = "transform: rotate(180deg);" if st.session_state.show_sources else ""

st.markdown(f"""
<div class="card" style="margin-top:24px;">
    <div class="sources-header" onclick="toggle_sources()">
        <h2 class="section-header" style="margin:0;">Status das Fontes de Dados</h2>
        <div style="transition:transform 0.2s; {rotation_style}">{icon_chevron}</div>
    </div>
""", unsafe_allow_html=True)

if st.session_state.show_sources:
    status_ok = not df.empty
    st.markdown(f"""
    <div class="sources-content">
        <div class="source-card">
            <h4>Osório</h4>
            <div class="source-item">
                <div style="display:flex; align-items:center; gap:8px;">
                    <div class="dot {'ok' if status_ok else 'down'}"></div>
                    <span>Open-Meteo</span>
                </div>
                <span class="status-text {'ok' if status_ok else 'down'}">{'Online' if status_ok else 'Offline'}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.caption("Protótipo não oficial. Dados: Open-Meteo. Layout inspirado no painel solicitado.")