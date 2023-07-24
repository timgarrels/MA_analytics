import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import median, mean
from typing import List, Tuple, Dict, Union
import re

import matplotlib.pyplot as plt
import json
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, graphlet_class_to_name
from tqdm import tqdm

from report_creation.util import get_frequency_data, get_zscore, figsize, dpi, font_size, short_metric_names

plt.rcParams.update({'font.size': font_size})

RANDOM_GRAPH_DIR_REGEX = re.compile(r"\d+_random\.edgelist")

ORIGINAL_MISSING_GRAPHLET_CLASS = "ORIGINAL_MISSING_GRAPHLET_CLASS"
RANDOM_MISSING_GRAPHLET_CLASS = "RANDOM_MISSING_GRAPHLET_CLASS"


def get_random_graph_paths(analysis_out: Path) -> List[Path]:
    """Return paths pointing to all random graphs found."""
    paths = []
    for d in os.listdir(analysis_out):
        if not (analysis_out / d).is_dir():
            continue
        if RANDOM_GRAPH_DIR_REGEX.match(d) is None:
            continue
        paths.append(analysis_out / d)
    return paths


def split_equal_above_below(value: float, compare_values: List[float]) -> Tuple[int, int, int]:
    """Count how many values in `compare_values` are the same, above, or below `value`."""
    equal, above, below = (0, 0, 0)
    for v in compare_values:
        if value == v:
            equal += 1
        elif value < v:
            above += 1
        elif value > v:
            below += 1
    return equal, above, below


def plot_frequency_histogram(analysis_out: Path, original: Path, random_graphs: List[Path], graphlet_size: int):
    """For each graphlet class plot the count of graphlet occurrences per random graph in a histogram.
    Highlight the count of graphlet occurrences in the original graph."""
    graphlet_classes = graphlet_classes_from_size(graphlet_size)
    global_frequencies: Dict[str, List[int]] = defaultdict(list)
    for random_graph in tqdm(random_graphs, desc="Collecting Frequency Data"):
        frequency = get_frequency_data(random_graph)
        for graphlet_class in graphlet_classes:
            global_frequencies[graphlet_class].append(frequency.get(graphlet_class, 0))
        del frequency

    original_frequency = get_frequency_data(original)
    for graphlet_class, frequencies in tqdm(global_frequencies.items(), leave=False, desc="Plotting frequency data"):
        highlight = original_frequency[graphlet_class]
        z_score = get_zscore(highlight, frequencies)

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.hist(frequencies, label="Random Graphs")
        ax.axvline(
            highlight,
            color="tab:orange",
            label=f"Original",
        )

        ax.set_title(graphlet_class_to_name(graphlet_class))
        ax.set_xlabel("Occurrence Count")
        ax.set_ylabel("#")
        ax.legend()

        fig.tight_layout()

        fig.savefig(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency.png")
        fig.savefig(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency.pdf")
        fig.savefig(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency.svg")
        plt.close(fig)

        equal, above, below = split_equal_above_below(highlight, frequencies)
        with open(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency_split.json", "w", encoding="utf-8") as f:
            json.dump({"equal": equal, "above": above, "below": below, "z-score": z_score}, f, indent=4)


def get_metrics(random_graph: Path) -> List[str]:
    """Return all available metrics which were compared pairwise."""
    files = [random_graph / f for f in os.listdir(random_graph)]
    files = [f for f in files if f.suffix == ".data"]
    return [f.stem for f in files]


def load_pairwise_data(random_graph: Path, metric_name: str) -> Dict[str, Dict[str, float]]:
    """Retrieve the pairwise data from disk."""
    with open(random_graph / f"{metric_name}.data", "r", encoding="utf-8") as f:
        return json.load(f)


def analyse_relevance(analysis_out: Path, random_graphs: List[Path], graphlet_size: int):
    """Create artifacts used to analyse the relevance of a graphlet class in the context of p-motif analysis."""
    graphlet_classes = graphlet_classes_from_size(graphlet_size)
    metric_names = get_metrics(random_graphs[0])

    for metric_name in tqdm(metric_names, desc="Analysing Metric Relevance"):
        os.makedirs(analysis_out / metric_name, exist_ok=True)
        for graphlet_class in tqdm(graphlet_classes, leave=False, desc="Graphlet Class Progress"):
            relevancy_out = analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_pairwise.json"
            try:
                pair_wise_data = extract_pairwise_data(
                    graphlet_class,
                    metric_name,
                    random_graphs,
                )
                original_median = pair_wise_data["original_median"]
                sample_median = pair_wise_data["sample_median"]
                plot_sample_median(analysis_out, metric_name, original_median, sample_median, graphlet_class)
            except ValueError:
                dump_pairwise_data(relevancy_out, {}, len(random_graphs), error=ORIGINAL_MISSING_GRAPHLET_CLASS)
                continue

            dump_pairwise_data(relevancy_out, pair_wise_data, len(random_graphs), error=None)


def dump_pairwise_data(out: Path, pair_wise_data: Dict[str, Union[float, List[float]]], total: int, error: Union[str, None]):
    """Create a json file logging data important for p-motif relevance analysis."""
    if len(pair_wise_data.keys()) == 0:
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"error": error}, f, indent=4)
        return

    mean_corr_coef = mean(pair_wise_data["correlation_coefficients"])
    median_corr_coef = median(pair_wise_data["correlation_coefficients"])

    # MAD
    abs_deviations = [pair_wise_data["original_median"] - sample_median for sample_median in pair_wise_data["sample_median"]]
    abs_mean_average_deviation = mean(abs_deviations)
    abs_median_average_deviation = median(abs_deviations)

    try:
        rel_deviations = [pair_wise_data["original_median"] / sample_median for sample_median in pair_wise_data["sample_median"]]
        rel_mean_average_deviation = mean(rel_deviations)
        rel_median_average_deviation = median(rel_deviations)
    except ZeroDivisionError:
        rel_mean_average_deviation = None
        rel_median_average_deviation = None

    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "error": error,
            "p-values": pair_wise_data["p_values"],
            "mean_corr_coef": mean_corr_coef,
            "median_corr_coef": median_corr_coef,
            "abs_mean_average_deviation": abs_mean_average_deviation,
            "abs_median_average_deviation": abs_median_average_deviation,
            "rel_mean_average_deviation": rel_mean_average_deviation,
            "rel_median_average_deviation": rel_median_average_deviation,
            "total": len(pair_wise_data["p_values"]),
            "real_total": total,
        }, f, indent=4)


