# Regular imports
import math
import numpy as np
from importlib import resources as impresources
from plotly import graph_objects as go
import datetime

# Constants
radius = 6378 # Earth radius in km
walking_speed = 4.5 # Walking speed in kmph
place_name = "Prague"
k_precision = 10 # How many k-closest nodes to consider when creating transfer edges
url = "https://data.pid.cz/PID_GTFS.zip"
save_path = "PID_GTFS.zip"
min_transfer_time = 0
transfer_penalty = 160

# Classes
class Node:
    def __init__(self, node_id, lon, lat):
        self.id = node_id
        self.lon = lon
        self.lat = lat


class EdgeSet:
    def __init__(self, node1_id, node2_id, travel_time):
        self.edges = []
        self.root = node1_id
        self.goal = node2_id
        self.travel_time = travel_time

    def addEdge(self, depart_time, trip_tid, route_id):
        self.edges.append([depart_time, trip_tid, route_id])

    def sortEdges(self):
        self.edges.sort(key=lambda x: x[0])
    
    def getEdge(self, time, translator):
        # Returns departure time of the soonest departure with operational trip tid from the current time
        low = 0
        high = len(self.edges) - 1
        while high >= low:
            mid = low + (high - low) // 2
            if((mid == 0 or time > self.edges[mid - 1][0]) and (self.edges[mid][0] >= time or self.edges[mid][0] == -1)):
                for i in range(mid, len(self.edges)):
                    if translator.isEdgeOperational(self.edges[i][1], translator.date, time):
                        if self.edges[i][0] != -1:
                            """return self.edges[i][0], self.edges[i][2]"""
                            if time + min_transfer_time <= self.edges[i][0]:
                                return self.edges[i][0], self.edges[i][2]
                        else:
                            return time, -1
                return False, False
            elif(time > self.edges[mid][0]):
                low = mid + 1
            else:
                high = mid - 1
        return False, False


class Translator:
    def __init__(self, trip_to_service, service_schedule, service_exception, date):
        self.trip_to_service = trip_to_service
        self.service_schedule = service_schedule
        self.service_exception = service_exception
        self.date = date
        self.datetime_date = datetime.datetime(date//10000, (date//100)%100, date%100)
        self.day = self.datetime_date.weekday()

    def isEdgeOperational(self, trip_tid, date, time):
        if trip_tid == -1:
            return True
        ser_tid = self.trip_to_service[trip_tid]
        if (ser_tid != None and self.service_schedule[ser_tid][7] <= date 
                and self.service_schedule[ser_tid][8] >= date and self.service_schedule[ser_tid][self.day] == 1):
            return True
        return False    


# Helper functions
def haversineDistance(lat1, lat2, lon1, lon2):
    """
    Return Haversine distance of two geographical points in km
    """
    lon1 = math.radians(lon1)
    lon2 = math.radians(lon2)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return c * radius

def timeToSec(time):
    """
    Return integer time in seconds from time in hh:mm:ss
    """
    h, m, s = [int(i) for i in time.split(":")]
    return 3600 * h + m * 60 + s

def travelTime(depart_time, arrival_time):
    """
    Return integer travel time between two pid nodes in seconds
    """
    dtime = timeToSec(depart_time)
    atime = timeToSec(arrival_time)
    return atime - dtime

def getCartesian(lat=None,lon=None):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    x = radius * math.cos(lat) * math.cos(lon)
    y = radius * math.cos(lat) * math.sin(lon)
    z = radius * math.sin(lat)
    return [x,y,z]

def fromCartasian(A):
    lat = math.asin(A[2] / radius) * 180 / math.pi
    lon = math.atan2(A[1], A[0]) * 180 / math.pi
    return lat, lon

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
       return v
    return v / norm

def showTransferEdge(plat, plon, walk_nodes, te, te2):
    n1id, n2id = te[1], te2[1]
    lon1, lat1 = walk_nodes[n1id][1], walk_nodes[n1id][2]
    lon2, lat2 = walk_nodes[n2id][1], walk_nodes[n2id][2]
    mapbox_access_token = "pk.eyJ1IjoiZGFuaWRlb3MiLCJhIjoiY2w5cTJxNnMxMDVhZjNwbDcxdng5cW84NyJ9.k2kz26pJ1gk4NSdc0N0HHQ"
    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
                                mode='markers+lines',
                                opacity=1,
                                lon=[lon1, lon2],
                                lat=[lat1, lat2],
                               
                                marker={'size': 8,
                                        'color': "blue"}
                            ))
    fig.add_trace(go.Scattermapbox(
                                mode='markers',
                                opacity=1,
                                lon=[plon],
                                lat=[plat],
                               
                                marker={'size': 8,
                                        'color': "blue"}
                            )) 
        
    fig.update_layout(
        autosize=True,
        hovermode='closest',
        margin=dict(l=75, r=75, t=25, b=25),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=plat,
                lon=plon
            ),
            pitch=0,
            zoom=15
        )
    )
    fig.show()
