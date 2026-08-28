# src point
# adjacency list
import heapq
from collections import defaultdict
from typing import List, Tuple

# example_graph = {
#    "A": {"B": 3, "C": 3},
#    "B": {"A": 3, "D": 3.5, "E": 2.8},
#    "C": {"A": 3, "E": 2.8, "F": 3.5},
#    "D": {"B": 3.5, "E": 3.1, "G": 10},
#    "E": {"B": 2.8, "C": 2.8, "D": 3.1, "G": 7},
#    "F": {"G": 2.5, "C": 3.5},
#    "G": {"F": 2.5, "E": 7, "D": 10},
# }

input_src = 'A'
input_edges = [
    ("A", "B", 3),
    ("A", "C", 3),
    ("B", "D", 3.5),
    ("B", "E", 2.8),
    ("C", "E", 2.8),
    ("C", "F", 3.5),
    ("D", "E", 3.1),
    ("D", "G", 10),
    ("E", "G", 7),
    ("F", "G", 2.5),
]


def shortest_path(edges: List[Tuple[str, str, float]], src: str) -> dict[str, int]:
    adj = defaultdict(list)

    for s, d, w in edges:
        adj[s].append((d, w))

    shortest = {}
    min_heap = [(0, src)]

    while min_heap:
        weight1, node1 = heapq.heappop(min_heap)
        if node1 in shortest:
            continue

        shortest[node1] = weight1

        for node2, weight2 in adj[node1]:
            if node2 not in shortest:
                heapq.heappush(min_heap, (weight1 + weight2, node2))

    return shortest


print(shortest_path(input_edges, input_src))
