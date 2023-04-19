import math
import os
from dotmap import DotMap

from py2neo import Graph, NodeMatcher
from sport_activities_features import GPXFile, TCXFile
from geopy.distance import geodesic

from setup import geo_connector

gpxFolderList: [str] = [x[0] for x in os.walk('data/gpx/')]
tcxFolderList: [str] = [x[0] for x in os.walk('data/tcx/')]
gpxFolderList.pop(0)
tcxFolderList.pop(0)

neo4j_graph = geo_connector.neo4j_db()
neo4j_matcher = NodeMatcher(neo4j_graph)



def readFolder(folderList):
    folder: str
    for folder in gpxFolderList + tcxFolderList:
        print("#################\nFolder:" + folder + "\n################")
        (from_index, to_index) = (folder.rfind("/") + 1, len(folder))
        athlete = folder[from_index:to_index]
        fileList: [str] = os.listdir(folder)
        for index, file in enumerate(fileList):
            print(f"""Processing: {index}/{len(fileList)} \t [{file}]""")
            processFile(folder, file, athlete)

def processFile(folder, file, athlete):
    file_path = f"{folder}/{file}"
    data = None
    if file.endswith(".gpx"):
        gpx_file = GPXFile()
        data = gpx_file.read_one_file(file_path)
    elif file.endswith(".tcx"):
        tcx_file=TCXFile()
        data = tcx_file.read_one_file(file_path)

    box = {'max_lat' : -1000, 'min_lat': 1000,
                      'max_lon':-1000, 'min_lon':1000}
    nearby = []
    intersection_boost = []
    for position in data['positions']:
        if position[0]>box['max_lat'] or position[0]<box['min_lat'] or position[1]>box['max_lon'] or position[1]<box['min_lon']:
            box = {'max_lat' : position[0]+0.009, 'min_lat': position[0]-0.009,
                   'max_lon':position[1]+0.009, 'min_lon':position[1]-0.001}
            q = f"""MATCH (n:Intersection) WHERE {position[0]-0.01}<n.latitude<{position[0]+0.01} and {position[1]-0.01}<n.longitude<{position[1]+0.01} RETURN n"""
            nearby = neo4j_graph.query(q).data()
        elif len(nearby)>0:
            closest_id = None
            distance = 99999999
            for intersection in nearby:
                (i_lat, i_lon) = (intersection['n']['latitude'],intersection['n']['longitude'])
                if math.sqrt(abs(i_lat-position[0])**2+abs(i_lon-position[1])**2) < 0.00035:
                    d= geodesic((i_lat, i_lon), position).meters
                    if d<distance:
                        distance=d
                        closest_id=intersection['n']['node_id']
            try_append_to_intersection_boost(closest_id, distance, intersection_boost)
    for i in intersection_boost:
        print("""verifying:{i}""")
        update_verified_node(i, 1)
    print(file)
    a=10

def update_verified_node(node_id, count):
    q=f"""MATCH(n:Intersection{{node_id:{node_id}}}) SET n.verified=n.verified+{count} RETURN n"""
    verify = neo4j_graph.run(q)



def try_append_to_intersection_boost(closest_id, distance, intersectionBoost):
    if (distance < 20):
        if (len(intersectionBoost) == 0):
            intersectionBoost.append(closest_id)
        elif (len(intersectionBoost) == 1 and intersectionBoost[-1] != closest_id):
            intersectionBoost.append(closest_id)
        elif (len(intersectionBoost) > 1 and intersectionBoost[-1] != closest_id and intersectionBoost[-2] != closest_id):
            intersectionBoost.append(closest_id)


readFolder(gpxFolderList+tcxFolderList)