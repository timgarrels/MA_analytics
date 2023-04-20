"""We have results computed with an old pmotif_lib version.
Their format is not readable anymore by the current pmotif_lib version, but theoretically compatible.
This converts an old format into the new one."""
import json
import os
import statistics
from pathlib import Path
from tqdm import tqdm

TARGET = Path("./conversion_target/kaggle_star_wars.edgelist_motifs/3/positional_data")


def read_graphlet_metrics(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        total = int(f.readline().strip())
        data = [json.loads(l) for l in tqdm(f, total=total)]
    return data


def read_graph_modules(file_path: Path):
    graph_modules = []
    with open(file_path, "r", encoding="utf-8") as f:
        total = int(f.readline().strip())
        for l in tqdm(f, total=total):
            graph_modules.append(l.strip().split(" "))

    return graph_modules


def read_anchor_nodes(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        total = int(f.readline().strip())
        data = [l.strip() for l in tqdm(f, total=total)]
    return data


def read_anchor_node_shortest_path(file_path: Path):
    data = {}
    with open(file_path, "r", encoding="utf-8") as f:
        total = int(f.readline().strip())
        for l in tqdm(f, total=total):
            anchor_node, *parts = l.split(" ")
            data[anchor_node] = json.loads(" ".join(parts))
    return data


def convert_degree(metrics, outpath: Path):
    os.makedirs(outpath / "pDegree" / "pre_compute")
    with open(outpath / "pDegree" / "graphlet_metrics", "w", encoding="utf-8") as out:
        out.write(str(len(metrics)))
        out.write("\n")
        for metric_lookup in metrics:
            out.write(json.dumps(metric_lookup["degree"]))
            out.write("\n")


def convert_graph_modules(metrics, graph_modules, outpath: Path):
    os.makedirs(outpath / "pGraphModuleParticipation" / "pre_compute")
    with open(outpath / "pGraphModuleParticipation" / "pre_compute" / "graph_modules", "w", encoding="utf-8") as out:
        json.dump(graph_modules, out)

    with open(outpath / "pGraphModuleParticipation" / "graphlet_metrics", "w", encoding="utf-8") as out:
        out.write(str(len(metrics)))
        out.write("\n")
        for metric_lookup in metrics:
            out.write(json.dumps(metric_lookup["graph_module_participation"]))
            out.write("\n")


def convert_anchor_node_distance(metrics, anchor_nodes, anchor_node_shortest_paths, outpath: Path):
    os.makedirs(outpath / "pAnchorNodeDistance" / "pre_compute")
    with open(outpath / "pAnchorNodeDistance" / "pre_compute" / "anchor_nodes", "w", encoding="utf-8") as out:
        json.dump(anchor_nodes, out)
    with open(outpath / "pAnchorNodeDistance" / "pre_compute" / "nodes_shortest_path_lookup", "w", encoding="utf-8") as out:
        json.dump(anchor_node_shortest_paths, out)
    closeness_centrality = {
        anchor_node: statistics.mean(shortest_path_lookup.values())
        for anchor_node, shortest_path_lookup in anchor_node_shortest_paths.items()
    }
    with open(outpath / "pAnchorNodeDistance" / "pre_compute" / "closeness_centrality", "w", encoding="utf-8") as out:
        json.dump(closeness_centrality, out)

    with open(outpath / "pAnchorNodeDistance" / "graphlet_metrics", "w", encoding="utf-8") as out:
        out.write(str(len(metrics)))
        out.write("\n")
        for metric_lookup in metrics:
            out.write(json.dumps(metric_lookup["anchor_node_distances"]))
            out.write("\n")


def main():
    metrics = read_graphlet_metrics(TARGET / "graphlet_metrics")
    anchor_nodes = read_anchor_nodes(TARGET / "anchor_nodes")
    graph_modules = read_graph_modules(TARGET / "graph_modules")
    anchor_node_shortest_paths = read_anchor_node_shortest_path(TARGET / "anchor_node_shortest_paths")

    outpath = TARGET.parent / "pmetrics"
    os.makedirs(outpath)
    convert_degree(metrics, outpath)
    convert_graph_modules(metrics, graph_modules, outpath)
    convert_anchor_node_distance(metrics, anchor_nodes, anchor_node_shortest_paths, outpath)


if __name__ == "__main__":
    main()
