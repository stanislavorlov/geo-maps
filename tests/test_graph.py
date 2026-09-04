import unittest
from graph.graph import Graph, Node, Edge


class TestGraphAndNearestNode(unittest.TestCase):

    def setUp(self):
        # Sample coordinates around Central London
        self.node_big_ben = Node(id=1, lat=51.5007, lon=-0.1246, name="Big Ben")
        self.node_london_eye = Node(id=2, lat=51.5033, lon=-0.1195, name="London Eye")
        self.node_trafalgar = Node(id=3, lat=51.5080, lon=-0.1281, name="Trafalgar Square")
        self.node_piccadilly = Node(id=4, lat=51.5100, lon=-0.1340, name="Piccadilly Circus")

        self.nodes = {
            1: self.node_big_ben,
            2: self.node_london_eye,
            3: self.node_trafalgar,
            4: self.node_piccadilly,
        }

        self.edges = [
            Edge(from_id=1, to_id=2, distance=500.0, speed=30.0, road_type="primary"),
            Edge(from_id=2, to_id=3, distance=700.0, speed=20.0, road_type="secondary"),
            Edge(from_id=3, to_id=4, distance=400.0, speed=25.0, road_type="primary"),
        ]

        self.graph = Graph(nodes=self.nodes, edges=self.edges)

    def test_find_nearest_node_exact_match(self):
        # Query exactly at Big Ben coordinates
        nearest = self.graph.find_nearest_node(51.5007, -0.1246)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 1)
        self.assertEqual(nearest.name, "Big Ben")

    def test_find_nearest_node_close_proximity(self):
        # Slightly offset from Trafalgar Square (lat: 51.5080, lon: -0.1281)
        nearest = self.graph.find_nearest_node(51.5082, -0.1280)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 3)
        self.assertEqual(nearest.name, "Trafalgar Square")

    def test_find_nearest_node_closest_among_many(self):
        # Coordinate closer to Piccadilly than Trafalgar
        nearest = self.graph.find_nearest_node(51.5098, -0.1335)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 4)

        # Coordinate closer to London Eye
        nearest = self.graph.find_nearest_node(51.5030, -0.1200)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 2)

    def test_find_nearest_node_empty_graph(self):
        empty_graph = Graph(nodes={}, edges=[])
        nearest = empty_graph.find_nearest_node(51.5007, -0.1246)
        self.assertIsNone(nearest)

    def test_find_nearest_node_single_node(self):
        single_node = Node(id=99, lat=52.0, lon=0.0, name="Single")
        single_graph = Graph(nodes={99: single_node}, edges=[])
        nearest = single_graph.find_nearest_node(0.0, 0.0)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 99)

    def test_find_nearest_node_longitude_scaling(self):
        # At lat 60, cos(60 deg) = 0.5.
        # A degree of longitude is half as long as a degree of latitude.
        # Node A is 0.1 deg away along latitude -> physical distance ~ 0.1 deg
        # Node B is 0.15 deg away along longitude -> physical distance ~ 0.15 * 0.5 = 0.075 deg (closer!)
        node_lat = Node(id=1, lat=60.1, lon=0.0, name="North")
        node_lon = Node(id=2, lat=60.0, lon=0.15, name="East")
        graph = Graph(nodes={1: node_lat, 2: node_lon}, edges=[])

        nearest = graph.find_nearest_node(60.0, 0.0)
        self.assertIsNotNone(nearest)
        self.assertEqual(nearest.id, 2, "East node should be chosen due to cos(lat) longitude scaling")

    def test_adjacency_list_pre_built(self):
        # Node 1 has outgoing edge to 2
        self.assertIn(1, self.graph.adjacency)
        self.assertEqual(len(self.graph.adjacency[1]), 1)
        self.assertEqual(self.graph.adjacency[1][0].to_id, 2)

        # Node 4 has no outgoing edges, but exists in adjacency dict
        self.assertIn(4, self.graph.adjacency)
        self.assertEqual(len(self.graph.adjacency[4]), 0)

    def test_data_stats(self):
        stats = self.graph.data_stats()
        self.assertEqual(stats["locations_count"], 4)
        self.assertEqual(stats["roads_count"], 3)


if __name__ == "__main__":
    unittest.main()
