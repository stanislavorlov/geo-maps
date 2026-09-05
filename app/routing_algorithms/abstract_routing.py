from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from graph.graph import Graph, Node, Edge


@dataclass
class RouteResult:
    found: bool
    distance: float = 0.0
    """distance in meters"""
    time: float = 0.0
    """estimated travel time in minutes"""
    path: list[list[float]] = field(default_factory=list)  # [[lat, lon], ...]
    edges: list[Edge] = field(default_factory=list)
    nodes_visited_count: int = 0
    execution_time: float = 0.0


class AbstractRoutingAlgorithm(ABC):
    """default spped in mph"""
    DEFAULT_SPEED = 30.0

    def __init__(self, speed: float = DEFAULT_SPEED):
        self.default_speed = speed

    @abstractmethod
    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
        pass