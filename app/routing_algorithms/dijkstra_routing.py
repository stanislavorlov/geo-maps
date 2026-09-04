import heapq
from graph.graph import Graph, Node, Edge
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult

DEFAULT_SPEED = 30.0  # mph

# For shortest distance:
# new_distance = distance + road.distance

# For fastest route:
# travel_time = road.distance / road.speed

# and Dijkstra minimizes:
# new_distance = distance + road.distance / road.speed

class DijkstraRoutingAlgorithm(AbstractRoutingAlgorithm):
    def __init__(self, default_speed: float = DEFAULT_SPEED):
        self.default_speed = default_speed

    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
        if start_node.id == target_node.id:
            return RouteResult(
                found=True,
                distance=0.0,
                time=0.0,
                path=[[start_node.lat, start_node.lon]],
                edges=[]
            )

        distances = {start_node.id: 0.0}
        previous: dict[int, tuple[int, Edge]] = {}
        min_heap = [(0.0, start_node.id)]

        while min_heap:
            current_dist, current_id = heapq.heappop(min_heap)

            if current_dist > distances.get(current_id, float("inf")):
                continue

            if current_id == target_node.id:
                break

            for edge in graph.adjacency.get(current_id, []):
                new_dist = current_dist + edge.distance

                if new_dist < distances.get(edge.to_id, float("inf")):
                    distances[edge.to_id] = new_dist
                    previous[edge.to_id] = (current_id, edge)
                    heapq.heappush(min_heap, (new_dist, edge.to_id))

        if target_node.id not in distances:
            return RouteResult(found=False)

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

        return RouteResult(
            found=True,
            distance=total_distance,
            time=total_time,
            path=coordinates,
            edges=edges_path
        )