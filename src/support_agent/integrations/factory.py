"""Construct the configured demo adapter at API/graph boundaries."""

from support_agent.config import Settings, get_settings
from support_agent.integrations.mock_shop import MockShopAdapter


def create_mock_shop_adapter(settings: Settings | None = None) -> MockShopAdapter:
    settings = settings or get_settings()
    return MockShopAdapter(
        base_url=settings.mock_shop_api_base_url,
        service_key=settings.mock_shop_api_key,
        timeout_seconds=settings.logistics_timeout_seconds,
    )
