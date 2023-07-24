"""PMetric to calculate the number of predefined graph modules a graphlet touches.
ONLY WORKS ON THE ORIGINAL GRAPH!"""
from typing import List
import networkx as nx

from pmotif_lib.p_metric.p_metric import PMetric, PreComputation


class GivenModuleParticipation(PMetric):
    """Measures how many unique graph modules a graphlet participates in.
    Graph modules are previously known.
    A graphlet participates in a module, if at least one graphlet node belongs to that module.

    This metrics relies on predefined modules, and therefore can not be calculated on random graphs!
    (as the predefined modules lose their meaning during the randomization of edges)
    """

    def __init__(self, modules: List[List[str]]):
        self.modules = modules
        super().__init__("pGivenModuleParticipation")

    def pre_computation(self, graph: nx.Graph) -> PreComputation:
        """No precomputation needed, as modules are given."""
        return {}

    def metric_calculation(
        self,
        graph: nx.Graph,
        graphlet_nodes: List[str],
        pre_compute: PreComputation,
    ) -> List[int]:
        """Returns a list of indices
        indicating which modules contain nodes of the graphlet occurrence."""
        participations = []
        for i, graph_module in enumerate(self.modules):
            for node in graphlet_nodes:
                if node in graph_module:
                    participations.append(i)
                    break
        return participations
