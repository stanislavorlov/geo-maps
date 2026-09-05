import heapq

def heuristic(a, b):
    # Standard Manhattan distance heuristic for grid-based pathfinding
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def a_star_algorithm(
        graph:  dict[tuple[int, int], dict[tuple[int, int], int]],
        start: tuple[int, int],
        goal: tuple[int, int]):
    # Priority queue stores tuples of: (f_score, current_node)
    open_list: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(open_list, (0, start))

    # Tracking dictionaries
    came_from = {}
    # actual cost travel
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0

    # total estimates cost = actual + heuristic
    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    # Set to quickly check if a node is in the open list
    open_set = {start}

    while open_list:
        # Get the node with the lowest f_score
        _, current = heapq.heappop(open_list)
        open_set.remove(current)

        # Goal reached, backtrack to extract the final path
        if current == goal:
            path : list[tuple[int, tuple[int, int]]] = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Return reversed path (start to goal)

        # Process adjacent neighbors
        for neighbor, weight in graph[current].items():
            tentative_g_score = g_score[current] + weight

            # If a shorter path to neighbor is found
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)

                if neighbor not in open_set:
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))
                    open_set.add(neighbor)

    return None  # Return None if no path exists

# Nodes are coordinates (x, y); values are dicts of {neighbor: edge_weight}
example_graph = {
    (0, 0): {(0, 1): 1, (1, 0): 1},
    (0, 1): {(0, 0): 1, (1, 1): 5}, # (1, 1) has high cost terrain
    (1, 0): {(0, 0): 1, (1, 1): 1},
    (1, 1): {(0, 1): 5, (1, 0): 1}
}

a_star_path = a_star_algorithm(example_graph, (0, 0), (1, 1))
print(a_star_path)