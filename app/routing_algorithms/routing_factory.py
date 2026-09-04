from models.search_model import RouteRequest
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm


def get_routing_algorithm(request: RouteRequest) -> AbstractRoutingAlgorithm:
    match request.routeType:
        case "dijkstra":
            return DijkstraRoutingAlgorithm()
        case "astar":
            pass
        case _:
            raise NotImplementedError