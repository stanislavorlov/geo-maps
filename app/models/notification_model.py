from graph.graph import Node


class Notification:
    def __init__(self, node: Node, coordinates: list, num_visited: int, current_distance: float):
        self.node = node
        self.coordinates = coordinates
        self.num_visited = num_visited
        self.current_distance = current_distance