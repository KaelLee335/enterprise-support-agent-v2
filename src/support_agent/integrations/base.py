"""The stable business-facing contract implemented by each platform adapter."""

from typing import Protocol

from support_agent.integrations.models import (
    AftersaleApplication,
    AftersaleEligibility,
    LogisticsInfo,
    PlatformOrder,
)


class ECommerceAdapter(Protocol):
    platform_name: str

    def get_order(self, order_id: str) -> PlatformOrder: ...

    def get_logistics(self, order_id: str) -> LogisticsInfo: ...

    def check_aftersale_eligibility(
        self, order_id: str, reason: str
    ) -> AftersaleEligibility: ...

    def create_aftersale(
        self, order_id: str, reason: str, idempotency_key: str
    ) -> AftersaleApplication: ...

    def get_aftersale_status(self, aftersale_id: str) -> AftersaleApplication: ...
