"""Script to test that all graphs have been processd and properly saved."""
import os
import subprocess
from pathlib import Path
import sys
from typing import List
from tqdm import tqdm


def is_complete_pmetric_out(pmetric: Path):
    with open(pmetric / "graphlet_metrics", "r") as f:
        total_expected = int(f.readline().strip())

    file_path_as_str = str(pmetric / "graphlet_metrics")

    total = int(subprocess.check_output(['bash','-c', f"wc -l < {file_path_as_str}"]))
    return total_expected == total - 1


def swapped_graphs_valid(swapped_graphs: List[Path], k: int):

    for g in tqdm(swapped_graphs, desc=f"Checking random graphs ({k})"):
        out = g / str(k) / "pmetrics"
        if not out.exists():
            return False, "Graphlet Size missing!"

        if not all([is_complete_pmetric_out(out / pmetric) for pmetric in os.listdir(out)]):
            return False, "Not all metrics complete!"
    return True, "All good"


def main(base: Path):
    edge_swappings = base / "edge_swappings"
    swapped_graphs = [edge_swappings / f for f in os.listdir(edge_swappings) if (edge_swappings / f).is_dir()]

    for k in [3, 4]:
        good, msg = swapped_graphs_valid(swapped_graphs, k)
        if not good:
            print(base, k, msg)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
