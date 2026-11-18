"""Provider-independent models consumed by support business logic."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IntegrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    demo_only: Literal[True] = True


class PlatformOrder(IntegrationModel):
    order_id: str
    platform: str
    store_id: str
    tenant_id: str
    customer_id: str
    product_name: str
    quantity: int = Field(ge=1)
    status: Literal["pending_shipment", "shipped", "delivered", "aftersale_pending", "refunded"]
    returnable: bool
    amount_cents: int = Field(ge=0)


class LogisticsInfo(IntegrationModel):
    order_id: str
    tracking_number: str | None = None
    status: str
    events: list[dict[str, str]] = Field(default_factory=list)


class AftersaleEligibility(IntegrationModel):
    order_id: str
    eligible: bool
    reason_code: str
    explanation: str


class AftersaleApplication(IntegrationModel):
    aftersale_id: str
    order_id: str
    status: Literal["pending_demo", "approved_demo", "rejected_demo", "closed_demo"]
    message: str


class AftersaleRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=128)
