# Programming documentation

## High level overview of preparation steps 

### `preparation.py`

Performs preparation steps neccessary for the project:

1. **Download GTFS Data:**
   - Download the latest GTFS (General Transit Feed Specification) data.
   - Extract relevant information from the GTFS data and store it in the `pid_data` folder.

2. **Extract PID Graph:**
   - Extract the PID graph from the `pid_data` folder.

3. **Fetch and Extract Walk Graph:**
   - Utilize OSMnx (OpenStreetMap) to fetch and extract the walk graph.

4. **Data Transformation:**
   - Translate node IDs in the graphs to make them indexable from 0.
   - Do the same for trip IDs belonging to PID edges.

5. **Find Transfer Edges:**
   - Find transfer edges between graphs by connecting each PID node to the nearest walk edge.

6. **Trip Schedule Extraction:**
   - Extract and save trip schedules, indicating whether a trip commences on a particular date.

7. **Merge graphs:**
   - Merge the PID and walk graphs into a final data structure.
   - This merged data structure will be used to efficiently find the shortest path for your application.

---

## Lower level overview of preparation steps

### `graph_construction/getPidGraph.py`
Extract the pid graph(as nodes and edges) from the `pid_data` folder. More specifically the nodes from `stops.txt` and the edges from `stop_times.txt`. Current graph representation:

Node format: `[ node_ID, node_longitude, node_latitude, node_name ]`

Edge format: `[ node1_ID, node2_ID, departure_time, travel_time,  trip_id ]` 

---

### graph_construction/getWalkGraph.py

Using OSMnx(OpenStreetMap) fetch the pedestrian graph data. Convert it to our above mentioned desired format - with the addition that `departure_time` and `trip_id` are not necessary for the walk edges so placeholder value -1 will be used instead. The travel time is calculated using Haversine distance.

---

### graph_construction/mergeGraphs.py

### translateGraphIds()

The walk nodes and pid nodes have a different `node_id` formats. All of them will be given new IDs sequentially from 0 to number of nodes for the ease of indexing a neighbor list in the `shortestPath.py`. IDs need to be changed across all the edges. The same for `trip_id`.

### getTransferEdges()

Find the nearest walk edge to each pid node. Add transfer edges to the pid node from both of its end points. Assumption: the nearest walk edge has at least one of its end points in the closest `k_precision` (default 10) walk nodes. Reason for the assumption: I couln't find a quick way to find the nearest edge other then calculating the minimal distance for every walk edge, which is too slow, even in C++.

__Definition of the nearest edge to a node:__ distance from the node to any part of the edge segment is minimized. (perpendicular distance to the edge if possible or the distance to one of the end points)

__Discussion about alternative approaches:__ I also considered just adding transfer edges to `k-closest` nodes or nodes in a radius around the node, but that would allow for passing through solid terrain in some cases. In real life scenario a pid stop is accesible from one walk edge only and the nearest walk edge as defined seems like a good enough aproximation. 

### getTripSchedules()

Each `trip_id` has a `service_id`, which corresponds to a schedule(whether a trip commences on a particular day in the week). Schedule has exceptions. Create a suitable data structure to access this information from `trips.txt`, `caledar.txt`, `calendar_dates.txt`. 

__TODO:__ `service_id` exceptions not handled yet

### createMergedGraph()

There are many pid edges, which start and end in the same pid nodes. To optimize create `edge_set`, which will be defined by the same start and end nodes. In the set the edges will be distinguished by: `departure_time` and `trip id`, they will be sorted by `departure_time` to allow binary search. 

Additionaly, create new edges, which will include every reachable station on a trip, e.g. create edge from node 1 to node 2,3,4... on a trip and from node 2 to 3,4,5... and so on.

### saveMergedGraph()
use `pickle` to `pickle.dump` the whole merged graph data structure for faster load time. Concretely the `nodes` and the `neighbour_list`.

---

### graphHeader.py

A simple encapsulation for commonly used functions to not clutter the main code.



---



# Finding the shortest path

## main.py

Responsible for taking user input, starting the shortestPath.py and plotting the found path. 

## shortestPath.py

Load the graph from graphs/merged_graph.txt as a neighbor list. Load the trip id operational timetable from calendars.txt and calendar_dates.txt to list(trip ids are index-able thanks to transformation in mergeGraphs.py).  



For the actual algorithm: A classic Dijkstra with a twist. When looking at neighbors of the current closest unvisited node, we must consider the whole edge set between the two nodes. For this there will be a simple function, which will return an edge from the set, which arrives at the end node first. This function will be logarithmic with regard to the set size(binary search on departure times that will be sorted in the set - assuming the travel times are the same). It will take current time (start time + dist) as a parameter and return edge with the closest bigger departure time, which has trip id that is currently operational(calendars.txt and calendar_dates.txt).
