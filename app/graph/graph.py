import math
from dataclasses import dataclass, asdict
from typing import Optional


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
    speed: Optional[float] = None  # speed limit in mph/kph
    road_type: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "distance": round(self.distance, 2),
            "speed": self.speed,
            "road_type": self.road_type,
        }


class Graph:
    def __init__(self, nodes: dict[int, Node], edges: list[Edge]):
        self.nodes: dict[int, Node] = nodes
        self.edges: list[Edge] = edges

        # Pre-build adjacency list for fast O(1) neighbor lookups
        self.adjacency: dict[int, list[Edge]] = {node_id: [] for node_id in nodes}
        for edge in edges:
            if edge.from_id in self.adjacency:
                self.adjacency[edge.from_id].append(edge)

    def find_nearest_node(self, lat: float, lng: float) -> Optional[Node]:
        """Find the closest Node to the given (lat, lng) coordinates."""
        if not self.nodes:
            return None

        best_node: Optional[Node] = None
        best_dist = float("inf")
        lng_scale = math.cos(math.radians(lat))

        for node in self.nodes.values():
            d = (node.lat - lat) ** 2 + ((node.lon - lng) * lng_scale) ** 2
            if d < best_dist:
                best_dist = d
                best_node = node

        return best_node

    def data_stats(self) -> dict:
        return {
            "locations_count": len(self.nodes),
            "roads_count": len(self.edges),
        }
