from database.models import Location, Road
from graph.graph import Graph
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm


class AStarRoutingAlgorithm(AbstractRoutingAlgorithm):
    def find_route(self, graph: Graph, from_: Location, to_: Location) -> list[Road]:
        pass

    # ToDo: implement Dijkstra first
