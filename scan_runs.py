# scan_runs.py
import os
import sqlite3
from config import RUNS_ROOT, DB_PATH
from core.database import init_db
from modules.parser_nextseq import parse_complete_run

def start_orion_scan():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT run_id FROM runs")
    known = {row[0] for row in cursor.fetchall()}

    for run_name in os.listdir(RUNS_ROOT):
        run_path = os.path.join(RUNS_ROOT, run_name)
        if os.path.isdir(run_path) and run_name not in known:
            if os.path.exists(os.path.join(run_path, "RTAComplete.txt")):
                print(f"🧬 Analyse du run : {run_name}...")
                try:
                    data = parse_complete_run(run_path)
                    dr = run_name.split('_')[0]
                    formatted_date = f"20{dr[0:2]}-{dr[2:4]}-{dr[4:6]}"

                    # Ordre strict des colonnes SQL
                    cursor.execute('''
                        INSERT INTO runs (
                            run_id, date_run, instrument_id, yield_gb, 
                            pct_q30_total, pct_q30_r1, pct_q30_r2, 
                            pct_undetermined, cluster_density, pct_pf, status
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                        (run_name, formatted_date, data['instrument_id'], data['yield_gb'], 
                         data['pct_q30_total'], data['pct_q30_r1'], data['pct_q30_r2'], 
                         data['pct_undetermined'], data['cluster_density'], data['pct_pf'], 'Completed'))
                    
                    conn.commit()
                    print(f"✅ Intégré.")
                except Exception as e:
                    print(f"⚠️ Erreur : {e}")
    conn.close()

if __name__ == "__main__":
    start_orion_scan()
