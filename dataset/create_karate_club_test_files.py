"""Only used to generate files to test scripts. Generates all content from the karate club graph."""
import json
from pathlib import Path
from collections import defaultdict
import random
from string import ascii_lowercase

import networkx as nx
from pmotif_lib.gtrieScanner.graph_io import write_shifted_edgelist
from pmotif_lib.p_motif_graph import PMotifGraph


g = nx.karate_club_graph()
write_shifted_edgelist(g, Path("karate_club.edgelist"), reindex=True)
del g

p_m_g = PMotifGraph(Path("karate_club.edgelist"), Path("."))
g = p_m_g.load_graph()


# Arbitrary weights (random)
nx.set_edge_attributes(g, {e: random.randint(0, 10) + random.random() for e in g.edges}, "weight")

# Arbitrary clusters by decimal digit number
clusters = defaultdict(list)
for n in g.nodes:
    if int(n) < 10:
        clusters["1"].append(n)
    else:
        clusters[int(n[-2]) + 1].append(n)

# Relabel nodes to provide a mapping later
get_new_label = lambda n: ".".join([ascii_lowercase[int(c)] for c in n])
node_mapping = {n: get_new_label(n) for n in g.nodes}
g = nx.relabel_nodes(g, node_mapping)

nx.write_edgelist(g, "karate_club_w_weights.edgelist", data=True)

with open("karate_club_node_mapping.json", "w") as f:
    json.dump(node_mapping, f)


# relabel clusters too
clusters = {
    node_mapping[str(cluster_name)]: [node_mapping[str(n)] for n in cluster_nodes]
    for cluster_name, cluster_nodes in clusters.items()
}
with open("karate_club_clusters.json", "w") as f:
    json.dump(clusters, f)

