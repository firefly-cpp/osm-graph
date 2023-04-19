import random
import pickle
import igraph as ig
import numpy
import numpy as np


""" This example demonstrates how to import exported binary file (from export_graph.py) and import it inside a Python library igraph network analysis package object.
The example generates a sample shortest (distance) route between two OpenStreetMap ids' https://www.openstreetmap.org/node/41217379 and https://www.openstreetmap.org/node/851215607.
The resulting object returns a shortest path object with all the resulting nodes, distance, ascent, and descent calculation.
{'epath': array([118656, 110139,  53784,  24039,  92205, 406910, 350709, 399592,
       301551, 195882,  78446,  79362,  76688, 298800, 374065, 407993,
       130441], dtype=uint64), 'nodes': array([[  41217379,  870595475],
       [ 870595475,  862290510],
       [ 862290510,  265799535],
       [ 265799535,   55421476],
       [  55421476,   55421472],
       [  55421472, 1665687106],
       [1665687106,   60886369],
       [  60886369,   55421459],
       [  55421459,   55421452],
       [  55421452, 3428312436],
       [3428312436,   60740778],
       [  60740778,   60740780],
       [  60740780,  497870075],
       [ 497870075,  269176966],
       [ 269176966,  851215544],
       [ 851215544,  851255280],
       [ 851255280,  851215607]], dtype=uint64), 'ascents': array([0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 1., 0., 0., 0., 0., 0., 0.]), 'descents': array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]), 'distances': array([128.74743326,  74.71519445,  68.21589965,  73.98543975,
        80.71996532,  62.66416465,  61.83094438,  64.88713233,
       149.23543464,  65.81156845, 123.94570141,  12.42540025,
        53.57033647,  70.71352518,  59.09435311,   7.75236093,
        44.35859654]), 'evaluation': {'total_cost': 1202.6734507679469, 'total_distance': 1202.6734507679469, 'total_ascent': 2.0, 'total_descent': 0.0}}
"""


class NodeConverter:

    def __init__(self, edges: np.core.ndarray):
        """
        Class for converting between igraph node ids' and OpenStreetMap real world node ids'
        :param edges: all the intersections
        """
        self.nodes_igraph = edges
        self.nodes_osm = {}
        i = 0
        for node in edges:
            self.nodes_osm[node] = i
            i += 1

    def get_osm(self, igraph_id):
        return self.nodes_igraph[igraph_id]

    def get_igraph(self, osm_id):
        return self.nodes_osm[osm_id]


class IgraphHelper:

    def __init__(self, edges=None, rel_a=None, rel_b=None, verifications=None, distances=None,
                 ascents=None, descents=None,
                 costs="distances"):
        """
        Sample class for generating shortest routes between A and B, from pickle import

        """
        self.g = ig.Graph(directed=True)
        self.ascents = ascents
        self.descents = descents
        self.distances = distances
        self.rel_a = rel_a
        self.rel_b = rel_b
        self.verifications = verifications
        self.used_paths = np.empty([ascents.size], dtype=float)
        self.costs = []
        self.nodes: NodeConverter = NodeConverter(edges)
        if edges is not None:
            self.init_vertices(edges)
        if rel_a is not None and rel_b is not None and len(rel_a) == len(rel_b):
            self.init_relationships(rel_a, rel_b)
            self.set_costs(costs)

    def set_costs(self, attr="distances"):
        self.costs = self.__getattribute__(attr).copy()

    def init_vertices(self, node_list):
        self.g.add_vertices(len(node_list))

    def init_relationships(self, a, b):
        edges = []
        for index in range(len(a)):
            edges.append((self.nodes.get_igraph(a[index]), self.nodes.get_igraph(b[index])))
        self.g.add_edges(edges)

    def route_between_a_b(self, a, b, property="distance"):
        # set costs
        if (property == "distance"):
            self.costs = self.distances.copy()
        elif (property == "ascent"):
            self.costs = self.ascents.copy()

        a = self.nodes.get_igraph(a)
        b = self.nodes.get_igraph(b)

        path = self.get_shortest_path(a, b, input_type="igraph")
        return path

    def get_shortest_path(self, a, b, input_type):
        """

        :param a:
        :type a:
        :param b:
        :type b:
        :param input_type:
        :type input_type:
        :return:
        :rtype:
        """
        if input_type == "neo4j":
            a = self.nodes.get_igraph(a)
            b = self.nodes.get_igraph(b)
        elif input_type != "igraph":
            return None

        path = self.g.get_shortest_paths(a, b, weights=self.costs, output="epath")

        cost = 0
        ascent = 0
        descent = 0
        distance = 0

        nodes = np.empty([len(path[0]), 2], dtype=np.uint64)
        ascents = np.empty([len(path[0])])
        descents = np.empty([len(path[0])])
        distances = np.empty([len(path[0])])
        costs = np.empty([len(path[0])])

        i = 0
        for e in path[0]:
            nodes[i][0] = self.rel_a[e]
            nodes[i][1] = self.rel_b[e]
            costs[i] = self.costs[e]
            ascents[i] = self.ascents[e]
            descents[i] = self.descents[e]
            distances[i] = self.distances[e]
            cost += self.costs[e]
            ascent += self.ascents[e]
            descent += self.descents[e]
            distance += self.distances[e]
            i += 1

        return {
            "epath"     : np.array(path[0], dtype=np.uint64),  # epath
            "nodes"     : nodes,
            "ascents"   : ascents,
            "descents"  : descents,
            "distances" : distances,
            "evaluation": {
                "total_cost"    : cost,
                "total_distance": distance,
                "total_ascent"  : ascent,
                "total_descent" : descent,
                },
            }


read = open('graph.pickle', 'rb')
data = pickle.load(read)
ig = IgraphHelper(data['edges'], rel_a=data['rel_a'], rel_b=data['rel_b'],
                  distances=data['distances'],
                  ascents=data['ascents'], descents=data['descents'])
route = ig.route_between_a_b(41217379, 851215607)
a = 100
