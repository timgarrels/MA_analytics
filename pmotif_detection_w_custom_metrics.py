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

from pmotif_lib.p_motif_graph import PMotifGraph
from pmotif_lib.p_metric.p_anchor_node_distance import PAnchorNodeDistance
from pmotif_lib.p_metric.p_degree import PDegree
from pmotif_lib.p_metric.p_graph_module_participation import PGraphModuleParticipation

from custom_pmetrics.ExternalWeight import ExternalWeight
from custom_pmetrics.GivenModuleParticipation import GivenModuleParticipation
from custom_pmetrics.InternalWeight import InternalWeight
from pmotif_cml_interface import add_common_args, add_experiment_out_arg
from util import process_graph, get_edgelist_format


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

    process_graph(
        pmotif_graph,
        graphlet_size,
        metrics,
        edgelist_format=get_edgelist_format(edgelist),
    )

    # No random graphs, as given modules, external weight, and internal weight are not defined on randomized graphs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    add_experiment_out_arg(parser)
    parser.add_argument("--weighted-edgelist-path", required=True, type=Path)
    parser.add_argument(
        "--node-mapping",
        required=False,
        type=Path,
        help="Path to JSON of nodemapping to apply to the `edgelist_name_w_weight` graph and the `node_modules` nodes.",
    )
    parser.add_argument(
        "--node-modules",
        required=True,
        type=Path,
        help="Path to JSON of node modules.",
    )

    args = parser.parse_args()
    # General Args
    graph_edgelist = args.edgelist_path
    out = args.experiment_out / graph_edgelist.stem
    graphlet_size = args.graphlet_size

    # External knowledge Args
    weighted_graph_edgelist = args.weighted_edgelist_path
    weighted_graph = nx.read_edgelist(weighted_graph_edgelist)

    node_mapping = {}
    if args.node_mapping:
        with open(args.node_mapping, "r") as f:
            node_mapping = json.load(f)
    weighted_graph = nx.relabel_nodes(
        weighted_graph,
        {v: k for k, v in node_mapping.items()},  # Invert node mapping to original -> gtrie
    )

    with open(args.node_modules, "r") as f:
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
