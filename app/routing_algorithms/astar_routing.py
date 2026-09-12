import math
import heapq
import time
from graph.graph import Graph, Node, Edge
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance(node1: Node, node2: Node) -> float:
    """Calculate the great-circle distance between two nodes in meters (admissible heuristic)."""
    lat1, lon1 = math.radians(node1.lat), math.radians(node1.lon)
    lat2, lon2 = math.radians(node2.lat), math.radians(node2.lon)
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = math.sin(d_lat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


class AStarRoutingAlgorithm(AbstractRoutingAlgorithm):
    def __init__(
            self,
            speed_limit_service: SpeedLimitService,
            travel_time_service: TravelTimeService,
            speed: float = AbstractRoutingAlgorithm.DEFAULT_SPEED):
        super().__init__(speed_limit_service=speed_limit_service, travel_time_service=travel_time_service, speed=speed)

    def find_route(self, graph: Graph, start_node: Node, target_node: Node, travel_mode: str) -> RouteResult:
        if start_node.id == target_node.id:
            return RouteResult(
                found=True,
                distance=0.0,
                time=0.0,
                path=[[start_node.lat, start_node.lon]],
                edges=[],
                nodes_visited_count=0,
                execution_time=0.0,
            )

        start_time = time.perf_counter()

        # Priority queue stores (f_score, node_id)
        queue: list[tuple[float, int]] = [(0.0, start_node.id)]
        previous: dict[int, tuple[int, Edge]] = {}
        g_score: dict[int, float] = {start_node.id: 0.0}
        visited: set[int] = set()

        while queue:
            current_f, current_id = heapq.heappop(queue)

            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id == target_node.id:
                break

            current_g = g_score.get(current_id, float("inf"))

            for edge in graph.adjacency.get(current_id, []):
                speed = self.speed_limit_service.get_effective_speed(edge.road_type, travel_mode, edge.speed, edge.tags, edge.is_reverse)
                if speed is None:
                    continue  # Inaccessible edge for this travel mode

                tentative_g = current_g + edge.distance

                if tentative_g < g_score.get(edge.to_id, float("inf")):
                    g_score[edge.to_id] = tentative_g
                    previous[edge.to_id] = (current_id, edge)
                    to_node = graph.nodes[edge.to_id]
                    h = haversine_distance(to_node, target_node)
                    f = tentative_g + h
                    heapq.heappush(queue, (f, edge.to_id))

        if target_node.id not in g_score or (target_node.id not in previous and start_node.id != target_node.id):
            end_time = time.perf_counter()
            return RouteResult(
                found=False,
                nodes_visited_count=len(visited),
                execution_time=end_time - start_time
            )

        # Backtrack path
        edges_path: list[Edge] = []
        curr_id = target_node.id
        while curr_id != start_node.id:
            prev_id, edge = previous[curr_id]
            edges_path.append(edge)
            curr_id = prev_id

        edges_path.reverse()

        # Build output coordinates and metrics
        coordinates: list[list[float]] = [[start_node.lat, start_node.lon]]
        total_distance = 0.0
        total_time = 0.0

        for edge in edges_path:
            to_node = graph.nodes[edge.to_id]
            coordinates.append([to_node.lat, to_node.lon])
            total_distance += edge.distance
            speed_mph = self.speed_limit_service.get_effective_speed(edge.road_type, travel_mode, edge.speed, edge.tags, edge.is_reverse) or self.default_speed
            total_time += self.travel_time_service.calculate_travel_time(edge.distance, speed_mph)

        end_time = time.perf_counter()

        return RouteResult(
            found=True,
            distance=total_distance,
            time=total_time,
            path=coordinates,
            edges=edges_path,
            nodes_visited_count=len(visited),
            execution_time=end_time - start_time
        )
