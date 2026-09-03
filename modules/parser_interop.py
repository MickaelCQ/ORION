import os
import pandas as pd
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary

def parse_run_metrics(run_path):
    """
    Lit les fichiers binaires du dossier InterOp d'un run.
    Retourne un dictionnaire contenant les métriques de performance.
    """
    # 1. Chargement des métriques binaires depuis le dossier du run
    run_metrics = py_interop_run_metrics.run_metrics()
    try:
        run_metrics.read(run_path)
    except Exception as e:
        raise Exception(f"Erreur lors de la lecture des fichiers InterOp : {e}")

    # 2. Création d'un résumé via l'API Illumina
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)
    
    # 3. Extraction des métriques globales (Total Yield et Q30 global)
    total_summary = summary.total_summary()
    
    # 4. Extraction par Read (R1 et R2)
    # Les indices 0 et 3 correspondent généralement au Read 1 et Read 2 (PE)
    q30_r1 = 0
    q30_r2 = 0
    phasing = 0
    prephasing = 0
    
    for i in range(summary.size()):
        read_info = summary.at(i)
        if not read_info.is_index(): # On ignore les reads d'indexation
            if read_info.number() == 1:
                q30_r1 = read_info.percent_gt_q30()
                phasing = read_info.phasing()
                prephasing = read_info.prephasing()
            elif read_info.number() == 2:
                q30_r2 = read_info.percent_gt_q30()

    # 5. Calcul des moyennes sur toutes les Lanes (Densité et %PF)
    lanes = summary.lane_count()
    # On divise par 1000 pour exprimer la densité en K/mm2 (standard Illumina)
    mean_density = sum([summary.lane_summary(l).at(0).density().mean() for l in range(lanes)]) / lanes / 1000
    mean_pf = sum([summary.lane_summary(l).at(0).percent_pf().mean() for l in range(lanes)]) / lanes

    # Construction du dictionnaire final
    return {
        "yield_gb": round(total_summary.yield_g(), 2),
        "pct_q30_total": round(total_summary.percent_gt_q30(), 2),
        "pct_q30_r1": round(q30_r1, 2),
        "pct_q30_r2": round(q30_r2, 2),
        "cluster_density": round(mean_density, 2),
        "pct_pf": round(mean_pf, 2),
        "phasing_r1": round(phasing, 4),
        "prephasing_r1": round(prephasing, 4),
        "status": "Completed"
    }
