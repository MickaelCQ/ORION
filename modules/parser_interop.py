import os
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary

def parse_run_metrics(run_path):
    """
    Version 'ORION-Universal' - Conçue pour CHUNBIOTEST2.
    Cette version explore dynamiquement l'API InterOp pour trouver les métriques
    quelles que soient les variations de noms (tile_metrics vs tile_metric_set).
    """
    
    # 1. Chargement des métriques binaires
    run_metrics = py_interop_run_metrics.run_metrics()
    try:
        run_metrics.read(run_path)
    except Exception as e:
        raise Exception(f"Erreur de lecture InterOp : {e}")

    # 2. Synthèse des métriques (Summarize)
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)
    
    # 3. Extraction du Q30 et Rendement (Stable via total_summary)
    total_summary = summary.total_summary()
    
    # --- FONCTION DE RÉCUPÉRATION DYNAMIQUE ---
    def get_val(obj, method_names):
        """
        Cherche un attribut/méthode dans une liste de noms possibles.
        Gère les cas où la valeur est une méthode ou un objet avec .mean()
        """
        for name in method_names:
            if hasattr(obj, name):
                attr = getattr(obj, name)
                # Si c'est une fonction, on l'appelle
                val = attr() if callable(attr) else attr
                # Si l'objet retourné a une méthode .mean() (cas des Metrics)
                if hasattr(val, 'mean'): 
                    return val.mean()
                return val
        return 0
    # ------------------------------------------

    # 4. Extraction des KPIs Globaux
    # Ces noms sont les plus courants pour le rendement et le Q30 global
    yield_total = get_val(total_summary, ['yield_g', 'yield_gb', 'total_yield'])
    q30_total = get_val(total_summary, ['percent_gt_q30', 'percent_q30', 'percent_greater_than_q30'])

    # 5. Extraction par Read (R1 et R2)
    q30_r1, q30_r2, phasing_r1, prephasing_r1 = 0, 0, 0, 0
    
    for i in range(summary.size()):
        read_summary = summary.at(i)
        read_info = read_summary.read()
        
        if not read_info.is_index():
            q30_val = get_val(read_summary, ['percent_gt_q30', 'percent_q30'])
            
            if read_info.number() == 1:
                q30_r1 = q30_val
                phasing_r1 = get_val(read_summary, ['phasing'])
                prephasing_r1 = get_val(read_summary, ['prephasing'])
            else:
                q30_r2 = q30_val

    # 6. MÉTRIQUES PHYSIQUES (DENSITÉ / PF)
    # On tente 3 stratégies par ordre de précision décroissante :
    mean_density = 0
    mean_pf = 0

    # Stratégie A : Via l'objet de métriques brutes (tile_metrics ou tile_metric_set)
    try:
        t_set = None
        for attr in ['tile_metrics', 'tile_metric_set', 'tile_metrics_set']:
            if hasattr(run_metrics, attr):
                t_set = getattr(run_metrics, attr)()
                break
        
        if t_set and t_set.size() > 0:
            densities = [t_set.at(j).density() / 1000 for j in range(t_set.size())]
            pfs = [t_set.at(j).percent_pf() for j in range(t_set.size())]
            mean_density = sum(densities) / len(densities)
            mean_pf = sum(pfs) / len(pfs)
    except:
        pass

    # Stratégie B : Repli sur le total_summary si la Stratégie A a échoué
    if mean_density == 0:
        # On cherche 'cluster_density' ou 'density' dans le résumé global
        mean_density = get_val(total_summary, ['cluster_density', 'density', 'density_kmm2'])
        # Si la valeur est brute, on divise par 1000
        if mean_density > 5000: mean_density /= 1000 
        
    if mean_pf == 0:
        mean_pf = get_val(total_summary, ['percent_pf', 'pct_pf'])

    # 7. Finalisation des résultats pour la base SQLite
    return {
        "yield_gb": round(yield_total, 2),
        "pct_q30_total": round(q30_total, 2),
        "pct_q30_r1": round(q30_r1, 2),
        "pct_q30_r2": round(q30_r2, 2),
        "cluster_density": round(mean_density, 2),
        "pct_pf": round(mean_pf, 2),
        "phasing_r1": round(phasing_r1, 4),
        "prephasing_r1": round(prephasing_r1, 4),
        "status": "Completed"
    }
