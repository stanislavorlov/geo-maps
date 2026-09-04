from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from graph.graph import Graph, Node, Edge


@dataclass
class RouteResult:
    found: bool
    distance: float = 0.0  # in meters
    time: float = 0.0      # estimated travel time
    path: list[list[float]] = field(default_factory=list)  # [[lat, lon], ...]
    edges: list[Edge] = field(default_factory=list)


class AbstractRoutingAlgorithm(ABC):
    @abstractmethod
    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
        pass