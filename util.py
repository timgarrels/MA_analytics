from enum import Enum
from typing import List

import networkx as nx
from pmotif_lib.config import GTRIESCANNER_EXECUTABLE
from pmotif_lib.gtrieScanner.wrapper import run_gtrieScanner
from pmotif_lib.p_metric import p_metric as PMetric
from pmotif_lib.p_metric.metric_processing import calculate_metrics
from pmotif_lib.p_motif_graph import PMotifGraph


def assert_validity(pmotif_graph: PMotifGraph):
    """Raises a ValueError of underlying graph is not valid for gtrieScanner input"""
    nx_graph = pmotif_graph.load_graph()

    if len(list(nx.selfloop_edges(nx_graph))) > 0:
        raise ValueError("Graph contains Self-Loops!")  # Asserts simple graph

    if min(map(int, nx_graph.nodes)) < 1:
        raise ValueError(
            "Graph contains node ids below '1'!"
        )  # Assert the lowest node index is >= 1


class EdgelistFormat(Enum):
    simple: "u v"
    simple_weight: "u v weight"


def get_edgelist_format(edgelist) -> EdgelistFormat:
    with open(edgelist, "r", encoding="utf-8") as f:
        l = f.readline()
        parts = l.split(" ")
        if len(parts) == 3:
            return EdgelistFormat.simple_weight

    return EdgelistFormat.simple


def process_graph(
    pmotif_graph: PMotifGraph,
    graphlet_size: int,
    metrics: List[PMetric.PMetric],
    edgelist_format: EdgelistFormat,
    check_validity: bool = True,
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
        with_weights=True if edgelist_format == EdgelistFormat.simple_weight else False,
    )

    if len(metrics) == 0:
        return

    calculate_metrics(pmotif_graph, graphlet_size, metrics, True)
