"""Script to quickly generate an instruction file for slurm's sbtach command
to run p-motif detection on multiple datasets and different graphlet sizes."""
from pathlib import Path

LOG_BASE = "/hpi/fs00/home/tim.garrels/masterthesis/logs/data_collection/"

DATASETS = [
    # "com-dblp.ungraph.txt",
    "kaggle_so_tags.edgelist",
    "kaggle_star_wars.edgelist",
    # "email-Eu-core.txt",
    # "kaggle_so_tags.node_mapping",
    # "kaggle_star_wars.node_mapping",
    "yeastInter_st.txt",
    "random_graphs/0_barabasi_albert_graph_m_1",
    "random_graphs/0_barabasi_albert_graph_m_2",
    "random_graphs/0_barabasi_albert_graph_m_3",
    "random_graphs/0_ferdos_renyi_graph_m_2000",
    # "random_graphs/0_scale_free_graph_a_28_b_7_g_02",
    # "random_graphs/0_scale_free_graph_a_35_b_3_g_35",
    # "random_graphs/0_scale_free_graph_a_65_b_1_g_25",
    "random_graphs/1_barabasi_albert_graph_m_1",
    "random_graphs/1_barabasi_albert_graph_m_2",
    "random_graphs/1_barabasi_albert_graph_m_3",
    "random_graphs/1_ferdos_renyi_graph_m_2000",
    # "random_graphs/1_scale_free_graph_a_28_b_7_g_02",
    # "random_graphs/1_scale_free_graph_a_35_b_3_g_35",
    # "random_graphs/1_scale_free_graph_a_65_b_1_g_25",
    "random_graphs/2_barabasi_albert_graph_m_1",
    "random_graphs/2_barabasi_albert_graph_m_2",
    "random_graphs/2_barabasi_albert_graph_m_3",
    "random_graphs/2_ferdos_renyi_graph_m_2000",
    # "random_graphs/2_scale_free_graph_a_28_b_7_g_02",
    # "random_graphs/2_scale_free_graph_a_35_b_3_g_35",
    # "random_graphs/2_scale_free_graph_a_65_b_1_g_25",
    "random_graphs/3_barabasi_albert_graph_m_1",
    "random_graphs/3_barabasi_albert_graph_m_2",
    "random_graphs/3_barabasi_albert_graph_m_3",
    "random_graphs/3_ferdos_renyi_graph_m_2000",
    # "random_graphs/3_scale_free_graph_a_28_b_7_g_02",
    # "random_graphs/3_scale_free_graph_a_35_b_3_g_35",
    # "random_graphs/3_scale_free_graph_a_65_b_1_g_25",
    "random_graphs/4_barabasi_albert_graph_m_1",
    "random_graphs/4_barabasi_albert_graph_m_2",
    "random_graphs/4_barabasi_albert_graph_m_3",
    "random_graphs/4_ferdos_renyi_graph_m_2000",
    # "random_graphs/4_scale_free_graph_a_28_b_7_g_02",
    # "random_graphs/4_scale_free_graph_a_35_b_3_g_35",
    # "random_graphs/4_scale_free_graph_a_65_b_1_g_25",
    "human_cancer_cutoff_0.935.edgelist",
    "human_brain_development_cutoff_0.772.edgelist",
]

GRAPHLET_SIZES = [3, 4]
RANDOM_GRAPHS = 1000

PREAMBLE_LINES = [
    "#!/bin/bash",
    "#SBATCH -A renard",
    "#SBATCH --time=40:00:00",
    "#SBATCH --cpus-per-task=8",
    "#SBATCH --mem-per-cpu=150G",
]


def generate_line(edgelist: Path, graphlet_size: int, random_graphs: int):
    """Create a line for the sbatch file, representing a single p-motif detection task."""
    log_path = LOG_BASE + str(graphlet_size) + "/" + edgelist.name
    return f"./run_data_collection.sh {log_path} {str(edgelist)} {graphlet_size} {random_graphs}"


def main():
    """Generate sbatch file."""
    random_graphs_for_dataset = {}
    for graphlet_size in GRAPHLET_SIZES:
        with open(f"slurm_{graphlet_size}.batch", "w", encoding="utf-8") as sbtach_file:
            for line in PREAMBLE_LINES:
                sbtach_file.write(line)
                sbtach_file.write("\n")

            sbtach_file.write("\n")

            for dataset in DATASETS:
                _random_graphs = random_graphs_for_dataset.get(dataset, 1000)

                sbtach_file.write(generate_line(Path(dataset), graphlet_size, _random_graphs))
                sbtach_file.write("\n")

                random_graphs_for_dataset[dataset] = -1
            # sbtach_file.write("wait\n")


if __name__ == "__main__":
    main()
