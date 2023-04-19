"""3. Find intersections from neo4j and identify pathways between them"""

import time
import overpy
from py2neo import NodeMatcher
from graph.Pathway import Pathway
from setup import DisallowedRoadConditions, MapBoundaries, geo_connector, OverpassAPI, MONGO_DB_OPTIONAL
import pymongo


client = geo_connector.mongo_db(MONGO_DB_OPTIONAL)
db = None
collection=None
if(MONGO_DB_OPTIONAL):
    db=client.geo
    collection: pymongo.collection.Collection = db.pathways

nodes = geo_connector.redis_db().keys()
api = overpy.Overpass(url=OverpassAPI.url)

from datetime import datetime

neo4j_graph = geo_connector.neo4j_db()
neo4j_matcher = NodeMatcher(neo4j_graph)


def timePrint():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return " [" + current_time + "] "


def find_ways_of_node(node_id):
    q = f"""(node({node_id});<;);out geom;"""
    query = api.query(q)
    return query


def find_forward_intersections(starting_node_index, node_ids, keys, starting_id):
    i = starting_node_index
    while i < len(node_ids):  # forward search
        if keys[i] is not None and node_ids[i] != starting_id:
            return i
        i += 1
    return -1


def find_backward_intersectons(starting_node_index, node_ids, keys, starting_id):
    i = starting_node_index
    while i >= 0:  # backward search
        if keys[i] is not None and node_ids[i] != starting_id:
            return i
        i -= 1
    return -1


def redis_node_count(node_ids):
    node_count = ""
    while True:
        try:
            if 'all_nodes' not in globals():
                global all_nodes
                all_nodes=geo_connector.redis_db().keys()
                all_nodes = list(map(lambda x: int(x.decode()), all_nodes))
        except Exception as e:
            print(e)
            print("Error on (node_count = redis_db.exists(*node_ids)")
            print(*node_ids)
            time.sleep(2)
        else:
            break
    return sum(x in node_ids for x in all_nodes)


def redis_db_addressed_set(key, pathways):
    while True:
        try:
            geo_connector.redis_db_addressed().set(key, len(pathways))
        except Exception as e:
            print(e)
            print("redis_db_addressed.set(key, len(pathways))")
            print(key)
            time.sleep(2)
        else:
            break

def check_for_intersections(nodes):
    if 'all_nodes' not in globals():
        global all_nodes
        all_nodes = geo_connector.redis_db().keys()
    intersections = []
    for node in nodes:
        if node.id in all_nodes:
            intersections.append(True)
        else:
            intersections.append(None)
    return intersections

def find_connections(query_way_result, starting_id, checked_ways):
    way: overpy.Way
    pathways = []
    for way in query_way_result.ways:
        try:
            # If the type is right
            if way.tags['highway'] not in DisallowedRoadConditions.highway and way.id not in checked_ways:
                checked_ways.append(way.id)  # Add to checked ways
                nodes = way.get_nodes(resolve_missing=True)
                node_ids = list(map(lambda node: node.id, nodes))
                node_count = redis_node_count(node_ids)

                if node_count > 1:  # If any other node except for intersection is found
                    print("Get mget keys")
                    keys = ""
                    while True:
                        try:
                            if 'all_nodes' not in globals():
                                global all_nodes
                                all_nodes = geo_connector.redis_db().keys()
                            keys = check_for_intersections(nodes)
                        except Exception as e:
                            print(e)
                            print("keys = redis_db.mget(list(map(lambda node: node.id, nodes)))")
                            time.sleep(2)
                        else:
                            break
                    starting_node_index = node_ids.index(starting_id)
                    intersection_after = find_forward_intersections(starting_node_index, node_ids, keys, starting_id)
                    i_before_nodes = []
                    i_after_nodes = []
                    if starting_node_index != 0:
                        intersection_before = find_backward_intersectons(starting_node_index, node_ids, keys,
                                                                         starting_id)
                        if intersection_before == -1:  # Not found before ?----x
                            i_before_nodes.extend(nodes[:starting_node_index + 1])
                            sub_query_ways = find_ways_of_node(node_ids[0])
                            if len(sub_query_ways.way_ids) > 1:
                                result = find_connections(query_way_result=sub_query_ways, starting_id=node_ids[0],
                                                          checked_ways=checked_ways)
                                if (result != None):
                                    pathway = Pathway()
                                    pathway.generate(i_before_nodes, type=way.tags['highway'])
                                    if (len(result) == 1):
                                        pathway = pathway + result[0]
                                        pathways.append(pathway)
                                print('Išči dalje nazaj')
                        else:  # Found before y----x
                            i_before_nodes.extend(nodes[intersection_before:starting_node_index + 1])
                            pathway = Pathway()
                            pathway.generate(i_before_nodes, type=way.tags['highway'])
                            pathways.append(pathway)
                            # OK
                    if starting_node_index != len(node_ids) - 1:
                        if intersection_after == -1:  # not found after x----?
                            i_after_nodes.extend(nodes[starting_node_index - 1:])
                            sub_query_ways = find_ways_of_node(node_ids[len(node_ids) - 1])
                            if len(sub_query_ways.way_ids) > 1:
                                result = find_connections(query_way_result=sub_query_ways, starting_id=node_ids[0],
                                                          checked_ways=checked_ways)
                                if (result != None):
                                    pathway = Pathway()
                                    pathway.generate(i_after_nodes, type=way.tags['highway'])
                                    if (len(result) == 1):
                                        pathway = pathway + result[0]
                                        pathways.append(pathway)
                                print('Išči dalje naprej')
                        else:  # found after x----y
                            i_after_nodes.extend(nodes[starting_node_index:intersection_after + 1])
                            pathway = Pathway()
                            pathway.generate(i_after_nodes, type=way.tags['highway'])
                            pathways.append(pathway)
                            # OK
        except KeyError:
            print(f'Not a OSM highway! {way.id}')
    return pathways

