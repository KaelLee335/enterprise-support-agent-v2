import pytest
from fastapi.testclient import TestClient

from support_agent import main
from support_agent.config import Settings
from support_agent.integrations.errors import IntegrationUnavailable
from support_agent.integrations.models import (
    AftersaleApplication,
    AftersaleEligibility,
    LogisticsInfo,
    PlatformOrder,
)


class FakeShopAdapter:
    platform_name = "mock-shop"

    def __init__(self, *, unavailable: bool = False):
        self.unavailable = unavailable
        self.calls: list[tuple] = []
        self.applications: dict[tuple[str, str], AftersaleApplication] = {}

    def close(self):
        pass

    def get_order(self, order_id: str) -> PlatformOrder:
        if self.unavailable:
            raise IntegrationUnavailable("hidden detail")
        fixtures = {
            "2003": ("shop-demo-a", "demo-a", "customer-demo-a"),
            "2004": ("shop-demo-a", "demo-a", "customer-demo-b"),
            "2006": ("shop-demo-b", "demo-b", "customer-demo-c"),
        }
        if order_id not in fixtures:
            from support_agent.integrations.errors import IntegrationNotFound
            raise IntegrationNotFound("hidden detail")
        store_id, tenant_id, customer_id = fixtures[order_id]
        return PlatformOrder(
            order_id=order_id, platform=self.platform_name, store_id=store_id,
            tenant_id=tenant_id, customer_id=customer_id, product_name="虚构商品",
            quantity=1, status="delivered", returnable=True, amount_cents=1000,
        )

    def get_logistics(self, order_id: str) -> LogisticsInfo:
        self.calls.append(("logistics", order_id))
        return LogisticsInfo(order_id=order_id, tracking_number="MOCK-2003", status="已签收")

    def check_aftersale_eligibility(self, order_id: str, reason: str) -> AftersaleEligibility:
        self.calls.append(("eligibility", order_id, reason))
        return AftersaleEligibility(order_id=order_id, eligible=True, reason_code="ELIGIBLE_DEMO", explanation="符合虚构演示规则")

    def create_aftersale(self, order_id: str, reason: str, idempotency_key: str) -> AftersaleApplication:
        self.calls.append(("create", order_id, reason, idempotency_key))
        key = (order_id, idempotency_key)
        if key not in self.applications:
            self.applications[key] = AftersaleApplication(
                aftersale_id=f"AS-{len(self.applications) + 1}", order_id=order_id,
                status="pending_demo", message="Mock only",
            )
        return self.applications[key]

    def get_aftersale_status(self, aftersale_id: str) -> AftersaleApplication:
        raise NotImplementedError


@pytest.fixture
def commerce_client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "settings", Settings(
        database_path=tmp_path / "commerce.db",
        checkpoint_path=tmp_path / "checkpoints.sqlite",
    ))
    monkeypatch.setattr(main, "SEED_PATH", tmp_path / "orders.json")
    main.SEED_PATH.write_text('{"orders": []}', encoding="utf-8")
    adapter = FakeShopAdapter()
    monkeypatch.setattr(main, "_new_mock_shop_adapter", lambda: adapter)
    with TestClient(main.app) as client:
        yield client, adapter


def auth(token="demo-a-local-token"):
    return {"Authorization": f"Bearer {token}"}


def test_ecommerce_order_and_logistics_are_identity_scoped(commerce_client):
    client, adapter = commerce_client
    own = client.get("/ecommerce/orders/2003", headers=auth())
    other_customer = client.get("/ecommerce/orders/2004", headers=auth())
    other_shop = client.get("/ecommerce/orders/2006", headers=auth())
    demo_b_own = client.get("/ecommerce/orders/2006", headers=auth("demo-b-local-token"))
    approver = client.get("/ecommerce/orders/2004", headers=auth("demo-a-approver-local-token"))
    logistics = client.get("/ecommerce/orders/2003/logistics", headers=auth())

    assert own.status_code == 200
    assert own.json()["status"] == "delivered"
    assert own.json()["demo_only"] is True
    assert other_customer.status_code == 404
    assert other_shop.status_code == 404
    assert demo_b_own.status_code == 200
    assert demo_b_own.json()["tenant_id"] == "demo-b"
    assert approver.status_code == 200
    assert logistics.json()["tracking_number"] == "MOCK-2003"
    assert adapter.calls == [("logistics", "2003")]


