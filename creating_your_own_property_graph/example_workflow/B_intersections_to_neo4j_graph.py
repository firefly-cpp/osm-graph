"""2. Parse identified intersections from redis to neo4j graph"""

import overpy
from setup import OverpassAPI, geo_connector
import msgpack
from py2neo import Node

try:
    current_lat = geo_connector.redis_db().delete('current_lat')
    current_lon = geo_connector.redis_db().delete('current_lon')
    print("Current lat / lon deleted")
except:
    print("Current lat / lon not in db")

nodes = geo_connector.redis_db().keys()
neo4j_graph = geo_connector.neo4j_db()
i = 0
api = overpy.Overpass(url=OverpassAPI.url)


def chunks(l, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield l[i::n]


lists = list(chunks(nodes, 1000));  # chunk into 1000
import multiprocessing as mp


def findWaysOfNode(node_id):
    q = f"""(node({node_id});<;);out geom;"""
    query = api.query(q)
    return query


def addNodes(nodes):
    i = 0
    graph_nodes = []
    for node_key in nodes:
        node = msgpack.unpackb(geo_connector.redis_db().get(node_key))
        print('Added (' + str(i) + '):' + str(node[0]))
        i += 1
        graph_node = Node('Intersection', node_id= node[0], latitude= node[1], longitude= node[2],way_ids= findWaysOfNode(node[0]).way_ids)
        graph_nodes.append(graph_node)
    return graph_nodes


if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())
    results = pool.map(addNodes, [list for list in lists])

    a = 0
    for list in results:
        for node in list:
            neo4j_graph.create(node)
            print("Adding:" + str(a))
            a += 1

    pool.close()

