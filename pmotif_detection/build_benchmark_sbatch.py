"""Script to quickly generate an instruction file for slurm's sbtach command
to benchmark p-motif detection on multiple datasets and different graphlet sizes and in
multiple runs to be robust against fluctuations."""
from pathlib import Path

LOG_BASE = "/hpi/fs00/home/tim.garrels/masterthesis/logs/benchmarking_logs/"

DATASETS = [
    "kaggle_so_tags.edgelist",
    "kaggle_star_wars.edgelist",
    "yeastInter_st.txt",
    "random_graphs/0_barabasi_albert_graph_m_1",
    "random_graphs/0_barabasi_albert_graph_m_2"
    "random_graphs/0_ferdos_renyi_graph_m_2000",
    "human_cancer_cutoff_0.935.edgelist",
    "human_brain_development_cutoff_0.772.edgelist",
]

GRAPHLET_SIZES = [3, 4]
BENCHMARKING_RUNS = [1, 2, 3, 4, 5]

PREAMBLE_LINES = [
    "#!/bin/bash",
    "#SBATCH -A renard",
    "#SBATCH --time=40:00:00",
    "#SBATCH --cpus-per-task=1",
    "#SBATCH --mem-per-cpu=150G",
]


def generate_line(edgelist_path: Path, graphlet_size: int, benchmarking_run: int):
    """Create a line for the sbatch file, representing a single benchmarking task."""
    log_path = LOG_BASE + str(graphlet_size) + "/" + edgelist_path.name
    return f"./run_benchmark.sh {log_path} {str(edgelist_path)} {graphlet_size} {benchmarking_run}"


def main():
    """Generate sbatch file."""
    with open("slurm_benchmark.batch", "w", encoding="utf-8") as sbtach_file:
        for line in PREAMBLE_LINES:
            sbtach_file.write(line)
            sbtach_file.write("\n")

        sbtach_file.write("\n")

        for graphlet_size in GRAPHLET_SIZES:
            for dataset in DATASETS:
                for benchmarking_run in BENCHMARKING_RUNS:
                    sbtach_file.write(generate_line(Path(dataset), graphlet_size, benchmarking_run))
                    sbtach_file.write("\n")


if __name__ == "__main__":
    main()
