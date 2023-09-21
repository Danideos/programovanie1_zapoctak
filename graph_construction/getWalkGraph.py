# Import projext folders
from graph_construction import header as H
# Regular imports
import osmnx as ox

def fetchOxGraph():
    print("Fetching ox graph...", end=" ")
    ox_graph = ox.graph_from_place(H.place_name, network_type="walk")
    print("done.")
    return ox_graph

def extractOxNodes(ox_graph):
    print("Extracting walk nodes...", end=" ")
    graph_nodes = []
    for node_id in ox_graph.nodes:
        formatted_node = [
            node_id, ox_graph.nodes[node_id]["x"], ox_graph.nodes[node_id]["y"], "NA"
        ]
        graph_nodes.append(formatted_node)
    print("done.")
    return graph_nodes

def extractOxEdges(ox_graph):
    print("Extracting ox edges...", end=" ")
    graph_edges = []
    for edge in ox_graph.edges:
        node1_id, node2_id = edge[0], edge[1]
        distance = H.haversineDistance(ox_graph.nodes[node1_id]["y"], ox_graph.nodes[node2_id]["y"],
                                        ox_graph.nodes[node1_id]["x"], ox_graph.nodes[node2_id]["x"])
        travel_time = int(distance / H.walking_speed * 3600)
        formatted_edge = [
            node1_id, node2_id, -1, travel_time, -1
        ]
        # Found out that there are "useless" edges from the same node to the same node -> prevention
        if node1_id != node2_id: 
            graph_edges.append(formatted_edge)
    print("done.")
    return graph_edges

