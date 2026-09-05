import heapq
import time
from graph.graph import Graph, Node, Edge
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult

# For shortest distance:
# new_distance = distance + road.distance

# For fastest route:
# travel_time = road.distance / road.speed

# and Dijkstra minimizes:
# new_distance = distance + road.distance / road.speed


class DijkstraRoutingAlgorithm(AbstractRoutingAlgorithm):
    def __init__(self, speed: float = AbstractRoutingAlgorithm.DEFAULT_SPEED):
        super().__init__(speed)

    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
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

        distances = {start_node.id: 0.0}
        previous: dict[int, tuple[int, Edge]] = {}
        min_heap = [(0.0, start_node.id)]
        visited: set[int] = set()

        while min_heap:
            current_dist, current_id = heapq.heappop(min_heap)

            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id == target_node.id:
                break

            for edge in graph.adjacency.get(current_id, []):
                new_dist = current_dist + edge.distance

                if new_dist < distances.get(edge.to_id, float("inf")):
                    distances[edge.to_id] = new_dist
                    previous[edge.to_id] = (current_id, edge)
                    heapq.heappush(min_heap, (new_dist, edge.to_id))

        if target_node.id not in distances:
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
            speed = edge.speed if edge.speed else self.default_speed
            total_time += edge.distance / speed

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