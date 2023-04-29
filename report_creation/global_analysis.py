import os
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Union
import re

import matplotlib.pyplot as plt
import json
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, graphlet_class_to_name
from tqdm import tqdm

from report_creation.util import get_frequency_data, get_zscore

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

        fig, ax = plt.subplots()
        ax.hist(frequencies, label="Random Graphs")
        ax.axvline(
            highlight,
            color="tab:orange",
            label=f"Original (zscore={round(z_score, 2)})",
        )

        ax.set_title(graphlet_class_to_name(graphlet_class))
        ax.set_xlabel("Occurrence Count")
        ax.set_ylabel("#")
        ax.legend()

        fig.savefig(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency.png")
        fig.savefig(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency.pdf")
        plt.close(fig)

        equal, above, below = split_equal_above_below(highlight, frequencies)
        with open(analysis_out / f"{graphlet_class_to_name(graphlet_class)}_frequency_split.json", "w", encoding="utf-8") as f:
            json.dump({"equal": equal, "above": above, "below": below, "z-score": z_score}, f)


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
            relevancy_out = analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_relevance.json"
            try:
                original_median, p_values, sample_median = extract_pairwise_data(
                    graphlet_class,
                    metric_name,
                    random_graphs,
                )
                plot_sample_median(analysis_out, metric_name, original_median, sample_median, graphlet_class)
            except ValueError:
                dump_relevancy_json(relevancy_out, [], len(random_graphs), error=ORIGINAL_MISSING_GRAPHLET_CLASS)
                continue

            dump_relevancy_json(relevancy_out, p_values, len(random_graphs), error=None)


def dump_relevancy_json(out: Path, p_values: List[float], total: int, error: Union[str, None]):
    """Create a json file logging data important for p-motif relevance analysis."""
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "error": error,
            "p-values": p_values,
            "total": len(p_values),
            "real_total": total,
        }, f)


def plot_sample_median(
        analysis_out: Path,
        metric_name: str,
        original_median: float,
        sample_median: List[float],
        graphlet_class: str,
):
    """Plot a median histogram, highlighting the original median."""
    fig, ax = plt.subplots()
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
    ax.set_xlabel(f"{metric_name} median")
    ax.set_ylabel("#")
    ax.legend()
    fig.savefig(analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_sample_median.png")
    fig.savefig(analysis_out / metric_name / f"{graphlet_class_to_name(graphlet_class)}_sample_median.pdf")
    plt.close(fig)


def extract_pairwise_data(
        graphlet_class: str, metric_name: str, random_graphs: List[Path],
) -> Tuple[float, List[float], List[float]]:
    """Extract the original median, the p-values, and the medians of all random graphs for a given metrics for the
    pairwise comparision data and return.
    Raises a ValueError if the original graph did not contain the specified graphlet class.
    Skips a random graph, if it does not contain the specified graphlet class,
    thus reducing the size of p-values and sample medians by one."""
    original_median = None
    p_values = []
    sample_median = []
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
    return original_median, p_values, sample_median



