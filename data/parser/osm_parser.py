import xml.etree.ElementTree as ET
import math
import re
from typing import Dict, List, Optional, Tuple
from app.graph.graph import Node, Edge, Graph
import time
from app.database.database import engine
from app.database.models import Road, Location
from sqlalchemy import insert
import asyncio
import argparse
import sys

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
    Parses map.osm or .pbf file and returns a dictionary of nodes and a list of edges.
    """
    nodes: Dict[int, Node] = {}
    edges: List[Edge] = []

    if file_path.endswith('.pbf'):
        import osmiter
        print("Using osmiter to parse PBF file...")
        # Since osmiter streams elements, and nodes are ordered before ways in PBF files,
        # we can build the node map and generate edges in a single pass.
        display_node = False
        display_edge = False
        for elem in osmiter.iter_from_osm(file_path):
            el_type = elem.get("type")
            if el_type == "node":
                node_id = elem["id"]
                tags = elem.get("tag", {})
                name = tags.get("name")
                description = tags.get("description")
                nodes[node_id] = Node(id=node_id, lat=elem["lat"], lon=elem["lon"], name=name, description=description)
                if not display_node:
                    display_node = True
                    print(elem)
            elif el_type == "way":
                if not display_edge:
                    display_edge = True
                    print(elem)
                tags = elem.get("tag", {})
                road_type = tags.get("highway")
                if not road_type:
                    continue
                nd_refs = elem.get("nd", [])
                if len(nd_refs) < 2:
                    continue
                speed = parse_speed(tags.get("maxspeed"))
                oneway = tags.get("oneway")
                
                is_oneway = oneway in ("yes", "1")
                is_reverse = oneway == "-1"
                
                for i in range(len(nd_refs) - 1):
                    u_id = nd_refs[i]
                    v_id = nd_refs[i+1]
                    
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
    else:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # 1. Parse all nodes
        for node_elem in root.findall("node"):
            node_id = int(node_elem.get("id"))
            lat = float(node_elem.get("lat"))
            lon = float(node_elem.get("lon"))
            
            tags = {tag.get("k"): tag.get("v") for tag in node_elem.findall("tag")}
            name = tags.get("name")
            description = tags.get("description")
            
            nodes[node_id] = Node(id=node_id, lat=lat, lon=lon, name=name, description=description)

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
    parser = argparse.ArgumentParser(description="OSM Parser to Database or JSON File")
    parser.add_argument(
        "--file", "-f",
        default="data/maps_osm_pbf/greater-london-latest.osm.pbf",
        help="Path to the OSM/PBF file"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["db", "file"],
        default="db",
        help="Storage mode: 'db' (PostgreSQL) or 'file' (JSON)"
    )
    parser.add_argument(
        "--output", "-o",
        default="graph.json",
        help="Output JSON file path (only used in 'file' mode)"
    )
    
    args = parser.parse_args()
    osm_file = args.file
    
    print(f"Parsing '{osm_file}'...")

    start_time = time.perf_counter()
    try:
        nodes, edges = parse_osm_to_graph(osm_file)
        end_time = time.perf_counter()
        execution_time = end_time - start_time

        print(f"Parsing complete in : {execution_time:.6f} seconds")
        print(f"Total Nodes: {len(nodes)}")
        print(f"Total Edges: {len(edges)}")
        
        # Show sample node and edge
        if nodes:
            sample_node_id = list(nodes.keys())[0]
            print(f"\nSample Node:\n  {nodes[sample_node_id].to_dict()}")
        if edges:
            print(f"\nSample Edge:\n  {edges[0].to_dict()}")

        if args.mode == "file":
            print(f"\nSaving graph to JSON file '{args.output}'...")
            start_save_time = time.perf_counter()
            graph = Graph(nodes=list(nodes.values()), edges=edges)
            graph.save_file(args.output)
            end_save_time = time.perf_counter()
            print(f"File save complete in : {end_save_time - start_save_time:.6f} seconds")
        else:
            async def insert_data(nodes: Dict[int, Node], edges: List[Edge]):
                print("\nStarting database insertion...")
                start_db_time = time.perf_counter()
                
                # We can insert nodes and edges in batches
                batch_size = 1000
                
                async with engine.begin() as conn:
                    # 1. Insert Nodes as Locations
                    print(f"Inserting {len(nodes)} nodes...")
                    node_list = list(nodes.values())
                    for i in range(0, len(node_list), batch_size):
                        batch = node_list[i:i+batch_size]
                        values = [{
                            'id': n.id,
                            'name': n.name,
                            'description': n.description,
                            'geom': f"SRID=4326;POINT({n.lon} {n.lat})"
                        } for n in batch]
                        
                        await conn.execute(insert(Location).values(values))
                        print(f"Inserted nodes batch {i // batch_size + 1}/{(len(node_list) + batch_size - 1) // batch_size} ({len(values)} nodes)")
                        
                    # 2. Insert Edges as Roads
                    print(f"\nInserting {len(edges)} edges...")
                    for i in range(0, len(edges), batch_size):
                        batch = edges[i:i+batch_size]
                        values = [{
                            'from_id': e.from_id,
                            'to_id': e.to_id,
                            'distance': e.distance,
                            'speed': e.speed,
                            'road_type': e.road_type
                        } for e in batch]
                        
                        await conn.execute(insert(Road).values(values))
                        print(f"Inserted edges batch {i // batch_size + 1}/{(len(edges) + batch_size - 1) // batch_size} ({len(values)} edges)")
                        
                end_db_time = time.perf_counter()
                print(f"Database insertion complete in : {end_db_time - start_db_time:.6f} seconds")

            # Run insertion asynchronously
            asyncio.run(insert_data(nodes, edges))

    except Exception as e:
        print(f"Error: {e}")
