import xml.etree.ElementTree as ET
import math
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

@dataclass
class Node:
    id: int
    lat: float
    lon: float

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Edge:
    from_id: int
    to_id: int
    distance: float  # in meters
    speed: Optional[int]  # speed limit in mph/kph as integer
    road_type: str

    def to_dict(self) -> dict:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "distance": round(self.distance, 2),
            "speed": self.speed,
            "road_type": self.road_type
        }

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth 
    surface in meters using the Haversine formula.
    """
    R = 6371000.0  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def parse_speed(speed_str: Optional[str]) -> Optional[int]:
    """
    Parses speed limits (e.g. '20 mph', '30', '50 km/h') to an integer.
    """
    if not speed_str:
        return None
    match = re.match(r'^(\d+)', speed_str.strip())
    if match:
        return int(match.group(1))
    return None

def parse_osm_to_graph(file_path: str) -> Tuple[Dict[int, Node], List[Edge]]:
    """
    Parses map.osm file and returns a dictionary of nodes and a list of edges.
    """
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()

    nodes: Dict[int, Node] = {}
    edges: List[Edge] = []

    # 1. Parse all nodes
    for node_elem in root.findall("node"):
        node_id = int(node_elem.get("id"))
        lat = float(node_elem.get("lat"))
        lon = float(node_elem.get("lon"))
        nodes[node_id] = Node(id=node_id, lat=lat, lon=lon)

    # 2. Parse all ways that represent roads (have a 'highway' tag)
    for way_elem in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way_elem.findall("tag")}
        
        # Check if this way is a highway (road)
        road_type = tags.get("highway")
        if not road_type:
            continue

        # Get node references
        nd_refs = [int(nd.get("ref")) for nd in way_elem.findall("nd")]
        if len(nd_refs) < 2:
            continue

        # Parse speed and oneway status
        speed = parse_speed(tags.get("maxspeed"))
        oneway = tags.get("oneway")

        # Determine directional connectivity
        # Default in OSM is bidirectional unless oneway is explicitly 'yes', '1', or '-1'
        is_oneway = oneway in ("yes", "1")
        is_reverse = oneway == "-1"

        # Create edges between consecutive nodes in the way
        for i in range(len(nd_refs) - 1):
            u_id = nd_refs[i]
            v_id = nd_refs[i+1]

            # Verify that both nodes exist in our parsed nodes list
            if u_id not in nodes or v_id not in nodes:
                continue

            node_u = nodes[u_id]
            node_v = nodes[v_id]
            dist = haversine_distance(node_u.lat, node_u.lon, node_v.lat, node_v.lon)

            if not is_reverse:
                edges.append(Edge(
                    from_id=u_id,
                    to_id=v_id,
                    distance=dist,
                    speed=speed,
                    road_type=road_type
                ))
            
            if not is_oneway:
                edges.append(Edge(
                    from_id=v_id,
                    to_id=u_id,
                    distance=dist,
                    speed=speed,
                    road_type=road_type
                ))

    return nodes, edges

if __name__ == "__main__":
    import sys
    osm_file = "map.osm" if len(sys.argv) < 2 else sys.argv[1]
    print(f"Parsing '{osm_file}'...")
    try:
        nodes, edges = parse_osm_to_graph(osm_file)
        print(f"Parsing complete!")
        print(f"Total Nodes: {len(nodes)}")
        print(f"Total Edges: {len(edges)}")
        
        # Show sample node and edge
        if nodes:
            sample_node_id = list(nodes.keys())[0]
            print(f"\nSample Node:\n  {nodes[sample_node_id].to_dict()}")
        if edges:
            print(f"\nSample Edge:\n  {edges[0].to_dict()}")
    except Exception as e:
        print(f"Error: {e}")
