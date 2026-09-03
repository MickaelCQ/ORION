#!/usr/bin/env python3
"""
========================================================================================
    BiSHOP V2 , Module de Suivi Longitudinal des Runs NextSeq 2000 (ISO 15189)
    Laboratoire de Biologie Moléculaire Hospitalière
    Auteur :Mickael Coquerelle CHU Nîmes
========================================================================================
"""

import glob
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuration de la page Streamlit
st.set_page_config(
    page_title="BiSHOP, Suivi Runs NextSeq 2000",
    page_icon="",
    layout="wide",
)

st.title("BiSHOP V2 Tableau de Bord Qualité Séquenceur NextSeq 2000")
st.markdown(
    "**Suivi longitudinal du matériel et contrôle qualité des puces (ISO"
    " 15189 / COFRAC)**"
)

# 1. Extraction des données binationaux ou CSV des Runs du CHU
RUNS_BASE_DIR = "/mnt/ngs_ns2000/VH02532/RUNS/"

@st.cache_data(ttl=3600)
def load_all_runs_history():
    run_folders = glob.glob(os.path.join(RUNS_BASE_DIR, "*"))
    history = []

    for run_path in run_folders:
        run_id = os.path.basename(run_path)
        demux_stats = glob.glob(
            os.path.join(
                run_path,
                "Analysis",
                "*",
                "Read1Metrics",
                "Demultiplex_Stats.csv",
            )
        )

        if demux_stats:
            try:
                df = pd.read_csv(demux_stats[0])
                total_reads = df["# Reads"].sum()
                undetermined_reads = df[df["SampleID"] == "Undetermined"][
                    "# Reads"
                ].sum()
                pct_undetermined = (undetermined_reads / total_reads) * 100

                # Date du run depuis le nom du dossier (ex: 260821_...)
                date_str = (
                    "20" + run_id[:2] + "-" + run_id[2:4] + "-" + run_id[4:6]
                )

                history.append(
                    {
                        "Run_ID": run_id,
                        "Date": date_str,
                        "Total_Reads_M": round(total_reads / 1e6, 2),
                        "Total_Gb": round(total_reads * 151 * 2 / 1e9, 2),
                        "Pct_Undetermined": round(pct_undetermined, 2),
                        "Nb_Samples": len(df["SampleID"].unique()) - 1,
                    }
                )
            except Exception:
                pass

    res_df = pd.DataFrame(history)
    if not res_df.empty:
        res_df = res_df.sort_values(by="Date")
    return res_df


df_history = load_all_runs_history()

# 2. KPI Cards (Résumé Haut de Page)
if not df_history.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Runs Traités",
            value=f"{len(df_history)} Runs",
        )
    with col2:
        st.metric(
            label="Rendement Moyen / Run",
            value=f"{df_history['Total_Reads_M'].mean():.1f} M Reads",
        )
    with col3:
        st.metric(
            label="Volume Moyen de Données",
            value=f"{df_history['Total_Gb'].mean():.1f} Gb",
        )
    with col4:
        st.metric(
            label="Taux Moyen Undetermined",
            value=f"{df_history['Pct_Undetermined'].mean():.1f} %",
            delta="- Optimal < 15%",
        )

    st.divider()

    # 3. Cartes de Contrôle Longitudinales (Levey-Jennings)
    st.subheader("Carte de Contrôle Longitudinal : Rendement & Puce (PF)")
    col_left, col_right = st.columns(2)

    with col_left:
        # Graphique 1 : Evolution du nombre de reads par run
        fig_reads = px.bar(
            df_history,
            x="Run_ID",
            y="Total_Reads_M",
            title="Rendement Total de la Flowcell (Millions de Reads)",
            labels={"Total_Reads_M": "Millions de Reads", "Run_ID": "Code Run"},
            color="Total_Reads_M",
            color_continuous_scale="Viridis",
        )
        # Ligne de cible théorique P2 (500M)
        fig_reads.add_hline(
            y=500,
            line_dash="dash",
            line_color="green",
            annotation_text="Cible P2 (500M)",
        )
        st.plotly_chart(fig_reads, use_container_width=True)

    with col_right:
        # Graphique 2 : Suivi du taux d'Undetermined (Qualité Démultiplexage)
        fig_undem = px.line(
            df_history,
            x="Run_ID",
            y="Pct_Undetermined",
            title="Suivi du Taux de Reads Non-Attribués (% Undetermined)",
            markers=True,
            labels={
                "Pct_Undetermined": "% Undetermined",
                "Run_ID": "Code Run",
            },
        )
        # Seuil d'alerte à 15%
        fig_undem.add_hline(
            y=15,
            line_dash="dash",
            line_color="red",
            annotation_text="Seuil Alerte ISO 15%",
        )
        st.plotly_chart(fig_undem, use_container_width=True)

    # 4. Tableau Historique Complet
    st.subheader("Historique Détaillé des Runs de Séquençage")
    st.dataframe(df_history, use_container_width=True)

else:
    st.warning("Aucun historique de run trouvé dans " + RUNS_BASE_DIR)
