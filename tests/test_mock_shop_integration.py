import httpx
import pytest
from fastapi.testclient import TestClient

from support_agent.integrations.errors import (
    IntegrationNotFound,
    IntegrationInvalidResponse,
    IntegrationRejected,
    IntegrationNotFound,
    IntegrationProtocolError,
    IntegrationUnavailable,
)
from support_agent.integrations.mock_shop import MockShopAdapter
from support_agent.integrations.registry import AdapterRegistry
from support_agent.integrations.tools import build_mockshop_tools
from support_agent.auth import DemoIdentity
from support_agent.db import initialize_database
from support_agent.mock_shop_api import MockShopRepository, create_mock_shop_app


KEY = "demo-shop-local-key"
HEADERS = {"X-Demo-Platform-Key": KEY}


@pytest.fixture
def shop_client():
    app = create_mock_shop_app(MockShopRepository(), service_key=KEY)
    with TestClient(app) as client:
        yield client


def test_mock_shop_exposes_fictional_order_states_and_scoped_fixtures(shop_client):
    pending = shop_client.get("/mock-shop/orders/2001", headers=HEADERS)
    delivered = shop_client.get("/mock-shop/orders/2003", headers=HEADERS)
    refunded = shop_client.get("/mock-shop/orders/2005", headers=HEADERS)
    other_shop = shop_client.get("/mock-shop/orders/2006", headers=HEADERS)

    assert pending.json()["platform_status"] == "WAIT_SELLER_SEND_GOODS"
    assert delivered.json()["platform_status"] == "TRADE_SUCCESS"
    assert refunded.json()["platform_status"] == "REFUND_SUCCESS"
    assert other_shop.json()["shop_id"] == "shop-demo-b"
    assert all(result.json()["is_demo"] for result in (pending, delivered, refunded, other_shop))


def test_mock_shop_requires_internal_demo_service_key_and_hides_missing_orders(shop_client):
    assert shop_client.get("/mock-shop/orders/2001").status_code == 401
    assert shop_client.get("/mock-shop/orders/missing", headers=HEADERS).status_code == 404


def test_mock_shop_logistics_and_after_sale_eligibility(shop_client):
    assert shop_client.get("/mock-shop/orders/2002/logistics", headers=HEADERS).json()["platform_status"] == "IN_TRANSIT"
    eligible = shop_client.get("/mock-shop/orders/2003/aftersale-eligibility", headers=HEADERS).json()
    prior_after_sale = shop_client.get("/mock-shop/orders/2004/aftersale-eligibility", headers=HEADERS).json()
    unsupported = shop_client.get("/mock-shop/orders/2006/aftersale-eligibility", headers=HEADERS).json()

    assert eligible["eligible"] is True
    assert prior_after_sale["reason_code"] == "ALREADY_IN_AFTERSALE"
    assert unsupported["reason_code"] == "NOT_RETURNABLE"


def test_mock_shop_after_sale_creation_is_idempotent_and_status_is_queryable(shop_client):
    payload = {"reason": "质量问题（虚构演示）", "idempotency_key": "demo-order-2003-01"}
    first = shop_client.post("/mock-shop/orders/2003/aftersales", headers=HEADERS, json=payload)
    retry = shop_client.post("/mock-shop/orders/2003/aftersales", headers=HEADERS, json=payload)
    status = shop_client.get(f"/mock-shop/aftersales/{first.json()['aftersale_id']}", headers=HEADERS)

    assert first.status_code == 201
    assert retry.json()["aftersale_id"] == first.json()["aftersale_id"]
    assert status.json()["platform_status"] == "WAIT_REVIEW"
    assert status.json()["is_demo"] is True


def test_mock_shop_blocks_duplicate_application_and_reused_key_for_another_order(shop_client):
    payload = {"reason": "商品质量问题", "idempotency_key": "demo-idempotency-unique-01"}
    assert shop_client.post("/mock-shop/orders/2003/aftersales", headers=HEADERS, json=payload).status_code == 201
    duplicate = shop_client.post("/mock-shop/orders/2003/aftersales", headers=HEADERS, json={**payload, "idempotency_key": "demo-idempotency-unique-02"})
    key_conflict = shop_client.post("/mock-shop/orders/2002/aftersales", headers=HEADERS, json=payload)

    assert duplicate.status_code == 409
    assert key_conflict.status_code == 409


def test_adapter_maps_provider_fields_and_status_to_domain_models():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/mock-shop/orders/2002":
            body = {"order_id": "2002", "shop_id": "shop-demo-a", "customer_id": "customer-demo-a", "product_name": "演示背包", "quantity": 1, "platform_status": "WAIT_BUYER_RECEIVE", "returnable": True, "amount_cents": 12900, "is_demo": True}
        elif request.url.path == "/mock-shop/orders/2002/logistics":
            body = {"order_id": "2002", "tracking_no": "MOCK-2002", "platform_status": "IN_TRANSIT", "events": [], "is_demo": True}
        else:
            return httpx.Response(404, json={"detail": "not found"})
        return httpx.Response(200, json=body)

    adapter = MockShopAdapter(transport=httpx.MockTransport(handler))
    try:
        order = adapter.get_order("2002")
        shipment = adapter.get_logistics("2002")
    finally:
        adapter.close()

    assert order.status == "shipped"
    assert order.store_id == "shop-demo-a"
    assert order.tenant_id == "demo-a"
    assert shipment.tracking_number == "MOCK-2002"
    assert shipment.status == "运输中"


