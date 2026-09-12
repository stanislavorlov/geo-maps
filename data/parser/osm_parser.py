import sys
import os
import xml.etree.ElementTree as ET
import math
import re
import time
from typing import Dict, List, Optional, Tuple

# Ensure project root and app directory are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app")))

try:
    from graph.graph import Node, Edge, Graph
    from database.database import engine, Base
    from database.models import Road, Location
except ImportError:
    from app.graph.graph import Node, Edge, Graph
    from app.database.database import engine, Base
    from app.database.models import Road, Location

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
import asyncio
import argparse

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
                name = tags.get("name")
                speed = parse_speed(tags.get("maxspeed"))

                for i in range(len(nd_refs) - 1):
                    u_id = nd_refs[i]
                    v_id = nd_refs[i+1]

                    if u_id not in nodes or v_id not in nodes:
                        continue

                    node_u = nodes[u_id]
                    node_v = nodes[v_id]
                    dist = haversine_distance(node_u.lat, node_u.lon, node_v.lat, node_v.lon)

                    edges.append(Edge(
                        from_id=u_id,
                        to_id=v_id,
                        distance=dist,
                        speed=speed,
                        road_type=road_type,
                        name=name,
                        tags=tags,
                        is_reverse=False
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

            name = tags.get("name")
            speed = parse_speed(tags.get("maxspeed"))

            # Create base physical edge between consecutive nodes in the way
            for i in range(len(nd_refs) - 1):
                u_id = nd_refs[i]
                v_id = nd_refs[i+1]

                # Verify that both nodes exist in our parsed nodes list
                if u_id not in nodes or v_id not in nodes:
                    continue

                node_u = nodes[u_id]
                node_v = nodes[v_id]
                dist = haversine_distance(node_u.lat, node_u.lon, node_v.lat, node_v.lon)

                edges.append(Edge(
                    from_id=u_id,
                    to_id=v_id,
                    distance=dist,
                    speed=speed,
                    road_type=road_type,
                    name=name,
                    tags=tags,
                    is_reverse=False
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
            graph = Graph(nodes=nodes, edges=edges)
            graph.save_file(args.output)
            end_save_time = time.perf_counter()
            print(f"File save complete in : {end_save_time - start_save_time:.6f} seconds")
        else:
            async def insert_data(nodes: Dict[int, Node], edges: List[Edge]):
                print("\nStarting database upsert...")
                start_db_time = time.perf_counter()
                
                # We can insert nodes and edges in batches
                batch_size = 1000
                
                async with engine.begin() as conn:
                    # Ensure table schema exists
                    await conn.run_sync(Base.metadata.create_all)

                    # Migrate columns if roads table was created prior to name/tags schema update
                    await conn.execute(text("ALTER TABLE roads ADD COLUMN IF NOT EXISTS name VARCHAR;"))
                    await conn.execute(text("ALTER TABLE roads ADD COLUMN IF NOT EXISTS tags JSON;"))

                    # Clean up any legacy duplicate rows from older non-upsert runs before creating unique index
                    await conn.execute(text("""
                        DELETE FROM roads r1
                        USING roads r2
                        WHERE r1.id > r2.id
                          AND r1.from_id = r2.from_id
                          AND r1.to_id = r2.to_id
                          AND (r1.road_type = r2.road_type OR (r1.road_type IS NULL AND r2.road_type IS NULL));
                    """))

                    # Ensure unique index exists for upsert conflict targeting
                    await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_roads_from_to ON roads (from_id, to_id, road_type);"))

                    # 1. Upsert Nodes as Locations
                    print(f"Upserting {len(nodes)} nodes...")
                    node_list = list(nodes.values())
                    for i in range(0, len(node_list), batch_size):
                        batch = node_list[i:i+batch_size]
                        values = [{
                            'id': n.id,
                            'name': n.name,
                            'description': n.description,
                            'geom': f"SRID=4326;POINT({n.lon} {n.lat})"
                        } for n in batch]
                        
                        stmt = pg_insert(Location).values(values)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=[Location.id],
                            set_={
                                'name': stmt.excluded.name,
                                'description': stmt.excluded.description,
                                'geom': stmt.excluded.geom,
                            }
                        )
                        await conn.execute(stmt)
                        print(f"Upserted nodes batch {i // batch_size + 1}/{(len(node_list) + batch_size - 1) // batch_size} ({len(values)} nodes)")
                        
                    # 2. Upsert Edges as Roads
                    # Deduplicate edges by (from_id, to_id, road_type) to avoid intra-batch conflict collisions
                    unique_edges: dict[tuple[int, int, Optional[str]], Edge] = {}
                    for e in edges:
                        unique_edges[(e.from_id, e.to_id, e.road_type)] = e
                    edge_list = list(unique_edges.values())

                    print(f"\nUpserting {len(edge_list)} edges (deduplicated from {len(edges)})...")
                    for i in range(0, len(edge_list), batch_size):
                        batch = edge_list[i:i+batch_size]
                        values = [{
                            'from_id': e.from_id,
                            'to_id': e.to_id,
                            'distance': e.distance,
                            'speed': e.speed,
                            'road_type': e.road_type,
                            'name': e.name,
                            'tags': e.tags
                        } for e in batch]

                        stmt = pg_insert(Road).values(values)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=[Road.from_id, Road.to_id, Road.road_type],
                            set_={
                                'distance': stmt.excluded.distance,
                                'speed': stmt.excluded.speed,
                                'road_type': stmt.excluded.road_type,
                                'name': stmt.excluded.name,
                                'tags': stmt.excluded.tags,
                            }
                        )
                        await conn.execute(stmt)
                        print(f"Upserted edges batch {i // batch_size + 1}/{(len(edge_list) + batch_size - 1) // batch_size} ({len(values)} edges)")
                        
                end_db_time = time.perf_counter()
                print(f"Database upsert complete in : {end_db_time - start_db_time:.6f} seconds")

            # Run insertion asynchronously
            asyncio.run(insert_data(nodes, edges))

    except Exception as e:
        print(f"Error: {e}")
