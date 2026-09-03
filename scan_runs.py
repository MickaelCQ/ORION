import os
import sqlite3
import sys
from config import RUNS_ROOT, DB_PATH
from core.database import init_db
from modules.parser_interop import parse_run_metrics

def run_scanner():
    """
    Moteur de détection des runs - CHU de Nîmes.
    """
    print("--- DÉMARRAGE DU SCANNER ORION ---")
    
    # Étape 1 : Initialisation Base de données
    try:
        init_db()
        print(f"✅ Base de données vérifiée : {DB_PATH}")
    except Exception as e:
        print(f"❌ ERREUR INITIALISATION DB : {e}")
        return

    # Étape 2 : Connexion
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Étape 3 : Liste des runs déjà connus
    cursor.execute("SELECT run_id FROM runs")
    existing_runs = {row[0] for row in cursor.fetchall()}
    print(f"📊 Runs déjà en base : {len(existing_runs)}")
    
    # Étape 4 : Scan du répertoire NextSeq 2000
    print(f"🔎 Analyse du répertoire : {RUNS_ROOT}")
    
    if not os.path.exists(RUNS_ROOT):
        print(f"❌ ERREUR : Le dossier {RUNS_ROOT} est inaccessible ou n'existe pas.")
        return

    all_files = os.listdir(RUNS_ROOT)
    print(f"📁 Éléments trouvés dans le répertoire : {len(all_files)}")

    for run_name in all_files:
        run_path = os.path.join(RUNS_ROOT, run_name)
        
        # Filtre de sécurité
        if not os.path.isdir(run_path):
            continue
            
        print(f"  📂 Traitement de : {run_name}...", end=" ")

        if run_name in existing_runs:
            print("SKIP (Déjà en base)")
            continue

        # Vérification du fichier de fin de run
        if os.path.exists(os.path.join(run_path, "RTAComplete.txt")):
            # Extraction de la date (YYMMDD)
            date_raw = run_name.split('_')[0]
            formatted_date = f"20{date_raw[0:2]}-{date_raw[2:4]}-{date_raw[4:6]}"
            
            try:
                # Appel du parser InterOp (Deep Probe)
                metrics = parse_run_metrics(run_path)
                
                cursor.execute('''
                    INSERT INTO runs (
                        run_id, date_run, yield_gb, pct_q30_total, pct_q30_r1, 
                        pct_q30_r2, cluster_density, pct_pf, 
                        phasing_r1, prephasing_r1, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    run_id := run_name, 
                    formatted_date, 
                    metrics['yield_gb'], 
                    metrics['pct_q30_total'], 
                    metrics['pct_q30_r1'], 
                    metrics['pct_q30_r2'], 
                    metrics['cluster_density'], 
                    metrics['pct_pf'], 
                    metrics['phasing_r1'], 
                    metrics['prephasing_r1'], 
                    metrics['status']
                ))
                
                conn.commit()
                print("✅ IMPORTÉ")
            except Exception as e:
                print(f"❌ ERREUR PARSING : {e}")
        else:
            print("IGNORE (RTAComplete.txt absent)")

    conn.close()
    print("--- FIN DU SCAN ---")

# CE BLOC EST INDISPENSABLE POUR QUE LE SCRIPT SE LANCE
if __name__ == "__main__":
    run_scanner()
