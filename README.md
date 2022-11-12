# Neo4j graph dataset of cycling paths in Slovenia

Examples repository for the Neo4j graph dataset of cycling paths in Slovenia.

Data based on on: 
- A. Rajšp, M. Heričko, and I. Fister Jr., "Preprocessing of roads in OpenStreetMap based geographic data on a property graph," in Proceedings of the Central European Conference on Information and Intelligent Systems, 2921, pp. 193–199. Accessed: Jun. 27, 2022. [Online]. Available: http://archive.ceciis.foi.hr/app/public/conferences/2021/Proceedings/IS/IS3.pdf

Data available at: 
- A. Rajšp; I. Fister Jr., “Neo4j graph dataset of cycling paths in Slovenia”, Mendeley Data, V2, Accessed: Jun. 27, 2022. [Online]. Available: https://doi.org/10.17632/zkbfvsjr5f.1


## Examples
Prior to using the examples the **slovenia-graph-neo4j.dump** should be imported in a locally hosted [Neo4j](https://neo4j.com/) instance and **pathways.json** should be imported in a local [MongoDB](https://www.mongodb.com/) instance.
- export_graph.py -> Shows how to export the database in a binary file
- shortest_route_a_b.py -> Shows how to import the binary file in a [igraph](https://igraph.org/) network analysis package and generate a sample route.

## License

This package is distributed under the MIT License. This license can be found online at <http://www.opensource.org/licenses/MIT>.

## Disclaimer

This framework is provided as-is, and there are no guarantees that it fits your purposes or that it is bug-free. Use it at your own risk!
