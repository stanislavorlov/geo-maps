import json
import gzip
from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class Node:
    id: int
    lat: float
    lon: float
    name: Optional[str] = None
    description: Optional[str] = None

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

class Graph:
    def __init__(self, nodes: List[Node], edges: List[Edge]):
        # Normalize inputs to dataclass instances if they are dicts
        self.nodes = [Node(**n) if isinstance(n, dict) else n for n in nodes]
        self.edges = [
            Edge(from_id=e["from"], to_id=e["to"], distance=e["distance"], speed=e.get("speed"), road_type=e["road_type"])
            if isinstance(e, dict) else e
            for e in edges
        ]

        self.graph = {
            "nodes": self.nodes,
            "edges": self.edges
        }

    def save_file(self, filename: str):
        data = {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges]
        }
        if filename.endswith(".gz"):
            with gzip.open(filename, "wt", encoding="utf-8") as f:
                json.dump(data, f)
        else:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)

    def load_file(self, filename: str):
        if filename.endswith(".gz"):
            with gzip.open(filename, "rt", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with open(filename, "r") as f:
                data = json.load(f)
        self.nodes = [Node(**n) for n in data.get("nodes", [])]
        self.edges = [
            Edge(from_id=e["from"], to_id=e["to"], distance=e["distance"], speed=e.get("speed"), road_type=e["road_type"])
            for e in data.get("edges", [])
        ]
        self.graph = {
            "nodes": self.nodes,
            "edges": self.edges
        }