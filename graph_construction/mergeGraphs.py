# Import project folders
from graph_construction import header as H
from graph_construction import trip_schedules
from graph_construction import graphs
import pid_data
# Regular imports
from importlib import resources as impresources
from sklearn.neighbors import BallTree
import numpy as np
import math
import pickle

def translateGraphIds(cur_node_id, graph_nodes, graph_edges, graph_name):
    print(f"Translating {graph_name} ids...", end=" ")
    node_id_translation = {}
    for i in range(len(graph_nodes)):
        node_id_translation[graph_nodes[i][0]] = cur_node_id
        graph_nodes[i][0] = cur_node_id
        cur_node_id += 1
    
    # Get route ids for each edge
    route_id_translation = {}
    relative_path = (impresources.files(pid_data) / "trips.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            line = [str(i) for i in line.split(",")]
            route_id, trip_id = line[0], line[2]
            if trip_id not in route_id_translation:
                route_id_translation[trip_id] = route_id
    for i in range(len(graph_edges)):
        if graph_edges[i][4] != -1:
            graph_edges[i].append(route_id_translation[graph_edges[i][4]])
        else:
            graph_edges[i].append(-1)

    # Translate trip ids to translated trip ids (trip_tid)
    trip_id_translation = {}
    trip_id_count = 0
    for i in range(len(graph_edges)):
        graph_edges[i][0] = node_id_translation[graph_edges[i][0]]
        graph_edges[i][1] = node_id_translation[graph_edges[i][1]]
        if graph_edges[i][4] != -1:
            if graph_edges[i][4] in trip_id_translation:
                graph_edges[i][4] = trip_id_translation[graph_edges[i][4]] 
            else:
                trip_id_translation[graph_edges[i][4]] = trip_id_count
                graph_edges[i][4] = trip_id_count
                trip_id_count += 1
    print("done.")
    return cur_node_id, trip_id_translation, graph_edges

def getEdgeDist(C_lon, C_lat, A_lon, A_lat, B_lon, B_lat):
    """
    Return distance of point C from edge AB
    """
    A = H.getCartesian(A_lat, A_lon)
    B = H.getCartesian(B_lat, B_lon)
    C = H.getCartesian(C_lat, C_lon)

    G = np.cross(A, B)
    F = np.cross(C, G)
    T = np.cross(G, F)
    T = H.normalize(T) * H.radius
    T_lat, T_lon = H.fromCartasian(T)

    AT = H.haversineDistance(A_lat, T_lat, A_lon, T_lon)
    BT = H.haversineDistance(B_lat, T_lat, B_lon, T_lon)
    AB = H.haversineDistance(A_lat, B_lat, A_lon, B_lon)

    if abs(AB - AT - BT) < 0.00001:
        return H.haversineDistance(T_lat, C_lat, T_lon, C_lon)
    else:
        return min(H.haversineDistance(B_lat, C_lat, B_lon, C_lon),
                   H.haversineDistance(A_lat, C_lat, A_lon, C_lon))
    
def findNearestEdge(walk_nodes, walk_node_nblist, indices, pid_node_id, pid_node_lon, pid_node_lat):
    """
    Check all the walk edges, which have at least one common node with the k-closest nodes. Find the walk edge with 
    the minimal distance from current point, add edges from both its end points to the node.
    """
    min_node1_id = -1
    min_node2_id = -1
    min_dist = math.inf
    for j in range(H.k_precision):
        node1_id = indices[0][j]
        node1_lon, node1_lat = walk_nodes[node1_id][1], walk_nodes[node1_id][2]
        for k in range(len(walk_node_nblist[node1_id])):
            node2_id = walk_node_nblist[node1_id][k]
            node2_lon, node2_lat = walk_nodes[node2_id][1], walk_nodes[node2_id][2]
            dist = getEdgeDist(pid_node_lon, pid_node_lat, node1_lon, node1_lat, node2_lon, node2_lat)

            if dist < min_dist:
                min_node1_id, min_node2_id, min_dist = node1_id, node2_id, dist

    dist1 = H.haversineDistance(pid_node_lat, walk_nodes[min_node1_id][2],  pid_node_lon, walk_nodes[min_node1_id][1]) 
    travel_time1 = int(dist1 / H.walking_speed * 3600)
    transfer_edge1 = [pid_node_id, min_node1_id, -1, travel_time1, -1, -1]

    dist2 = H.haversineDistance(pid_node_lat, walk_nodes[min_node2_id][2], pid_node_lon, walk_nodes[min_node2_id][1])
    travel_time2 = int(dist2 / H.walking_speed * 3600)
    transfer_edge2 = [pid_node_id, min_node2_id, -1, travel_time2, -1, -1]
        
    return transfer_edge1, transfer_edge2

def getTransferEdges(walk_nodes, walk_edges, pid_nodes):
    print("Getting transfer edges between pid and walk graphs...", end=" ")
    transfer_edges = []
    # Prepare BallTree data structure for querying k-closest points according to haversine distance
    preprocessed_walk_nodes = np.array([[x[2], x[1]] for x in walk_nodes])[:, :]
    ball_tree = BallTree(np.deg2rad(preprocessed_walk_nodes), metric='haversine')

    # Create neighbor list for walk nodes
    walk_node_nblist = [[] for i in range(len(walk_nodes))]
    for i in range(len(walk_edges)):
        node1_id, node2_id = walk_edges[i][0], walk_edges[i][1]
        walk_node_nblist[node1_id].append(node2_id)
        walk_node_nblist[node2_id].append(node1_id)
   
    # For each pid node, query k-closest walk nodes
    for i in range(len(pid_nodes)):
        pid_node_id, pid_node_lon, pid_node_lat = pid_nodes[i][0], pid_nodes[i][1], pid_nodes[i][2]
        array = [[np.deg2rad(pid_node_lat), np.deg2rad(pid_node_lon)]]
        dists, indices = ball_tree.query(array, k=H.k_precision)
        transfer_edge1, transfer_edge2 = findNearestEdge(walk_nodes, walk_node_nblist, indices, 
                                                         pid_node_id, pid_node_lon, pid_node_lat)

        transfer_edges.append(transfer_edge1)
        # Switch root/goal because of directed edges...
        node1_id, node2_id, depart_time, travel_time, trip_tid, route_id = transfer_edge1
        transfer_edge1 = [node2_id, node1_id, depart_time, travel_time, trip_tid, route_id]
        transfer_edges.append(transfer_edge1)

        transfer_edges.append(transfer_edge2)
        node1_id, node2_id, depart_time, travel_time, trip_tid, route_id = transfer_edge2
        transfer_edge2 = [node2_id, node1_id, depart_time, travel_time, trip_tid, route_id]
        transfer_edges.append(transfer_edge2)
    print("done.")
    return transfer_edges
    
def getTripSchedules(trip_id_translation):
    print("Translating and saving trip id schedules...", end=" ")
    # Translate service ids to range from 0 for indexing. Assign each trip id a service id. 
    service_id_translation = {}
    cur_ser_id = 0

    trip_to_service = [None for i in range(len(trip_id_translation))]
    relative_path = (impresources.files(pid_data) / "trips.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            line = [str(i) for i in line.split(",")]
            ser_id, trip_id = line[1], line[2]
            if trip_id in trip_id_translation:
                trans_trip_id = trip_id_translation[trip_id]
                if ser_id in service_id_translation:
                    trip_to_service[trans_trip_id] = service_id_translation[ser_id]
                else:
                    trip_to_service[trans_trip_id] = cur_ser_id
                    service_id_translation[ser_id] = cur_ser_id
                    cur_ser_id += 1
    
    # Assign schedules to service ids. 
    relative_path = (impresources.files(pid_data) / "calendar.txt")
    service_schedule = [[-1 for i in range(9)] for j in range(len(service_id_translation))]
    with open(relative_path, "r", encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            line = [str(i) for i in line.split(",")]
            ser_id, start_date, end_date = line[0], line[8], line[9].strip()
            if ser_id in service_id_translation:
                trans_ser_id = service_id_translation[ser_id]
                for i in range(7):
                    service_schedule[trans_ser_id][i] = 1 if line[i + 1] == "1" else 0
                service_schedule[trans_ser_id][7] = start_date
                service_schedule[trans_ser_id][8] = end_date

    # Create service exceptions
    service_exception = [[None, None] for i in range(len(service_id_translation))]
    relative_path = (impresources.files(pid_data) / "calendar_dates.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            line = [str(i) for i in line.split(",")]
            if line[0] in service_id_translation:
                trans_ser_id = service_id_translation[line[0]]
                service_exception[trans_ser_id] = [line[1], line[2].strip()]

    # Save trip_to_service, service_schedule, service_exception
    relative_path = (impresources.files(trip_schedules) / "trip_to_service.txt")
    with open(relative_path, "w", encoding="utf-8") as f:
        text = ""
        for service in trip_to_service:
            text += str(service) + "\n"
        f.write(text)

    relative_path = (impresources.files(trip_schedules) / "service_schedule.txt")
    with open(relative_path, "w", encoding="utf-8") as f:
        text = ""
        for i in service_schedule:
            text += " ".join(map(str, i)) + "\n"
        f.write(text)
    
    relative_path = (impresources.files(trip_schedules) / "service_exception.txt")
    with open(relative_path, "w", encoding="utf-8") as f:
        text = ""
        for i in service_exception:
            if i[0] != None:
                text += " ".join(map(str, i)) + "\n"
            else:
                text += "-1" + "\n"
        f.write(text)
    print("done.")
    
def createMergedGraph(walk_nodes, walk_edges, pid_nodes, pid_edges, transfer_edges):
    print("Creating merged graph...", end=" ")
    merged_nodes = walk_nodes + pid_nodes

    # Create final node representation
    final_nodes = []
    for i in range(len(merged_nodes)):
        node_id, node_lon, node_lat, node_name = merged_nodes[i]
        node = H.Node(node_id, node_lon, node_lat, node_name)
        final_nodes.append(node)

    # Create final neighbor list representation with edge sets. 
    # For each pid trip create edge for each reachable node.

    # Walk edge sets
    neigh_list = [[] for i in range(len(merged_nodes))]
    edge_set_amount = len(walk_edges)
    for walk_edge in walk_edges:
        root, goal, depart_time, travel_time, trip_tid, route_id = walk_edge
        edge_set = H.EdgeSet(root, goal, travel_time)
        edge_set.addEdge(-1, -1, -1)
        neigh_list[root].append(edge_set)
    
    # Transfer edge sets
    edge_set_amount += len(transfer_edges)
    for transfer_edge in transfer_edges:
        root, goal, depart_time, travel_time, trip_tid, route_id = transfer_edge
        edge_set = H.EdgeSet(root, goal, travel_time)
        edge_set.addEdge(-1, -1, -1)
        neigh_list[root].append(edge_set)
    
    # Pid edge sets
    neigh_list_dict = [{} for i in range(len(merged_nodes))]
    pid_edges.sort(key=lambda x: x[2]) 
    pid_edges.sort(key=lambda x: x[4]) # this way we have all edges on a trip sequentially according to depart time
    last_tid = -1
    tid_amount = 0
    for i in range(len(pid_edges)):
        trip_tid = pid_edges[i][4]
        if trip_tid != last_tid:
            for j in range(i - tid_amount, i):
                for k in range(j, i):
                    root = pid_edges[j][0]
                    goal = pid_edges[k][1]
                    travel_time = pid_edges[k][2] - pid_edges[j][2] + pid_edges[k][3]
                    if goal not in neigh_list_dict[root]:
                        neigh_list_dict[root][goal] = {}
                    if travel_time not in neigh_list_dict[root][goal]:
                        neigh_list_dict[root][goal][travel_time] = H.EdgeSet(root, goal, travel_time)
                    neigh_list_dict[root][goal][travel_time].addEdge(pid_edges[j][2], pid_edges[j][4], pid_edges[j][5])
            tid_amount = 0
        last_tid = trip_tid
        tid_amount += 1

    # Add edge sets from neigh dict list to neigh list
    for root in range(len(merged_nodes)):
        for goal in neigh_list_dict[root]:
            for travel_time in neigh_list_dict[root][goal]:
                neigh_list_dict[root][goal][travel_time].sortEdges()
                edge_set = neigh_list_dict[root][goal][travel_time]
                neigh_list[root].append(edge_set)
                edge_set_amount += 1

    print("done.")
    return final_nodes, neigh_list

def saveMergedGraph(walk_node_amount, final_nodes, neigh_list):
    print("Saving merged graph...", end=" ")

    relative_path = (impresources.files(graphs) / "final_nodes.obj")
    with open(relative_path, "wb") as f:
        pickle.dump(final_nodes, f)

    relative_path = (impresources.files(graphs) / "neigh_list.obj")
    with open(relative_path, "wb") as f:
        pickle.dump(neigh_list, f)
    
    relative_path = (impresources.files(graphs) / "walk_node_amount.obj")
    with open(relative_path, "wb") as f:
        pickle.dump(walk_node_amount, f)
    
    print("done.")
    


    

    

