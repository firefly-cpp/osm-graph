# Concise instructions for use of Geo Map Processor for creating Two-Way Property Graph from OpenStreetMap and EU-DEM data

## Prerequisites
- Python 3.09>
- Self-hosted OpenElevation API instance ([instructions](https://open-elevation.com/#host-your-own)).
  - EU-DEM dataset ([download](https://land.copernicus.eu/imagery-in-situ/eu-dem/eu-dem-v1.1))
- Self-hosted Overpass API instance ([instructions](https://wiki.openstreetmap.org/wiki/Overpass_API/Installation))
  - OpenStreetMap bz2 files ([download](https://download.geofabrik.de/))
- 2 redis database instances (one for intersections, one for processed intersections)  ([download](https://redis.io/download))
- 1 neo4j database instance for storing the graph ([download](https://neo4j.com/download/))
- (optional) 1 MongoDB instance for storing the individual relationship nodes ([download](https://www.mongodb.com/download-center/community))

## Creating the property graph
1. Clone the repository
2. Install the dependencies with [poetry](https://python-poetry.org/) - poetry install
3. Install / prepare the requirements and prepare the necessary EU-DEM (OpenElevation) and OpenStreetMap (Overpass) data
4. Setup the configuration file (setup.py) with the necessary information, such as connection strings and map parameters
5. Run the python scripts in the example workflow in the following order:
    - A_intersection_db_parser.py -> creates the intersection nodes in the redis database
    - B_intersections_to_neo4j_graph.py -> creates the intersection nodes in the neo4j database
    - C_connections_to_graph.py -> creates the relationship nodes in the neo4j database
    - (optional) D_merge.py -> merges the relationship nodes in the neo4j database (optional)
You now have a working property graph.

### MongoDB
If you want to use MongoDB to also save individual nodes (their latitudes and longitudes) of each relationship / path within the graph you need to configure it in the setup.py file.
