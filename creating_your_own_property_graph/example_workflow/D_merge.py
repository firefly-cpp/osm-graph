""" Merge the paths that have only two intersections in between them."""

import pickle

from py2neo import Graph, NodeMatcher
import asyncio

import setup
from setup import geo_connector

neo4j_graph = geo_connector.neo4j_db()
neo4j_matcher = NodeMatcher(neo4j_graph)

middle_eliminated = []

import pymongo

client = None
db = None
collection = None

if setup.MONGO_DB_OPTIONAL:
    client = geo_connector.mongo_db()
    db = client.geo
    collection: pymongo.collection.Collection = db.pathways

a=100

class MergedRoute:
    def __init__(self, middle_id=None, end_id=None, start_id=None,
                 distance=None, ascent=None, descent=None, type=None):
        self.middle_id = middle_id
        self.end_id = end_id
        self.start_id = start_id
        self.distance = distance
        self.ascent = ascent
        self.descent = descent
        self.type = type
        self.mongo_start = []
        self.mongo_end = []

    def generateQuery(self):
        create_query = lambda id_a, id_b, distance, ascent, descent, type: \
            f"MATCH (i_a:Intersection{{node_id:{id_a}}}) \n" \
            f"MATCH (i_b:Intersection{{node_id:{id_b}}}) \n" \
            f"CREATE (i_a)-[:Path{{distance:{distance}, ascent:{ascent}, descent:{descent}, type:'{type}'}}]->(i_b)"
        forward = create_query(self.start_id, self.end_id, self.distance, self.ascent, self.descent, self.type)
        backward = create_query(self.end_id, self.start_id, self.distance, self.descent, self.ascent, self.type)
        remove_original = f"MATCH (n {{node_id: {self.middle_id}}}) DETACH DELETE n"
        return forward, backward, remove_original


def toMongoNode(node):
    return {'id': node.id, 'lat': float(node.lat), 'lon': float(node.lon)}




async def prepare_relationships(list):
    merger_routes_list = []
    middle_eliminated = []
    merged_route = MergedRoute()
    queries = []
    i = 0
    while i < len(list):
        print(i)
        if list['connected_id'][i] not in middle_eliminated:
            if merged_route.middle_id == None:
                merged_route.middle_id = list['middle_id'][i]
                merged_route.end_id = list['connected_id'][i]
                merged_route.distance = list['distance'][i]
                merged_route.ascent = list['fromAscent'][i]
                merged_route.descent = list['fromDescent'][i]
                merged_route.type = list['fromType'][i]
                if setup.MONGO_DB_OPTIONAL:
                    merged_route.mongo_end = collection.find_one(
                        {'intersection_a': int(merged_route.middle_id), 'intersection_b': int(merged_route.end_id)})[
                        'nodes']
            elif merged_route.middle_id == list['middle_id'][i]:
                merged_route.start_id = list['connected_id'][i]
                merged_route.distance += list['distance'][i]
                merged_route.descent += list['fromAscent'][i]
                merged_route.ascent += list['fromDescent'][i]
                if setup.MONGO_DB_OPTIONAL:
                    merged_route.mongo_start = collection.find_one(
                        {'intersection_a': int(merged_route.start_id), 'intersection_b': int(merged_route.middle_id)})[
                        'nodes']
            elif merged_route.middle_id != list['middle_id'][i]:
                if merged_route.start_id != None and merged_route.end_id != None:
                    merger_routes_list.append(merged_route)
                    middle_eliminated.append(merged_route.middle_id)
                merged_route = MergedRoute()
                i -= 1
            else:
                merged_route = MergedRoute()
        else:
            merged_route = MergedRoute()
        i += 1
    i = 0
    with open("test.pickle", "wb") as fp:  # Pickling
        pickle.dump(merger_routes_list, fp)


async def process_route(merged_route):
    forward, backward, remove_original = merged_route.generateQuery()
    fwd = neo4j_query(forward)
    bwd = neo4j_query(backward)
    rm_o = neo4j_query(remove_original)
    if setup.MONGO_DB_OPTIONAL:
        to_nodes = to_mongo_nodes_reverse(merged_route)
        from_nodes = to_mongo_nodes(merged_route)
    await to_nodes
    await from_nodes
    await fwd
    await bwd
    await rm_o


async def neo4j_query(query):
    neo4j_graph.run(query)
    return 1

async def to_mongo_nodes_reverse(merged_route):
    if collection.count_documents({
        'intersection_a': int(merged_route.start_id),
        'intersection_b': int(merged_route.end_id),
    }) == 0:
        collection.insert_one({
            'intersection_a': int(merged_route.start_id),
            'intersection_b': int(merged_route.end_id),
            'nodes': [*merged_route.mongo_start[:-1], *merged_route.mongo_end]
        })
        if len([*merged_route.mongo_start[:-1], *merged_route.mongo_end]) < 2:
            a = "HALT"
    return 1


async def process_pickle(merged_route):
    i = 0
    for mr in merged_route:
        await process_route(mr)
        print(str(i))
        i += 1


async def to_mongo_nodes(merged_route):
    if collection.count_documents({
        'intersection_a': int(merged_route.end_id),
        'intersection_b': int(merged_route.start_id),
    }) == 0:
        reversed_list = [*merged_route.mongo_start[:-1], *merged_route.mongo_end]
        reversed_list.reverse()
        collection.insert_one({
            'intersection_a': int(merged_route.end_id),
            'intersection_b': int(merged_route.start_id),
            'nodes': [*reversed_list]
        })
        if len([*merged_route.mongo_start[:-1], *merged_route.mongo_end]) < 2:
            a = "HALT"
    return 2


#pred merganjem

res = neo4j_graph.query('''
MATCH (middleNode:Intersection)
WHERE size([(middleNode)-[:Path]->() | 1]) = 2
WITH middleNode
LIMIT 100000000
MATCH fromPath = (middleNode)-[fromMiddle:Path]->(end)
MATCH toPath = (end)-[toMiddle:Path]->(middleNode)
RETURN middleNode.node_id as middle_id,  end.node_id as connected_id, fromMiddle.distance as distance, fromMiddle.ascent as fromAscent, fromMiddle.descent as fromDescent, fromMiddle.type as fromType''')
candidates = res.to_data_frame()

prev_candidates = len(candidates)

while len(candidates) > 0:
    res = neo4j_graph.query('''
    MATCH (middleNode:Intersection)
    WHERE size([(middleNode)-[:Path]->() | 1]) = 2
    WITH middleNode
    LIMIT 100000000
    MATCH fromPath = (middleNode)-[fromMiddle:Path]->(end)
    MATCH toPath = (end)-[toMiddle:Path]->(middleNode)
    RETURN middleNode.node_id as middle_id,  end.node_id as connected_id, fromMiddle.distance as distance, fromMiddle.ascent as fromAscent, fromMiddle.descent as fromDescent, fromMiddle.type as fromType''')
    candidates = res.to_data_frame()
    print('remaining '+str(len(candidates)))

    if(prev_candidates==len(candidates)):
        break

    loop = asyncio.new_event_loop()
    prepare_r=prepare_relationships(candidates)
    loop.run_until_complete(prepare_r)
    loop.close()

    x = None
    with open('test.pickle', 'rb') as f:
        x = pickle.load(f)
    loop2 = asyncio.new_event_loop()
    p_p = process_pickle(x)
    loop2.run_until_complete(p_p)
    loop2.close()
    prev_candidates = len(candidates)

print('Completed')