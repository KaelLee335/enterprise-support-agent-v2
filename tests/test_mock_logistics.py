import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from support_agent import mock_logistics
from support_agent.mock_logistics import app


@pytest.fixture
def client():
    return TestClient(app)


def test_mock_logistics_requires_service_key(client):
    assert client.get("/shipments/1001").status_code == 401
    assert client.get(
        "/shipments/1001", headers={"X-Demo-Service-Key": "wrong"}
    ).status_code == 401


def test_mock_logistics_returns_only_fictional_tracking_fixture(client):
    response = client.get(
        "/shipments/1001",
        headers={"X-Demo-Service-Key": mock_logistics.SERVICE_KEY},
    )
    assert response.status_code == 200
    assert response.json()["tracking_number"] == "DEMO-SHIP-1001"
    assert response.json()["demo_only"] is True


def test_mock_logistics_unknown_order_returns_not_found(client):
    response = client.get(
        "/shipments/NO-SUCH-ORDER",
        headers={"X-Demo-Service-Key": mock_logistics.SERVICE_KEY},
    )
    assert response.status_code == 404
