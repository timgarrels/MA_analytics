"""Script to run a p-graphlet or p-motif detection from command line."""
import argparse
from os import makedirs
from pathlib import Path

from tqdm import tqdm

from pmotif_lib.p_motif_graph import PMotifGraph, PMotifGraphWithRandomization
from pmotif_lib.config import (
    EXPERIMENT_OUT,
    DATASET_DIRECTORY,
)
from pmotif_lib.p_metric.p_anchor_node_distance import PAnchorNodeDistance
from pmotif_lib.p_metric.p_degree import PDegree
from pmotif_lib.p_metric.p_graph_module_participation import PGraphModuleParticipation

from util import process_graph, get_edgelist_format, EdgelistFormat


def main(edgelist: Path, out: Path, graphlet_size: int, random_graphs: int = 0):
    """Create three p-Metrics, generate random graphs from the original graph, and
    run a p-motif detection on the graphs (or a graphlet-detection if random_graphs=0)."""
    degree = PDegree()
    anchor_node = PAnchorNodeDistance()
    graph_module_participation = PGraphModuleParticipation()

    pmotif_graph = PMotifGraph(edgelist, out)

    process_graph(
        pmotif_graph,
        graphlet_size,
        [degree, anchor_node, graph_module_participation],
        edgelist_format=get_edgelist_format(edgelist),
    )

    randomized_pmotif_graph = PMotifGraphWithRandomization.create_from_pmotif_graph(
        pmotif_graph, random_graphs
    )
    del pmotif_graph

    pbar_swapped_graphs = tqdm(
        randomized_pmotif_graph.swapped_graphs,
        desc="Processing swapped graphs",
        leave=True,
    )
    swapped_graph: PMotifGraph
    for swapped_graph in pbar_swapped_graphs:
        process_graph(
            swapped_graph,
            graphlet_size,
            [degree, anchor_node, graph_module_participation],
            check_validity=False,
            edgelist_format=EdgelistFormat.simple_weight,  # Random Graphs are generated to contain weights
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist_name", required=True, type=str)
    parser.add_argument(
        "--graphlet_size", required=True, type=int, default=3, choices=[3, 4]
    )
    parser.add_argument("--random_graphs", required=False, type=int, default=0)

    args = parser.parse_args()

    GRAPH_EDGELIST = DATASET_DIRECTORY / args.edgelist_name
    OUT = EXPERIMENT_OUT / GRAPH_EDGELIST.stem
    GRAPHLET_SIZE = args.graphlet_size
    RANDOM_GRAPHS = args.random_graphs

    makedirs(OUT, exist_ok=True)

    main(GRAPH_EDGELIST, OUT, GRAPHLET_SIZE, RANDOM_GRAPHS)
