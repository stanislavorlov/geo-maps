from abc import ABC, abstractmethod
from database.models import Location, Road
from graph.graph import Graph


class AbstractRoutingAlgorithm(ABC):

    @abstractmethod
    def find_route(self, graph: Graph, from_: Location, to_: Location) -> list[Road]:
        pass