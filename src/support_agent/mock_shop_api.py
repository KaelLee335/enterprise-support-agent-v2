"""Standalone fictional MockShop API used to exercise the integration boundary."""

from __future__ import annotations

import hmac
import os
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class ShopOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: str
    shop_id: str
    customer_id: str
    product_name: str
    quantity: int = Field(ge=1)
    platform_status: str
    returnable: bool
    amount_cents: int = Field(ge=0)
    is_demo: bool = True


class ShopLogistics(BaseModel):
    order_id: str
    tracking_no: str | None = None
    platform_status: str
    events: list[dict[str, str]] = Field(default_factory=list)
    is_demo: bool = True


class ShopAfterSaleCreate(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)


class ShopAfterSale(BaseModel):
    aftersale_id: str
    order_id: str
    platform_status: str
    reason: str
    is_demo: bool = True


class MockShopRepository:
    """Process-local fixture repository; persistence is added in a later phase."""

    def __init__(self) -> None:
        self.orders = {
            "2001": ShopOrder(order_id="2001", shop_id="shop-demo-a", customer_id="customer-demo-a", product_name="演示水杯", quantity=1, platform_status="WAIT_SELLER_SEND_GOODS", returnable=True, amount_cents=5900),
            "2002": ShopOrder(order_id="2002", shop_id="shop-demo-a", customer_id="customer-demo-a", product_name="演示背包", quantity=1, platform_status="WAIT_BUYER_RECEIVE", returnable=True, amount_cents=12900),
            "2003": ShopOrder(order_id="2003", shop_id="shop-demo-a", customer_id="customer-demo-a", product_name="演示耳机", quantity=1, platform_status="TRADE_SUCCESS", returnable=True, amount_cents=19900),
            "2004": ShopOrder(order_id="2004", shop_id="shop-demo-a", customer_id="customer-demo-b", product_name="演示键盘", quantity=1, platform_status="AFTERSALE_PROCESSING", returnable=True, amount_cents=25900),
            "2005": ShopOrder(order_id="2005", shop_id="shop-demo-a", customer_id="customer-demo-b", product_name="演示鼠标", quantity=1, platform_status="REFUND_SUCCESS", returnable=True, amount_cents=8900),
            "2006": ShopOrder(order_id="2006", shop_id="shop-demo-b", customer_id="customer-demo-c", product_name="定制演示商品", quantity=1, platform_status="TRADE_SUCCESS", returnable=False, amount_cents=9900),
        }
        self.logistics = {
            "2001": ShopLogistics(order_id="2001", platform_status="NOT_SHIPPED"),
            "2002": ShopLogistics(order_id="2002", tracking_no="MOCK-2002", platform_status="IN_TRANSIT", events=[{"time": "2026-11-17T08:30:00+08:00", "status": "IN_TRANSIT", "location": "虚构演示分拨中心"}]),
            "2003": ShopLogistics(order_id="2003", tracking_no="MOCK-2003", platform_status="DELIVERED", events=[{"time": "2026-11-16T14:05:00+08:00", "status": "DELIVERED", "location": "虚构演示收货站"}]),
        }
        self.aftersales: dict[str, ShopAfterSale] = {}
        self.idempotency: dict[str, tuple[str, str]] = {}


def create_mock_shop_app(
    repository: MockShopRepository | None = None,
    service_key: str | None = None,
) -> FastAPI:
    repo = repository or MockShopRepository()
    service_key = service_key or os.getenv("MOCK_SHOP_API_KEY", "demo-shop-local-key")
    app = FastAPI(title="Fictional MockShop API", version="0.1.0")

    def authenticate(key: str | None) -> None:
        if key is None or not hmac.compare_digest(key, service_key):
            raise HTTPException(status_code=401, detail="Demo platform key required")

    def order_or_404(order_id: str) -> ShopOrder:
        order = repo.orders.get(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/mock-shop/orders/{order_id}", response_model=ShopOrder)
    def get_order(order_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        return order_or_404(order_id)

    @app.get("/mock-shop/orders/{order_id}/scope")
    def get_order_scope(order_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        """Return only identifiers needed for caller authorization before details."""
        authenticate(service_key_header)
        order = order_or_404(order_id)
        return {"order_id": order.order_id, "shop_id": order.shop_id,
                "customer_id": order.customer_id, "is_demo": order.is_demo}

    @app.get("/mock-shop/orders/{order_id}/logistics", response_model=ShopLogistics)
    def get_logistics(order_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        order_or_404(order_id)
        info = repo.logistics.get(order_id)
        if info is None:
            raise HTTPException(status_code=404, detail="Logistics not found")
        return info

    @app.get("/mock-shop/orders/{order_id}/aftersale-eligibility")
    def check_eligibility(order_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        order = order_or_404(order_id)
        existing = any(item.order_id == order_id for item in repo.aftersales.values())
        if order.platform_status in {"AFTERSALE_PROCESSING", "REFUND_SUCCESS"} or existing:
            return {"order_id": order_id, "eligible": False, "reason_code": "ALREADY_IN_AFTERSALE", "message": "该演示订单已有售后记录。", "is_demo": True}
        if not order.returnable:
            return {"order_id": order_id, "eligible": False, "reason_code": "NOT_RETURNABLE", "message": "该虚构商品按演示规则不支持退货。", "is_demo": True}
        return {"order_id": order_id, "eligible": True, "reason_code": "ELIGIBLE_DEMO", "message": "符合当前 MockShop 演示资格规则；提交后只创建待处理演示申请。", "is_demo": True}

    @app.post("/mock-shop/orders/{order_id}/aftersales", response_model=ShopAfterSale, status_code=201)
    def create_aftersale(order_id: str, body: ShopAfterSaleCreate, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        order = order_or_404(order_id)
        previous = repo.idempotency.get(body.idempotency_key)
        if previous is not None:
            previous_order, previous_id = previous
            if previous_order != order_id:
                raise HTTPException(status_code=409, detail="Idempotency key already used for another order")
            return repo.aftersales[previous_id]
        existing = any(item.order_id == order_id for item in repo.aftersales.values())
        if existing or order.platform_status in {"AFTERSALE_PROCESSING", "REFUND_SUCCESS"}:
            raise HTTPException(status_code=409, detail="Order already has an aftersale")
        if not order.returnable:
            raise HTTPException(status_code=422, detail="Product is not returnable under demo rules")
        application = ShopAfterSale(aftersale_id=f"AS-{uuid4().hex[:12]}", order_id=order_id, platform_status="WAIT_REVIEW", reason=body.reason)
        repo.aftersales[application.aftersale_id] = application
        repo.idempotency[body.idempotency_key] = (order_id, application.aftersale_id)
        return application

    @app.get("/mock-shop/aftersales/{aftersale_id}", response_model=ShopAfterSale)
    def get_aftersale(aftersale_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        application = repo.aftersales.get(aftersale_id)
        if application is None:
            raise HTTPException(status_code=404, detail="Aftersale not found")
        return application

    @app.get("/mock-shop/aftersales/{aftersale_id}/scope")
    def get_aftersale_scope(aftersale_id: str, service_key_header: str | None = Header(default=None, alias="X-Demo-Platform-Key")):
        authenticate(service_key_header)
        application = repo.aftersales.get(aftersale_id)
        if application is None:
            raise HTTPException(status_code=404, detail="Aftersale not found")
        return {"aftersale_id": application.aftersale_id,
                "order_id": application.order_id, "is_demo": application.is_demo}

    app.state.repository = repo
    return app


app = create_mock_shop_app()