def test_adapter_fails_closed_on_unknown_platform_status_and_registry_lookup():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"order_id": "2002", "shop_id": "shop-demo-a", "customer_id": "customer-demo-a", "product_name": "演示背包", "quantity": 1, "platform_status": "NEW_UNKNOWN_STATE", "returnable": True, "amount_cents": 12900, "is_demo": True})

    adapter = MockShopAdapter(transport=httpx.MockTransport(handler))
    registry = AdapterRegistry()
    registry.register(adapter)
    try:
        with pytest.raises(IntegrationProtocolError) as error:
            adapter.get_order("2002")
        assert error.value.code == "unsupported_platform_value"
        assert registry.get("MOCK-SHOP") is adapter
        with pytest.raises(LookupError):
            registry.get("shopify")
    finally:
        adapter.close()


@pytest.mark.parametrize(
    ("response", "expected_error"),
    [
        (httpx.Response(404, json={"detail": "sensitive provider text"}), IntegrationNotFound),
        (httpx.Response(503, json={"detail": "internal provider details"}), IntegrationUnavailable),
    ],
)
def test_adapter_normalizes_provider_http_errors(response, expected_error):
    adapter = MockShopAdapter(transport=httpx.MockTransport(lambda request: response))
    try:
        with pytest.raises(expected_error) as error:
            adapter.get_order("missing")
        assert "sensitive provider text" not in str(error.value)
        assert "internal provider details" not in str(error.value)
    finally:
        adapter.close()


def test_adapter_normalizes_timeout_and_invalid_json():
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("sensitive transport detail", request=request)

    timed_adapter = MockShopAdapter(transport=httpx.MockTransport(timeout))
    try:
        with pytest.raises(IntegrationUnavailable):
            timed_adapter.get_order("2001")
    finally:
        timed_adapter.close()

    invalid_adapter = MockShopAdapter(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="not-json"))
    )
    try:
        with pytest.raises(IntegrationInvalidResponse):
            invalid_adapter.get_order("2001")
    finally:
        invalid_adapter.close()


def test_langchain_tools_bind_identity_and_guard_demo_write_confirmation(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/mock-shop/orders/2003/scope":
            return httpx.Response(200, json={"order_id": "2003", "shop_id": "shop-demo-a", "customer_id": "customer-demo-a", "is_demo": True})
        if request.url.path == "/mock-shop/orders/2003":
            return httpx.Response(200, json={"order_id": "2003", "shop_id": "shop-demo-a", "customer_id": "customer-demo-a", "product_name": "演示耳机", "quantity": 1, "platform_status": "TRADE_SUCCESS", "returnable": True, "amount_cents": 19900, "is_demo": True})
        if request.url.path == "/mock-shop/orders/2003/logistics":
            return httpx.Response(200, json={"order_id": "2003", "tracking_no": "MOCK-2003", "platform_status": "DELIVERED", "events": [], "is_demo": True})
        if request.url.path == "/mock-shop/orders/2003/aftersale-eligibility":
            return httpx.Response(200, json={"order_id": "2003", "eligible": True, "reason_code": "ELIGIBLE_DEMO", "message": "eligible demo", "is_demo": True})
        if request.url.path == "/mock-shop/orders/2003/aftersales":
            return httpx.Response(201, json={"aftersale_id": "AS-2003", "order_id": "2003", "platform_status": "WAIT_REVIEW", "reason": "虚构质量问题", "is_demo": True})
        if request.url.path == "/mock-shop/aftersales/AS-2003":
            return httpx.Response(200, json={"aftersale_id": "AS-2003", "order_id": "2003", "platform_status": "WAIT_REVIEW", "reason": "虚构质量问题", "is_demo": True})
        if request.url.path == "/mock-shop/aftersales/AS-2003/scope":
            return httpx.Response(200, json={"aftersale_id": "AS-2003", "order_id": "2003", "is_demo": True})
        return httpx.Response(404, json={"detail": "not found"})

    adapter = MockShopAdapter(transport=httpx.MockTransport(handler))
    seed = tmp_path / "seed.json"
    seed.write_text('{"orders": []}', encoding="utf-8")
    database_path = tmp_path / "tools.db"
    initialize_database(database_path, seed)
    tools = build_mockshop_tools(
        DemoIdentity("user-demo-a", "demo-a", "requester"), adapter=adapter,
        database_path=database_path,
    )
    try:
        assert tools.get_order.invoke({"order_id": "2003"})["status"] == "delivered"
        assert tools.get_logistics.invoke({"order_id": "2003"})["status"] == "已签收"
        assert tools.check_aftersale_eligibility.invoke({"order_id": "2003", "reason": "质量问题"})["eligible"]
        with pytest.raises(IntegrationRejected):
            tools.create_aftersale.invoke({"order_id": "2003", "reason": "质量问题", "idempotency_key": "tool-key-2003", "confirmed": False})
        result = tools.create_aftersale.invoke({"order_id": "2003", "reason": "虚构质量问题", "idempotency_key": "tool-key-2003", "confirmed": True})
        status = tools.get_aftersale_status.invoke({"aftersale_id": "AS-2003"})
        assert result["status"] == status["status"] == "pending_demo"
        from support_agent.db import connect
        with connect(database_path) as connection:
            stored = connection.execute(
                "SELECT user_id, actor_id, customer_id FROM aftersale_requests"
            ).fetchone()
        assert tuple(stored) == ("user-demo-a", "user-demo-a", "customer-demo-a")
    finally:
        tools.close()

    denied_adapter = MockShopAdapter(transport=httpx.MockTransport(handler))
    denied_tools = build_mockshop_tools(
        DemoIdentity("user-legacy-demo", "legacy-demo"), adapter=denied_adapter,
        database_path=database_path,
    )
    try:
        with pytest.raises(IntegrationNotFound):
            denied_tools.get_order.invoke({"order_id": "2003"})
    finally:
        denied_tools.close()
