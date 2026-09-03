# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from config import DB_PATH, PROJECT_NAME

# CONFIGURATION DE LA PAGE STREAMLIT
st.set_page_config(page_title=PROJECT_NAME, layout="wide")

def load_data():
    """Connexion à la base SQLite et chargement des données dans un DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    # On trie par date pour que le suivi longitudinal soit chronologique
    df = pd.read_sql_query("SELECT * FROM runs ORDER BY date_run ASC", conn)
    conn.close()
    return df

def plot_levey_jennings(df, metric_name, title):
    """
    Génère un graphique de contrôle Levey-Jennings.
    Affiche la moyenne, +/- 2SD (Alerte) et +/- 3SD (Action/Rejet).
    """
    data = df[metric_name]
    mean = data.mean()
    std = data.std()
    
    # Création du graphique Plotly
    fig = go.Figure()

    # 1. Ajout de la ligne de données réelles
    fig.add_trace(go.Scatter(
        x=df['date_run'], y=data,
        mode='lines+markers',
        name=title,
        line=dict(color='blue', width=2),
        hovertemplate='%{x}<br>Valeur: %{y:.2f}'
    ))

    # 2. Ajout des lignes de contrôle (Moyenne et Écarts-types)
    colors = {'mean': 'green', '2sd': 'orange', '3sd': 'red'}
    
    # Moyenne
    fig.add_hline(y=mean, line_dash="dash", line_color=colors['mean'], annotation_text="Moyenne")
    
    # Limites à 2 Écarts-types (95% de confiance - Zone d'alerte)
    if std > 0:
        fig.add_hline(y=mean + 2*std, line_dash="dot", line_color=colors['2sd'], annotation_text="+2SD")
        fig.add_hline(y=mean - 2*std, line_dash="dot", line_color=colors['2sd'], annotation_text="-2SD")
        
        # Limites à 3 Écarts-types (99% de confiance - Zone de rejet/audit)
        fig.add_hline(y=mean + 3*std, line_dash="solid", line_color=colors['3sd'], annotation_text="+3SD")
        fig.add_hline(y=mean - 3*std, line_dash="solid", line_color=colors['3sd'], annotation_text="-3SD")

    fig.update_layout(
        title=f"Suivi Longitudinal : {title}",
        xaxis_title="Date du Run",
        yaxis_title="Valeur mesurée",
        template="plotly_white",
        height=500
    )
    return fig

# INTERFACE UTILISATEUR (UI)

st.title(f" {PROJECT_NAME}")
st.markdown("---")

# Chargement des données
df = load_data()

if df.empty:
    st.warning("Aucune donnée disponible dans la base. Lancez 'scan_runs.py' d'abord.")
else:
    # --- Sidebar pour les filtres ---
    st.sidebar.header("Options de visualisation")
    st.sidebar.write(f"Nombre de runs analysés : {len(df)}")
    
    # --- Zone des KPIs (Chiffres clés du dernier run) ---
    last_run = df.iloc[-1]
    st.subheader(f"Dernier Run analysé : {last_run['run_id']}")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rendement (Gb)", f"{last_run['yield_gb']:.1f}")
    col2.metric("% Q30 Global", f"{last_run['pct_q30_total']:.1f}%")
    col3.metric("Densité (K/mm²)", f"{last_run['cluster_density']:.0f}")
    col4.metric("% Pass Filter", f"{last_run['pct_pf']:.1f}%")

    st.markdown("---")

    # --- Zone des Graphiques Levey-Jennings ---
    st.subheader("Cartes de Contrôle Qualité (ISO 15189)")
    
    # Choix de la métrique à afficher
    metric_choice = st.selectbox(
        "Sélectionnez la métrique à surveiller :",
        ["yield_gb", "pct_q30_total", "pct_q30_r1", "pct_q30_r2", "cluster_density", "pct_pf"]
    )
    
    # Affichage du graphique
    fig = plot_levey_jennings(df, metric_choice, metric_choice.replace('_', ' ').upper())
    st.plotly_chart(fig, use_container_width=True)

    # --- Tableau de données brut ---
    with st.expander("Voir le tableau historique complet"):
        st.dataframe(df, use_container_width=True)

# Footer pour l'audit
st.sidebar.markdown("---")
st.sidebar.info("Outil développé pour le suivi de performance NextSeq 2000 - CHU Nantes.")
