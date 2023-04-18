import os
from pathlib import Path

import pandas as pd

from pmotif_lib.graphlet_representation import graphlet_class_to_name


def create_global_scope_basic(basepath):
    return f"""
<img src="{basepath}/global/motifs.png">
"""


def create_global_scope(basepath, metric):
    significance = pd.read_csv(f"{basepath}/global/{metric}/significance.csv")
    significance_html = "Relevance of motifs:<br>"
    for _, (_, graphlet_class, relevant, total) in significance.iterrows():
        significance_html += (
            f"<p>{graphlet_class_to_name(graphlet_class)}: {relevant} / {total}</p>\n"
        )

    return f"""
<div class="metric {metric.replace(' ', '_')}" style="display: none">
    {significance_html}
    <div style="display: flex;">
        <img src="{basepath}/global/{metric}/median.png" style="width: 50%">
        <img src="{basepath}/global/{metric}/sample_size.png" style="width: 50%">
    </div>
</div>
"""


def create_local_scope(basepath, metric):
    mann_u = pd.read_csv(f"{basepath}/local/{metric}/mann_whitneyu.csv")
    mann_u_html = mann_u.to_html()

    return f"""
<div class="metric {metric.replace(' ', '_')}" style="display: none">
    <img src="{basepath}/local/{metric}/occurrence_percentiles.png">
    {mann_u_html}
</div>
"""


def create_metric_visibility_js(metrics):
    return """
    function metricChanged() {
        [...document.querySelectorAll('.metric')].forEach(e => {
            e.style.display = "none";
        })
        
        let chosenMetric = document.getElementById("metricSelector").value;
        [...document.querySelectorAll('.' + chosenMetric)].forEach(e => {
            e.style.display = "initial";
        })
    }
    window.onload = function() {
        metricChanged();
};
    """


def local_scope_intro():
    return """<p>
This Scope allows to compare the graphlets in <i>G</i> with each other. Common insights are the counts of graphlets per class
and the distribution of positional metrics within each graphlet class.
</p>
"""


def generate_metric_select_options(metrics):
    html = ""
    for i, m in enumerate(metrics):
        selected = "selected" if i == 0 else ""
        html += f'<option name={m} value={m.replace(" ", "_")} selected="{selected}">{m}</option>\n'
    return html


def create(basepath: str):
    basepath = str(Path(basepath).absolute())

    metrics = os.listdir(f"{basepath}/local")
    html = f"""
<html>
    <head>
    <style>
    </style>
    <script>
        {create_metric_visibility_js(metrics)}
    </script>
    </head>
    <body>
        <label for="metricSelector">Select a Metric!</label>
        <select id="metricSelector" onChange="metricChanged()">
            {generate_metric_select_options(metrics)}
        </select>
        
        <div id="local">
            <h1>Local Scope</h1>
            {local_scope_intro()}
"""
    for m in metrics:
        html += create_local_scope(basepath, m)
    html += f"""
        </div>
        <div id="global">
            <h1>Global Scope</h1>
            {create_global_scope_basic(basepath)}
"""
    for m in metrics:
        html += create_global_scope(basepath, m)
    html += """
        </div>
    </body>
</html>
"""
    with open(f"{basepath}/report.html", "w") as f:
        f.write(html)
