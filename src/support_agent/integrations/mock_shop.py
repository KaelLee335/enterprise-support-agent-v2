"""Typed HTTP client and mapping adapter for the fictional MockShop provider."""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field, ValidationError

from support_agent.integrations.errors import (
    IntegrationConflict,
    IntegrationInvalidResponse,
    IntegrationNotFound,
    IntegrationProtocolError,
    IntegrationRejected,
    IntegrationUnauthorized,
    IntegrationUnavailable,
)

from support_agent.integrations.models import (
    AftersaleApplication,
    AftersaleEligibility,
    LogisticsInfo,
    PlatformOrder,
)


class MockShopOrder(BaseModel):
    order_id: str
    shop_id: str
    customer_id: str
    product_name: str
    quantity: int
    platform_status: str
    returnable: bool
    amount_cents: int
    is_demo: bool = True


class MockShopOrderScope(BaseModel):
    order_id: str
    shop_id: str
    customer_id: str
    is_demo: bool = True


class MockShopLogistics(BaseModel):
    order_id: str
    tracking_no: str | None = None
    platform_status: str
    events: list[dict[str, str]] = Field(default_factory=list)
    is_demo: bool = True


class MockShopAfterSale(BaseModel):
    aftersale_id: str
    order_id: str
    platform_status: str
    reason: str
    is_demo: bool = True


def normalize_order_status(status: str) -> str:
    mapping = {
        "WAIT_SELLER_SEND_GOODS": "pending_shipment",
        "WAIT_BUYER_RECEIVE": "shipped",
        "TRADE_SUCCESS": "delivered",
        "AFTERSALE_PROCESSING": "aftersale_pending",
        "REFUND_SUCCESS": "refunded",
    }
    try:
        return mapping[status]
    except KeyError as exc:
        raise IntegrationProtocolError("Unsupported MockShop order status") from exc


class MockShopAdapter:
    platform_name = "mock-shop"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8092",
        service_key: str = "demo-shop-local-key",
        timeout_seconds: float = 3.0,
        transport: httpx.BaseTransport | None = None,
        tenant_by_store: dict[str, str] | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-Demo-Platform-Key": service_key},
            timeout=timeout_seconds,
            transport=transport,
        )
        self._tenant_by_store = tenant_by_store or {
            "shop-demo-a": "demo-a",
            "shop-demo-b": "demo-b",
        }

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        try:
            response = self._client.request(method, path, **kwargs)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise IntegrationUnavailable("MockShop request timed out or could not connect") from exc
        if response.status_code == 404:
            raise IntegrationNotFound("MockShop resource not found")
        if response.status_code in {401, 403}:
            raise IntegrationUnauthorized("MockShop rejected service authentication")
        if response.status_code == 409:
            raise IntegrationConflict("MockShop rejected a conflicting operation")
        if response.status_code == 422:
            raise IntegrationRejected("MockShop rejected the requested operation")
        if response.is_error:
            raise IntegrationUnavailable("MockShop returned a service error")
        try:
            payload = response.json()
        except ValueError as exc:
            raise IntegrationInvalidResponse("MockShop response was not valid JSON") from exc
        if not isinstance(payload, dict):
            raise IntegrationInvalidResponse("MockShop response was not a JSON object")
        return payload

    @staticmethod
    def _validate(model: type[BaseModel], payload: dict):
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise IntegrationInvalidResponse("MockShop response did not match its schema") from exc

    @staticmethod
    def _map_status(status: str) -> str:
        return normalize_order_status(status)

    def get_order(self, order_id: str) -> PlatformOrder:
        raw = self._validate(MockShopOrder, self._request("GET", f"/mock-shop/orders/{order_id}"))
        tenant_id = self._tenant_by_store.get(raw.shop_id)
        if tenant_id is None:
            raise IntegrationProtocolError("MockShop store has no demo tenant mapping")
        return PlatformOrder(
            order_id=raw.order_id, platform=self.platform_name, store_id=raw.shop_id,
            tenant_id=tenant_id,
            customer_id=raw.customer_id, product_name=raw.product_name,
            quantity=raw.quantity, status=self._map_status(raw.platform_status),
            returnable=raw.returnable, amount_cents=raw.amount_cents, demo_only=True,
        )

    def get_order_scope(self, order_id: str) -> MockShopOrderScope:
        return self._validate(
            MockShopOrderScope,
            self._request("GET", f"/mock-shop/orders/{order_id}/scope"),
        )

    def get_logistics(self, order_id: str) -> LogisticsInfo:
        raw = self._validate(MockShopLogistics, self._request("GET", f"/mock-shop/orders/{order_id}/logistics"))
        status = {"NOT_SHIPPED": "未发货", "IN_TRANSIT": "运输中", "DELIVERED": "已签收"}.get(raw.platform_status)
        if status is None:
            raise IntegrationProtocolError("Unsupported MockShop logistics status")
        return LogisticsInfo(order_id=raw.order_id, tracking_number=raw.tracking_no, status=status, events=raw.events, demo_only=True)

    def check_aftersale_eligibility(self, order_id: str, reason: str) -> AftersaleEligibility:
        payload = self._request("GET", f"/mock-shop/orders/{order_id}/aftersale-eligibility")
        return AftersaleEligibility(
            order_id=payload["order_id"], eligible=bool(payload["eligible"]),
            reason_code=payload["reason_code"], explanation=payload["message"], demo_only=True,
        )

    def create_aftersale(self, order_id: str, reason: str, idempotency_key: str) -> AftersaleApplication:
        raw = self._validate(
            MockShopAfterSale,
            self._request(
                "POST", f"/mock-shop/orders/{order_id}/aftersales",
                json={"reason": reason, "idempotency_key": idempotency_key},
            ),
        )
        status = {"WAIT_REVIEW": "pending_demo", "APPROVED": "approved_demo", "REJECTED": "rejected_demo", "CLOSED": "closed_demo"}.get(raw.platform_status)
        if status is None:
            raise IntegrationProtocolError("Unsupported MockShop aftersale status")
        return AftersaleApplication(aftersale_id=raw.aftersale_id, order_id=raw.order_id, status=status, message="仅创建了 MockShop 演示售后申请；未执行退款或退货。", demo_only=True)

    def get_aftersale_status(self, aftersale_id: str) -> AftersaleApplication:
        raw = self._validate(MockShopAfterSale, self._request("GET", f"/mock-shop/aftersales/{aftersale_id}"))
        status = {"WAIT_REVIEW": "pending_demo", "APPROVED": "approved_demo", "REJECTED": "rejected_demo", "CLOSED": "closed_demo"}.get(raw.platform_status)
        if status is None:
            raise IntegrationProtocolError("Unsupported MockShop aftersale status")
        return AftersaleApplication(aftersale_id=raw.aftersale_id, order_id=raw.order_id, status=status, message="MockShop 演示状态；不表示已退款。", demo_only=True)

    def get_aftersale_scope(self, aftersale_id: str) -> str:
        payload = self._request("GET", f"/mock-shop/aftersales/{aftersale_id}/scope")
        return str(payload["order_id"])
