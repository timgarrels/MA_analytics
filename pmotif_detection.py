"""Script to run a p-graphlet or p-motif detection from command line."""
import argparse
from os import makedirs
from pathlib import Path

from tqdm import tqdm

from pmotif_lib.p_motif_graph import PMotifGraph, PMotifGraphWithRandomization
from pmotif_lib.p_metric.p_anchor_node_distance import PAnchorNodeDistance
from pmotif_lib.p_metric.p_degree import PDegree
from pmotif_lib.p_metric.p_graph_module_participation import PGraphModuleParticipation

from pmotif_cml_interface import add_common_args, add_experiment_out_arg, add_workers_arg
from util import process_graph, get_edgelist_format, EdgelistFormat


def main(edgelist: Path, out: Path, graphlet_size: int, workers: int = 1, random_graphs: int = 0):
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
        workers=workers,
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
            edgelist_format=EdgelistFormat.SIMPLE_WEIGHT,  # Random Graphs are generated to contain weights
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    add_experiment_out_arg(parser)
    add_workers_arg(parser)
    parser.add_argument("--random-graphs", required=False, type=int, default=1)

    args = parser.parse_args()

    GRAPH_EDGELIST = args.edgelist_path
    OUT = args.experiment_out / GRAPH_EDGELIST.stem
    GRAPHLET_SIZE = args.graphlet_size
    RANDOM_GRAPHS = args.random_graphs

    makedirs(OUT, exist_ok=True)

    main(GRAPH_EDGELIST, OUT, GRAPHLET_SIZE, random_graphs=RANDOM_GRAPHS, workers=args.workers)
