from graph.graph import Graph, Node
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult


class AStarRoutingAlgorithm(AbstractRoutingAlgorithm):
    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
        # TODO: Implement A* routing algorithm
        raise NotImplementedError("A* routing is not implemented yet")
