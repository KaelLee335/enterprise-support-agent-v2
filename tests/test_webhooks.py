import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from support_agent import main
from support_agent.config import Settings
from support_agent.integrations.models import (
    AftersaleApplication,
    AftersaleEligibility,
    LogisticsInfo,
    PlatformOrder,
)


class FakeShopAdapter:
    platform_name = "mock-shop"

    def __init__(self):
        self.calls = []

    def close(self):
        pass

    def get_order(self, order_id):
        shop_id, tenant_id, customer_id = (
            ("shop-demo-b", "demo-b", "customer-demo-c")
            if order_id == "2006" else
            ("shop-demo-a", "demo-a", "customer-demo-a")
        )
        return PlatformOrder(
            order_id=order_id, platform="mock-shop", store_id=shop_id,
            tenant_id=tenant_id, customer_id=customer_id,
            product_name="虚构商品", quantity=1, status="delivered",
            returnable=True, amount_cents=1000,
        )

    def get_order_scope(self, order_id):
        from types import SimpleNamespace
        shop_id, _, customer_id = (
            ("shop-demo-b", "demo-b", "customer-demo-c")
            if order_id == "2006" else
            ("shop-demo-a", "demo-a", "customer-demo-a")
        )
        return SimpleNamespace(order_id=order_id, shop_id=shop_id,
                               customer_id=customer_id, is_demo=True)

    def get_logistics(self, order_id):
        self.calls.append(order_id)
        return LogisticsInfo(order_id=order_id, status="已签收")

    def check_aftersale_eligibility(self, order_id, reason):
        return AftersaleEligibility(order_id=order_id, eligible=True, reason_code="ELIGIBLE_DEMO", explanation="demo")

    def create_aftersale(self, order_id, reason, idempotency_key):
        return AftersaleApplication(aftersale_id="AS-DEMO", order_id=order_id, status="pending_demo", message="demo")

    def get_aftersale_status(self, aftersale_id):
        return AftersaleApplication(aftersale_id=aftersale_id, order_id="2003", status="pending_demo", message="demo")


@pytest.fixture
def webhook_client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(
        database_path=tmp_path / "commerce.db",
        checkpoint_path=tmp_path / "checkpoints.sqlite",
    ))
    monkeypatch.setattr(main, "SEED_PATH", tmp_path / "orders.json")
    main.SEED_PATH.write_text('{"orders": []}', encoding="utf-8")
    adapter = FakeShopAdapter()
    monkeypatch.setattr(main, "_new_mock_shop_adapter", lambda: adapter)
    with TestClient(main.app) as test_client:
        yield test_client, adapter


def signed_headers(body: bytes, secret: str = "demo-shop-webhook-secret") -> dict[str, str]:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return {"X-MockShop-Signature": f"sha256={digest}", "Content-Type": "application/json"}


def event_body(**overrides) -> bytes:
    event = {
        "event_id": "event-demo-2003-0001",
        "event_type": "order.shipped",
        "occurred_at": "2026-11-18T10:00:00+08:00",
        "order_id": "2003",
        "shop_id": "shop-demo-a",
        "customer_id": "customer-demo-a",
        "platform_status": "WAIT_BUYER_RECEIVE",
    }
    event.update(overrides)
    return json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode()


def test_webhook_requires_signature_and_validated_payload(webhook_client):
    client, _ = webhook_client
    body = event_body()
    invalid = client.post("/webhooks/mock-shop", content=body, headers={"X-MockShop-Signature": "sha256=bad"})
    malformed_body = b'{"event_id":"too-short"}'
    malformed = client.post(
        "/webhooks/mock-shop", content=malformed_body,
        headers=signed_headers(malformed_body),
    )

    assert invalid.status_code == 401
    assert malformed.status_code == 422


def test_webhook_event_id_is_idempotent_and_updates_order_status(webhook_client):
    client, adapter = webhook_client
    body = event_body()
    first = client.post("/webhooks/mock-shop", content=body, headers=signed_headers(body))
    duplicate = client.post("/webhooks/mock-shop", content=body, headers=signed_headers(body))
    order = client.get("/ecommerce/orders/2003", headers={"Authorization": "Bearer demo-a-local-token"})
    event = client.get(
        f"/webhooks/mock-shop/events/{json.loads(body)['event_id']}",
        headers={"Authorization": "Bearer demo-a-local-token"},
    )

    assert first.status_code == 200
    assert first.json()["order_status"] == "shipped"
    assert first.json()["duplicate"] is False
    assert duplicate.json()["duplicate"] is True
    assert order.json()["status"] == "shipped"
    assert event.json()["status"] == "processed"
    assert not adapter.calls


def test_webhook_rejects_event_id_payload_conflict_and_ignores_stale_state(webhook_client):
    client, _ = webhook_client
    body = event_body()
    first = client.post("/webhooks/mock-shop", content=body, headers=signed_headers(body))
    conflict_body = event_body(platform_status="TRADE_SUCCESS", event_type="order.delivered")
    conflict = client.post(
        "/webhooks/mock-shop", content=conflict_body,
        headers=signed_headers(conflict_body),
    )
    newer = event_body(event_id="event-demo-2003-0002", event_type="order.delivered", platform_status="TRADE_SUCCESS", occurred_at="2026-11-18T11:00:00+08:00")
    newer_response = client.post("/webhooks/mock-shop", content=newer, headers=signed_headers(newer))
    stale = event_body(event_id="event-demo-2003-0003", occurred_at="2026-11-18T09:00:00+08:00")
    stale_response = client.post("/webhooks/mock-shop", content=stale, headers=signed_headers(stale))
    order = client.get("/ecommerce/orders/2003", headers={"Authorization": "Bearer demo-a-local-token"})

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert newer_response.json()["order_status"] == "delivered"
    assert stale_response.json()["order_status"] == "delivered"
    assert order.json()["status"] == "delivered"


def test_webhook_derives_tenant_from_store_not_payload(webhook_client):
    client, _ = webhook_client
    body = event_body(event_id="event-demo-other-shop-0001", order_id="2006", shop_id="shop-demo-b", customer_id="customer-demo-c")
    response = client.post("/webhooks/mock-shop", content=body, headers=signed_headers(body))
    foreign_order = client.get("/ecommerce/orders/2006", headers={"Authorization": "Bearer demo-a-local-token"})
    event_as_foreign = client.get(
        "/webhooks/mock-shop/events/event-demo-other-shop-0001",
        headers={"Authorization": "Bearer demo-a-local-token"},
    )
    event_as_owner = client.get(
        "/webhooks/mock-shop/events/event-demo-other-shop-0001",
        headers={"Authorization": "Bearer demo-b-local-token"},
    )

    assert response.status_code == 200
    assert foreign_order.status_code == 404
    assert event_as_foreign.status_code == 404
    assert event_as_owner.status_code == 200
    assert event_as_owner.json()["event_id"] == "event-demo-other-shop-0001"
    assert event_as_owner.json()["demo_only"] is True
