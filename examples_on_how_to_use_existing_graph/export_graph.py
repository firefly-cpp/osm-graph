"""
The purpose of the script is querying all the nodes and relationships from the Neo4J database and exporting them into a pickle binary file.
The connection string is defined in the \textit{neo4j\_graph} variable.
The output is a binary file containing a list of all edges, relationships, together with their distances, ascents, and descents.
"""

import pickle  # Dependency for saving the database
import numpy as np  # Dependency for saving the lists into an numpy array
from py2neo import Graph  # Neo4J graph connector

neo4j_graph = Graph("bolt://localhost:7687", auth=("neo4j", "test"))  # Connection string

length_relationships = len(neo4j_graph.relationships)
a = np.empty([length_relationships], dtype=np.uint64)  # Intersection node A
b = np.empty([length_relationships], dtype=np.uint64)  # Intersection node B
distances = np.empty([length_relationships], dtype=float)  # Distance A->B
descents = np.empty([length_relationships], dtype=float)  # Descent A->B
ascents = np.empty([length_relationships], dtype=float)  # Ascent A->B

for i in range(int(length_relationships / 10000) + 1):
    skip = i * 10000  # Query relationships for 10000 at a time
    relationships = neo4j_graph.query(f"MATCH p=(a:Intersection)-[r:Path]->(b:Intersection) "
                                      f"RETURN a.node_id AS a," f"b.node_id AS b,"
                                      f"r.distance as distance,"  f"r.ascent as ascent,"
                                      f"r.descent as descent "
                                      f"SKIP {skip} LIMIT 10000").to_ndarray()

    for index in range(len(relationships)):
        a[index + skip] = relationships[index][0]
        b[index + skip] = relationships[index][1]
        distances[index + skip] = relationships[index][2]
        ascents[index + skip] = relationships[index][3]
        descents[index + skip] = relationships[index][4]

# Query all edges
node_list = neo4j_graph.query(f"MATCH p=(a:Intersection) RETURN a.node_id AS a").to_ndarray()
edges = np.empty([len(node_list)], dtype=np.uint64)

for index in range(len(node_list)):
    edges[index] = node_list[index][0]

data = {
    "edges"  : edges, "rel_a": a, "rel_b": b, "distances": distances,
    "ascents": ascents, "descents": descents
    }

read = open('graph.pickle', 'wb')
pickle.dump(data, read)
read.close()
