# Import project folders
from graph_construction import header as H
# Regular imports
from sklearn.neighbors import BallTree
import datetime
import shortestPath
import warnings
import numpy as np
import time as tm

def handleInput():
    with open("input.txt", "r", encoding="utf-8") as f:
        line = [str(i) for i in f.readline().split()]
        dest_count, date, time = handleFirstLine(line)
        places = []
        # Start node
        line = [str(i) for i in f.readline().split()]
        places.append([handleCoorLine(line), 0])
        for _ in range(dest_count - 2):
            # Inbetween nodes
            line = [str(i) for i in f.readline().split()]
            place = handleCoorLine(line)
            line = [str(i) for i in f.readline().split()]
            stay_time = handleStayTimeLine(line)
            places.append([place, stay_time])
        # End node
        line = [str(i) for i in f.readline().split()]
        places.append([handleCoorLine(line), 0])
    return places, date, time

def handleFirstLine(line):
    if len(line) != 3:
        raise ValueError("3 values should be on the first line")
    try:
        dest_count = int(line[0])
    except:
        raise ValueError("Incorrect destination_count format, should be an int")
    try:
        y, m, d = [str(i) for i in line[1].split(".")]
        date = int(y + m + d)
    except:
        raise ValueError("Incorrect date format, should be yyyy.mm.dd")
    try:
        time = H.timeToSec(line[2])
    except:
        raise ValueError("Incorrect time format, should be hh:mm:ss")
    return dest_count, date, time

def handleCoorLine(line):
    place = []
    if len(line) != 2:
        raise ValueError("2 values should be on the coordinate lines")
    for coor in line:
        try:
            a, b = [str(i) for i in coor.split(".")]
            if len(a) != 2 and len(b) != 7:
                raise ValueError("Incorrect latitude and longitude format, should be XX.XXXXXXX, YY.YYYYYYY")
            processed_coor = float(a + "." + b)
            place.append(processed_coor)
        except:
            raise ValueError("Incorrect latitude and longitude format, should be XX.XXXXXXX, YY.YYYYYYY")
    return place

def handleStayTimeLine(line):
    try:
        stay_time = H.timeToSec(line[0])
    except:
        raise ValueError("Incorrect stay_time format, should be hh:mm:ss")
    return stay_time

def findClosestNode(node, ball_tree):
    dists, indices = ball_tree.query([[np.deg2rad(node[0]), np.deg2rad(node[1])]], k=1)
    return indices[0][0]

def findPaths(places, date, time):
    stime = tm.time()
    trip_to_service, service_schedule, service_exception = shortestPath.openTripSchedules()
    translator = H.Translator(trip_to_service, service_schedule, service_exception, date)
    nodes, neigh_list, walk_node_amount = shortestPath.openGraph()
    print(f"Graph load length: {tm.time() - stime:.3f} sec")

    preprocessed_nodes = np.array([[x.lat, x.lon] for x in nodes])[:, :]
    ball_tree = BallTree(np.deg2rad(preprocessed_nodes), metric='haversine')
    start_time = time
    for i in range(len(places) - 1):
        stime = tm.time()
        start = findClosestNode(places[i][0], ball_tree)
        goal = findClosestNode(places[i + 1][0], ball_tree)
        if start == goal:
            warnings.warn(f"Destination {i} and {i + 1} are registered as the same node, skipping...")
        if i != 0:
            start_time = dist[goal] + places[i][1]
            if start_time >= 24*3600:
                warnings.warn("Inaccurate result warning, time passing midnight is not yet handled...")

        prev, dist, trip_type, depart = shortestPath.Dijkstra(nodes, neigh_list, start, goal, start_time, translator)
        if prev == False:
            raise ValueError("Something went wrong in the Dijkstra algo...")
        shortestPath.showPath(nodes, dist, prev, trip_type, depart, goal, walk_node_amount)
        print(f"Algo length: {tm.time() - stime:.3f} sec")
        print(f"Parametres: start_time={datetime.timedelta(seconds=start_time)}, date={datetime.datetime.strptime(str(date), '%Y%m%d').date()}, start node id={start}, goal node id={goal}")
        print(f"Travel time delta: {datetime.timedelta(seconds=dist[goal] - start_time)}")


if __name__ == "__main__":
    places, date, time = handleInput()
    findPaths(places, date, time)
    
    
    
    
        
        