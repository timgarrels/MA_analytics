"""Script to run a p-graphlet detection from command line.
This script contains pMetrics which rely on external knowledge such as edge weights and graph modules.
It is not capable to compute results on randomized graphs!
"""
import argparse
import json
from os import makedirs
from pathlib import Path
from typing import List

import networkx as nx

import pmotif_lib.p_metric.p_metric as PMetric
from pmotif_lib.p_motif_graph import PMotifGraph
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

from custom_pmetrics.ExternalWeight import ExternalWeight
from custom_pmetrics.GivenModuleParticipation import GivenModuleParticipation
from custom_pmetrics.InternalWeight import InternalWeight
from util import assert_validity


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


def main(
    edgelist: Path,
    weighted_graph: nx.Graph,
    given_modules: List[List[str]],
    out: Path,
    graphlet_size: int,
):
    """Create three p-Metrics, generate random graphs from the original graph, and
    run a p-motif detection on the graphs (or a graphlet-detection if random_graphs=0).

    :param edgelist: Path to edgelist of a graph, node ids only above 0 and incremental (1,2,3,4,...).
    Can contain an edge per line ("s d") or an edge and an ignored weight per line ("s d 1")
    :param weighted_graph: the same nx.Graph as the graph behind `edgelist`, but with edge weights.
    :param given_modules: A list of node lists. Node labels have to be in `edgelist` param nodes labels. Each node
    may only occur once.
    """

    metrics = [
        PDegree(),
        PAnchorNodeDistance(),
        PGraphModuleParticipation(),
        # Custom pMetrics which rely on external knowledge
        InternalWeight(weighted_graph),
        ExternalWeight(weighted_graph),
        GivenModuleParticipation(given_modules),
    ]

    pmotif_graph = PMotifGraph(edgelist, out)

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
        metrics,
        with_weights=with_weights,
    )

    # No random graphs, as given modules, external weight, and internal weight are not defined on randomized graphs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist_name", required=True, type=str)
    parser.add_argument("--edgelist_name_w_weight", required=True, type=str)
    parser.add_argument(
        "--node_mapping",
        required=False,
        type=str,
        help="JSON of nodemapping to apply to the `edgelist_name_w_weight` graph and the `node_modules` nodes.",
    )
    parser.add_argument("--node_modules", required=True, type=str)
    parser.add_argument(
        "--graphlet_size", required=True, type=int, default=3, choices=[3, 4]
    )

    args = parser.parse_args()
    # General Args
    graph_edgelist = DATASET_DIRECTORY / args.edgelist_name
    out = EXPERIMENT_OUT / graph_edgelist.stem
    graphlet_size = args.graphlet_size

    # External knowledge Args
    weighted_graph_edgelist = DATASET_DIRECTORY / args.edgelist_name_w_weight
    weighted_graph = nx.read_edgelist(weighted_graph_edgelist)

    node_mapping = {}
    if args.node_mapping:
        with open(DATASET_DIRECTORY / args.node_mapping, "r") as f:
            node_mapping = json.load(f)
    weighted_graph = nx.relabel_nodes(
        weighted_graph,
        {v: k for k, v in node_mapping.items()},  # Invert node mapping to original -> gtrie
    )

    with open(DATASET_DIRECTORY / args.node_modules, "r") as f:
        modules = json.load(f)
    reverse_node_mapping = {v: k for k, v in node_mapping.items()}
    mapped_modules = []
    for module_name, module_nodes in modules.items():
        mapped_modules.append(
            [
                reverse_node_mapping[n]
                for n in module_nodes
            ]
        )

    makedirs(out, exist_ok=True)

    main(graph_edgelist, weighted_graph, mapped_modules, out, graphlet_size)
