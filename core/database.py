# core/database.py
import sqlite3
import os
from config import DB_PATH

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Nous définissons les 11 colonnes attendues pour le NextSeq 2000
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            date_run TEXT,
            instrument_id TEXT,
            yield_gb REAL,
            pct_q30_total REAL,
            pct_q30_r1 REAL,
            pct_q30_r2 REAL,
            pct_undetermined REAL,
            cluster_density REAL,
            pct_pf REAL,
            status TEXT,
            date_entry TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("Schéma SQL initialisé (11 colonnes).")

if __name__ == "__main__":
    init_db()
