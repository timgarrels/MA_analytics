"""Utilities to plot graphs in the context of graphlets."""
import json
from typing import List, Dict

import networkx as nx
import pandas as pd
from matplotlib.axes import Axes

from pmotif_lib.p_motif_graph import PMotifGraph


def get_kamada_kawai_layout(pmotif_graph: PMotifGraph):
    """Return a kamda kawai layout of the given graph.
    Load it from disk if present, create it on disk if not."""
    layout_output_path = pmotif_graph.output_directory / "kamada_kawai_layout.json"
    if not layout_output_path.is_file():
        nx_g = pmotif_graph.load_graph()
        pos = _kamada_kawai_layout_with_multiple_components(nx_g)

        # Cast nd-Array type (from coords) to json serializable list
        pos = {k: list(v) for k, v in pos.items()}

        with open(layout_output_path, "w", encoding="utf-8") as layout_output:
            json.dump(pos, layout_output)

    with open(layout_output_path, "r", encoding="utf-8") as layout_output:
        return json.load(layout_output)


def _kamada_kawai_layout_with_multiple_components(graph: nx.Graph) -> Dict[str, List[float]]:
    """Create a kamada kawai layout,
    placing disconnected components at maximum distance from center"""
    pos_df = pd.DataFrame(index=graph.nodes(), columns=graph.nodes())
    max_dist = -1
    for row, data in nx.shortest_path_length(graph):
        for col, dist in data.items():
            pos_df.loc[row, col] = dist
            max_dist = max(max_dist, dist)

    pos_df = pos_df.fillna(max_dist / 2 + 2)

    return nx.kamada_kawai_layout(graph, dist=pos_df.to_dict())


def highlight_nodes(graph: nx.Graph, nodes: List[str], axis: Axes, pos: Dict[str, List[float]]):
    """Highlight a given set of nodes in a color on the given axes."""
    subgraph = nx.induced_subgraph(graph, nodes)

    nx.draw_networkx_nodes(
        graph,
        nodelist=subgraph.nodes,
        node_color="r",
        pos=pos,
        ax=axis,
        node_size=20,
    )
    nx.draw_networkx_labels(
        graph,
        labels={node: node for node in subgraph.nodes},
        pos=pos,
        ax=axis,
        font_size=6,
        font_color="b",
    )
    nx.draw_networkx_edges(
        graph,
        pos=pos,
        edgelist=subgraph.edges,
        ax=axis,
        edge_color="r",
    )


def plot_graph_with_multiple_node_set_highlights(
    graph: nx.Graph,
    node_sets: List[List[str]],
    pos: Dict[str, List[float]],
    axis: Axes,
    title: str = "",
):
    """Draw a given graph onto a given axis using a given position lookup,
    but highlight given sets of nodes in a color."""
    nx.draw(graph, pos=pos, ax=axis, node_size=20)

    for nodes in node_sets:
        highlight_nodes(graph, nodes, axis, pos)

    axis.set_title(title)


def get_zommed_graph(graph: nx.Graph, nodes: List[str], node_range: int = 3) -> nx.Graph:
    """Reduce given graph to a given set of nodes, plotting ony the nodes and neighbors in
    a radius of node_range."""
    relevant_nodes = []
    for node in nodes:
        neighbors = nx.descendants_at_distance(graph, node, node_range)
        relevant_nodes.extend(neighbors)
        relevant_nodes.append(node)

    subgraph = nx.induced_subgraph(graph, relevant_nodes)

    return subgraph
