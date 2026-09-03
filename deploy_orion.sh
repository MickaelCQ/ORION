#!/bin/bash
# CHU de Nîmes - ORION High-End Deployer

echo "PROJET ORION, déploiement"
echo "------------------------------------------------------"

# 1. OPTION DE RESET (SÉCURISÉE)
# Si vous lancez : ./deploy_orion.sh --reset
if [[ "$1" == "--reset" ]]; then
    echo "⚠️reset total de la db detecté"
    echo "Effacement de l'historique et recalibrage complet..."
    rm -f data/runs_history.db
    sleep 1
fi

# 2. VÉRIFICATION DU PYTHON
PYTHON_EXEC=$(which python3)
echo "Utilisation de : $PYTHON_EXEC"

# 3. ÉTAPE 1 : SCAN DES DOSSIERS (INCREMENTAL)
echo "Mise à jour de l'historique SQL..."
$PYTHON_EXEC scan_runs.py

if [ $? -ne 0 ]; then
    echo "Erreur critique lors du scan. Arrêt de la pipeline."
    exit 1
fi

# 4. ÉTAPE 2 : GÉNÉRATION DU RAPPORT HTML
echo "Génération de l'interface HTML..."
$PYTHON_EXEC generate_report.py

if [ $? -ne 0 ]; then
    echo "Erreur lors du rendu HTML."
    exit 1
fi

echo "------------------------------------------------------"
echo "Succès"
echo "Lien : /mnt/ngs_ns2000/VH02532/ORION_Dashboard.html"
echo "Windows : B:\VH02532\ORION_Dashboard.html"
echo "------------------------------------------------------"
