import asyncio
import heapq
import time
from typing import Optional, Any
from graph.graph import Graph, Node, Edge
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult
from services.speed_limit_service import SpeedLimitService
from services.travel_time_service import TravelTimeService


class BidirectionalDijkstraRoutingAlgorithm(AbstractRoutingAlgorithm):
    def __init__(self,
                 speed_limit_service: SpeedLimitService,
                 travel_time_service: TravelTimeService,
                 speed: float = AbstractRoutingAlgorithm.DEFAULT_SPEED) -> None:
        super().__init__(speed_limit_service=speed_limit_service, travel_time_service=travel_time_service, speed=speed)

    async def find_route(
            self,
            graph: Graph,
            start_node: Node,
            target_node: Node,
            travel_mode: str,
            websocket: Optional[Any] = None) -> RouteResult:
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

        # Build incoming adjacency list for reverse graph traversal (target -> start)
        incoming_adjacency: dict[int, list[Edge]] = {node_id: [] for node_id in graph.nodes}
        for edge in graph.edges:
            if edge.to_id in incoming_adjacency:
                incoming_adjacency[edge.to_id].append(edge)

        # Forward search structures
        distances_forward: dict[int, float] = {start_node.id: 0.0}
        previous_forward: dict[int, tuple[int, Edge]] = {}  # to_node_id -> (from_node_id, edge)
        heap_forward: list[tuple[float, int]] = [(0.0, start_node.id)]
        visited_forward: set[int] = set()

        # Backward search structures
        distances_backward: dict[int, float] = {target_node.id: 0.0}
        previous_backward: dict[int, tuple[int, Edge]] = {}  # from_node_id -> (to_node_id, edge)
        heap_backward: list[tuple[float, int]] = [(0.0, target_node.id)]
        visited_backward: set[int] = set()

        # Shortest connection found so far
        mu = float('inf')
        best_intersection_node: Optional[int] = None

        while heap_forward and heap_backward:
            # Termination condition: when the sum of min distances in both heaps meets or exceeds the shortest path
            if heap_forward[0][0] + heap_backward[0][0] >= mu:
                break

            # Step 1: Forward search step
            forward_dist, forward_id = heapq.heappop(heap_forward)
            if forward_id not in visited_forward:
                visited_forward.add(forward_id)

                if websocket is not None:
                    forward_node = graph.nodes.get(forward_id)
                    if forward_node is not None:
                        edge_coordinates = None
                        if forward_id in previous_forward:
                            prev_id, _ = previous_forward[forward_id]
                            prev_node = graph.nodes.get(prev_id)
                            if prev_node is not None:
                                edge_coordinates = [[prev_node.lat, prev_node.lon], [forward_node.lat, forward_node.lon]]
                        try:
                            await websocket.send_json({
                                "type": "progress",
                                "node": [forward_node.lat, forward_node.lon],
                                "edge": edge_coordinates,
                                "nodes_visited_count": len(visited_forward) + len(visited_backward),
                                "current_distance": forward_dist,
                            })
                            await asyncio.sleep(0.001)
                        except Exception:
                            pass

                for edge in graph.adjacency.get(forward_id, []):
                    speed = self.speed_limit_service.get_effective_speed(
                        edge.road_type,
                        travel_mode,
                        edge.speed,
                        edge.tags,
                        edge.is_reverse
                    )
                    if speed is None:
                        continue  # Inaccessible edge for this travel mode

                    new_dist = forward_dist + edge.distance

                    if new_dist < distances_forward.get(edge.to_id, float("inf")):
                        distances_forward[edge.to_id] = new_dist
                        previous_forward[edge.to_id] = (forward_id, edge)
                        heapq.heappush(heap_forward, (new_dist, edge.to_id))

                    if edge.to_id in distances_backward:
                        total_dist = new_dist + distances_backward[edge.to_id]
                        if total_dist < mu:
                            mu = total_dist
                            best_intersection_node = edge.to_id

            # Step 2: Backward search step
            backward_dist, backward_id = heapq.heappop(heap_backward)
            if backward_id not in visited_backward:
                visited_backward.add(backward_id)

                if websocket is not None:
                    backward_node = graph.nodes.get(backward_id)
                    if backward_node is not None:
                        edge_coordinates = None
                        if backward_id in previous_backward:
                            next_id, _ = previous_backward[backward_id]
                            next_node = graph.nodes.get(next_id)
                            if next_node is not None:
                                edge_coordinates = [[backward_node.lat, backward_node.lon], [next_node.lat, next_node.lon]]
                        try:
                            await websocket.send_json({
                                "type": "progress",
                                "node": [backward_node.lat, backward_node.lon],
                                "edge": edge_coordinates,
                                "nodes_visited_count": len(visited_forward) + len(visited_backward),
                                "current_distance": backward_dist,
                            })
                            await asyncio.sleep(0.001)
                        except Exception:
                            pass

                for edge in incoming_adjacency.get(backward_id, []):
                    speed = self.speed_limit_service.get_effective_speed(
                        edge.road_type,
                        travel_mode,
                        edge.speed,
                        edge.tags,
                        edge.is_reverse
                    )
                    if speed is None:
                        continue  # Inaccessible edge for this travel mode

                    new_dist = backward_dist + edge.distance

                    if new_dist < distances_backward.get(edge.from_id, float("inf")):
                        distances_backward[edge.from_id] = new_dist
                        previous_backward[edge.from_id] = (backward_id, edge)
                        heapq.heappush(heap_backward, (new_dist, edge.from_id))

                    if edge.from_id in distances_forward:
                        total_dist = distances_forward[edge.from_id] + new_dist
                        if total_dist < mu:
                            mu = total_dist
                            best_intersection_node = edge.from_id

        if best_intersection_node is None or mu == float('inf'):
            end_time = time.perf_counter()
            return RouteResult(
                found=False,
                nodes_visited_count=len(visited_forward) + len(visited_backward),
                execution_time=end_time - start_time
            )

        # Reconstruct path from start to intersection node
        forward_edges: list[Edge] = []
        curr_id = best_intersection_node
        while curr_id != start_node.id:
            if curr_id not in previous_forward:
                break
            prev_id, edge = previous_forward[curr_id]
            forward_edges.append(edge)
            curr_id = prev_id
        forward_edges.reverse()

        # Reconstruct path from intersection node to target node
        backward_edges: list[Edge] = []
        curr_id = best_intersection_node
        while curr_id != target_node.id:
            if curr_id not in previous_backward:
                break
            next_id, edge = previous_backward[curr_id]
            backward_edges.append(edge)
            curr_id = next_id

        edges_path = forward_edges + backward_edges

        coordinates: list[list[float]] = [[start_node.lat, start_node.lon]]
        total_distance = 0.0
        total_time = 0.0

        for edge in edges_path:
            to_node = graph.nodes[edge.to_id]
            coordinates.append([to_node.lat, to_node.lon])
            total_distance += edge.distance
            speed_mph = self.speed_limit_service.get_effective_speed(
                edge.road_type,
                travel_mode,
                edge.speed,
                edge.tags,
                edge.is_reverse
            ) or self.default_speed
            total_time += self.travel_time_service.calculate_travel_time(edge.distance, speed_mph)

        end_time = time.perf_counter()

        return RouteResult(
            found=True,
            distance=total_distance,
            time=total_time,
            path=coordinates,
            edges=edges_path,
            nodes_visited_count=len(visited_forward) + len(visited_backward),
            execution_time=end_time - start_time
        )