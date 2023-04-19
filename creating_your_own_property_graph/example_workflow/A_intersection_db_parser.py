""" 1. Parse map and save intersections to redis db by calling save_to_db(). The script uses Overpass API to get the map data. """

from setup import MapBoundaries, geo_connector
from geo_classes.intersection import IdenitifyIntersections
import msgpack


class IntersectionDbParser:
    def save_to_db(self, nodes: []):
        """ Save intersection nodes to redis db"""
        for node in nodes:
            packed_node = msgpack.packb(node)
            geo_connector.redis_db().set(node.id, packed_node)

    def parse_map(self):
        """ Parse map and save intersections to redis db by calling save_to_db()"""
        map_boundaries = MapBoundaries()
        parserSquare = 0.03
        """Initial values for current_lat and current_lon are set to the minimum values of the map boundaries."""
        current_lat = current_lon = None
        try:
            current_lat=float(geo_connector.redis_db().get('current_lat'))
            current_lon=float(geo_connector.redis_db().get('current_lon'))
        except:
            print("lat / lon not in db")
            current_lat = map_boundaries.min_lat
            current_lon = map_boundaries.min_lon

        while current_lat < map_boundaries.max_lat+parserSquare:
            while current_lon < map_boundaries.max_lon+parserSquare:
                iden_intersections = IdenitifyIntersections(min_lat=current_lat, max_lat=current_lat + parserSquare,
                                                            min_lon=current_lon, max_lon=current_lon + parserSquare)
                nodes = iden_intersections.query()
                self.save_to_db(nodes)
                geo_connector.redis_db().set('current_lat', current_lat)
                geo_connector.redis_db().set('current_lon', current_lon)
                print(
                    f"Remaining: {(current_lat - map_boundaries.min_lat) / (map_boundaries.max_lat - map_boundaries.min_lat)}")
                current_lon += parserSquare - 0.00010
            current_lon = map_boundaries.min_lon
            current_lat += parserSquare - 0.00010

if __name__ == '__main__':
    idb = IntersectionDbParser()
    idb.parse_map()

"""
intersections = idIntersections.query()

packed = msgpack.packb(mycontainer)

r.set('foo', packed)
value = r.get('foo')
unpacked = Container(*msgpack.unpackb(value))
print(value)
print(unpacked)
"""
