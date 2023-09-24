# Import project folders
from graph_construction import getPidGraph, getWalkGraph, header as H, mergeGraphs
import getPidData

def tokenCheck():
    with open("mapbox_access_token.txt", "r", encoding="utf-8") as f:
        token = f.readline().strip()
        if token == "":
            raise ValueError("Mapbox token not provided")
        

if __name__ == "__main__":
    # Download necessary PID data 
    getPidData.downloadFile(H.url, H.save_path)
    getPidData.extractFromFile(H.save_path)

    # Check for mapbox access token 
    tokenCheck()

    # Construct PID graph from the PID data
    pid_nodes = getPidGraph.ExtractPidNodes()
    pid_edges = getPidGraph.ExtractPidEdges()

    # Fetch the walk graph data from OSMnx(Open Street Map)
    ox_graph = getWalkGraph.fetchOxGraph()

    # Extract nodes and edges from ox graph
    walk_nodes = getWalkGraph.extractOxNodes(ox_graph)
    walk_edges = getWalkGraph.extractOxEdges(ox_graph)

    # Translate trip ids to be consecutive
    cur_node_id, whatever, walk_edges = mergeGraphs.translateGraphIds(0, walk_nodes, walk_edges, 
                                                                      graph_name="walk graph")
    cur_node_id, trip_id_translation, pid_edges = mergeGraphs.translateGraphIds(cur_node_id, pid_nodes, pid_edges, 
                                                                                graph_name="pid graph")
    

    # Get transfer edges between PID and walk graph
    transfer_edges = mergeGraphs.getTransferEdges(walk_nodes, walk_edges, pid_nodes)

    # Extract trip schedules for looking up if trip id has operational service
    mergeGraphs.getTripSchedules(trip_id_translation)

    # Merge PID and walk graphs and save the final merged graph
    final_nodes, neigh_list = mergeGraphs.createMergedGraph(walk_nodes, walk_edges, pid_nodes, 
                                                               pid_edges, transfer_edges)
    mergeGraphs.saveMergedGraph(len(walk_nodes), final_nodes, neigh_list)


    