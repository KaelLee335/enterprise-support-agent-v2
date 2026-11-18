"""Schemas and safe mappings for fictional MockShop webhook events."""

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MockShopWebhookEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=8, max_length=128)
    event_type: Literal[
        "order.created", "order.shipped", "order.delivered",
        "aftersale.status_changed", "refund.status_changed",
    ]
    occurred_at: datetime
    order_id: str = Field(min_length=1, max_length=64)
    shop_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)
    platform_status: str = Field(min_length=1, max_length=64)

    @field_validator("event_id", "order_id", "shop_id", "customer_id")
    @classmethod
    def strip_required_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


def normalized_order_status(event: MockShopWebhookEvent) -> str:
    valid = {
        ("order.created", "WAIT_SELLER_SEND_GOODS"): "pending_shipment",
        ("order.shipped", "WAIT_BUYER_RECEIVE"): "shipped",
        ("order.delivered", "TRADE_SUCCESS"): "delivered",
        ("aftersale.status_changed", "AFTERSALE_PROCESSING"): "aftersale_pending",
        ("refund.status_changed", "REFUND_SUCCESS"): "refunded",
    }
    try:
        return valid[(event.event_type, event.platform_status)]
    except KeyError as exc:
        raise ValueError("event type and platform status do not match") from exc