def test_ecommerce_endpoints_require_identity_and_keep_platform_errors_safe(commerce_client, monkeypatch):
    client, _ = commerce_client
    assert client.get("/ecommerce/orders/2003").status_code == 401

    unavailable = FakeShopAdapter(unavailable=True)
    monkeypatch.setattr(main, "_new_mock_shop_adapter", lambda: unavailable)
    response = client.get("/ecommerce/orders/2003", headers=auth())
    assert response.status_code == 503
    assert "hidden detail" not in response.text


def test_aftersale_requires_requester_confirmation_and_eligibility(commerce_client):
    client, adapter = commerce_client
    path = "/ecommerce/orders/2003/aftersales"
    payload = {"reason": "质量问题（虚构）", "idempotency_key": "request-key-2003-01"}

    unconfirmed = client.post(path, headers=auth(), json=payload)
    approver = client.post(path, headers=auth("demo-a-approver-local-token"), json={**payload, "confirmed": True})
    created = client.post(path, headers=auth(), json={**payload, "confirmed": True})

    assert unconfirmed.status_code == 409
    assert approver.status_code == 403
    assert created.status_code == 200
    assert created.json()["status"] == "pending_demo"
    assert created.json()["demo_only"] is True
    assert "不代表已审批" in created.json()["message"]
    assert [call[0] for call in adapter.calls] == ["eligibility", "create"]


def test_aftersale_request_is_idempotent_scoped_and_queryable(commerce_client):
    client, adapter = commerce_client
    path = "/ecommerce/orders/2003/aftersales"
    payload = {"reason": "质量问题（虚构）", "idempotency_key": "request-key-2003-02", "confirmed": True}
    first = client.post(path, headers=auth(), json=payload)
    retry = client.post(path, headers=auth(), json=payload)
    conflict = client.post(path, headers=auth(), json={**payload, "reason": "changed"})
    status = client.get(f"/ecommerce/aftersales/{first.json()['request_id']}", headers=auth())
    foreign = client.get(f"/ecommerce/aftersales/{first.json()['request_id']}", headers=auth("legacy-demo-local-token"))

    assert first.status_code == retry.status_code == 200
    assert first.json()["request_id"] == retry.json()["request_id"]
    assert sum(call[0] == "create" for call in adapter.calls) == 1
    assert conflict.status_code == 409
    assert status.json()["status"] == "pending_demo"
    assert foreign.status_code == 404


def test_aftersale_does_not_submit_when_order_is_not_authorized(commerce_client):
    client, adapter = commerce_client
    response = client.post(
        "/ecommerce/orders/2004/aftersales", headers=auth(),
        json={"reason": "质量问题", "idempotency_key": "request-key-2004-01", "confirmed": True},
    )
    assert response.status_code == 404
    assert not adapter.calls


def test_langgraph_routes_mockshop_order_and_logistics_to_adapter_tools(commerce_client, monkeypatch):
    client, adapter = commerce_client
    monkeypatch.setattr("support_agent.agent.nodes.create_mock_shop_adapter", lambda: adapter)

    order = client.post("/chat", headers=auth(), json={"question": "查询平台订单2003状态"})
    logistics = client.post("/chat", headers=auth(), json={"question": "查询平台订单2003物流到哪了"})

    assert order.status_code == 200
    assert order.json()["intent"] == "mockshop_order_lookup"
    assert order.json()["platform_order"]["status"] == "delivered"
    assert logistics.json()["intent"] == "mockshop_logistics_lookup"
    assert logistics.json()["platform_logistics"]["tracking_number"] == "MOCK-2003"


def test_langgraph_checks_demo_eligibility_then_policy_without_submitting(monkeypatch, commerce_client):
    from support_agent.agent import nodes

    client, adapter = commerce_client
    monkeypatch.setattr(nodes, "create_mock_shop_adapter", lambda: adapter)
    monkeypatch.setattr(
        nodes, "create_siliconflow_embeddings",
        lambda settings: (_ for _ in ()).throw(RuntimeError("offline test: no model call")),
    )

    response = client.post(
        "/chat", headers=auth(),
        json={"question": "我的平台订单2003有质量问题，我想退货"},
    )
    result = response.json()

    assert response.status_code == 200
    assert result["intent"] == "mockshop_aftersale_check"
    assert result["platform_order"]["order_id"] == "2003"
    assert result["aftersale_eligibility"]["eligible"] is True
    assert "符合当前 MockShop 演示资格规则" in result["answer"]
    assert "不等于申请已提交" in result["answer"]
    assert [call[0] for call in adapter.calls] == ["eligibility"]
