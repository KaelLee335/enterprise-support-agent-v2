"""Typed HTTP client for the local, fictional logistics service."""

from __future__ import annotations

from pydantic import BaseModel, Field
import httpx

from support_agent.config import Settings, get_settings


class TrackingEvent(BaseModel):
    time: str
    status: str
    location: str


class Shipment(BaseModel):
    order_id: str
    tracking_number: str
    status: str
    estimated_delivery: str | None = None
    events: list[TrackingEvent] = Field(default_factory=list)
    demo_only: bool = True


def fetch_shipment(order_id: str, settings: Settings | None = None) -> Shipment:
    """Call the configured demo logistics endpoint and validate its JSON contract."""
    settings = settings or get_settings()
    with httpx.Client(
        base_url=settings.logistics_api_base_url,
        headers={"X-Demo-Service-Key": settings.logistics_api_key},
        timeout=settings.logistics_timeout_seconds,
    ) as client:
        response = client.get(f"/shipments/{order_id}")
        response.raise_for_status()
        return Shipment.model_validate(response.json())
