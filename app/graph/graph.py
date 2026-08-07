import json
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
        self.nodes = nodes
        self.edges = edges

        self.graph = {
            "nodes": nodes,
            "edges": edges
        }

    def save_file(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.graph, f, indent=4)

    def load_file(self, filename: str):
        with open(filename, "r") as f:
            self.graph = json.load(f)

test = Graph(
    nodes=[{'id': 108395, 'lat': 51.5230075, 'lon': -0.1022238}],
    edges=[{'from': 18691639, 'to': 18691141, 'distance': 24.68, 'speed': 20, 'road_type': 'residential'}]
)

test.save_file("test.json")
test.load_file("test.json")

print(test.graph)