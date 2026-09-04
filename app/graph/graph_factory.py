from geoalchemy2.shape import to_shape
from database.models import Road, Location
from graph.graph import Node, Graph, Edge


def build_graph(roads: list[tuple[Road, Location, Location]]):
    local_nodes = {}
    local_edges = []

    for road, loc_from, loc_to in roads:
        # Extract and add unique source nodes
        if loc_from.id not in local_nodes:
            point_from = to_shape(loc_from.geom)
            local_nodes[loc_from.id] = Node(
                id=loc_from.id,
                lon=point_from.x,
                lat=point_from.y,
                name=loc_from.name,
                description=loc_from.description
            )

        # Extract and add unique target nodes
        if loc_to.id not in local_nodes:
            point_to = to_shape(loc_to.geom)
            local_nodes[loc_to.id] = Node(
                id=loc_to.id,
                lon=point_to.x,
                lat=point_to.y,
                name=loc_to.name,
                description=loc_to.description
            )

        # Create edges
        local_edges.append(Edge(
            from_id=road.from_id,
            to_id=road.to_id,
            distance=road.distance,
            speed=road.speed,
            road_type=road.road_type
        ))

    return Graph(
        nodes=list(local_nodes.values()),
        edges=local_edges
    )