import pytest
from app.graph.graph import Graph, Node, Edge
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm
from routing_algorithms.astar_routing import AStarRoutingAlgorithm
from routing_algorithms.routing_factory import get_routing_algorithm
from models.search_model import RouteRequest
from models.geocode_model import ReverseGeocodeRequest


ALGORITHMS = [
    DijkstraRoutingAlgorithm(),
    AStarRoutingAlgorithm(),
]


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_direct_route(algo):
    n1 = Node(id=1, lat=51.500, lon=-0.120)
    n2 = Node(id=2, lat=51.510, lon=-0.130)
    e1 = Edge(from_id=1, to_id=2, distance=500.0, speed=25.0, road_type="primary")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])
    result = algo.find_route(graph, n1, n2)

    assert result.found is True
    assert result.distance == 500.0
    assert result.time == 500.0 / 25.0
    assert result.path == [[51.500, -0.120], [51.510, -0.130]]
    assert len(result.edges) == 1


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_multi_hop_route(algo):
    n1 = Node(id=1, lat=51.500, lon=-0.120)
    n2 = Node(id=2, lat=51.505, lon=-0.125)
    n3 = Node(id=3, lat=51.510, lon=-0.130)
    n4 = Node(id=4, lat=51.515, lon=-0.135)

    e1 = Edge(from_id=1, to_id=2, distance=300.0, speed=30.0, road_type="primary")
    e2 = Edge(from_id=2, to_id=3, distance=400.0, speed=20.0, road_type="secondary")
    e3 = Edge(from_id=3, to_id=4, distance=500.0, speed=10.0, road_type="residential")

    graph = Graph(nodes={1: n1, 2: n2, 3: n3, 4: n4}, edges=[e1, e2, e3])
    result = algo.find_route(graph, n1, n4)

    assert result.found is True
    assert result.distance == 1200.0
    expected_time = (300.0 / 30.0) + (400.0 / 20.0) + (500.0 / 10.0)
    assert pytest.approx(result.time) == expected_time
    assert result.path == [
        [51.500, -0.120],
        [51.505, -0.125],
        [51.510, -0.130],
        [51.515, -0.135]
    ]
    assert len(result.edges) == 3


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_chooses_shorter_path(algo):
    # Graph with 2 paths from 1 to 4:
    # Path A: 1 -> 2 -> 4 (dist = 400 + 400 = 800)
    # Path B: 1 -> 3 -> 4 (dist = 200 + 300 = 500) -> SHORTER
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    n3 = Node(id=3, lat=51.2, lon=0.2)
    n4 = Node(id=4, lat=51.3, lon=0.3)

    e1 = Edge(from_id=1, to_id=2, distance=400.0, speed=30.0, road_type="primary")
    e2 = Edge(from_id=2, to_id=4, distance=400.0, speed=30.0, road_type="primary")
    e3 = Edge(from_id=1, to_id=3, distance=200.0, speed=30.0, road_type="secondary")
    e4 = Edge(from_id=3, to_id=4, distance=300.0, speed=30.0, road_type="secondary")

    graph = Graph(nodes={1: n1, 2: n2, 3: n3, 4: n4}, edges=[e1, e2, e3, e4])
    result = algo.find_route(graph, n1, n4)

    assert result.found is True
    assert result.distance == 500.0
    assert result.path == [[51.0, 0.0], [51.2, 0.2], [51.3, 0.3]]


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_same_start_and_destination(algo):
    n1 = Node(id=1, lat=51.500, lon=-0.120)
    graph = Graph(nodes={1: n1}, edges=[])

    result = algo.find_route(graph, n1, n1)

    assert result.found is True
    assert result.distance == 0.0
    assert result.time == 0.0
    assert result.path == [[51.500, -0.120]]
    assert result.edges == []


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_disconnected_graph_no_route(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    n3 = Node(id=3, lat=51.2, lon=0.2)
    # 1 -> 2 exists, but 3 is isolated
    e1 = Edge(from_id=1, to_id=2, distance=100.0, speed=30.0, road_type="primary")

    graph = Graph(nodes={1: n1, 2: n2, 3: n3}, edges=[e1])
    result = algo.find_route(graph, n1, n3)

    assert result.found is False
    assert result.distance == 0.0
    assert result.path == []
    assert result.edges == []


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_one_way_road_respects_direction(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    # Directed edge 1 -> 2
    e1 = Edge(from_id=1, to_id=2, distance=250.0, speed=30.0, road_type="primary")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])

    # Forward route succeeds
    forward_result = algo.find_route(graph, n1, n2)
    assert forward_result.found is True

    # Reverse route fails
    reverse_result = algo.find_route(graph, n2, n1)
    assert reverse_result.found is False


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_default_speed_fallback(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    # Edge with speed=None
    e1 = Edge(from_id=1, to_id=2, distance=60.0, speed=None, road_type="residential")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])
    result = algo.find_route(graph, n1, n2)

    assert result.found is True
    assert result.distance == 60.0
    # Default speed is 30.0, so time = 60.0 / 30.0 = 2.0
    assert pytest.approx(result.time) == 2.0


def test_routing_factory_returns_dijkstra():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="dijkstra",
        travelMode="driving"
    )
    algo = get_routing_algorithm(req)
    assert isinstance(algo, DijkstraRoutingAlgorithm)


def test_routing_factory_returns_astar():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="astar",
        travelMode="driving"
    )
    algo = get_routing_algorithm(req)
    assert isinstance(algo, AStarRoutingAlgorithm)


def test_routing_factory_unsupported_type_raises():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="unknown_algo",
        travelMode="driving"
    )
    with pytest.raises(NotImplementedError):
        get_routing_algorithm(req)
