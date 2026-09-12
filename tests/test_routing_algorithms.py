import pytest
from app.graph.graph import Graph, Node, Edge
from models.geocode_model import ReverseGeocodeRequest
from models.search_model import RouteRequest
from routing_algorithms.astar_routing import AStarRoutingAlgorithm
from routing_algorithms.dijkstra_routing import DijkstraRoutingAlgorithm
from routing_algorithms.routing_factory import get_routing_algorithm
from services.speed_limit_service import SpeedLimitService, TravelMode
from services.travel_time_service import TravelTimeService

speed_limit_service = SpeedLimitService()
travel_time_service = TravelTimeService()


def calculate_travel_time(distance_meters: float, speed_mph: float, in_minutes: bool = True) -> float:
    return travel_time_service.calculate_travel_time(distance_meters, speed_mph, in_minutes)


ALGORITHMS = [
    DijkstraRoutingAlgorithm(speed_limit_service, travel_time_service),
    AStarRoutingAlgorithm(speed_limit_service, travel_time_service),
]


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_direct_route(algo):
    n1 = Node(id=1, lat=51.500, lon=-0.120)
    n2 = Node(id=2, lat=51.510, lon=-0.130)
    e1 = Edge(from_id=1, to_id=2, distance=500.0, speed=25.0, road_type="primary", name="Primary St")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])
    result = algo.find_route(graph, n1, n2, travel_mode="driving")

    assert result.found is True
    assert result.distance == 500.0
    expected_time = calculate_travel_time(500.0, 25.0)
    assert pytest.approx(result.time) == expected_time
    assert result.path == [[51.500, -0.120], [51.510, -0.130]]
    assert len(result.edges) == 1
    assert result.edges[0].name == "Primary St"


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
    result = algo.find_route(graph, n1, n4, travel_mode="driving")

    assert result.found is True
    assert result.distance == 1200.0
    expected_time = (
        calculate_travel_time(300.0, 30.0) +
        calculate_travel_time(400.0, 20.0) +
        calculate_travel_time(500.0, 10.0)
    )
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
    result = algo.find_route(graph, n1, n4, travel_mode="driving")

    assert result.found is True
    assert result.distance == 500.0
    assert result.path == [[51.0, 0.0], [51.2, 0.2], [51.3, 0.3]]


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_same_start_and_destination(algo):
    n1 = Node(id=1, lat=51.500, lon=-0.120)
    graph = Graph(nodes={1: n1}, edges=[])

    result = algo.find_route(graph, n1, n1, travel_mode="driving")

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
    result = algo.find_route(graph, n1, n3, travel_mode="driving")

    assert result.found is False
    assert result.distance == 0.0
    assert result.path == []
    assert result.edges == []


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_one_way_road_respects_direction(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    # Forward and reverse edges created with oneway tag
    e1_fwd = Edge(from_id=1, to_id=2, distance=250.0, speed=30.0, road_type="primary", tags={"oneway": "yes"}, is_reverse=False)
    e1_rev = Edge(from_id=2, to_id=1, distance=250.0, speed=30.0, road_type="primary", tags={"oneway": "yes"}, is_reverse=True)

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1_fwd, e1_rev])

    # Forward route succeeds for driving
    forward_result = algo.find_route(graph, n1, n2, travel_mode="driving")
    assert forward_result.found is True

    # Reverse route fails for driving
    reverse_result = algo.find_route(graph, n2, n1, travel_mode="driving")
    assert reverse_result.found is False


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_one_way_multimodal_pedestrian_and_contraflow_bicycle(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)

    # 1. Standard one-way: pedestrian can still walk reverse, car cannot
    e_fwd = Edge(from_id=1, to_id=2, distance=200.0, speed=30.0, road_type="residential", tags={"oneway": "yes"}, is_reverse=False)
    e_rev = Edge(from_id=2, to_id=1, distance=200.0, speed=30.0, road_type="residential", tags={"oneway": "yes"}, is_reverse=True)
    graph1 = Graph(nodes={1: n1, 2: n2}, edges=[e_fwd, e_rev])

    # Pedestrian walking reverse is allowed
    walk_rev = algo.find_route(graph1, n2, n1, travel_mode="walking")
    assert walk_rev.found is True

    # Cycling reverse is disallowed without contraflow
    cycle_rev_fail = algo.find_route(graph1, n2, n1, travel_mode="cycling")
    assert cycle_rev_fail.found is False

    # 2. One-way with bicycle contraflow (oneway:bicycle=no)
    e_cf_fwd = Edge(from_id=1, to_id=2, distance=200.0, speed=30.0, road_type="residential", tags={"oneway": "yes", "oneway:bicycle": "no"}, is_reverse=False)
    e_cf_rev = Edge(from_id=2, to_id=1, distance=200.0, speed=30.0, road_type="residential", tags={"oneway": "yes", "oneway:bicycle": "no"}, is_reverse=True)
    graph2 = Graph(nodes={1: n1, 2: n2}, edges=[e_cf_fwd, e_cf_rev])

    # Cycling reverse is now allowed
    cycle_rev_ok = algo.find_route(graph2, n2, n1, travel_mode="cycling")
    assert cycle_rev_ok.found is True


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_access_restrictions_and_overrides(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)

    # 1. Gated private road: all modes fail by default
    e_priv = Edge(from_id=1, to_id=2, distance=100.0, speed=20.0, road_type="residential", tags={"access": "private"})
    graph_priv = Graph(nodes={1: n1, 2: n2}, edges=[e_priv])

    assert algo.find_route(graph_priv, n1, n2, travel_mode="driving").found is False
    assert algo.find_route(graph_priv, n1, n2, travel_mode="walking").found is False
    assert algo.find_route(graph_priv, n1, n2, travel_mode="cycling").found is False

    # 2. Private road with foot=yes override: pedestrian allowed, driving blocked
    e_foot = Edge(from_id=1, to_id=2, distance=100.0, speed=20.0, road_type="residential", tags={"access": "private", "foot": "yes"})
    graph_foot = Graph(nodes={1: n1, 2: n2}, edges=[e_foot])

    assert algo.find_route(graph_foot, n1, n2, travel_mode="walking").found is True
    assert algo.find_route(graph_foot, n1, n2, travel_mode="driving").found is False

    # 3. Private road with bicycle=yes override: cycling allowed, driving blocked
    e_bike = Edge(from_id=1, to_id=2, distance=100.0, speed=20.0, road_type="residential", tags={"access": "private", "bicycle": "yes"})
    graph_bike = Graph(nodes={1: n1, 2: n2}, edges=[e_bike])

    assert algo.find_route(graph_bike, n1, n2, travel_mode="cycling").found is True
    assert algo.find_route(graph_bike, n1, n2, travel_mode="driving").found is False


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_surface_factor_speed_adjustment(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)

    # Residential road with cobblestone surface (driving base 20.0 * 0.8 = 16.0 mph, cycling base 12.0 * 0.6 = 7.2 mph)
    e_cobble = Edge(from_id=1, to_id=2, distance=800.0, speed=None, road_type="residential", tags={"surface": "cobblestone"})
    graph = Graph(nodes={1: n1, 2: n2}, edges=[e_cobble])

    drive_res = algo.find_route(graph, n1, n2, travel_mode="driving")
    assert drive_res.found is True
    assert pytest.approx(drive_res.time) == calculate_travel_time(800.0, 16.0)

    cycle_res = algo.find_route(graph, n1, n2, travel_mode="cycling")
    assert cycle_res.found is True
    assert pytest.approx(cycle_res.time) == calculate_travel_time(800.0, 7.2)


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_cycleway_infrastructure_boost(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)

    # Primary road with dedicated cycleway lane -> cycling speed boosted to 14.0 mph
    e_cycle_lane = Edge(from_id=1, to_id=2, distance=1000.0, speed=30.0, road_type="primary", tags={"cycleway": "lane"})
    graph = Graph(nodes={1: n1, 2: n2}, edges=[e_cycle_lane])

    cycle_res = algo.find_route(graph, n1, n2, travel_mode="cycling")
    assert cycle_res.found is True
    assert pytest.approx(cycle_res.time) == calculate_travel_time(1000.0, 14.0)


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_default_speed_fallback(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    # Edge with speed=None, residential speed for driving is 20.0 mph
    e1 = Edge(from_id=1, to_id=2, distance=60.0, speed=None, road_type="residential")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])
    result = algo.find_route(graph, n1, n2, travel_mode="driving")

    assert result.found is True
    assert result.distance == 60.0
    expected_time = calculate_travel_time(60.0, 20.0)
    assert pytest.approx(result.time) == expected_time


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_travel_mode_pedestrian_cannot_use_motorway(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    e1 = Edge(from_id=1, to_id=2, distance=1000.0, speed=70.0, road_type="motorway")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])

    # Walking on motorway is forbidden
    walk_result = algo.find_route(graph, n1, n2, travel_mode="walking")
    assert walk_result.found is False

    # Driving on motorway is allowed
    drive_result = algo.find_route(graph, n1, n2, travel_mode="driving")
    assert drive_result.found is True
    assert pytest.approx(drive_result.time) == calculate_travel_time(1000.0, 70.0)


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_travel_mode_car_cannot_use_footway(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    e1 = Edge(from_id=1, to_id=2, distance=300.0, speed=None, road_type="footway")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])

    # Driving on footway is forbidden
    drive_result = algo.find_route(graph, n1, n2, travel_mode="driving")
    assert drive_result.found is False

    # Walking on footway is allowed (footway speed = 3.1 mph)
    walk_result = algo.find_route(graph, n1, n2, travel_mode="walking")
    assert walk_result.found is True
    assert pytest.approx(walk_result.time) == calculate_travel_time(300.0, 3.1)


