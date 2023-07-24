import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict
import base64

from jinja2 import Template
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, graphlet_class_to_name
from util import short_metric_names


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
def get_pairwise_data(global_out: Path, metric: str, graphlet_class: str) -> Dict:
    pairwise_file = global_out / metric / f"{graphlet_class_to_name(graphlet_class)}_pairwise.json"
    with open(pairwise_file, "r", encoding="utf-8") as f:
        return json.load(f)


def to_base_64(p: Path) -> str:
    """Converts the given image to base64 representation in html"""
    p = Path(str(p) + ".png")

    with open(p, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return f"data:image/png;base64,{encoded_string.decode()}"


def create_report(analysis_out: Path, local_out: Path, global_out: Path, report_out: Path):
    with open(Path(__file__).parent / "jinja_template.jinja2", "r") as f:
        t = Template(f.read())

    metrics = sorted([f for f in os.listdir(local_out) if (local_out / f).is_dir()])
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
        get_pairwise_data=get_pairwise_data,
        short_metric_names=short_metric_names,
        to_base_64=to_base_64,
    )

    with open(report_out, "w") as f:
        f.write(e)
