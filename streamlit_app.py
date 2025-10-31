import base64
import datetime as dt
from typing import Dict, List, Tuple

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go

# ---------- Config da página ----------
FAVICON_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2" />
    <path d="M12.59 19.41A2 2 0 1 0 14 16H2" />
    <path d="M2 12h17.59a2 2 0 1 0 0-4H12" />
</svg>
"""
FAVICON_B64 = base64.b64encode(FAVICON_SVG.encode("utf-8")).decode("utf-8")
FAVICON_URI = f"data:image/svg+xml;base64,{FAVICON_B64}"

st.set_page_config(page_title="Vento em Osório, RS", page_icon=FAVICON_URI, layout="wide")

# ---------- Estilos ----------
CARD_CSS = """
<style>
:root {
    --bg: #f0f2f6;
    --card: #ffffff;
    --muted: #64748b;
    --text: #1e293b;
    --border: #e2e8f0;
}
body { background-color: var(--bg); }
/* Center the main content area and give it a max-width for better readability on large screens. */
.block-container {
    max-width: 1280px;
    margin-left: auto;
    margin-right: auto;
    padding: 1.5rem 2rem;
}
.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
}
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
}
.kpi {
    display: flex;
    align-items: center;
    gap: 16px;
}
.kpi .icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.meta {
    font-size: 0.875rem;
    color: var(--muted);
}
.section-header {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text);
    margin-top: 24px;
    margin-bottom: 16px;
}
.table-header, .table-row {
    display: grid;
    grid-template-columns: 1fr 1fr 2fr;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
    align-items: center;
}
.table-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
}
.table-row:last-child { border-bottom: none; }
.wind-speed { font-size: 1.25rem; font-weight: 700; color: var(--text); }
.gust-speed { font-size: 0.75rem; color: var(--muted); }
.direction { display: flex; align-items: center; gap: 8px; }
.direction-icon { color: #3b82f6; }
.direction-text { font-size: 0.875rem; color: var(--text); }
.sources-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; }
.sources-content { padding-top: 16px; margin-top: 16px; border-top: 1px solid var(--border); }
.source-card { background: #f8fafc; border-radius: 8px; padding: 16px; }
.source-card h4 { font-size: 1rem; font-weight: 600; margin-bottom: 12px; }
.source-item { display: flex; justify-content: space-between; align-items: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.dot.ok { background-color: #22c55e; }
.dot.down { background-color: #ef4444; }
.status-text.ok { color: #16a34a; }
.status-text.down { color: #dc2626; }
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

def create_wind_chart(df: pd.DataFrame) -> go.Figure:
    now = pd.Timestamp.now(tz="America/Sao_Paulo")
    future_72h = df[(df["time"] >= now) & (df["time"] < now + pd.Timedelta(hours=72))].copy()

    if future_72h.empty:
        return go.Figure()

    fig = go.Figure()

    # Series de dados
    fig.add_trace(go.Scatter(
        x=future_72h["time"], y=future_72h["windspeed_10m"],
        mode='lines+markers', name='Vento Sustentado (km/h)',
        line=dict(color='#2E86C1', width=2.5), marker=dict(symbol='circle', size=5)
    ))
    fig.add_trace(go.Scatter(
        x=future_72h["time"], y=future_72h["windgusts_10m"],
        mode='lines+markers', name='Rajadas (km/h)',
        line=dict(color='#EB984E', width=2.5, dash='dash'), marker=dict(symbol='triangle-up', size=5)
    ))

    # Eixo Y
    max_val = max(future_72h["windspeed_10m"].max(), future_72h["windgusts_10m"].max())
    y_max = (int(max_val / 5) + 1) * 5 if max_val > 0 else 5

    # Eventos Chave (10 mais severos)
    strong_winds = future_72h[(future_72h['windspeed_10m'] >= 20) | (future_72h['windgusts_10m'] >= 20)].copy()
    strong_winds['severity'] = strong_winds[['windspeed_10m', 'windgusts_10m']].max(axis=1)

    calm_periods = future_72h[future_72h['windspeed_10m'] < 3].copy()
    calm_periods['severity'] = calm_periods['windspeed_10m'] # Menor é mais "severo"

    # Ordenar por severidade e pegar os 10 mais relevantes
    top_strong = strong_winds.sort_values(by='severity', ascending=False)
    top_calm = calm_periods.sort_values(by='severity', ascending=True)

    # Combinar e garantir que não tenhamos mais de 10 eventos no total
    key_events = pd.concat([top_strong, top_calm]).sort_values(by='severity', ascending=False).head(10)

    # Eixo X: Ticks a cada 3 horas e ticks de eventos
    tickvals = pd.date_range(start=future_72h['time'].min().ceil('3H'), end=future_72h['time'].max(), freq='3H')
    ticktext = [t.strftime('%d/%m %Hh') for t in tickvals]

    event_times = key_events['time'].tolist()
    final_tickvals = sorted(list(set(tickvals.to_list() + event_times)))
    final_ticktext = []
    for t in final_tickvals:
        if t in event_times:
            final_ticktext.append(f"<b>{t.strftime('%d/%m %H:%M')}</b>")
        elif t in tickvals:
            final_ticktext.append(t.strftime('%d/%m %Hh'))
        else: # Caso raro de sobreposição, prioriza evento
            final_ticktext.append(f"<b>{t.strftime('%d/%m %H:%M')}</b>")


    fig.update_layout(
        title="Vento – próximas 72h (Osório, RS)",
        xaxis_title=None, yaxis_title="Velocidade (km/h)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white', width=1200, height=600,
        margin=dict(l=60, r=40, t=100, b=80),
        xaxis=dict(
            showgrid=True, gridwidth=1, gridcolor='#E5E7E9',
            tickvals=final_tickvals,
            ticktext=final_ticktext,
            tickangle=45,
        ),
        yaxis=dict(
            range=[0, y_max], dtick=5,
            showgrid=True, gridwidth=1, gridcolor='#D6DBDF',
        )
    )

    # Zonas sombreadas
    fig.add_hrect(y0=0, y1=3, fillcolor="#E9F7EF", opacity=0.6, layer="below", line_width=0)
    fig.add_hrect(y0=20, y1=y_max, fillcolor="#FDEDEC", opacity=0.6, layer="below", line_width=0)

    # Linhas de grade e eventos
    for t in tickvals:
        fig.add_vline(x=t, line_width=1, line_color='#E5E7E9', layer="below")

    # Linha separadora de dias (mais espessa)
    start_day = future_72h['time'].min().normalize() + pd.Timedelta(days=1)
    for i in range(4): # Max de 4 dias
        day_break = start_day + pd.Timedelta(days=i)
        if day_break < future_72h['time'].max():
            fig.add_vline(x=day_break, line_width=3, line_color='#566573', layer="below")

    # Linhas e anotações para eventos chave
    for _, event in key_events.iterrows():
        is_strong = event['severity'] >= 20
        color = "#E74C3C" if is_strong else "#2ECC71"

        # Adiciona uma linha vertical dedicada para o evento
        fig.add_vline(x=event['time'], line_width=2, line_dash="dot", line_color="#5D6D7E", layer="below")

        # Garante que o rótulo do evento apareça no eixo X
        if event['time'] not in final_tickvals:
            final_tickvals.append(event['time'])
            final_ticktext.append(f"<b>{event['time'].strftime('%d/%m %H:%M')}</b>")

        y_pos = max(event['windspeed_10m'], event['windgusts_10m'])
        fig.add_annotation(
            x=event['time'], y=y_pos + (y_max * 0.05),
            text="Forte" if is_strong else "Calmaria",
            showarrow=False, font=dict(size=11, color="white"),
            bgcolor=color, borderpad=4, border_radius=4
        )
        # Marcador extra no ponto exato do evento
        fig.add_trace(go.Scatter(
            x=[event['time']], y=[y_pos], mode='markers',
            marker=dict(color=color, size=12, symbol='star-diamond', line=dict(color='white', width=2)),
            showlegend=False
        ))

    return fig

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
icon_wind = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-wind"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path></svg>'

st.markdown(f"""
<div class="header">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="color:#0284c7;">{icon_wind}</div>
        <div>
            <h1 style="font-size:1.5rem; font-weight:700; color:var(--text); margin:0;">Vento em Osório, RS</h1>
            <p style="font-size:0.875rem; color:var(--muted); margin:0;">Atualizado em: {now_str}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Cards superiores ----------
s = summarize(df)
icon_trending_up = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trending-up"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
icon_chevrons_up = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevrons-up"><polyline points="17 11 12 6 7 11"></polyline><polyline points="17 18 12 13 7 18"></polyline></svg>'
icon_chevrons_down = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-chevrons-down"><polyline points="7 13 12 18 17 13"></polyline><polyline points="7 6 12 11 17 6"></polyline></svg>'

st.markdown(f"""
<div class="card">
    <div class="kpi">
        <div class="icon" style="background:#e0f2fe; color:#0ea5e9;">{icon_trending_up}</div>
        <div>
            <div class="meta">Velocidade média (próx. 24h)</div>
            <div style="font-size:2.25rem; font-weight:700; color:var(--text);">
                {s['media']:.0f} <span style="font-size:1.25rem; font-weight:500; color:var(--muted);">km/h</span>
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
            <div class="icon" style="background:#fee2e2; color:#ef4444;">{icon_chevrons_up}</div>
            <div>
                <div class="meta">Pico de Vento</div>
                <div style="font-size:1.875rem; font-weight:700; color:var(--text);">
                    {s['pico']:.0f} <span style="font-size:1rem; font-weight:500; color:var(--muted);">km/h</span>
                </div>
                <div class="meta">previsto para ~ {s['hora_pico']}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with colB:
    calm_text = "Sem previsão de calmaria."
    st.markdown(f"""
    <div class="card">
        <div class="kpi">
            <div class="icon" style="background:#dcfce7; color:#22c55e;">{icon_chevrons_down}</div>
            <div>
                <div class="meta">Período de Calmaria</div>
                <div style="font-size:1.125rem; font-weight:600; color:var(--text); height: 60px; display:flex; align-items:center;">{calm_text}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Gráfico de 72h ----------
st.markdown('<h2 class="section-header">Previsão para as Próximas 72 Horas</h2>', unsafe_allow_html=True)
wind_chart = create_wind_chart(df)
st.plotly_chart(wind_chart, use_container_width=True)

# ---------- Tabela detalhada ----------
st.markdown('<h2 class="section-header">Previsão Detalhada por Hora</h2>', unsafe_allow_html=True)

icon_nav = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-navigation"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>'

# Paginação
if "rows" in st.query_params:
    try:
        st.session_state.rows = int(st.query_params["rows"])
    except (ValueError, TypeError):
        st.session_state.rows = 8
elif "rows" not in st.session_state:
    st.session_state.rows = 8

# Renderizar linhas da tabela
now = pd.Timestamp.now(tz="America/Sao_Paulo").floor('h')
future_df = df[df["time"] >= now]

table_html = '<div class="card">'

# Cabeçalho da tabela
table_html += """
<div class="table-header">
    <div class="col">HORA</div>
    <div class="col">VENTO (KM/H)</div>
    <div class="col">DIREÇÃO</div>
</div>
"""

for _, r in future_df.head(st.session_state.rows).iterrows():
    gust = int(r["windgusts_10m"])
    ws = int(r["windspeed_10m"])
    arrow_style = f"transform:rotate({int(r['winddirection_10m'])}deg);"
    _, desc = wind_dir_text(float(r["winddirection_10m"]))

    table_html += f"""
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
    """
# Botão "Carregar mais" como um link com query parameters
if st.session_state.rows < len(future_df):
    new_rows = st.session_state.rows + 8
    button_html = f"""
    <div style="text-align: center; padding: 20px 0 10px 0; border-top: 1px solid var(--border);">
        <a href="?rows={new_rows}" target="_self" style="
            display: inline-block;
            padding: 0.5rem 1.5rem;
            background-color: var(--card);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            text-decoration: none;
            font-weight: 500;
            transition: background-color 0.2s, border-color 0.2s;
        ">
            Carregar mais
        </a>
    </div>
    """
    table_html += button_html

table_html += '</div>' # Fecha o .card

st.markdown(table_html, unsafe_allow_html=True)


# ---------- Status das fontes ----------
st.markdown('<h2 class="section-header">Status das Fontes de Dados</h2>', unsafe_allow_html=True)
status_ok = not df.empty
st.markdown(
    f"""
    <div class="card">
        <div class="source-item">
            <div style="display:flex; align-items:center; gap:8px;">
                <div class="dot {'ok' if status_ok else 'down'}"></div>
                <span>Open-Meteo</span>
            </div>
            <span class="status-text {'ok' if status_ok else 'down'}">{'Online' if status_ok else 'Offline'}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
