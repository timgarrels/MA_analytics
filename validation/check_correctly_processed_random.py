"""We might process random graphs wrongly by loading them without weights, despite them having weights.
This script runs the gtrieScanner on the original graph, and one random graph with 3, and one with 4 graphlet size.

And checks whether the stored motif frequency is the same as gtrieScanner computes.
"""
import os
import shutil
import sys
from pathlib import Path
from typing import Dict
from uuid import uuid1

from pmotif_lib.gtrieScanner.wrapper import run_gtrieScanner
from pmotif_lib.gtrieScanner.parsing import parse_graphlet_detection_results_table


OLD_OUTPUT = Path("/hpi/fs00/home/tim.garrels/masterthesis/output/_data_collection_out/")
BASE_PATH = Path("/hpi/fs00/home/tim.garrels/masterthesis/datasets/")


def detect_weights(dataset):
    """Whether the edgelist contains weights."""
    with open(dataset, "r") as f:
        l = f.readline()
        parts = l.split(" ")
        if len(parts) == 2:
            weights = False
        else:
            weights = True
    return weights


def find_random_graph(dataset: Path, k: int) -> Dict[str, Path]:
    """Returns a single edgelist generated for dataset which has detection results for graphlets of size k"""
    edge_swappings = OLD_OUTPUT / dataset.name / "edge_swappings"

    random_graphs = [g for g in os.listdir(edge_swappings) if (edge_swappings / g).is_file()]

    for r in random_graphs:
        out_dir = edge_swappings / f"{r}_motifs"
        if (out_dir / str(k)).is_dir():
            if (out_dir / str(k) / "motif_freq").is_file():
                return {"graph": edge_swappings / r, "motif_freq": (out_dir / str(k) / "motif_freq")}
    raise FileNotFoundError(f"Could not find a random graph for {dataset.name} for size {k}")


def original_motif_freq(dataset: Path, k: int):
    """Returns the motif frequency stored for dataset and k"""
    motif_freq_file = (OLD_OUTPUT / dataset.name / f"{dataset.name}_motifs" / str(k) / "motif_freq")
    return parse_graphlet_detection_results_table(motif_freq_file, k=k)


def rerun(dataset: Path, k: int, out: Path):
    """Runs gtriescanner with manually checked weight parameter"""
    weights = detect_weights(dataset)

    run_gtrieScanner(
        graph_edgelist=dataset,
        graphlet_size=k,
        output_directory=out,
        with_weights=weights
    )
    result = parse_graphlet_detection_results_table(out / str(k) / "motif_freq", k=k)
    shutil.rmtree(out / str(k))
    return result


def test_correct(dataset: Path, k: int, temp_out: Path):
    # Dataset
    correct = rerun(dataset, k, temp_out)
    original = original_motif_freq(dataset, k)

    classes = list(correct.keys()) + list(original.keys())
    for c in classes:
        if correct[c] != original[c]:
            print("\t", "MISMATCHED CLASS COUNT")
            print("\t", c)
            print("\t", dataset)
            print("\t", k)
            break

    # Random
    try:
        r = find_random_graph(dataset, k)
    except FileNotFoundError:
        print("\t", "MISSING RANDOM GRAPH (was not computed yet)")
        return

    correct = rerun(r["graph"], k, temp_out)
    original = parse_graphlet_detection_results_table(r["motif_freq"], k=k)

    classes = list(correct.keys()) + list(original.keys())
    for c in classes:
        if correct[c] != original[c]:
            print("\t", "MISMATCHED CLASS COUNT")
            print("\t", c)
            print("\t", dataset)
            print("\t", f"Random: {r['graph']}")
            print("\t", k)
            break


def main(dataset: str):

    out: Path = Path(f"./temp/{uuid1()}")
    dataset_path: Path = BASE_PATH / dataset

    test_correct(dataset_path, 3, temp_out=out)
    test_correct(dataset_path, 4, temp_out=out)


if __name__ == "__main__":
    _, d = sys.argv
    main(d)
