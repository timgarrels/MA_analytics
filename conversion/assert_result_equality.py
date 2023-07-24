"""Compares two pmotif_lib results and compares them for equality.
Make sure to supply ENV needed by pmotif_lib to find the dataset and the experiment out!
"""
import argparse
from pathlib import Path

from pmotif_lib.result_transformer import ResultTransformer


def compare_graph_module(converted: ResultTransformer, new: ResultTransformer):
    """Compare the pMetric for graph modules."""
    converted = converted.get_p_metric_result("pGraphModuleParticipation")
    new = new.get_p_metric_result("pGraphModuleParticipation")

    assert converted.graphlet_metrics == new.graphlet_metrics

    for i, m in enumerate(new.pre_compute["graph_modules"]):
        assert sorted(m) == sorted(converted.pre_compute["graph_modules"][i]), f"Graph module nr {i} differs!"
    print("pGraphModuleParticipation is same!")


def compare_degree(converted: ResultTransformer, new: ResultTransformer):
    """Compare the pMetric for degree."""
    converted = converted.get_p_metric_result("pDegree")
    new = new.get_p_metric_result("pDegree")
    assert converted.graphlet_metrics == new.graphlet_metrics, "PDegree differs!"
    print("pDegree is same!")


def compare_anchor(converted: ResultTransformer, new: ResultTransformer):
    """Compare the pMetric for anchor node distance."""
    converted = converted.get_p_metric_result("pAnchorNodeDistance")
    new = new.get_p_metric_result("pAnchorNodeDistance")
    assert converted.graphlet_metrics == new.graphlet_metrics

    for i, m in enumerate(new.pre_compute["anchor_nodes"]):
        assert sorted(m) == sorted(converted.pre_compute["anchor_nodes"][i]), f"Anchor node {i} differs!"

    centrality_same = new.pre_compute["closeness_centrality"] == converted.pre_compute["closeness_centrality"]
    assert centrality_same, "Closeness Centrality differs!"

    shortest_path_same = new.pre_compute["nodes_shortest_path_lookup"] == converted.pre_compute["nodes_shortest_path_lookup"]
    assert shortest_path_same, "Shortest Paths differ!"
    print("pAnchorNodeDistance is same!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--edgelist-path", required=True, type=Path)
    parser.add_argument("--graphlet_size", required=True, type=int, default=3, choices=[3, 4])
    parser.add_argument("--first_result", required=True, type=Path)
    parser.add_argument("--second_result", required=True, type=Path)

    args = parser.parse_args()

    first_result = ResultTransformer.load_result(args.edgelist_path, args.first_result, args.graphlet_size)
    second_result = ResultTransformer.load_result(args.edgelist_path, args.second_result, args.graphlet_size)

    compare_graph_module(first_result, second_result)
    compare_degree(first_result, second_result)
    compare_anchor(first_result, second_result)
