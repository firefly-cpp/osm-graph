from collections import namedtuple

import overpy

from setup import OverpassAPI

Intersection = namedtuple('Intersection', ['id', 'lat', 'lon'])


class IdenitifyIntersections:
    def __init__(self, max_lat, min_lat, max_lon, min_lon):
        self.max_lat = max_lat
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.min_lon = min_lon

    def query(self):
        """ Query Overpass Api for intersections in given area."""
        q = f"""way
      ["highway"]
      ["highway"!~"footway|cycleway|path|proposed|motorway|bridleway|trunk"]
      ({self.min_lat}, {self.min_lon}, {self.max_lat}, {self.max_lon})
      ->.relevant_ways;
    foreach.relevant_ways->.this_way{{
      node(w.this_way)->.this_ways_nodes;
      way(bn.this_ways_nodes)->.linked_ways;
      way.linked_ways
        ["highway"]
        ["highway"!~"footway|cycleway|path|proposed|motorway|bridleway|trunk"]
        ->.linked_ways;
        (
            .linked_ways->.linked_ways;
            -
            .this_way->.this_way;
        )->.linked_ways_only;
        node(w.linked_ways_only)->.linked_ways_only_nodes;
        node.linked_ways_only_nodes.this_ways_nodes;
        out;
    }}
    """
        api = overpy.Overpass(url=OverpassAPI.url).query(q)
        nodes = []
        for node in api.nodes:
            nodes.append(Intersection(id=node.id, lat=float(node.lat), lon=float(node.lon)))
        return nodes
