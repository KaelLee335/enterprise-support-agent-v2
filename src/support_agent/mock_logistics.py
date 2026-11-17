"""Local-only mock service with fictional tracking events."""

import hmac
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv()
app = FastAPI(title="Fictional Logistics API", version="0.1.0")
SERVICE_KEY = os.getenv("MOCK_LOGISTICS_API_KEY", "demo-logistics-local-key")

_SHIPMENTS = {
    "1001": {
        "order_id": "1001",
        "tracking_number": "DEMO-SHIP-1001",
        "status": "已签收",
        "estimated_delivery": None,
        "events": [
            {"time": "2026-11-15 09:20", "status": "运输中", "location": "杭州演示分拨中心"},
            {"time": "2026-11-16 14:05", "status": "已签收", "location": "虚构收货站"},
        ],
        "demo_only": True,
    },
    "1002": {
        "order_id": "1002",
        "tracking_number": "DEMO-SHIP-1002",
        "status": "运输中",
        "estimated_delivery": "2026-11-19",
        "events": [
            {"time": "2026-11-17 08:30", "status": "运输中", "location": "苏州演示分拨中心"},
        ],
        "demo_only": True,
    },
}


class ShipmentResponse(BaseModel):
    order_id: str
    tracking_number: str
    status: str
    estimated_delivery: str | None = None
    events: list[dict[str, str]]
    demo_only: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/shipments/{order_id}", response_model=ShipmentResponse)
def get_shipment(
    order_id: str,
    service_key: str | None = Header(default=None, alias="X-Demo-Service-Key"),
) -> ShipmentResponse:
    if service_key is None or not hmac.compare_digest(service_key, SERVICE_KEY):
        raise HTTPException(status_code=401, detail="Demo service key required")
    shipment = _SHIPMENTS.get(order_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return ShipmentResponse(**shipment)
