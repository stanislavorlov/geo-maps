import heapq
from graph.graph import Graph, Node, Edge
from routing_algorithms.abstract_routing import AbstractRoutingAlgorithm, RouteResult


def heuristic(start_node, target_node):
    # Standard Manhattan distance heuristic for grid-based pathfinding
    return abs(start_node.lat - target_node.lat) + abs(start_node.lon - target_node.lon)

class AStarRoutingAlgorithm(AbstractRoutingAlgorithm):

    def find_route(self, graph: Graph, start_node: Node, target_node: Node) -> RouteResult:
        if start_node.id == target_node.id:
            return RouteResult(
                found=True,
                distance=0.0,
                time=0.0,
                path=[[start_node.lat, start_node.lon]],
                edges=[]
            )

        queue = []
        heapq.heappush(queue, (0, start_node.id))
        previous = {}
        g_score = {node: float('inf') for node in graph.nodes}
        g_score[start_node.id] = 0

        f_score = {node: float('inf') for node in graph.nodes}
        f_score[start_node.id] = heuristic(start_node, target_node)

        # set to check if a node is in the open list
        visited = {start_node.id}

        while queue:
            distance, node_id = heapq.heappop(queue)
            visited.remove(node_id)

            if node_id == target_node.id:
                path : list[Edge] = []
                while node_id in previous:
                    path.append(previous[node_id])
                    node_id = previous[node_id]
                path.append(start_node.id)

                # ToDo: return list of Graph edges
                return path[::-1]

            for edge in graph.adjacency.get(node_id, []):
                tentative_g_score = g_score[node_id] + edge.distance

                if tentative_g_score < g_score[edge.to_id]:
                    previous[edge.to_id] = node_id
                    g_score[edge.to_id] = tentative_g_score
                    f_score[edge.to_id] = tentative_g_score + heuristic(graph.nodes.get(edge.to_id), target_node)

                    if edge.to_id not in visited:
                        heapq.heappush(queue, (f_score[edge.to_id], edge.to_id))
                        visited.add(edge.to_id)

        return RouteResult(
            found=False,
        )
