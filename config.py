import os

# CONFIGURATION DES CHEMINS ET PARAMÈTRES GÉNÉRAUX

# Nom officiel du projet pour les rapports d'audit
PROJECT_NAME = "ORION, Optimized Run Illumina Observatory & NextSeq-tracker"

# Racine du stockage des données brutes du séquenceur NextSeq 2000
# C'est ici que le script cherchera les dossiers de runs
RUNS_ROOT = "/mnt/ngs_ns2000/VH02532/RUNS/"

# Chemin local pour la base de données SQLite (Stockage historique)
DB_PATH = "/NFS/cluster-share/home/mcoquerelle/ORION/data/runs_history.db"

# Seuil de qualité cible (ISO 15189 : Critère d'acceptation par défaut)
MIN_Q30_THRESHOLD = 75.0  

# Liste des métriques suivies pour les cartes de contrôle Levey-Jennings
METRICS_TO_TRACK = [
    'yield_gb', 'pct_q30_total', 'cluster_density', 
    'pct_pf', 'phasing_r1', 'prephasing_r1'
]
