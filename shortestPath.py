# Import project folders
from graph_construction import trip_schedules
from graph_construction import graphs
from graph_construction import header as H
# Regular imports
from importlib import resources as impresources
import plotly.graph_objects as go
import heapq
import datetime
import pickle
import time
    
def openGraph():
    relative_path = (impresources.files(graphs) / "final_nodes.obj")
    with open(relative_path, "rb") as f:
        nodes = pickle.load(f)

    relative_path = (impresources.files(graphs) / "neigh_list.obj")
    with open(relative_path, "rb") as f:
        neigh_list = pickle.load(f)
    
    relative_path = (impresources.files(graphs) / "walk_node_amount.obj")
    with open(relative_path, "rb") as f:
        walk_node_amount = pickle.load(f)

    return nodes, neigh_list, walk_node_amount

def openTripSchedules():
    trip_to_service = []
    # relative_path = os.path.join("graph_construction", "trip_schedules", "trip_to_service.txt")
    relative_path = (impresources.files(trip_schedules) / "trip_to_service.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            ser_tid = line.strip()
            if ser_tid != "None":
                trip_to_service.append(int(ser_tid))
            else:
                trip_to_service.append(None)

    service_schedule = []
    relative_path = (impresources.files(trip_schedules) / "service_schedule.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            service_schedule.append([int(i) for i in line.split()])

    service_exception = []
    relative_path = (impresources.files(trip_schedules) / "service_exception.txt")
    with open(relative_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            service_exception.append([int(i) for i in line.split()])
    
    return trip_to_service, service_schedule, service_exception

def Dijkstra(nodes, nox, start, end, time, translator):
    trip_type = [[]] * len(nodes)
    depart = [[]] * len(nodes)
    previous = [-1] * len(nodes)
    distance = [1e9] * len(nodes)
    penalized_distance = [1e9] * len(nodes)

    distance[start] = time
    priority_queue = [(time, start, 0)]
    while priority_queue:
        cur_penalized_distance, node, transfer_amount = heapq.heappop(priority_queue)
        if node == end:
            return previous, distance, trip_type, depart
        for edge_set in nox[node]:
            depart_time, route_id = edge_set.getEdge(distance[node], translator)
            if depart_time != False:
                distance_to_neighbor = depart_time + edge_set.travel_time
                penalty = transfer_amount * H.transfer_penalty
                if route_id != -1:
                    penalty += H.transfer_penalty
                if distance_to_neighbor + penalty < distance[edge_set.goal]:
                    trip_type[edge_set.goal].append([route_id, edge_set.root, edge_set.goal])
                    depart[edge_set.root].append([depart_time, edge_set.root, edge_set.goal])
                    previous[edge_set.goal] = edge_set.root
                    distance[edge_set.goal] = distance_to_neighbor
                    penalized_distance[edge_set.goal] = distance_to_neighbor + penalty
                    if route_id != -1:
                        heapq.heappush(priority_queue, (penalized_distance[edge_set.goal], edge_set.goal, transfer_amount + 1))
                    else:
                        heapq.heappush(priority_queue, (penalized_distance[edge_set.goal], edge_set.goal, transfer_amount))
    return False

def chooseNodeColor(last_node_id, cur_node_id, walk_node_amount):
    if last_node_id < walk_node_amount and cur_node_id < walk_node_amount:
        color = "blue"
    elif last_node_id < walk_node_amount or cur_node_id < walk_node_amount:
        color = "green"
    else:
        color = "red"
    return color

def showPath(nodes, dist, res, trip_type, depart, goal, walk_node_amount):
    # Prepare the path for plotting
    path = [goal]
    while res[path[-1]] != -1:
        path.append(res[path[-1]])
    path.reverse()
    
    mapbox_access_token = "pk.eyJ1IjoiZGFuaWRlb3MiLCJhIjoiY2w5cTJxNnMxMDVhZjNwbDcxdng5cW84NyJ9.k2kz26pJ1gk4NSdc0N0HHQ"
    fig = go.Figure()
    
    def findDepartTime(root, goal, depart_list):
        for i in range(len(depart_list)):
            if depart_list[i][1] == root and depart_list[i][2] == goal:
                return datetime.timedelta(seconds=depart_list[i][0])
        return 0
    
    def findTripType(root, goal, trip_list):
        for i in range(len(trip_list)):
            if trip_list[i][1] == root and trip_list[i][2] == goal:
                return trip_list[i][0]
        return -1
            
    # Add the start node
    last_lon, last_lat = nodes[path[0]].lon, nodes[path[0]].lat
    color = chooseNodeColor(path[0], path[1], walk_node_amount)
    timestamp = datetime.timedelta(seconds=dist[path[0]])
    # route_id = trip_type[path[0]] if trip_type[path[0]] != -1 else "walk"
    route_id = findTripType(path[0], path[1], trip_type[0])
    depart_time = findDepartTime(path[0], path[1], depart[path[0]])
    fig.add_trace(go.Scattermapbox(
        mode='markers',
        opacity=1,
        lon=[last_lon],
        lat=[last_lat],
        text=f"Timestamp: {timestamp}, Route id: {route_id}, Depart time: {depart_time}",
        marker={'size': 16,
                'color': color}
    ))

    # Add the path nodes and edges
    for i in range(1, len(path)):
        lon, lat = nodes[path[i]].lon, nodes[path[i]].lat
        color = chooseNodeColor(path[i-1], path[i], walk_node_amount)
        timestamp = datetime.timedelta(seconds=dist[path[i - 1]])
        route_id = findTripType(path[i - 1], path[i], trip_type[i - 1])
        depart_time = findDepartTime(path[i - 1], path[i], depart[path[i - 1]])
        fig.add_trace(go.Scattermapbox(
            mode='markers+lines',
            opacity=1,
            lon=[last_lon, lon],
            lat=[last_lat, lat],
            text=f"Timestamp: {timestamp}, Route id: {route_id}, Depart time: {depart_time}",
            marker={'size': 8,
                    'color': color}
            
        ))
        last_lon, last_lat = nodes[path[i]].lon, nodes[path[i]].lat

    # Add the goal node
    timestamp = datetime.timedelta(seconds=dist[path[-1]])
    fig.add_trace(go.Scattermapbox(
        mode='markers',
        opacity=1,
        lon=[last_lon],
        lat=[last_lat],
        text=f"Timestamp: {timestamp}",
        marker={'size': 16,
                'color': color}
    ))
    
    fig.update_layout(
        autosize=True,
        hovermode='closest',
        margin=dict(l=75, r=75, t=25, b=25),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=last_lat,
                lon=last_lon
            ),
            pitch=0,
            zoom=15
        ),
    )
    fig.show()

    
if __name__ == "__main__":
    stime = time.time()
    date = 20230919
    start_time = 3600*15+4*60

    trip_to_service, service_schedule, service_exception = openTripSchedules()
    translator = H.Translator(trip_to_service, service_schedule, service_exception, date)
    print(f"Translator load length: {time.time() - stime:.3f} sec")
    
    stime = time.time()
    nodes, neigh_list, walk_node_amount = openGraph()
    print(f"Graph load length: {time.time() - stime:.3f} sec")

    stime = time.time()
    start = 150000
    goal = 0
    
    res, dists, trip_type, depart = Dijkstra(nodes, neigh_list, start, goal, start_time, translator)
    path = showPath(nodes, dists, res, trip_type, depart, goal, walk_node_amount)
    print(f"Algo length: {time.time() - stime:.3f} sec")
    print(f"Parametres: start_time={datetime.timedelta(seconds=start_time)}, date={datetime.datetime.strptime(str(date), '%Y%m%d').date()}, start node id={start}, goal node id={goal}")
    print(f"Travel time total: {datetime.timedelta(seconds=dists[goal] - start_time)}")

    