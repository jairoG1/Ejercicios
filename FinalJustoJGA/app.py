import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.spatial import distance
from sklearn.preprocessing import MinMaxScaler

st.set_page_config(page_title="Elite Scouting System", layout="wide")

st.markdown("""
    <style>
    /* Fondo principal y textos */
    .main { background-color: #1a120b; color: #e5d9b6; }
    
    /* Estilo de las metricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #2c1e12;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #d4af37;
    }
    div[data-testid="stMetric"] label { color: #d4af37 !important; font-weight: bold; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #ffffff; }

    /* Barra lateral */
    section[data-testid="stSidebar"] { background-color: #2c1e12; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] p {
        color: #d4af37 !important;
    }

    /* Tablas y Dataframes */
    .stDataFrame { border: 1px solid #d4af37; border-radius: 5px; }
    
    /* Titulos */
    h1, h2, h3 { color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
        return pd.read_csv('players_data.csv')


df = load_data()

if df is not None:
    st.sidebar.title("SISTEMA DE SCOUTING")
    st.sidebar.markdown("---")
    target_player = st.sidebar.selectbox("Agente Objetivo", df['Nombre'].unique())
    
    st.sidebar.subheader("PARAMETROS TACTICOS")
    prioridad = st.sidebar.radio("Prioridad de busqueda", ["Similitud Actual", "Potencial Juvenil"])
    umbral_edad = st.sidebar.slider("Limite de edad", 15, 40, 28)
    presupuesto = st.sidebar.number_input("Presupuesto Maximo (MEUR)", 0, 250, 150)

    metrics = ['Goles', 'Asistencias', 'Pases_%', 'Regates', 'Recuperaciones', 'Duelos_Aereos', 'xG']
    scaler = MinMaxScaler()
    df_norm = df.copy()
    df_norm[metrics] = scaler.fit_transform(df[metrics])

    def get_clones(name, data_norm, original_df, n=5):
        vec = data_norm[data_norm['Nombre'] == name][metrics].values[0]
        distances = []
        for i, row in data_norm.iterrows():
            if row['Nombre'] == name: continue
            dist = distance.euclidean(vec, row[metrics].values)
            distances.append({'Nombre': original_df.iloc[i]['Nombre'], 'Distancia': dist, 'idx': i})
        return pd.DataFrame(distances).sort_values('Distancia').head(n)

    clones = get_clones(target_player, df_norm, df)
    p_info = df[df['Nombre'] == target_player].iloc[0]
    st.title("PANEL DE ANALISIS DE SCOUTING")
    st.markdown(f"Analisis detallado de {target_player} y busqueda de candidatos compatibles.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Unidad / Equipo", p_info['Equipo'])
    k2.metric("Edad", f"{p_info['Edad']} años")
    k3.metric("Valor Mercado", f"{p_info['Valor_Mercado']} MEUR")
    k4.metric("Potencial", p_info['Potencial'])

    st.markdown("---")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Perfil Estadistico (Radar)")
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=p_info[metrics].tolist(),
            theta=metrics,
            fill='toself',
            name=target_player,
            line_color='#d4af37',
            fillcolor='rgba(212, 175, 55, 0.3)'
        ))
        fig_radar.update_layout(
            polar=dict(
                bgcolor='#2c1e12', 
                radialaxis=dict(visible=True, gridcolor='#5e4531', linecolor='#d4af37'),
                angularaxis=dict(gridcolor='#5e4531')
            ),
            paper_bgcolor='rgba(0,0,0,0)', font_color="#e5d9b6",
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)
    with col_right:
        st.subheader("Posicionamiento Tactico")
        fig_map = go.Figure()
        fig_map.add_trace(go.Scatter(
            x=[p_info['Coord_X_Media']], y=[p_info['Coord_Y_Media']],
            mode='markers+text', 
            marker=dict(size=20, color='#d4af37', symbol='diamond', line=dict(color='white', width=1)),
            text=["OBJETIVO"], textposition="bottom center"
        ))
        fig_map.update_layout(
            xaxis=dict(title="Anchura", range=[0, 100], gridcolor='#3d2b1f', zeroline=False), 
            yaxis=dict(title="Profundidad", range=[0, 100], gridcolor='#3d2b1f', zeroline=False),
            paper_bgcolor='#2c1e12', plot_bgcolor='#2c1e12', height=400, font_color="#d4af37"
        )
        st.plotly_chart(fig_map, use_container_width=True)
    st.subheader("Candidatos Identificados")
    display_df = df[df['Nombre'].isin(clones['Nombre'])][['Nombre', 'Equipo', 'Edad', 'Valor_Mercado', 'Potencial']]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("---")
    comp_player = st.selectbox("Seleccione candidato para comparativa tecnica", clones['Nombre'].unique())
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("Comparativa de Habilidades")
        c_info = df[df['Nombre'] == comp_player].iloc[0]
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatterpolar(r=p_info[metrics].tolist(), theta=metrics, fill='toself', name=target_player, line_color='#d4af37'))
        fig_comp.add_trace(go.Scatterpolar(r=c_info[metrics].tolist(), theta=metrics, fill='toself', name=comp_player, line_color='#8b5a2b'))
        fig_comp.update_layout(polar=dict(bgcolor='#2c1e12'), paper_bgcolor='rgba(0,0,0,0)', font_color="#e5d9b6")
        st.plotly_chart(fig_comp, use_container_width=True)

    with c_right:
        st.subheader(f"Proyeccion de Crecimiento: {comp_player}")
        anos = [2024, 2025, 2026, 2027]
        progreso = [c_info['Goles'], c_info['Goles'] + 2, c_info['Goles'] + 4, c_info['Goles'] + 7]
        fig_line = go.Figure(go.Scatter(x=anos, y=progreso, line=dict(color='#d4af37', width=3)))
        fig_line.update_layout(
            xaxis=dict(title="Año", gridcolor='#3d2b1f'),
            yaxis=dict(title="Rendimiento Proyectado", gridcolor='#3d2b1f'),
            paper_bgcolor='#2c1e12', plot_bgcolor='rgba(0,0,0,0)', font_color="#e5d9b6"
        )
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.error("Error al cargar el archivo de datos. Verifique que players_data.csv este presente.")
