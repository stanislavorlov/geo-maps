from geoalchemy2.shape import to_shape
from database.models import Road, Location
from graph.graph import Graph, Node, Edge


class GraphFactory:
    @staticmethod
    def create_from_db_records(records: list[tuple[Road, Location, Location]]) -> Graph:
        nodes: dict[int, Node] = {}
        edges: list[Edge] = []

        for road, loc_from, loc_to in records:
            if loc_from.id not in nodes:
                point_from = to_shape(loc_from.geom)
                nodes[loc_from.id] = Node(
                    id=loc_from.id,
                    lat=point_from.y,
                    lon=point_from.x,
                    name=loc_from.name,
                    description=loc_from.description
                )

            if loc_to.id not in nodes:
                point_to = to_shape(loc_to.geom)
                nodes[loc_to.id] = Node(
                    id=loc_to.id,
                    lat=point_to.y,
                    lon=point_to.x,
                    name=loc_to.name,
                    description=loc_to.description
                )

            road_tags = road.tags if hasattr(road, "tags") and road.tags else {}
            road_name = road.name if hasattr(road, "name") else None

            # Forward edge (u -> v)
            edges.append(Edge(
                from_id=road.from_id,
                to_id=road.to_id,
                distance=road.distance,
                speed=road.speed,
                road_type=road.road_type,
                name=road_name,
                tags=road_tags,
                is_reverse=False
            ))

            # Backward edge (v -> u)
            edges.append(Edge(
                from_id=road.to_id,
                to_id=road.from_id,
                distance=road.distance,
                speed=road.speed,
                road_type=road.road_type,
                name=road_name,
                tags=road_tags,
                is_reverse=True
            ))

        return Graph(nodes=nodes, edges=edges)


def get_geo_graph(records: list[tuple[Road, Location, Location]]) -> Graph:
    """Convenience functional wrapper for GraphFactory."""
    return GraphFactory.create_from_db_records(records)