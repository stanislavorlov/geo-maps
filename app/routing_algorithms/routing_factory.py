from models.search_model import RouteRequest
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm
from routing_algorithms.bidirectional_dijkstra_routing import BidirectionalDijkstraRoutingAlgorithm
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm
from routing_algorithms.astar_routing import AStarRoutingAlgorithm
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService
from typing import Type

RoutingAlgorithmKey = tuple[str, bool]
RoutingAlgorithmClass = Type[AbstractRoutingAlgorithm]

class RoutingAlgorithmFactory:

    _algorithms: dict[
        RoutingAlgorithmKey,
        RoutingAlgorithmClass
    ] = {
        ("dijkstra", False): DijkstraRoutingAlgorithm,
        ("dijkstra", True): BidirectionalDijkstraRoutingAlgorithm,
        ("astar", False): AStarRoutingAlgorithm,
        # ("astar", True): BidirectionalAStarRoutingAlgorithm,
        # ("bellman_ford", False): BellmanFordRoutingAlgorithm,
    }

    @classmethod
    def create(
        cls,
        request: RouteRequest,
        speed_limit_service: SpeedLimitService,
        travel_time_service: TravelTimeService,
    ) -> AbstractRoutingAlgorithm:

        key = (request.routeType, request.bidirectional)

        algorithm_class = cls._algorithms.get(key)

        if algorithm_class is None:
            raise NotImplementedError(
                f"Routing algorithm '{request.routeType}' "
                f"with bidirectional={request.bidirectional} "
                f"is not supported"
            )

        return algorithm_class(
            speed_limit_service=speed_limit_service,
            travel_time_service=travel_time_service,
        )

def get_routing_algorithm(
    request: RouteRequest,
    speed_limit_service: SpeedLimitService,
    travel_time_service: TravelTimeService,
) -> AbstractRoutingAlgorithm:

    return RoutingAlgorithmFactory.create(
        request=request,
        speed_limit_service=speed_limit_service,
        travel_time_service=travel_time_service,
    )