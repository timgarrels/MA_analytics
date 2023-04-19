"""Script to run a p-motif detection with logging of runtimes for benchmark purposes."""
import argparse
import shutil
from os import makedirs
from pathlib import Path
from typing import List, Dict
import time
import logging
from tqdm import tqdm
import networkx as nx

from pmotif_lib.p_metric.p_metric import PMetric
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
    metrics: List[PMetric],
    check_validity: bool = True,
) -> Dict[str, float]:
    """Run a graphlet detection and metric calculation (if any) on the given graph measuring
    runtimes."""
    if check_validity:
        assert_validity(pmotif_graph)

    graphlet_runtime_start = time.time()
    run_gtrieScanner(
        graph_edgelist=pmotif_graph.get_graph_path(),
        gtrieScanner_executable=GTRIESCANNER_EXECUTABLE,
        directed=False,
        graphlet_size=graphlet_size,
        output_directory=pmotif_graph.get_graphlet_directory(),
    )
    graphlet_runtime = time.time() - graphlet_runtime_start

    if len(metrics) == 0:
        return {}

    metric_runtime_start = time.time()
    calculate_metrics(pmotif_graph, graphlet_size, metrics, True)
    metric_runtime = time.time() - metric_runtime_start
    return {
        "graphlet_runtime": graphlet_runtime,
        "metric_runtime": metric_runtime,
    }


def main(edgelist: Path, out: Path, graphlet_size: int, random_graphs: int = 0):
    """Create three p-Metrics, generate random graphs from the original graph, and
    run a p-motif detection on the graphs (or a graphlet-detection if random_graphs=0),
    collecting runtime logs."""
    metrics = [PDegree(), PAnchorNodeDistance(), PGraphModuleParticipation()]

    pmotif_graph = PMotifGraph(edgelist, out)

    log_r = process_graph(
        pmotif_graph,
        graphlet_size,
        metrics,
    )
    for runtime_name, runtime in log_r.items():
        logger.info("%s: %s", runtime_name, runtime)

    random_creation_runtime_start = time.time()
    randomized_pmotif_graph = PMotifGraphWithRandomization.create_from_pmotif_graph(
        pmotif_graph, random_graphs
    )
    random_creation_runtime = time.time() - random_creation_runtime_start
    logger.info(
        "Random Creation Runtime: %s (created %s)", random_creation_runtime, random_graphs
    )

    del pmotif_graph

    pbar_swapped_graphs = tqdm(
        randomized_pmotif_graph.swapped_graphs,
        desc="Processing swapped graphs",
        leave=True,
    )
    swapped_graph: PMotifGraph
    for i, swapped_graph in enumerate(pbar_swapped_graphs):
        log_r = process_graph(
            swapped_graph,
            graphlet_size,
            metrics,
            check_validity=False,
        )
        for runtime_name, runtime in log_r.items():
            logger.info("Random %s, %s: %s", i, runtime_name, runtime)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist_name", required=True, type=str)
    parser.add_argument(
        "--graphlet_size", required=True, type=int, default=3, choices=[3, 4]
    )
    parser.add_argument("--random_graphs", required=False, type=int, default=0)
    parser.add_argument(
        "--benchmarking_run", required=True, type=int, choices=[1, 2, 3, 4, 5]
    )

    args = parser.parse_args()

    GRAPH_EDGELIST = DATASET_DIRECTORY / args.edgelist_name
    OUT = EXPERIMENT_OUT / "benchmarking" / "out" / GRAPH_EDGELIST.stem
    GRAPHLET_SIZE = args.graphlet_size
    RANDOM_GRAPHS = args.random_graphs
    BENCHMARKING_RUN = args.benchmarking_run

    makedirs(OUT, exist_ok=True)
    logs_out = EXPERIMENT_OUT / "benchmarking" / "benchmarking_logs"
    makedirs(logs_out, exist_ok=True)

    logfile = f"{BENCHMARKING_RUN}_{GRAPH_EDGELIST.stem}_{GRAPHLET_SIZE}_{RANDOM_GRAPHS}.benchmark"
    logging.basicConfig(
        filename=logs_out / logfile,
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )

    logger = logging.getLogger("benchmark")

    total_runtime_start = time.time()
    main(GRAPH_EDGELIST, OUT, GRAPHLET_SIZE, RANDOM_GRAPHS)
    total_runtime = time.time() - total_runtime_start
    logger.info("Total Runtime: %s", total_runtime)
    shutil.rmtree(EXPERIMENT_OUT / "benchmarking" / "out")
