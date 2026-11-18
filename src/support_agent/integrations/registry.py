"""Small explicit adapter registry; no plugin framework is needed for one demo."""

from support_agent.integrations.base import ECommerceAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ECommerceAdapter] = {}

    def register(self, adapter: ECommerceAdapter) -> None:
        name = adapter.platform_name.strip().lower()
        if not name:
            raise ValueError("platform_name must not be empty")
        if name in self._adapters:
            raise ValueError(f"adapter already registered: {name}")
        self._adapters[name] = adapter

    def get(self, platform_name: str) -> ECommerceAdapter:
        try:
            return self._adapters[platform_name.strip().lower()]
        except KeyError as exc:
            raise LookupError(f"unsupported demo platform: {platform_name}") from exc
