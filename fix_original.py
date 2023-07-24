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

from pmotif_lib.p_motif_graph import PMotifGraph
from pmotif_lib.config import (
    EXPERIMENT_OUT,
    DATASET_DIRECTORY,
)
from pmotif_lib.p_metric.p_anchor_node_distance import PAnchorNodeDistance
from pmotif_lib.p_metric.p_degree import PDegree
from pmotif_lib.p_metric.p_graph_module_participation import PGraphModuleParticipation

from util import process_graph, get_edgelist_format


def main(edgelist: Path, out: Path, graphlet_size: int):
    """Create three p-Metrics, generate random graphs from the original graph, and
    run a p-motif detection on the graphs (or a graphlet-detection if random_graphs=0)."""
    degree = PDegree()
    anchor_node = PAnchorNodeDistance()
    graph_module_participation = PGraphModuleParticipation()

    pmotif_graph = PMotifGraph(edgelist, out)

    # Remove the faulty result
    shutil.rmtree(pmotif_graph.get_graphlet_directory() / str(graphlet_size))

    process_graph(
        pmotif_graph,
        graphlet_size,
        [degree, anchor_node, graph_module_participation],
        edgelist_format=get_edgelist_format(edgelist),
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
