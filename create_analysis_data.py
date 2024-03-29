"""Prepare the generation of analysis artifacts by refining metrics and storing them on disk."""
import argparse
import json
import os
from multiprocessing import Pool
from pathlib import Path
from statistics import median
from typing import Dict
from scipy.stats import mannwhitneyu
from tqdm import tqdm

import pandas as pd
from pmotif_lib.graphlet_representation import graphlet_classes_from_size, get_graphlet_size_from_class
from pmotif_lib.p_metric.metric_consolidation import metrics
from pmotif_lib.p_motif_graph import PMotifGraphWithRandomization, PMotifGraph
from pmotif_lib.result_transformer import ResultTransformer

from pmotif_cml_interface import add_common_args, add_analysis_out_arg, add_workers_arg, add_experiment_out_arg

ORIGINAL_MISSING_GRAPHLET_CLASS = "ORIGINAL_MISSING_GRAPHLET_CLASS"
RANDOM_MISSING_GRAPHLET_CLASS = "RANDOM_MISSING_GRAPHLET_CLASS"

SUPRESS_TQDM = True


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


def process_random_graph(analysis_out: Path, original_r: ResultTransformer, random_graph: PMotifGraph):
    """Dump frequency and pairwise comparison with the original graph for the given random graph to disk."""
    os.makedirs(analysis_out / random_graph.edgelist_path.name, exist_ok=True)
    random_r = ResultTransformer.load_result(
        random_graph.edgelist_path,
        random_graph.output_directory,
        original_r.graphlet_size,
        supress_tqdm=SUPRESS_TQDM,
    )
    dump_frequency(analysis_out, random_r)
    add_consolidated_metrics(random_r)
    for metric_name in original_r.consolidated_metrics:
        data = single_pairwise_result(original_r, random_r, metric_name)
        with open(analysis_out / random_graph.edgelist_path.name / f"{metric_name}.data", "w", encoding="utf-8") as out:
            json.dump(data, out)


def compute_pairwise_results(original_r: ResultTransformer, analysis_out: Path, workers: int):
    """Compare the original result with each random graph, sequentially per metric.
    Stores the result on disk, grouped by metric and random graph."""
    randomized_graph = PMotifGraphWithRandomization.create_from_pmotif_graph(original_r.pmotif_graph, -1)

    with Pool(processes=workers) as pool:
        compare_args = [
            (analysis_out, original_r, r_g)
            for r_g in randomized_graph.swapped_graphs
        ]

        pool.starmap(
            process_random_graph,
            tqdm(
                compare_args,
                desc="Processing random graphs",
            ),
            chunksize=1,
        )


def dump_frequency(analysis_out: Path, r: ResultTransformer):
    """Dump the graphlet class frequency to disk."""
    frequency = to_graphlet_class_frequency(r.positional_metric_df)
    os.makedirs(analysis_out / r.pmotif_graph.edgelist_path.name, exist_ok=True)
    with open(analysis_out / r.pmotif_graph.edgelist_path.name / f"frequency", "w", encoding="utf-8") as out:
        json.dump(frequency, out)


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


def create_analysis_data(analysis_out: Path, experiment_out: Path, edgelist: Path, graphlet_size: int, workers: int):
    """Calculate frequency data and (consolidated) pmetric data and store to disk for later use."""
    analysis_out = analysis_out / edgelist.name
    analysis_out = analysis_out / "raw" / str(graphlet_size)
    os.makedirs(analysis_out, exist_ok=True)

    graphlet_data = experiment_out / edgelist.stem

    original_r = ResultTransformer.load_result(edgelist, graphlet_data, graphlet_size, supress_tqdm=SUPRESS_TQDM)
    dump_frequency(analysis_out, original_r)
    # PMetric Data
    add_consolidated_metrics(original_r)
    dump_consolidated_metrics(original_r, analysis_out)
    dump_graphlet_occurrences(original_r, analysis_out)

    try:
        compute_pairwise_results(original_r, analysis_out, workers=workers)
    except FileNotFoundError:
        raise FileNotFoundError("Most likely there are no edge swapping?")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    add_common_args(parser)
    add_experiment_out_arg(parser)
    add_analysis_out_arg(parser)
    add_workers_arg(parser)

    args = parser.parse_args()

    create_analysis_data(
        analysis_out=args.analysis_out,
        experiment_out=args.experiment_out,
        edgelist=args.edgelist_path,
        graphlet_size=args.graphlet_size,
        workers=args.workers,
    )
