import math
from dataclasses import dataclass, asdict
from typing import Optional
from scipy.spatial import cKDTree


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

        # Build KDTree for spatial indexing
        if nodes:
            self._node_list = list(nodes.values())
            mean_lat = sum(n.lat for n in self._node_list) / len(self._node_list)
            self._cos_lat = math.cos(math.radians(mean_lat))
            points = [[node.lat, node.lon * self._cos_lat] for node in self._node_list]
            self.kdTree: Optional[cKDTree] = cKDTree(points)
        else:
            self._node_list = []
            self._cos_lat = 1.0
            self.kdTree = None

    def find_nearest_node(self, lat: float, lng: float) -> Optional[Node]:
        """Find the closest Node to the given (lat, lng) coordinates using KDTree."""
        if not self.nodes or self.kdTree is None:
            return None

        scaled_lng = lng * self._cos_lat
        _, index = self.kdTree.query([lat, scaled_lng])

        return self._node_list[index]

    def data_stats(self) -> dict:
        return {
            "locations_count": len(self.nodes),
            "roads_count": len(self.edges),
        }
