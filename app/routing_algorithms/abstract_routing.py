from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from graph.graph import Graph, Node, Edge
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService


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

    def __init__(
            self,
            speed_limit_service: SpeedLimitService,
            travel_time_service: TravelTimeService,
            speed: float = DEFAULT_SPEED):
        self.default_speed = speed
        self.speed_limit_service = speed_limit_service
        self.travel_time_service = travel_time_service

    @abstractmethod
    def find_route(self, graph: Graph, start_node: Node, target_node: Node, travel_mode: str) -> RouteResult:
        pass