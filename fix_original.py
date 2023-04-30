"""The pmotif detection script had a bug:
It did not check whether the input graph had weights or not, which can mess up the input parsing of the gtrieScanner.
This script recomputes the motifs and pmetrics of the original graph, not touching the random graphs.
This saves time, but corrects the mistake.
However, analysis data will have to be recomputed anyways.
"""
import argparse
import shutil
from os import makedirs
from pathlib import Path
from typing import List

import networkx as nx
from tqdm import tqdm

import pmotif_lib.p_metric.p_metric as PMetric
from pmotif_lib.p_motif_graph import PMotifGraph, PMotifGraphWithRandomization
from pmotif_lib.config import (
    GTRIESCANNER_EXECUTABLE,
    EXPERIMENT_OUT,
    DATASET_DIRECTORY,
)
from pmotif_lib.gtrieScanner.wrapper import run_gtrieScanner
from pmotif_lib.p_metric.p_anchor_node_distance import PAnchorNodeDistance
from pmotif_lib.p_metric.p_degree import PDegree
from pmotif_lib.p_metric.p_graph_module_participation import PGraphModuleParticipation
from pmotif_lib.p_metric.metric_processing import calculate_metrics


def assert_validity(pmotif_graph: PMotifGraph):
    """Raises a ValueError of underlying graph is not valid for gtrieScanner input"""
    nx_graph = pmotif_graph.load_graph()

    if len(list(nx.selfloop_edges(nx_graph))) > 0:
        raise ValueError("Graph contains Self-Loops!")  # Asserts simple graph

    if min(map(int, nx_graph.nodes)) < 1:
        raise ValueError(
            "Graph contains node ids below '1'!"
        )  # Assert the lowest node index is >= 1


def process_graph(
    pmotif_graph: PMotifGraph,
    graphlet_size: int,
    metrics: List[PMetric.PMetric],
    check_validity: bool = True,
    with_weights: bool = False,
):
    """Run a graphlet detection and metric calculation (if any) on the given graph."""
    if check_validity:
        assert_validity(pmotif_graph)

    run_gtrieScanner(
        graph_edgelist=pmotif_graph.get_graph_path(),
        gtrieScanner_executable=GTRIESCANNER_EXECUTABLE,
        directed=False,
        graphlet_size=graphlet_size,
        output_directory=pmotif_graph.get_graphlet_directory(),
        with_weights=with_weights,
    )

    if len(metrics) == 0:
        return

    calculate_metrics(pmotif_graph, graphlet_size, metrics, True)


def main(edgelist: Path, out: Path, graphlet_size: int):
    """Create three p-Metrics, generate random graphs from the original graph, and
    run a p-motif detection on the graphs (or a graphlet-detection if random_graphs=0)."""
    degree = PDegree()
    anchor_node = PAnchorNodeDistance()
    graph_module_participation = PGraphModuleParticipation()

    pmotif_graph = PMotifGraph(edgelist, out)

    # Remove the faulty result
    shutil.rmtree(pmotif_graph.get_graphlet_directory() / str(graphlet_size))

    with open(edgelist, "r", encoding="utf-8") as f:
        l = f.readline()
        parts = l.split(" ")
        if len(parts) == 3:
            with_weights = True
        else:
            with_weights = False

    process_graph(
        pmotif_graph,
        graphlet_size,
        [degree, anchor_node, graph_module_participation],
        with_weights=with_weights,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist_name", required=True, type=str)
    parser.add_argument(
        "--graphlet_size", required=True, type=int, default=3, choices=[3, 4]
    )

    args = parser.parse_args()

    GRAPH_EDGELIST = DATASET_DIRECTORY / args.edgelist_name
    OUT = EXPERIMENT_OUT / GRAPH_EDGELIST.stem
    GRAPHLET_SIZE = args.graphlet_size

    makedirs(OUT, exist_ok=True)

    main(GRAPH_EDGELIST, OUT, GRAPHLET_SIZE)
