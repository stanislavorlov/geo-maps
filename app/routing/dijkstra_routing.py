import heapq
from collections import defaultdict
from database.models import Road, Location

# For shortest distance:
# new_distance = distance + road.distance

# For fastest route:
# travel_time = road.distance / road.speed

# and Dijkstra minimizes:
# new_distance = distance + road.distance / road.speed

def shortest_path_map(edges: list[tuple[Road, Location, Location]], from_: Location, to_: Location) -> list[Road]:
    adj_map = defaultdict(list)

    for road, src, dst in edges:
        adj_map[src.id].append((dst.id, road))

    distances = {from_.id: 0.0}
    previous = {}
    min_heap = [(0.0, from_.id)]

    while min_heap:
        distance, current_id = heapq.heappop(min_heap)

        if distance > distances.get(current_id, float("inf")):
            continue

        if current_id == to_.id:
            break

        for next_id, road in adj_map[current_id]:
            new_distance = distance + road.distance

            if new_distance < distances.get(next_id, float("inf")):
                distances[next_id] = new_distance

                previous[next_id] = road

                heapq.heappush(min_heap, (new_distance, next_id))

    if to_.id not in distances:
        return []

    routes : list[Road] = []
    current_id = to_.id

    while current_id != from_.id:
        road = previous[current_id]

        # Return the original Road instances - rebuilding them would lose the id
        # (and SQLAlchemy models only accept keyword arguments anyway).
        routes.append(road)
        current_id = road.from_id

    routes.reverse()

    return routes