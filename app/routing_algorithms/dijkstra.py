import heapq
from collections import defaultdict, deque

edges = [
    ("A","C", 3),
    ("A","F", 2),
    ("C","F", 2),
    ("C","E", 1),
    ("C","D", 4),
    ("F","E", 3),
    ("F","B", 6),
    ("F","G", 5),
    ("E","B", 2),
    ("D","B", 1),
    ("B","G", 2),
]

def build_graph(list_of_edges: list[tuple[str, str, int]], undirected=True):
    g = defaultdict(dict)
    for u,v,w in list_of_edges:
        g[u][v] = w
        if undirected:
            g[v][u]=w
    return g

graph = build_graph(edges, undirected=True)

# Dijkstra (returns distance and path)
def dijkstra(graph_map, start, goal):
    pq = [(0, start, [])]   # (dist,node,path)
    best = {start: 0}
    visited = set()

    while pq:
        dist, node, path = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        path = path + [node]

        if node == goal:
            return dist, path

        for neighbor, weight in graph_map[node].items():
            if neighbor in visited:
                continue
            new_dist = dist + weight
            if new_dist < best.get(neighbor, float('inf')):
                best[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor, path))

    return float('inf'), []

dist_AB, path_AB = dijkstra(graph, "A", "B")
print(dist_AB, path_AB)