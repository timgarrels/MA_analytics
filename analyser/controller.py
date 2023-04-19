"""Script to consolidate metrics of a p-motif detection output and place themn in an
html report."""
import argparse
from os import makedirs
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
from tqdm import tqdm

from pmotif_lib import config
from pmotif_lib.result_transformer import ResultTransformer

from pmotif_detection.analyse_scripts.util import add_consolidated_metrics
from pmotif_detection.analyse_scripts.local_scope import LocalScope
from pmotif_detection.analyse_scripts.global_scope import GlobalScope
from pmotif_detection.analyse_scripts.report_generator import create

OUTPUT_PATH = "out"


def create_analytics(output_path: Path, graphlet_size: int, dataset: str, experiment_out: str):
    """Loads result from disk and creates analytical results on a local (non-randomized) and
    global (randomized) level. Produces csv's and images."""
    makedirs(output_path / "local", exist_ok=True)
    makedirs(output_path / "global", exist_ok=True)

    print("Loading result")
    result = ResultTransformer.load_result(
        config.DATASET_DIRECTORY / dataset,
        config.EXPERIMENT_OUT / experiment_out,
        graphlet_size,
    )
    print("Consolidating metrics")
    add_consolidated_metrics(result)

    print("Processing Local Analysis")
    local_scope = LocalScope(result)
    for metric_name in tqdm(result.consolidated_metrics, desc="Metric"):
        makedirs(output_path / "local" / metric_name, exist_ok=True)
        # Repeats the occurrence percentiles plot without percentile highlights
        # fig = local_scope.plot_metric_distribution(metric_name)

        mann_whitneyu = local_scope.compute_mann_whitneyu(metric_name)
        mann_whitneyu.to_csv(output_path / "local" / metric_name / "mann_whitneyu.csv")

        occurrence_percentiles_fig = local_scope.plot_occurrence_percentiles(
            metric_name
        )
        save_and_close_fig(
            occurrence_percentiles_fig,
            output_path / "local" / metric_name,
            "occurrence_percentiles",
        )

    print("Processing Global Analysis")
    global_scope = GlobalScope(result)
    motif_fig = global_scope.plot_graphlet_frequency()
    save_and_close_fig(
        motif_fig,
        output_path / "global",
        "motifs",
    )

    for metric_name in tqdm(result.consolidated_metrics, desc="Metric"):
        makedirs(output_path / "global" / metric_name, exist_ok=True)
        significance = global_scope.pmotif_analysis_result(metric_name)
        significance.to_csv(output_path / "global" / metric_name / "significance.csv")

        sample_size_fig = global_scope.plot_sample_size_distribution(metric_name)
        save_and_close_fig(
            sample_size_fig,
            output_path / "global" / metric_name,
            "sample_size",
        )
        median_fig = global_scope.plot_median_distribution(metric_name)
        save_and_close_fig(
            median_fig,
            output_path / "global" / metric_name,
            "median",
        )


def save_and_close_fig(fig, outpath: Path, name: str, file_types: List[str] = None):
    """Save a given figure as image with different filetypes. Closes the figure."""
    if file_types is None:
        file_types = ["png", "pdf"]

    for file_type in file_types:
        fig.savefig(outpath / f"{name}.{file_type}")

    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist_name", required=True, type=str)
    parser.add_argument(
        "--graphlet_size", required=True, type=int, default=3, choices=[3, 4]
    )

    args = parser.parse_args()

    output = config.ANALYSIS_OUT / args.edgelist_name / str(args.graphlet_size)
    create_analytics(
        output,
        args.graphlet_size,
        args.edgelist_name,
        ".".join(args.edgelist_name.split(".")[:-1]),
    )

    create(output)
