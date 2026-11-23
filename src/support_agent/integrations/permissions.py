"""Backend authorization for fictional MockShop orders."""

from pathlib import Path

from support_agent.auth import DemoIdentity
from support_agent.db import fetch_platform_order_state, connect
from support_agent.integrations.errors import IntegrationNotFound
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


def stores_for_tenant(tenant_id: str) -> frozenset[str]:
    """Return the configured demo stores belonging to a trusted tenant scope."""
    return frozenset(_STORES_BY_TENANT.get(tenant_id, set()))


def can_access_order(identity: DemoIdentity, order: PlatformOrder, database_path: Path) -> bool:
    """Authorize by tenant and a persisted customer grant; approvers get no store-wide scope."""
    if identity.tenant_id != order.tenant_id:
        return False
    if order.store_id not in _STORES_BY_TENANT.get(identity.tenant_id, set()):
        return False
    role = "customer" if identity.role == "requester" else identity.role
    with connect(database_path) as connection:
        if role == "customer":
            row = connection.execute(
                """SELECT 1 FROM tenant_users AS u
                   JOIN order_customer_ownership AS o
                     ON o.tenant_id = u.tenant_id AND o.customer_id = u.customer_id
                    AND o.source = 'mock-shop' AND o.store_id = ? AND o.order_id = ? AND o.is_active = 1
                   WHERE u.tenant_id = ? AND u.user_id = ? AND u.role = 'customer'
                     AND u.is_active = 1 AND u.customer_id = ?""",
                (order.store_id, order.order_id, identity.tenant_id, identity.user_id, order.customer_id),
            ).fetchone()
        elif role == "service":
            row = connection.execute(
                """SELECT 1 FROM service_customer_grants AS g
                   JOIN tenant_users AS u ON u.tenant_id = g.tenant_id AND u.user_id = g.service_user_id
                    AND u.role = 'service' AND u.is_active = 1
                   JOIN order_customer_ownership AS o
                     ON o.tenant_id = g.tenant_id AND o.customer_id = g.customer_id
                    AND o.source = 'mock-shop' AND o.store_id = ? AND o.order_id = ? AND o.is_active = 1
                   WHERE g.tenant_id = ? AND g.service_user_id = ? AND g.customer_id = ?
                     AND g.is_active = 1""",
                (order.store_id, order.order_id, identity.tenant_id, identity.user_id, order.customer_id),
            ).fetchone()
        elif role == "approver":
            row = connection.execute(
                """SELECT 1 FROM approval_tasks WHERE tenant_id = ? AND approver_id = ?
                   AND source = 'mock-shop' AND store_id = ? AND order_id = ?
                   AND status = 'pending'""",
                (identity.tenant_id, identity.user_id, order.store_id, order.order_id),
            ).fetchone()
        else:
            row = None
    return row is not None


def get_authorized_platform_order(adapter, order_id: str, identity: DemoIdentity, database_path: Path) -> PlatformOrder:
    """Check minimal scope metadata before fetching the provider's order details."""
    scope = adapter.get_order_scope(order_id)
    tenant_id = tenant_for_store(scope.shop_id)
    if tenant_id is None:
        raise IntegrationNotFound("Order not found for this identity")
    scoped_order = PlatformOrder(
        order_id=scope.order_id, platform=adapter.platform_name, store_id=scope.shop_id,
        tenant_id=tenant_id, customer_id=scope.customer_id, product_name="",
        quantity=1, status="pending_shipment", returnable=False, amount_cents=0,
        demo_only=True,
    )
    if not can_access_order(identity, scoped_order, database_path):
        raise IntegrationNotFound("Order not found for this identity")
    order = adapter.get_order(order_id)
    if (order.tenant_id, order.store_id, order.customer_id) != (
        scoped_order.tenant_id, scoped_order.store_id, scoped_order.customer_id
    ):
        raise IntegrationNotFound("Order scope changed during lookup")
    return order


def apply_webhook_order_state(
    order: PlatformOrder, database_path: Path
) -> PlatformOrder:
    """Overlay the latest verified webhook state for this same scoped platform order."""
    state = fetch_platform_order_state(
        database_path, order.order_id, order.tenant_id, order.store_id
    )
    if state is None:
        return order
    if state["store_id"] != order.store_id or state["customer_id"] != order.customer_id:
        return order
    return order.model_copy(update={"status": normalize_order_status(state["platform_status"])})
