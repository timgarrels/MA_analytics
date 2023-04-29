import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict

from jinja2 import Template
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, graphlet_class_to_name


def get_meta(analysis_out: Path) -> Dict:
    with open(analysis_out / "meta.json", "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def get_frequency_split(global_out: Path, graphlet_class: str) -> Dict:
    with open(global_out / f"{graphlet_class_to_name(graphlet_class)}_frequency_split.json", "r", encoding="utf-8") as f:
        return json.load(f)


def has_outlier_file(local_out: Path, metric: str, graphlet_class: str) -> bool:
    return (local_out / metric / f"{graphlet_class_to_name(graphlet_class)}_outliers.json").is_file()


@lru_cache(maxsize=None)
def get_outlier_data(local_out: Path, metric: str, graphlet_class: str) -> Dict:
    outlier_file = local_out / metric / f"{graphlet_class_to_name(graphlet_class)}_outliers.json"
    with open(outlier_file, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def get_relevancy_data(global_out: Path, metric: str, graphlet_class: str) -> Dict:
    relevancy_file = global_out / metric / f"{graphlet_class_to_name(graphlet_class)}_relevance.json"
    with open(relevancy_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_report(analysis_out: Path, local_out: Path, global_out: Path, report_out: Path):
    with open(Path(__file__).parent / "jinja_template.jinja2", "r") as f:
        t = Template(f.read())

    metrics = [f for f in os.listdir(local_out) if (local_out / f).is_dir()]
    meta = get_meta(analysis_out)

    e = t.render(
        graph_name=meta["edgelist"],
        graphlet_size=meta["graphlet_size"],
        local_out=local_out,
        global_out=global_out,
        metric_names=metrics,
        graphlet_pie=str(local_out.absolute() / "graphlet_pie.png"),
        graphlet_classes=graphlet_classes_from_size(meta["graphlet_size"]),
        # Methods
        graphlet_class_to_name=graphlet_class_to_name,
        has_outlier_file=has_outlier_file,
        get_outlier_data=get_outlier_data,
        get_frequency_split=get_frequency_split,
        round=round,
        get_relevancy_data=get_relevancy_data,
    )

    with open(report_out, "w") as f:
        f.write(e)
