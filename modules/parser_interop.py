import os
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary

def parse_run_metrics(run_path):
    """
    Lit les fichiers binaires du dossier InterOp d'un run.
    Retourne un dictionnaire contenant les métriques de performance.
    
    Correction : Accès à l'objet read_info via read_summary.read() pour vérifier
    si le read est un index ou un read biologique (R1/R2).
    """
    # 1. Chargement des métriques binaires depuis le dossier du run
    run_metrics = py_interop_run_metrics.run_metrics()
    try:
        run_metrics.read(run_path)
    except Exception as e:
        # Si le dossier est corrompu ou incomplet, on lève une exception pour le log
        raise Exception(f"Erreur lors de la lecture des fichiers InterOp : {e}")

    # 2. Création d'un résumé via l'API Illumina (py_interop_summary)
    # Cette étape agrège les données brutes des tiles pour calculer les moyennes
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)
    
    # 3. Extraction des métriques globales (Rendement total en Gb et Q30 global)
    total_summary = summary.total_summary()
    
    # 4. Extraction par Read (Read 1 et Read 2)
    # Initialisation pour éviter les erreurs si un run est incomplet
    q30_r1 = 0
    q30_r2 = 0
    phasing = 0
    prephasing = 0
    
    # Parcours de tous les reads présents dans le résumé (généralement 4 pour un PE avec index)
    for i in range(summary.size()):
        read_summary = summary.at(i)
        read_info = read_summary.read() # Récupération des métadonnées du read via l'API

        # ISO 15189 : On ne calcule les statistiques que sur les reads biologiques (non-index)
        if not read_info.is_index():
            if read_info.number() == 1:
                # Métriques spécifiques au Read 1
                q30_r1 = read_summary.percent_gt_q30()
                phasing = read_summary.phasing()
                prephasing = read_summary.prephasing()
            else:
                # Métriques spécifiques au Read 2 (dans le cas d'un séquençage Paired-End)
                q30_r2 = read_summary.percent_gt_q30()

    # 5. Calcul des moyennes sur toutes les Lanes (Densité et %PF)
    # Le NextSeq 2000 a une flowcell structurée ; on moyenne les données par Lane
    lanes = summary.lane_count()
    
    # Densité brute : on divise par 1000 pour exprimer la valeur en K/mm2
    densities = [summary.lane_summary(l).at(0).density().mean() / 1000 for l in range(lanes)]
    # Taux de clusters ayant réussi le filtre de chasteté (% Pass Filter)
    pfs = [summary.lane_summary(l).at(0).percent_pf().mean() for l in range(lanes)]
    
    mean_density = sum(densities) / lanes if lanes > 0 else 0
    mean_pf = sum(pfs) / lanes if lanes > 0 else 0

    # Retourne un dictionnaire prêt pour l'insertion en base de données SQLite
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
