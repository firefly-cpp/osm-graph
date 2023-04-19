# Description: Setup file for the project. It contains all the constants that are used in the project and the classes that are used to connect to the databases.

import py2neo
import pymongo
import redis


# Configure from here
OVERPASS_API_URL = "http://zabojnik.informatika.uni-mb.si:1101/api/interpreter"
OPEN_ELEVATION_API_URL = "http://zabojnik.informatika.uni-mb.si:8086/api/v1/lookup"
REDIS_DB_ADDRESS = "127.0.0.1"
REDIS_DB_PORT = 11001
REDIS_DB_PASSWORD = "intersectionPassword"

REDIS_DB_ADDRESSED_ADDRESS = "127.0.0.1"
REDIS_DB_ADDRESSED_PORT = 11002
REDIS_DB_ADDRESSED_PASSWORD = "processedIntersectionPassword"

NEO4J_DB_ADDRESS = "bolt://localhost:12002"
NEO4J_DB_USERNAME = "neo4j"
NEO4J_DB_PASSWORD = "graphPassword"

MONGO_DB_ADDRESS = "localhost"
MONGO_DB_PORT = 13001
MONGO_DB_USERNAME = "mongoPathwaysUser"
MONGO_DB_PASSWORD = "mongoPathwaysPassword"

MAXIMUM_LATITUDE = 46.6
MINIMUM_LATITUDE = 46.5
MAXIMUM_LONGITUDE = 15.7
MINIMUM_LONGITUDE = 15.6

# If you want to use mongo db, set MONGO_DB_OPTIONAL to True else set it to False
# If you don't use mongo db you don't need to configure MONGO_DB_ADDRESS, MONGO_DB_PORT, MONGO_DB_USERNAME, MONGO_DB_PASSWORD
MONGO_DB_OPTIONAL = True

# End of configuration, leave the rest of the file as it is

class MapParameters:
    def __init__(self, max_lat, min_lat, max_lon, min_lon):
        self.max_lat: float = max_lat
        self.min_lat: float = min_lat
        self.max_lon: float = max_lon
        self.min_lon: float = min_lon

    def __iter__(self):
        return iter((self.max_lat, self.min_lat, self.max_lon, self.min_lon))


class OverpassAPI:
    url = OVERPASS_API_URL

class OpenElevationAPI:
    url=OPEN_ELEVATION_API_URL

class GeoConnector():
    def __init__(self):
        self.__redis_db=False
        self.__redis_db_addressed=False
        self.__redis_db_pathways =False
        self.__redis_db_addressed_pathways=False

    def redis_db(self)->redis.client.Redis:
        if self.__redis_db == False:
            self.__redis_db = redis.Redis( host=REDIS_DB_ADDRESS, port=REDIS_DB_PORT,
                                           password=REDIS_DB_PASSWORD, retry_on_timeout=True
                                           )
        return self.__redis_db

    def redis_db_addressed(self)->redis.client.Redis:
        if self.__redis_db_addressed == False:
            self.__redis_db_addressed = redis.Redis(host=REDIS_DB_ADDRESSED_ADDRESS,
                                          port=REDIS_DB_ADDRESSED_PORT,
                                          retry_on_timeout=True,
                                          password=REDIS_DB_ADDRESSED_PASSWORD)
        return self.__redis_db_addressed
    def mongo_db(self, use=True):
        return pymongo.MongoClient(host=MONGO_DB_ADDRESS,
                                   port=MONGO_DB_PORT,
                                   username=MONGO_DB_USERNAME,
                                   password=MONGO_DB_PASSWORD)

    def neo4j_db(self)->py2neo.database.Graph:
        return py2neo.Graph(NEO4J_DB_ADDRESS, auth=(NEO4J_DB_USERNAME, NEO4J_DB_PASSWORD))


geo_connector = GeoConnector()

class MapBoundaries:
    def __init__(self, max_lat = MAXIMUM_LATITUDE, min_lat = MINIMUM_LATITUDE,
                 max_lon = MAXIMUM_LONGITUDE, min_lon=MINIMUM_LONGITUDE):
        ''' Tells the parser which area to parse '''
        self.max_lat=max_lat
        self.min_lat=min_lat
        self.max_lon=max_lon
        self.min_lon=min_lon

class DisallowedRoadConditions:
    highway = {'footway', 'cycleway', 'path', 'proposed', 'motorway', 'bridleway'}

