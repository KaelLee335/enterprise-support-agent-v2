"""Backend authorization for fictional MockShop orders."""

from pathlib import Path

from support_agent.auth import DemoIdentity
from support_agent.db import fetch_platform_order_state
from support_agent.integrations.models import PlatformOrder
from support_agent.integrations.mock_shop import normalize_order_status


_CUSTOMER_BY_USER = {
    "user-demo-a": "customer-demo-a",
    "user-demo-b": "customer-demo-c",
}
_STORES_BY_TENANT = {
    "demo-a": {"shop-demo-a"},
    "demo-b": {"shop-demo-b"},
}
_TENANT_BY_STORE = {
    "shop-demo-a": "demo-a",
    "shop-demo-b": "demo-b",
}


def tenant_for_store(store_id: str) -> str | None:
    return _TENANT_BY_STORE.get(store_id)


def can_access_order(identity: DemoIdentity, order: PlatformOrder) -> bool:
    """Requesters can see only their mock customer; approvers see their demo store."""
    if identity.tenant_id != order.tenant_id:
        return False
    if order.store_id not in _STORES_BY_TENANT.get(identity.tenant_id, set()):
        return False
    if identity.role == "approver":
        return True
    return _CUSTOMER_BY_USER.get(identity.user_id) == order.customer_id


def apply_webhook_order_state(
    order: PlatformOrder, database_path: Path
) -> PlatformOrder:
    """Overlay the latest verified webhook state for this same scoped platform order."""
    state = fetch_platform_order_state(database_path, order.order_id, order.tenant_id)
    if state is None:
        return order
    if state["store_id"] != order.store_id or state["customer_id"] != order.customer_id:
        return order
    return order.model_copy(update={"status": normalize_order_status(state["platform_status"])})
