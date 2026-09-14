import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from api import directions
from app.graph.graph import Graph, Node, Edge
from api.dependencies import get_graph_repository


class MockGraphRepository:
    def __init__(self, *args, **kwargs):
        n1 = Node(id=1, lat=51.500, lon=-0.120)
        n2 = Node(id=2, lat=51.510, lon=-0.130)
        e1 = Edge(from_id=1, to_id=2, distance=500.0, speed=25.0, road_type="primary", name="Primary St")
        self.graph = Graph(nodes={1: n1, 2: n2}, edges=[e1])

    async def query_route_graph(self, travel_mode, start, end, buffer_degree=0.01):
        return self.graph


def override_graph_repository():
    return MockGraphRepository()


@pytest.fixture
def client():
    test_app = FastAPI()
    test_app.include_router(directions.router)
    test_app.dependency_overrides[get_graph_repository] = override_graph_repository
    with TestClient(test_app) as test_client:
        yield test_client


def test_http_find_route(client):
    payload = {
        "from_": {"lat": 51.500, "lng": -0.120},
        "to": {"lat": 51.510, "lng": -0.130},
        "routeType": "dijkstra",
        "travelMode": "driving"
    }
    response = client.post("/api/find_route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["distance"] == 500.0
    assert len(data["path"]) == 2


def test_websocket_find_route(client):
    payload = {
        "from_": {"lat": 51.500, "lng": -0.120},
        "to": {"lat": 51.510, "lng": -0.130},
        "routeType": "astar",
        "travelMode": "driving"
    }
    with client.websocket_connect("/api/ws/find_route") as websocket:
        websocket.send_json(payload)
        
        # Read messages until result
        messages = []
        while True:
            msg = websocket.receive_json()
            messages.append(msg)
            if msg.get("type") == "result":
                break

        assert any(m.get("type") == "start" for m in messages)
        assert any(m.get("type") == "progress" for m in messages)
        final_result = messages[-1]
        assert final_result["type"] == "result"
        assert final_result["status"] == "success"
        assert final_result["distance"] == 500.0
