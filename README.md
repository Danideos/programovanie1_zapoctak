## preparation.py

Download latest pid GTFS data from "http://data.pid.cz/PID_GTFS.zip" with wget(need to pip install wget) and save relevant information to pid_data subfolder. Construct the graph, which will be used in shortestPath.py. 



# Graph construction

## getPidGraph.py

Extract pid graph from pid_data subfolder. More specifically the nodes from "stops.txt" and the edges from "stop_times.txt". Save in the graphs subfolder as "pid_graph.txt".

Node format: [ node ID, node longitude, node latitude ]

Edge format: [ node1 ID, node2 ID, departure time, travel time,  trip id ]



## getWalkGraph.py

Using OSMnx(OpenStreetMap) fetch the pedestrian graph data. Convert it to our desired format - with the addition that departure time and trip id are not necessary for walk edges so placeholder value -1 will be used instead. The travel time is calculated using Haversine distance of geographical points.  Save in the graphs subfolder as "walk_graph.txt"



## mergeGraphs.py

### translateGraphIds()

The walk nodes and pid nodes have a different node id formats. All of them will be given new ids sequentially from 0 to number of nodes for the ease of indexing a neighbor list in the shortestPath.py. Ids need to be changed across all the edges. The same for trip ids - We want to be able to quickly look up if the trip id is operational. Best done with list search by index.

### getTransferEdges()

Find the nearest walk edges to each pid node. Add transfer edges to the pid node from both of its end points. Assumption: the nearest walk edge has at least one of its end points in the closest "k_precision" (default 10) walk nodes. Reason for the assumption: I couln't find a quick way to find the nearest edge other then calculating the minimal distance for every walk edge, which is too slow, even in C++.

Definition of the nearest edge to a node: distance from the node to any part of the edge segment is minimized. (perpendicular distance to the edge if possible or the distance to one of the end points)

Discussion about alternative approaches: I also considered just adding transfer edges to k-closest nodes or nodes in a radius around the node, but that would allow for passing through solid terrain in some cases. In real life scenario a pid stop is accesible from one walk edge only and the nearest walk edge seems like a good enough aproximation. 

### getTripSchedules()

Each trip id has a service id. Service id corresponds to a schedule. Schedule has exceptions. Create a suitable data structure to access this information from trips.txt, caledar.txt, calendar_dates.txt. 

trip_id -> service_id == schedule -> exceptions

### createMergedGraph()

There are many pid edges, which start and end in the same pid nodes. To optimize create edge sets, which will be defined by the same start and end nodes. In the set they will be distinguished by: departure time, trip id(to know whether the trip commences on particular date). No new graph format needed - only put these edge sets together in the "merged_graph.txt". The actual sets will be created easily when loading graph in shortestPath.py.



## graphHeader.py

Just a simple encapsulation for commonly used functions to not clutter the main code... 



# Finding the shortest path

## main.py

Responsible for taking user input, starting the shortestPath.py and plotting the found path. 

## shortestPath.py

Load the graph from graphs/merged_graph.txt as a neighbor list. Load the trip id operational timetable from calendars.txt and calendar_dates.txt to list(trip ids are index-able thanks to transformation in mergeGraphs.py).  



For the actual algorithm: A classic Dijkstra with a twist. When looking at neighbors of the current closest unvisited node, we must consider the whole edge set between the two nodes. For this there will be a simple function, which will return an edge from the set, which arrives at the end node first. This function will be logarithmic with regard to the set size(binary search on departure times that will be sorted in the set - assuming the travel times are the same). It will take current time (start time + dist) as a parameter and return edge with the closest bigger departure time, which has trip id that is currently operational(calendars.txt and calendar_dates.txt).