keys = geo_connector.redis_db().keys()

def connectionExists(node_a, node_b) -> bool:
    q = f""" MATCH (i_a:Intersection{{node_id:{node_a.id}}})-[p:Path]->(i_b:Intersection{{node_id:{node_b.id}}}) 
    RETURN COUNT(*)
    """
    cursor_result = neo4j_graph.run(q)
    if cursor_result.evaluate() > 0:
        return True
    else:
        return False

i = 0
total = len(keys)
addressed_nodes = geo_connector.redis_db_addressed().keys()



MapBoundariesSearch = MapBoundaries()

# Just for defined MapBoundaries
q = f"""MATCH (i:Intersection) 
WHERE i.latitude > {MapBoundariesSearch.min_lat} AND 
i.latitude < {MapBoundariesSearch.max_lat} AND 
i.longitude > {MapBoundariesSearch.min_lon} AND 
i.longitude < {MapBoundariesSearch.max_lon} RETURN i"""

slovenia_nodes = neo4j_graph.run(q)

def toMongoNode(node):
    return {'id':node.id, 'lat':float(node.lat), 'lon':float(node.lon)}



# For testing purposes
to_delete = []
profiler = 1

for record in slovenia_nodes:
    key = record[0]['node_id']
    i += 1
    if (str(key).encode() not in addressed_nodes):
        profiler += 1
        print('querying ' + str(key) + '\t Progress: ' + str(i / total) + 'P:' + str(profiler) + " " + timePrint())
        queryResult = find_ways_of_node(key)
        pathways = find_connections(queryResult, key, [])
        for pathway in pathways:
            if connectionExists(pathway.intersection_a, pathway.intersection_b) is not True: #to Neo4j
                create_queryA = lambda id_a, id_b: f"MATCH (i_a:Intersection{{node_id:{id_a}}}) \n" \
                                                   f"MATCH (i_b:Intersection{{node_id:{id_b}}}) \n" \
                                                   f"CREATE (i_a)-[:Path{{distance:{pathway.distance}, ascent:{pathway.total_ascent}, descent:{pathway.total_descent}, type:'{list(pathway.type)[0]}'}}]->(i_b)"
                neo4j_graph.run(create_queryA(pathway.intersection_a.id, pathway.intersection_b.id))
            if connectionExists(pathway.intersection_b, pathway.intersection_a) is not True:
                create_queryB = lambda id_a, id_b: f"MATCH (i_a:Intersection{{node_id:{id_b}}}) \n" \
                                                   f"MATCH (i_b:Intersection{{node_id:{id_a}}}) \n" \
                                                   f"CREATE (i_a)-[:Path{{distance:{pathway.distance}, ascent:{pathway.total_descent}, descent:{pathway.total_ascent}, type:'{list(pathway.type)[0]}'}}]->(i_b)"
                neo4j_graph.run(create_queryB(pathway.intersection_a.id, pathway.intersection_b.id))

            if MONGO_DB_OPTIONAL:
                if collection.count_documents({'intersection_a':pathway.intersection_a.id, #to MONGO
                                               'intersection_b': pathway.intersection_b.id}) == 0:
                    collection.insert_one({
                        'intersection_a':pathway.intersection_a.id,
                        'intersection_b':pathway.intersection_b.id,
                        'nodes':list(map(toMongoNode, pathway.nodes_list))
                    })

                if collection.count_documents({'intersection_a':pathway.intersection_b.id,
                                               'intersection_b': pathway.intersection_a.id}) == 0:
                    reversed_list = pathway.nodes_list.reverse()
                    collection.insert_one({
                        'intersection_a':pathway.intersection_b.id,
                        'intersection_b': pathway.intersection_a.id,
                        'nodes':list(map(toMongoNode, pathway.nodes_list))
                    })

        redis_db_addressed_set(key, pathways)
        print("Addded" + timePrint())

    else:
        print("skipping " + str(key) + " " + str(i))
        to_delete.append(str(key).encode())

    a = 100
a = 0
