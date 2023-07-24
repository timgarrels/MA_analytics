"""ONLY WORKS ON THE ORIGINAL GRAPH!"""
from typing import List

import networkx as nx
from pmotif_lib.p_metric import p_metric
from pmotif_lib.p_metric.p_metric import PreComputation


class ExternalWeight(p_metric.PMetric):
    """PMetric to gather the weight of all edges connected to but outside the graphlet occurrence"""
    def __init__(self, graph_with_weights: nx.Graph, data_key="weight"):
        """GtrieScanner does not allow weights. Therefore, the edgelists handed to the pmotif lib never contain
        (meaningful) weights. This makes a side-channel to inject the weights necessary.
        Providing the same edgelist with weights for this metric is said side-channel."""
        self.graph_with_weights = graph_with_weights
        self.data_key = data_key

        super().__init__("pExternalWeight")

    def metric_calculation(
        self,
        graph: nx.Graph,
        graphlet_nodes: List[str],
        pre_compute: PreComputation,
    ) -> List[float]:
        """Gathers the edge weight of every external edge."""

        nodes = set(graphlet_nodes)

        external_edges = [
            (src, dst)
            for src, dst in graph.edges(graphlet_nodes)
            if src not in nodes or dst not in nodes
        ]

        return [
            self.graph_with_weights.get_edge_data(u, v)[self.data_key]
            for u, v in external_edges
        ]

    def pre_computation(self, graph: nx.Graph) -> PreComputation:
        """No pre-computation necessary for weight calculation."""
        return {}
