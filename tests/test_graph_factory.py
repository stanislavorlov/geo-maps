import unittest
from shapely.geometry import Point
from geoalchemy2.elements import WKBElement

from database.models import Location, Road
from app.graph.graph_factory import GraphFactory


class TestGraphFactory(unittest.TestCase):

    def _create_mock_location(self, loc_id: int, lat: float, lon: float, name: str = None, desc: str = None) -> Location:
        loc = Location()
        loc.id = loc_id
        loc.name = name
        loc.description = desc
        pt = Point(lon, lat)
        loc.geom = WKBElement(pt.wkb_hex, srid=4326)
        return loc

    def _create_mock_road(self, road_id: int, from_id: int, to_id: int, distance: float, speed: float = 30.0, road_type: str = "primary") -> Road:
        road = Road()
        road.id = road_id
        road.from_id = from_id
        road.to_id = to_id
        road.distance = distance
        road.speed = speed
        road.road_type = road_type
        return road

    def test_create_from_db_records(self):
        loc1 = self._create_mock_location(1, 51.500, -0.120, name="Point A")
        loc2 = self._create_mock_location(2, 51.505, -0.125, name="Point B")
        loc3 = self._create_mock_location(3, 51.510, -0.130, name="Point C")

        road1 = self._create_mock_road(101, 1, 2, 450.0, speed=30.0, road_type="primary")
        road2 = self._create_mock_road(102, 2, 3, 550.0, speed=20.0, road_type="secondary")

        records = [
            (road1, loc1, loc2),
            (road2, loc2, loc3),
        ]

        graph = GraphFactory.create_from_db_records(records)

        # Verify nodes extracted and deduplicated
        self.assertEqual(len(graph.nodes), 3)
        self.assertIn(1, graph.nodes)
        self.assertIn(2, graph.nodes)
        self.assertIn(3, graph.nodes)

        node1 = graph.nodes[1]
        self.assertEqual(node1.id, 1)
        self.assertAlmostEqual(node1.lat, 51.500)
        self.assertAlmostEqual(node1.lon, -0.120)
        self.assertEqual(node1.name, "Point A")

        # Verify edges
        self.assertEqual(len(graph.edges), 2)
        edge1 = graph.edges[0]
        self.assertEqual(edge1.from_id, 1)
        self.assertEqual(edge1.to_id, 2)
        self.assertEqual(edge1.distance, 450.0)
        self.assertEqual(edge1.speed, 30.0)
        self.assertEqual(edge1.road_type, "primary")

        # Verify pre-built adjacency
        self.assertEqual(len(graph.adjacency[1]), 1)
        self.assertEqual(len(graph.adjacency[2]), 1)
        self.assertEqual(len(graph.adjacency[3]), 0)

    def test_create_from_empty_records(self):
        graph = GraphFactory.create_from_db_records([])
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)
        self.assertEqual(graph.adjacency, {})


if __name__ == "__main__":
    unittest.main()
