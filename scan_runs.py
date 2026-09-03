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
    # Initialisation de la base (création de la table si absente au premier lancement)
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Récupération des IDs déjà en base pour éviter de parser deux fois le même run
    cursor.execute("SELECT run_id FROM runs")
    existing_runs = {row[0] for row in cursor.fetchall()}
    
    print(f"🔎 [SCAN] Analyse du répertoire : {RUNS_ROOT}")
    
    # Parcours des dossiers de runs sur le disque NFS
    for run_name in os.listdir(RUNS_ROOT):
        run_path = os.path.join(RUNS_ROOT, run_name)
        
        # Filtre : On ne traite que les dossiers non encore importés
        if os.path.isdir(run_path) and run_name not in existing_runs:
            # La présence de 'RTAComplete.txt' indique que le séquenceur a fini d'écrire
            if os.path.exists(os.path.join(run_path, "RTAComplete.txt")):
                print(f"[NEW RUN] Nouveau run détecté : {run_name}")
                
                # Extraction de la date depuis le nom Illumina standard (YYMMDD_...)
                # Exemple : '240515_...' devient '2024-05-15'
                try:
                    date_raw = run_name.split('_')[0]
                    formatted_date = f"20{date_raw[0:2]}-{date_raw[2:4]}-{date_raw[4:6]}"
                except:
                    formatted_date = "Unknown"
                
                try:
                    # Extraction des métriques via le module InterOp
                    metrics = parse_run_metrics(run_path)
                    
                    # Insertion dans la base de données historique
                    cursor.execute('''
                        INSERT INTO runs (
                            run_id, date_run, yield_gb, pct_q30_total, pct_q30_r1, 
                            pct_q30_r2, cluster_density, pct_pf, 
                            phasing_r1, prephasing_r1, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        run_name, formatted_date, metrics['yield_gb'], 
                        metrics['pct_q30_total'], metrics['pct_q30_r1'], 
                        metrics['pct_q30_r2'], metrics['cluster_density'], 
                        metrics['pct_pf'], metrics['phasing_r1'], 
                        metrics['prephasing_r1'], metrics['status']
                    ))
                    
                    conn.commit()
                    print(f"[SUCCESS] {run_name} ajouté à l'historique.")
                
                except Exception as e:
                    # En cas d'erreur de parsing, on log et on continue pour ne pas bloquer le scan
                    print(f"❌ [ERROR] Échec du traitement pour {run_name} : {e}")

    conn.close()
    print("[SCAN FINISHED] Fin de l'analyse.")

if __name__ == "__main__":
    run_scanner()
