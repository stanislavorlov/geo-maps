# For geographic nodes, you have two dimensions: (latitude, longitude)
from typing import List


class Node:
    def __init__(self, node_id: int, lat: float, lon: float):
        self.node_id = node_id
        self.lat = lat
        self.lon = lon

nodes_input = [
    Node(1, 49.84, 24.03),
    Node(2, 49.85, 24.02),
    Node(3, 49.83, 24.04),
    Node(4, 49.86, 24.05),
]

class KNode:
    def __init__(self, node: Node, left=None, right=None):
        self.node = node
        self.left = left
        self.right = right

def build_kd_tree(nodes: List[Node], depth = 0) -> KNode:
    if not nodes:
        return None

    axis = depth % 2

    nodes.sort(
        key=lambda node: node.lat if axis == 0 else node.lon
    )

    median = len(nodes) // 2

    return KNode(
        nodes[median],
        left=build_kd_tree(
            nodes[:median],
            depth + 1,
        ),
        right=build_kd_tree(
            nodes[median + 1:],
            depth + 1
        ))

print(build_kd_tree(nodes_input).node.node_id)

# python in-built implementation
from scipy.spatial import cKDTree
points = [
    (node.lat, node.lon)
    for node in nodes_input
]
tree = cKDTree(points)
distance, index = tree.query(
    (49.85, 24.02),
    k=1
)
nearest_node = nodes_input[index]
print(nearest_node.node_id)