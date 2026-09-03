import sqlite3
import os
from config import DB_PATH

def init_db():
    """
    Initialise la structure de la base de données SQLite.
    Crée la table 'runs' si elle n'existe pas.
    """
    # Création du dossier 'data' si manquant
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Création de la table avec des types de données stricts
    # Chaque champ correspond à une métrique extraite des fichiers InterOp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,        -- Identifiant unique (ex: 231027_VH02532_...)
            date_run TEXT,                  -- Date extraite du nom du run
            instrument_id TEXT,             -- Identifiant de la machine (VH02532)
            yield_gb REAL,                  -- Rendement total en Gigabases
            pct_q30_total REAL,             -- % de bases >= Q30 global
            pct_q30_r1 REAL,                -- % de bases >= Q30 pour le Read 1
            pct_q30_r2 REAL,                -- % de bases >= Q30 pour le Read 2
            cluster_density REAL,           -- Densité brute (K/mm2)
            pct_pf REAL,                    -- % de clusters passant les filtres (Pass Filter)
            phasing_r1 REAL,                -- Taux de phasing (Read 1)
            prephasing_r1 REAL,             -- Taux de pre-phasing (Read 1)
            status TEXT,                    -- État du run (ex: Completed, Failed)
            date_entry TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Date d'enregistrement en base
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[DATABASE] Base de données initialisée à : {DB_PATH}")

if __name__ == "__main__":
    init_db()
