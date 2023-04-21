"""Prepare the generation of analysis artifacts by refining metrics and storing them on disk."""
import argparse
import json
import os
from pathlib import Path
from statistics import median
from typing import Dict

import pandas as pd
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, get_graphlet_size_from_class
from pmotif_lib.p_metric.metric_consolidation import metrics
from pmotif_lib.p_motif_graph import PMotifGraphWithRandomization
from pmotif_lib.result_transformer import ResultTransformer
from scipy.stats import mannwhitneyu


ORIGINAL_MISSING_GRAPHLET_CLASS = "ORIGINAL_MISSING_GRAPHLET_CLASS"
RANDOM_MISSING_GRAPHLET_CLASS = "RANDOM_MISSING_GRAPHLET_CLASS"


def add_consolidated_metrics(result: ResultTransformer) -> ResultTransformer:
    """Apply all pre-implemented consolidation methods on the given result."""
    for metric_name, consolidation_metric_list in metrics.items():
        for consolidation_name, consolidation_method in consolidation_metric_list:
            result.consolidate_metric(
                metric_name, consolidation_name, consolidation_method
            )
    return result


def extract_metric_distribution(df: pd.DataFrame, metric_name: str):
    """Return the values of `metric_name` from the given `df` and groups them by graphlet classes."""
    return dict(df.groupby("graphlet_class").agg(list)[metric_name])


def to_graphlet_class_frequency(result_df: pd.DataFrame) -> Dict[str, int]:
    graphlet_size = get_graphlet_size_from_class(result_df["graphlet_class"][0])
    all_frequencies = dict.fromkeys(graphlet_classes_from_size(graphlet_size), 0)

    r = {
        **all_frequencies,
        **dict(result_df.groupby("graphlet_class").agg("count")["nodes"]),
    }

    return dict(zip(r.keys(), map(int, r.values())))


def single_pairwise_result(original: ResultTransformer, random: ResultTransformer, metric_name: str) -> Dict[str, Dict]:
    """Perform a mann whitney u test and return its pvalue and uvalue"""
    graphlet_classes = graphlet_classes_from_size(original.graphlet_size)

    original_distribution = extract_metric_distribution(
        original.positional_metric_df, metric_name
    )

    data = {}
    for graphlet_class in graphlet_classes:
        original_missing_class = graphlet_class not in original_distribution
        if original_missing_class:
            data[graphlet_class] = ORIGINAL_MISSING_GRAPHLET_CLASS
            continue

        random_distribution = extract_metric_distribution(random.positional_metric_df, metric_name)

        random_missing_class = graphlet_class not in random_distribution
        if random_missing_class:
            data[graphlet_class] = RANDOM_MISSING_GRAPHLET_CLASS
            continue

        mwu_result = mannwhitneyu(
            original_distribution[graphlet_class],
            random_distribution[graphlet_class],
        )

        data[graphlet_class] = {
            "u-statistic": mwu_result.statistic,
            "p-value": mwu_result.pvalue,
            "sample-size": len(random_distribution[graphlet_class]),
            "sample-median": median(
                random_distribution[graphlet_class]
            ),
            "original-size": len(original_distribution[graphlet_class]),
            "original-median": median(
                original_distribution[graphlet_class]
            ),
        }
    return data


def compute_pairwise_results(original_r: ResultTransformer, analysis_out: Path, graphlet_size: int):
    """Compare the original result with each random graph, sequentially per metric.
    Stores the result on disk, grouped by metric and random graph."""
    # TODO: Parallelize? How to do IO?
    randomized_graph = PMotifGraphWithRandomization.create_from_pmotif_graph(original_r.pmotif_graph, -1)

    for p_graph in randomized_graph.swapped_graphs:
        os.makedirs(analysis_out / p_graph.edgelist_path.name, exist_ok=True)

        random_r = ResultTransformer.load_result(p_graph.edgelist_path, p_graph.output_directory, graphlet_size)
        add_consolidated_metrics(random_r)

        for metric_name in original_r.consolidated_metrics:
            data = single_pairwise_result(original_r, random_r, metric_name)
            with open(analysis_out / p_graph.edgelist_path.name / f"{metric_name}.data", "w", encoding="utf-8") as out:
                json.dump(data, out)


def compute_metric_frequencies(original_r: ResultTransformer, analysis_out: Path):
    """Store the count of graphlet occurrences on disk, grouped by graphlet class.
    Done for the original and each random graph."""
    randomized_graph = PMotifGraphWithRandomization.create_from_pmotif_graph(original_r.pmotif_graph, -1)

    def dump_frequency(r: ResultTransformer):
        frequency = to_graphlet_class_frequency(r.positional_metric_df)
        os.makedirs(analysis_out / r.pmotif_graph.edgelist_path.name, exist_ok=True)
        with open(analysis_out / r.pmotif_graph.edgelist_path.name / f"frequency", "w", encoding="utf-8") as out:
            json.dump(frequency, out)

    dump_frequency(original_r)
    for r_p_graph in randomized_graph.swapped_graphs:
        randomized_result = ResultTransformer.load_result(
            r_p_graph.edgelist_path,
            r_p_graph.output_directory,
            original_r.graphlet_size,
        )
        dump_frequency(randomized_result)


def dump_consolidated_metrics(r: ResultTransformer, analysis_out: Path):
    """Dump each consolidated metric on disk."""
    outpath = analysis_out / r.pmotif_graph.edgelist_path.name / "consolidated_metrics"
    os.makedirs(outpath, exist_ok=True)
    for metric_name in r.consolidated_metrics:
        metric_values = r.positional_metric_df.groupby("graphlet_class").agg(list)[metric_name]
        with open(outpath / metric_name, "w", encoding="utf-8") as out:
            json.dump(dict(metric_values), out)


def dump_graphlet_occurrences(r: ResultTransformer, analysis_out: Path):
    """Dump the graphlet occurrences on disk."""
    outpath = analysis_out / r.pmotif_graph.edgelist_path.name
    occurrences = r.positional_metric_df.groupby("graphlet_class").agg(list)["nodes"]
    with open(outpath / "graphlet_occurrences", "w", encoding="utf-8") as out:
        json.dump(dict(occurrences), out)


def create_analysis_data(analysis_out: Path, edgelist: Path, graphlet_size: int, graphlet_data: Path):
    """Calculate frequency data and (consolidated) pmetric data and store to disk for later use."""
    analysis_out = analysis_out / edgelist.name
    analysis_out = analysis_out / "raw" / str(graphlet_size)
    os.makedirs(analysis_out, exist_ok=True)

    graphlet_data = graphlet_data / edgelist.stem

    original_r = ResultTransformer.load_result(edgelist, graphlet_data, graphlet_size)
    # Frequency Data
    compute_metric_frequencies(original_r, analysis_out)
    # PMetric Data
    add_consolidated_metrics(original_r)
    dump_consolidated_metrics(original_r, analysis_out)
    dump_graphlet_occurrences(original_r, analysis_out)

    compute_pairwise_results(original_r, analysis_out, graphlet_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis_out", required=True, type=Path)
    parser.add_argument("--edgelist_path", required=True, type=Path)
    parser.add_argument("--graphlet_size", required=True, type=int, default=3, choices=[3, 4])
    parser.add_argument("--graphlet_data", required=True, type=Path)

    args = parser.parse_args()
    create_analysis_data(args.analysis_out, args.edgelist_path, args.graphlet_size, args.graphlet_data)
