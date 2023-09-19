# Import project folders
from graph_construction import header as H
import pid_data
# Regular imports
from importlib import resources as impresources

def ExtractPidNodes():
    print("Extracting pid nodes...", end=" ")
    graph_nodes = []
    relative_path = (impresources.files(pid_data) / "stops.txt")
    with open(relative_path, encoding="utf8") as f:
        f.readline() # Get rid of the first format line
        for line in f.readlines():
            """
            Node format: [ node ID, node longitude, node latitude ] 
            """
            formatted_node = [0, 0, 0] # Placeholder values
            node_field = ""
            in_quotes = False
            comma_count = 0
            # Parsing chars because of problems with "stop_name" (field 2) -> can be omitted or contain commas...
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    if comma_count == 0:
                        formatted_node[0] = str(node_field.strip())
                    elif comma_count == 3:
                        formatted_node[1] = float(node_field.strip())
                    elif comma_count == 2:
                        formatted_node[2] = float(node_field.strip())
                    elif comma_count > 3:
                        break
                    node_field = ""
                    comma_count += 1
                else:
                    node_field += char

            graph_nodes.append(formatted_node)
    print("done.")
    return graph_nodes

def ExtractPidEdges():
    print("Extracting pid edges...", end=" ")
    graph_edges = []
    relative_path = (impresources.files(pid_data) / "stop_times.txt")
    with open(relative_path, encoding="utf8") as f:
        f.readline() # Get rid of the first format line

        line_data = [i for i in f.readline().split(",")]
        last_trip_id = line_data[0]
        last_depart_time = line_data[2]
        last_node_id = line_data[3]
        for line in f.readlines():
            """
            Edge format: [ node1 ID, node2 ID, departure time, travel time, trip_id ] 
            """
            line_data = [i for i in line.split(",")]
            cur_trip_id = line_data[0]
            cur_arrival_time = line_data[1]
            cur_depart_time = line_data[2]
            cur_node_id = line_data[3]
            if last_trip_id == cur_trip_id:
                formatted_edge = [
                    last_node_id, cur_node_id, H.timeToSec(last_depart_time),
                    H.travelTime(last_depart_time, cur_arrival_time), cur_trip_id
                ]
                graph_edges.append(formatted_edge)
            last_trip_id = cur_trip_id
            last_depart_time = cur_depart_time
            last_node_id = cur_node_id
    print("done.")
    return graph_edges

    
    
    