@pytest.mark.parametrize("algo", ALGORITHMS, ids=lambda a: type(a).__name__)
def test_travel_mode_cycling_profile(algo):
    n1 = Node(id=1, lat=51.0, lon=0.0)
    n2 = Node(id=2, lat=51.1, lon=0.1)
    e1 = Edge(from_id=1, to_id=2, distance=600.0, speed=None, road_type="cycleway")

    graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])

    # Driving on cycleway is forbidden
    drive_result = algo.find_route(graph, n1, n2, travel_mode="driving")
    assert drive_result.found is False

    # Cycling on cycleway is allowed (cycleway speed = 12.0 mph)
    cycle_result = algo.find_route(graph, n1, n2, travel_mode="cycling")
    assert cycle_result.found is True
    assert pytest.approx(cycle_result.time) == calculate_travel_time(600.0, 12.0)


def test_calculate_travel_time():
    # 1 mile (1609.344m) at 60 mph should be exactly 1.0 minute
    assert pytest.approx(calculate_travel_time(1609.344, 60.0, in_minutes=True)) == 1.0
    # 1 mile (1609.344m) at 30 mph should be exactly 2.0 minutes (120 seconds)
    assert pytest.approx(calculate_travel_time(1609.344, 30.0, in_minutes=True)) == 2.0
    assert pytest.approx(calculate_travel_time(1609.344, 30.0, in_minutes=False)) == 120.0
    # 0 distance or 0 speed returns 0.0
    assert calculate_travel_time(0.0, 30.0) == 0.0
    assert calculate_travel_time(100.0, 0.0) == 0.0


def test_routing_factory_returns_dijkstra():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="dijkstra",
        travelMode="driving"
    )
    algo = get_routing_algorithm(req, speed_limit_service, travel_time_service)
    assert isinstance(algo, DijkstraRoutingAlgorithm)


def test_routing_factory_returns_astar():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="astar",
        travelMode="driving"
    )
    algo = get_routing_algorithm(req, speed_limit_service, travel_time_service)
    assert isinstance(algo, AStarRoutingAlgorithm)


def test_routing_factory_unsupported_type_raises():
    req = RouteRequest(
        from_=ReverseGeocodeRequest(lat=51.5, lng=-0.1),
        to=ReverseGeocodeRequest(lat=51.6, lng=-0.2),
        routeType="unknown_algo",
        travelMode="driving"
    )
    with pytest.raises(NotImplementedError):
        get_routing_algorithm(req, speed_limit_service, travel_time_service)
