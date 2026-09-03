import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from jinja2 import Template
from config import DB_PATH, RUNS_ROOT

# --- CONFIGURATION CHU DE NÎMES ---
OUTPUT_HTML =  "/mnt/ngs_ns2000/VH02532/ORION_Dashboard.html"

def get_stats():
    """Récupère et prépare les données."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM runs ORDER BY date_run ASC", conn)
    conn.close()
    return df

def create_levey_jennings_json(df, metric, title, unit=""):
    """Génère le JSON Plotly pour une métrique avec calcul Sigma."""
    mean = df[metric].mean()
    std = df[metric].std()
    
    fig = go.Figure()
    
    # Zone d'ombre +/- 2SD
    fig.add_shape(type="rect", x0=df['date_run'].iloc[0], x1=df['date_run'].iloc[-1],
                  y0=mean-2*std, y1=mean+2*std, fillcolor="rgba(255, 165, 0, 0.1)", line_width=0)
    
    # Tracé des données
    fig.add_trace(go.Scatter(x=df['date_run'], y=df[metric], mode='lines+markers',
                             marker=dict(size=10, color='#00d1ff'), line=dict(width=3), name=title))
    
    # Lignes de contrôle
    fig.add_hline(y=mean, line=dict(color="#00ff88", width=2), annotation_text="Moyenne")
    fig.add_hline(y=mean+3*std, line=dict(color="#ff4b4b", dash="dash"), annotation_text="+3SD (Rejet)")
    fig.add_hline(y=mean-3*std, line=dict(color="#ff4b4b", dash="dash"), annotation_text="-3SD (Rejet)")

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#e0e0e0"), margin=dict(t=50, b=50, l=50, r=50),
        height=450, title=f"Contrôle Longitudinal : {title} {unit}"
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# --- LE TEMPLATE HTML (DESIGN HAUTE PERFORMANCE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>ORION - CHU DE NÎMES</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0a0e14; --card: #161b22; --accent: #00d1ff; --text: #f0f6fc; }
        body { font-family: 'Outfit', sans-serif; background-color: var(--bg); color: var(--text); margin:0; padding: 0; }
        .sidebar { position: fixed; width: 250px; height: 100vh; background: #010409; padding: 20px; border-right: 1px solid #30363d; }
        .content { margin-left: 290px; padding: 40px; }
        .hero-title { font-size: 2.5rem; font-weight: 700; color: var(--accent); margin-bottom: 5px; }
        .institution { font-size: 1rem; opacity: 0.6; letter-spacing: 2px; text-transform: uppercase; }
        
        .tab-nav { display: flex; gap: 10px; margin-bottom: 30px; }
        .tab-btn { background: var(--card); border: 1px solid #30363d; color: var(--text); padding: 12px 25px; border-radius: 8px; cursor: pointer; transition: 0.3s; }
        .tab-btn:hover, .tab-btn.active { border-color: var(--accent); background: #1f2937; }
        
        .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }
        .kpi-card { background: var(--card); padding: 25px; border-radius: 16px; border: 1px solid #30363d; text-align: center; }
        .kpi-value { font-size: 2rem; font-weight: 700; color: var(--accent); }
        .kpi-label { font-size: 0.9rem; opacity: 0.7; }
        
        .plot-container { background: var(--card); border-radius: 20px; padding: 20px; border: 1px solid #30363d; margin-top: 20px; }
        .bio-note { background: #1b2735; border-left: 4px solid var(--accent); padding: 20px; border-radius: 8px; line-height: 1.6; margin-top: 20px; font-style: italic; }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from {opacity:0; transform: translateY(10px);} to {opacity:1; transform: translateY(0);} }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="color: var(--accent)">ORION</h2>
        <p class="institution">CHU de Nîmes</p>
        <hr style="border-color: #30363d">
        <p style="font-size: 0.8rem">Génération : <br>{{ date_now }}</p>
    </div>

    <div class="content">
        <div class="hero-title">Plateforme de Surveillance NextSeq 2000</div>
        <p style="margin-bottom: 40px; opacity: 0.8">Interface de contrôle de performance - Conformité ISO 15189.</p>

        <div class="metrics-grid">
            <div class="kpi-card"> <div class="kpi-label">Dernier Rendement</div><div class="kpi-value">{{ last_run.yield_gb }} Gb</div> </div>
            <div class="kpi-card"> <div class="kpi-label">Score Q30 Global</div><div class="kpi-value">{{ last_run.pct_q30_total }} %</div> </div>
            <div class="kpi-card"> <div class="kpi-label">Undetermined</div><div class="kpi-value" style="color:{{ 'red' if last_run.pct_undetermined > 10 else '#00d1ff' }}">{{ last_run.pct_undetermined }} %</div> </div>
            <div class="kpi-card"> <div class="kpi-label">État du Run</div><div class="kpi-value">OPÉRATIONNEL</div> </div>
        </div>

        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('rendement')">RENDEMENT (Gb)</button>
            <button class="tab-btn" onclick="showTab('qualite')">QUALITÉ (Q30)</button>
            <button class="tab-btn" onclick="showTab('index')">INDICES</button>
        </div>

        <!-- ONGLET RENDEMENT -->
        <div id="rendement" class="tab-content active">
            <div class="plot-container" id="chart_yield"></div>
            <div class="bio-note">
                <strong>💡 Note technique :</strong> Le rendement est la quantité de données exploitables produites. Une baisse significative peut indiquer un problème de loading de la flowcell ou une dégradation précoce des réactifs. Le suivi longitudinal permet de s'assurer de la stabilité du coût par Gb produit au CHU de Nîmes.
            </div>
        </div>

        <!-- ONGLET QUALITÉ -->
        <div id="qualite" class="tab-content">
            <div class="plot-container" id="chart_q30"></div>
            <div class="bio-note">
                <strong>🔬 Intérêt Biologique :</strong> Le score Q30 mesure la probabilité d'une erreur d'appel de base (1/1000). Une dérive indique souvent une perte de focalisation optique ou un déphasage chimique durant le séquençage.
            </div>
        </div>
        
        <!-- ONGLET INDICES -->
        <div id="index" class="tab-content">
            <div class="plot-container" id="chart_undet"></div>
            <div class="bio-note">
                <strong>⚠️ Alerte Indéterminés :</strong> Un taux de <i>Undetermined Reads</i> supérieur à 10% nécessite une investigation : saturation d'index, problème de librairie, ou Index Hopping sur puces structurées.
            </div>
        </div>
    </div>

    <script>
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            window.dispatchEvent(new Event('resize')); // Recalibrage Plotly
        }
        
        // Données Plotly
        const charts = {
            'chart_yield': {{ plot_yield_json | safe }},
            'chart_q30': {{ plot_q30_json | safe }},
            'chart_undet': {{ plot_undet_json | safe }}
        };
        
        Object.keys(charts).forEach(id => {
            Plotly.newPlot(id, charts[id].data, charts[id].layout);
        });
    </script>
</body>
</html>
"""

# --- GÉNÉRATION DU RAPPORT ---
def build():
    df = get_stats()
    from datetime import datetime
    
    ctx = {
        'date_now': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'last_run': df.iloc[-1].to_dict(),
        'plot_yield_json': create_levey_jennings_json(df, 'yield_gb', 'Rendement Global', 'Gb'),
        'plot_q30_json': create_levey_jennings_json(df, 'pct_q30_total', 'Qualité Total', '%Q30'),
        'plot_undet_json': create_levey_jennings_json(df, 'pct_undetermined', 'Reads Indéterminés', '%')
    }
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(Template(HTML_TEMPLATE).render(ctx))
    print(f"✅ Dashboard international généré sur : {OUTPUT_HTML}")

if __name__ == "__main__":
    build()
