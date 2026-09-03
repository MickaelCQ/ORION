import os
import sqlite3
from config import RUNS_ROOT, DB_PATH
from core.database import init_db
from modules.parser_interop import parse_run_metrics

def run_scanner():
    """
    Scanne le répertoire du séquenceur, extrait les métriques des nouveaux 
    runs et les enregistre dans la base historique.
    """
    # S'assure que la base de données est prête
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupération des IDs déjà connus pour éviter les doublons (Idempotence)
    cursor.execute("SELECT run_id FROM runs")
    existing_runs = {row[0] for row in cursor.fetchall()}
    
    print(f"[SCAN] Analyse de : {RUNS_ROOT}")
    
    # Parcours des dossiers de runs
    for run_name in os.listdir(RUNS_ROOT):
        run_path = os.path.join(RUNS_ROOT, run_name)
        
        # Conditions pour traiter un dossier :
        # 1. C'est un répertoire
        # 2. Pas encore dans notre base de données
        # 3. Le run est terminé (présence de RTAComplete.txt)
        if os.path.isdir(run_path) and run_name not in existing_runs:
            if os.path.exists(os.path.join(run_path, "RTAComplete.txt")):
                print(f"📦 [NEW RUN] Détection de : {run_name}")
                
                try:
                    # Appel du module InterOp pour extraire les chiffres
                    metrics = parse_run_metrics(run_path)
                    
                    # Insertion sécurisée dans SQLite
                    cursor.execute('''
                        INSERT INTO runs (
                            run_id, yield_gb, pct_q30_total, pct_q30_r1, 
                            pct_q30_r2, cluster_density, pct_pf, 
                            phasing_r1, prephasing_r1, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_name, metrics['yield_gb'], metrics['pct_q30_total'],
                        metrics['pct_q30_r1'], metrics['pct_q30_r2'], 
                        metrics['cluster_density'], metrics['pct_pf'],
                        metrics['phasing_r1'], metrics['prephasing_r1'], 
                        metrics['status']
                    ))
                    
                    conn.commit()
                    print(f"✅ [SUCCESS] {run_name} intégré en base.")
                
                except Exception as e:
                    print(f"❌ [ERROR] Impossible de traiter {run_name} : {e}")

    conn.close()
    print("[SCAN FINISHED] La base de données est à jour.")

if __name__ == "__main__":
    run_scanner()