def plot_sample_median(
        analysis_out: Path,
        metric_name: str,
        original_median: float,
        sample_median: List[float],
        graphlet_class: str,
):
    """Plot a median histogram, highlighting the original median."""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.hist(
        sample_median,
        label="Random Graphs",
    )
    ax.axvline(
        original_median,
        color="tab:orange",
        label=f"Original ({round(original_median, 2)})",
    )
    ax.set_title(graphlet_class_to_name(graphlet_class))
    ax.set_xlabel(f"{short_metric_names[metric_name]} median")
    ax.set_ylabel("#")
    ax.legend()

    fig.tight_layout()

    fig.savefig(analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_sample_median.png")
    fig.savefig(analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_sample_median.pdf")
    fig.savefig(analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_sample_median.svg")
    plt.close(fig)


def extract_pairwise_data(
        graphlet_class: str, metric_name: str, random_graphs: List[Path],
) -> Dict[str, Union[float, List[float]]]:
    """Extract the original median, the p-values, and the medians of all random graphs for a given metrics for the
    pairwise comparision data and return.
    Raises a ValueError if the original graph did not contain the specified graphlet class.
    Skips a random graph, if it does not contain the specified graphlet class,
    thus reducing the size of p-values and sample medians by one."""
    original_median = None
    p_values = []
    sample_median = []
    correlation_coefficients = []
    for r_g in random_graphs:
        data = load_pairwise_data(r_g, metric_name)
        if data[graphlet_class] == ORIGINAL_MISSING_GRAPHLET_CLASS:
            # The original has no occurrence of that graphlet class
            # There are no p-values to extract and no original median
            raise ValueError("Original graph missing graphlet class")
        if data[graphlet_class] == RANDOM_MISSING_GRAPHLET_CLASS:
            # The current random graph has no occurrence of that graphlet class
            # Skip this graph in the comparison process
            continue
        sample_median.append(data[graphlet_class]["sample-median"])
        p_values.append(data[graphlet_class]["p-value"])
        original_median = data[graphlet_class]["original-median"]  # Same for all graphs

        correlation_coefficients.append(calculate_mwu_correlation_coefficient(
            data[graphlet_class]["u-statistic"],
            data[graphlet_class]["original-size"],
            data[graphlet_class]["sample-size"],
        ))

    return {
        "original_median": original_median,
        "p_values": p_values,
        "sample_median": sample_median,
        "correlation_coefficients": correlation_coefficients,
    }


def calculate_mwu_correlation_coefficient(u: float, original_size: float, sample_size: float) -> float:
    """Calculates the correlation coefficient of a mann whitney u test."""
    # after wendt (1972)
    # Dealing with a common problem in social science:
    # A simplified rank-biserial coefficient of correlation based on the U statistic
    r_wendt = 1 - (2 * u) / (original_size * sample_size)
    return r_wendt
