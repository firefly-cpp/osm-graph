from __future__ import annotations
from sport_activities_features import HillIdentification
from sport_activities_features.overpy_node_manipulation import OverpyNodesReader
from setup import OpenElevationAPI
from redisgraph import Node, Edge
import time


class Pathway:
    def __init__(self, intersection_a=None, intersection_b=None, distance=None, type=None, total_ascent=None, total_descent=None, nodes_list = None):
        self.intersection_a=intersection_a
        self.intersection_b=intersection_b
        self.distance=distance
        self.type=set([])
        self.total_ascent=total_ascent
        self.total_descent=total_descent
        self.nodes_list = nodes_list

    def generate(self,nodes,type):



        reader = OverpyNodesReader(open_elevation_api=OpenElevationAPI.url)
        reader_nodes = ""

        while True:
            try:
                reader_nodes = reader.read_nodes(nodes)
            except Exception as e:
                print(e)
                print("reader_nodes = reader.read_nodes(nodes)")
                time.sleep(2)
            else:
                break
        hill_identificator = ""
        while True:
            try:
                hill_identificator = HillIdentification(altitudes=reader_nodes["altitudes"], ascent_threshold=30)
                hill_identificator.identify_hills()
            except Exception as e:
                print(e)
                print("hill_identificator.identify_hills()")
                time.sleep(2)
            else:
                break
        self.distance = reader_nodes["total_distance"]
        self.total_ascent=hill_identificator.total_ascent
        self.total_descent=hill_identificator.total_descent
        self.intersection_a=nodes[0]
        self.intersection_b=nodes[-1]
        self.nodes_list=nodes
        self.type=set([type])

    def giveTwoWayRelationship(self, node_a:Node, node_b:Node):
        relationshipA = Edge(node_a, 'Path', node_b, properties={'distance': self.distance, 'ascent':self.total_ascent, 'descent':self.total_descent, 'type':self.type})
        relationshipB = Edge(node_b, 'Path', node_a, properties={'distance': self.distance, 'ascent':self.total_descent, 'descent':self.total_descent, 'type':self.type})
        return [relationshipA, relationshipB]

    def __add__(self, o: Pathway):
        self.distance += o.distance
        self.type.update(o.type)
        if self.intersection_b.id == o.intersection_a.id:
            self.total_ascent+=o.total_ascent
            self.total_descent+=o.total_descent
            self.intersection_b=o.intersection_b
            combined_nodes = [*self.nodes_list, *o.nodes_list]
            self.nodes_list = combined_nodes

        elif self.intersection_a.id == o.intersection_b.id:
            self.total_ascent+=o.total_ascent
            self.total_descent+=o.total_descent
            self.intersection_a=o.intersection_a
            combined_nodes = [*o.nodes_list, *self.nodes_list]
            self.nodes_list=combined_nodes

        elif self.intersection_b.id==o.intersection_b.id:
            self.intersection_b=o.intersection_a
            self.total_ascent+=o.total_descent
            self.total_descent+=o.total_ascent
            combined_nodes = [*self.nodes_list, *o.nodes_list.reverse()]
            self.nodes_list=combined_nodes

        elif self.intersection_a.id==o.intersection_a.id:
            self.intersection_a=o.intersection_b
            self.total_ascent += o.total_descent
            self.total_descent += o.total_ascent
            combined_nodes = [*o.nodes_list.reverse(), *self.nodes_list]
            self.nodes_list=combined_nodes

        return self


