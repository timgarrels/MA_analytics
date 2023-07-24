import json
import os
from functools import lru_cache
from pathlib import Path
from statistics import quantiles
from typing import Dict, List, Tuple

from matplotlib import pyplot as plt
from pmotif_lib.graphlet_representation import graphlet_class_to_name
from tqdm import tqdm


@lru_cache(maxsize=None)
def get_frequency_data(p: Path):
    """Load the graphlet class -> occurrence count lookup."""
    with open(p / "frequency", "r", encoding="utf-8") as frequency:
        return json.load(frequency)


def graphlet_pie_chart(frequency_data: Dict[str, int], analysis_out: Path):
    """Visualize the graphlet classes and their occurrence count in a pie chart."""
    fig, ax = plt.subplots()
    labels = [graphlet_class_to_name(graphlet_class) for graphlet_class in frequency_data.keys()]
    ax.pie(frequency_data.values(), labels=labels)
    ax.set_title("Distribution of Graphlet Classes in the original graph.")
    ax.legend()

    fig.tight_layout()

    fig.savefig(analysis_out / "graphlet_pie.png")
    fig.savefig(analysis_out / "graphlet_pie.pdf")
    fig.savefig(analysis_out / "graphlet_pie.svg")
    plt.close(fig)


def metric_distribution(original: Path, analysis_out: Path):
    """Create histograms for each consolidated metric."""
    if "random" in str(original):
        raise ValueError("Only call this on the original graph compute!")
    metrics = get_metrics(original)
    for metric_name, graphlet_class_to_metrics in tqdm(metrics.items(), desc="Processing metric distribution"):
        os.makedirs(analysis_out / metric_name, exist_ok=True)
        for graphlet_class, metric_values in graphlet_class_to_metrics.items():
            fig, ax = plt.subplots()
            ax.hist(
                metric_values,
                label=metric_name,
            )
            title = graphlet_class_to_name(graphlet_class)
            ax.set_title(title)
            ax.legend()

            fig.tight_layout()

            fig.savefig(analysis_out / metric_name / f"{title}.png")
            fig.savefig(analysis_out / metric_name / f"{title}.pdf")
            fig.savefig(analysis_out / metric_name / f"{title}.svg")
            plt.close(fig)


def outlier_detection(original: Path, analysis_out: Path):
    """Determine outlier thresholds, save thresholds and occurrences beyond those thresholds."""
    if "random" in str(original):
        raise ValueError("Only call this on the original graph compute!")

    occurrences = get_graphlet_occurrences(original)
    metrics = get_metrics(original)
    for metric_name, graphlet_class_to_metrics in tqdm(metrics.items(), desc="Processing outlier detection"):
        out = analysis_out / metric_name
        os.makedirs(out, exist_ok=True)
        for graphlet_class, metric_values in graphlet_class_to_metrics.items():
            occurrence_metric_pairs: List[Tuple[List[str], float]] = list(zip(occurrences[graphlet_class], metric_values))
            if len(occurrence_metric_pairs) == 0:
                continue

            percentile_cuts = get_percentile_cuts(occurrence_metric_pairs)
            with open(out / f"{graphlet_class_to_name(graphlet_class)}_outliers.json", "w", encoding="utf-8") as outliers:
                json.dump(percentile_cuts, outliers, indent=4)


def get_percentile_cuts(occurrence_metric_tuples: List[Tuple[List[str], float]]):
    """Compute cut values for 1%, 5%, 95%, 99% and counts each occurrence beyond those thresholds."""
    metric_values = [v for _, v in occurrence_metric_tuples]
    if len(metric_values) <= 1:
        # Can be only one occurrence of a graphlet class, making percentile calculation impossible
        invalid = {"cut_value": -1, "occurrence_count": 0, "occurrences": []}
        return {"<1%": invalid, "<5%": invalid, ">95%": invalid, ">99%": invalid}

    percentile_cuts = quantiles(metric_values, n=100, method="inclusive")

    cuts = {
        "<1%": {
            "cut_value": round(percentile_cuts[0], 2),
            "occurrence_count": 0,
            "occurrences": []
        },
        "<5%": {
            "cut_value": round(percentile_cuts[4], 2),
            "occurrence_count": 0,
            "occurrences": []
        },
        ">95%": {
            "cut_value": round(percentile_cuts[-5], 2),
            "occurrence_count": 0,
            "occurrences": []
        },
        ">99%": {
            "cut_value": round(percentile_cuts[-1], 2),
            "occurrence_count": 0,
            "occurrences": []
        },
    }

    for occurrence, v in occurrence_metric_tuples:
        if v < cuts["<1%"]["cut_value"]:
            cuts["<1%"]["occurrence_count"] += 1
            cuts["<1%"]["occurrences"].append(occurrence)
        if v < cuts["<5%"]["cut_value"]:
            cuts["<5%"]["occurrence_count"] += 1
            cuts["<5%"]["occurrences"].append(occurrence)
        if v > cuts[">95%"]["cut_value"]:
            cuts[">95%"]["occurrence_count"] += 1
            cuts[">95%"]["occurrences"].append(occurrence)
        if v > cuts[">99%"]["cut_value"]:
            cuts[">99%"]["occurrence_count"] += 1
            cuts[">99%"]["occurrences"].append(occurrence)
    return cuts


@lru_cache(maxsize=None)
def get_graphlet_occurrences(original: Path) -> Dict[str, List[List[int]]]:
    """Load all avaiable metrics from disk, return as a lookup
    metric_name -> graphlet_class -> values"""
    if "random" in str(original):
        raise ValueError("Only call this on the original graph compute!")

    with open(original / "graphlet_occurrences", "r", encoding="utf-8") as occurrences_file:
        return json.load(occurrences_file)


@lru_cache(maxsize=None)
def get_metrics(original: Path) -> Dict[str, Dict[str, List[float]]]:
    """Load all available metrics from disk, return as a lookup
    metric_name -> graphlet_class -> values"""
    if "random" in str(original):
        raise ValueError("Only call this on the original graph compute!")

    files = [f for f in os.listdir(original / "consolidated_metrics")]

    metrics = {}
    for f in files:
        with open(original / "consolidated_metrics" / f, "r", encoding="utf-8") as metric_file:
            metrics[f] = json.load(metric_file)
    return metrics
