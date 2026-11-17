from pathlib import Path

import httpx
import pytest

from support_agent.config import Settings
from support_agent.logistics import fetch_shipment


def test_fetch_shipment_sends_demo_auth_and_validates_response(monkeypatch):
    requests = []
    transport = httpx.MockTransport(lambda request: (
        requests.append(request)
        or httpx.Response(200, json={
            "order_id": "1001",
            "tracking_number": "DEMO-SHIP-1001",
            "status": "已签收",
            "events": [],
            "demo_only": True,
        })
    ))
    real_client = httpx.Client

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("support_agent.logistics.httpx.Client", mock_client)
    shipment = fetch_shipment("1001", Settings(
        database_path=Path("demo.db"),
        logistics_api_base_url="http://mock-logistics.test",
        logistics_api_key="synthetic-test-key",
    ))

    assert shipment.status == "已签收"
    assert shipment.demo_only is True
    assert requests[0].url.path == "/shipments/1001"
    assert requests[0].headers["X-Demo-Service-Key"] == "synthetic-test-key"


def test_fetch_shipment_surfaces_timeout_for_safe_node_fallback(monkeypatch):
    class TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, path):
            raise httpx.TimeoutException("synthetic timeout")

    monkeypatch.setattr("support_agent.logistics.httpx.Client", TimeoutClient)
    with pytest.raises(httpx.TimeoutException):
        fetch_shipment("1001", Settings(database_path=Path("demo.db")))


@pytest.mark.parametrize(
    "response,exception",
    [
        (httpx.Response(503, json={"detail": "offline"}), httpx.HTTPStatusError),
        (httpx.Response(200, json={"status": "malformed"}), ValueError),
    ],
)
def test_fetch_shipment_rejects_http_errors_and_invalid_json_contract(
    monkeypatch, response, exception
):
    transport = httpx.MockTransport(lambda request: response)
    real_client = httpx.Client

    def mock_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr("support_agent.logistics.httpx.Client", mock_client)
    with pytest.raises(exception):
        fetch_shipment("1001", Settings(database_path=Path("demo.db")))
