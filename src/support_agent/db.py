import json
import logging
import sqlite3
from uuid import uuid4
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    customer_id TEXT,
    product TEXT NOT NULL,
    product_type TEXT,
    is_customized INTEGER NOT NULL DEFAULT 0 CHECK (is_customized IN (0, 1)),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    amount_cents INTEGER,
    currency TEXT NOT NULL DEFAULT 'CNY',
    status TEXT NOT NULL,
    created_date TEXT,
    paid_date TEXT,
    shipped_date TEXT,
    received_date TEXT,
    feedback_date TEXT,
    issue_description TEXT,
    refund_started_date TEXT,
    refund_completed_date TEXT,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_orders_tenant_id ON orders(tenant_id);

CREATE TABLE IF NOT EXISTS demo_users (
    user_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    display_name TEXT NOT NULL,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_users_tenant_user
    ON demo_users(tenant_id, user_id);

CREATE TABLE IF NOT EXISTS customers (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    customer_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    PRIMARY KEY (tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS tenant_users (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('customer','service','approver','admin')),
    customer_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, user_id),
    FOREIGN KEY (tenant_id, user_id) REFERENCES demo_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, customer_id),
    CHECK ((role = 'customer' AND customer_id IS NOT NULL)
        OR (role <> 'customer' AND customer_id IS NULL))
);

CREATE TABLE IF NOT EXISTS service_customer_grants (
    tenant_id TEXT NOT NULL,
    service_user_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    granted_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, service_user_id, customer_id),
    FOREIGN KEY (tenant_id, service_user_id) REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS order_customer_ownership (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    source TEXT NOT NULL CHECK (source IN ('sqlite','mock-shop')),
    store_id TEXT NOT NULL DEFAULT '',
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    PRIMARY KEY (tenant_id, source, store_id, order_id),
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS approval_tasks (
    task_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    source TEXT NOT NULL CHECK (source IN ('sqlite','mock-shop')),
    store_id TEXT NOT NULL DEFAULT '',
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    thread_id TEXT UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending','approved_demo','rejected','cancelled')),
    decision TEXT CHECK (decision IN ('approve','reject') OR decision IS NULL),
    decision_by TEXT,
    decision_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (tenant_id, customer_id) REFERENCES customers(tenant_id, customer_id),
    FOREIGN KEY (tenant_id, requester_id) REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, actor_id) REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, approver_id) REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, decision_by) REFERENCES tenant_users(tenant_id, user_id),
    CHECK (requester_id <> approver_id AND actor_id <> approver_id)
);
CREATE INDEX IF NOT EXISTS idx_approval_tasks_assignee_status
    ON approval_tasks(tenant_id, approver_id, status, created_at);

CREATE TABLE IF NOT EXISTS approval_task_events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES approval_tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    actor_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('assigned','approved','rejected','cancelled')),
    created_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS agent_runs (
    run_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES demo_users(user_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    intent TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'pending', 'completed', 'failed')),
    error_type TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    is_demo INTEGER NOT NULL DEFAULT 1 CHECK (is_demo IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant ON agent_runs(tenant_id, started_at);

CREATE TABLE IF NOT EXISTS aftersale_requests (
    request_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES demo_users(user_id),
    actor_id TEXT,
    customer_id TEXT,
    order_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_aftersale_id TEXT,
    reason TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('submitting', 'pending_demo', 'failed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (tenant_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_aftersale_requests_scope
    ON aftersale_requests(tenant_id, user_id, order_id);

CREATE TABLE IF NOT EXISTS webhook_events (
    platform TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    store_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processed', 'rejected')),
    received_at TEXT NOT NULL,
    PRIMARY KEY (platform, event_id)
);
CREATE INDEX IF NOT EXISTS idx_webhook_events_tenant
    ON webhook_events(tenant_id, received_at);

CREATE TABLE IF NOT EXISTS platform_order_states (
    platform TEXT NOT NULL,
    order_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    store_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    platform_status TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (platform, order_id)
);
"""


class AftersaleIdempotencyConflict(ValueError):
    """A tenant reused an idempotency key for a different request."""


class WebhookEventConflict(ValueError):
    """An event id was replayed with a different signed payload."""


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _insert_order(connection: sqlite3.Connection, order: dict[str, Any]) -> None:
    columns = (
        "order_id", "tenant_id", "customer_id", "product", "product_type",
        "is_customized", "quantity", "amount_cents", "currency", "status",
        "created_date", "paid_date", "shipped_date", "received_date",
        "feedback_date", "issue_description", "refund_started_date",
        "refund_completed_date", "is_demo",
    )
    values = [order.get(name) for name in columns]
    values[5] = int(bool(values[5]))
    values[-1] = int(bool(values[-1]))
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"INSERT OR IGNORE INTO orders ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )


def initialize_database(database_path: Path, seed_path: Path) -> None:
    """Create the demo schema and idempotently import the V1/fixed demo orders."""
    logger.info("Initializing SQLite database at %s", database_path)
    source = json.loads(seed_path.read_text(encoding="utf-8"))
    with closing(connect(database_path)) as connection:
        with connection:
            connection.executescript(SCHEMA)
            aftersale_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(aftersale_requests)")
            }
            if "actor_id" not in aftersale_columns:
                connection.execute("ALTER TABLE aftersale_requests ADD COLUMN actor_id TEXT")
            if "customer_id" not in aftersale_columns:
                connection.execute("ALTER TABLE aftersale_requests ADD COLUMN customer_id TEXT")
            connection.executemany(
                "INSERT OR IGNORE INTO tenants (tenant_id, display_name, is_demo) VALUES (?, ?, 1)",
                [
                    ("legacy-demo", "V1 imported demo tenant"),
                    ("demo-a", "Fixed V2 demo tenant A"),
                    ("demo-b", "Fixed V2 demo tenant B"),
                ],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO customers (tenant_id, customer_id, display_name) VALUES (?, ?, ?)",
                [
                    ("demo-a", "customer-demo-a", "演示客户 A"),
                    ("demo-a", "customer-demo-b", "演示客户 A2"),
                    ("demo-b", "customer-demo-c", "演示客户 B"),
                    ("legacy-demo", "customer-legacy-unmapped", "历史演示客户（待映射）"),
                ],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO demo_users (user_id, tenant_id, display_name, is_demo) VALUES (?, ?, ?, 1)",
                [
                    ("user-demo-a", "demo-a", "Demo Customer A"),
                    ("user-demo-b", "demo-b", "Demo Customer B"),
                    ("user-demo-a-approver", "demo-a", "Demo Approver A"),
                    ("user-demo-a-approver-alt", "demo-a", "Demo Approver A2"),
                    ("user-demo-a-service", "demo-a", "Demo Service A"),
                    ("user-demo-a-admin", "demo-a", "Demo Admin A"),
                    ("user-demo-b-approver", "demo-b", "Demo Approver B"),
                    ("user-demo-b-admin", "demo-b", "Demo Admin B"),
                    ("user-legacy-demo", "legacy-demo", "Legacy Demo User"),
                ],
            )
            now = datetime.now(timezone.utc).isoformat()
            connection.executemany(
                """INSERT OR IGNORE INTO tenant_users
                   (tenant_id, user_id, role, customer_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    ("demo-a", "user-demo-a", "customer", "customer-demo-a", now),
                    ("demo-b", "user-demo-b", "customer", "customer-demo-c", now),
                    ("demo-a", "user-demo-a-approver", "approver", None, now),
                    ("demo-a", "user-demo-a-approver-alt", "approver", None, now),
                    ("demo-a", "user-demo-a-service", "service", None, now),
                    ("demo-a", "user-demo-a-admin", "admin", None, now),
                    ("demo-b", "user-demo-b-approver", "approver", None, now),
                    ("demo-b", "user-demo-b-admin", "admin", None, now),
                    ("legacy-demo", "user-legacy-demo", "customer", "customer-legacy-unmapped", now),
                ],
            )
            connection.executemany(
                """INSERT OR IGNORE INTO service_customer_grants
                   (tenant_id, service_user_id, customer_id, granted_by, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    ("demo-a", "user-demo-a-service", "customer-demo-a", "user-demo-a-admin", now),
                    ("demo-a", "user-demo-a-service", "customer-demo-b", "user-demo-a-admin", now),
                ],
            )
            for legacy_order in source["orders"]:
                _insert_order(connection, {
                    **legacy_order,
                    "tenant_id": "legacy-demo",
                    "customer_id": None,
                    "product_type": None,
                    "is_customized": False,
                    "feedback_date": None,
                    "issue_description": None,
                })

            _insert_order(connection, {
                "order_id": "1001", "tenant_id": "demo-a", "customer_id": "demo-a",
                "product": "定制商品", "product_type": "customized",
                "is_customized": True, "quantity": 1, "amount_cents": None,
                "currency": "CNY", "status": "已完成",
                "created_date": "2026-11-01", "paid_date": "2026-11-01",
                "shipped_date": None, "received_date": "2026-11-01",
                "feedback_date": "2026-11-11", "issue_description": "质量问题",
                "refund_started_date": None, "refund_completed_date": None,
                "is_demo": True,
            })

            # Ownership mappings are kept separate from source rows. Legacy rows are
            # intentionally not mapped because their customer ownership is unknown.
            connection.execute(
                """INSERT OR IGNORE INTO order_customer_ownership
                   (tenant_id, source, store_id, order_id, customer_id)
                   VALUES ('demo-a', 'sqlite', '', '1001', 'customer-demo-a')"""
            )
            connection.executemany(
                """INSERT OR IGNORE INTO order_customer_ownership
                   (tenant_id, source, store_id, order_id, customer_id)
                   VALUES (?, 'mock-shop', ?, ?, ?)""",
                [
                    ("demo-a", "shop-demo-a", "2001", "customer-demo-a"),
                    ("demo-a", "shop-demo-a", "2002", "customer-demo-a"),
                    ("demo-a", "shop-demo-a", "2003", "customer-demo-a"),
                    ("demo-a", "shop-demo-a", "2004", "customer-demo-b"),
                    ("demo-a", "shop-demo-a", "2005", "customer-demo-b"),
                    ("demo-b", "shop-demo-b", "2006", "customer-demo-c"),
                ],
            )


def fetch_tenant_user(database_path: Path, tenant_id: str, user_id: str) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT tenant_id, user_id, role, customer_id, is_active
               FROM tenant_users WHERE tenant_id = ? AND user_id = ?""",
            (tenant_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def list_tenant_users(database_path: Path, admin: Any) -> list[dict[str, Any]] | None:
    with closing(connect(database_path)) as connection:
        permitted = connection.execute(
            """SELECT 1 FROM tenant_users WHERE tenant_id = ? AND user_id = ?
               AND role = 'admin' AND is_active = 1""",
            (admin.tenant_id, admin.user_id),
        ).fetchone()
        if permitted is None:
            return None
        rows = connection.execute(
            """SELECT user_id, role, customer_id, is_active FROM tenant_users
               WHERE tenant_id = ? ORDER BY user_id""",
            (admin.tenant_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def find_customer_user(database_path: Path, tenant_id: str, customer_id: str) -> str | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT user_id FROM tenant_users WHERE tenant_id = ? AND customer_id = ?
               AND role = 'customer' AND is_active = 1 ORDER BY user_id LIMIT 1""",
            (tenant_id, customer_id),
        ).fetchone()
    return str(row["user_id"]) if row else None


def find_tenant_approver(database_path: Path, tenant_id: str) -> str | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT user_id FROM tenant_users WHERE tenant_id = ? AND role = 'approver'
               AND is_active = 1 ORDER BY user_id LIMIT 1""",
            (tenant_id,),
        ).fetchone()
    return str(row["user_id"]) if row else None


def set_tenant_user_role(
    database_path: Path, admin: Any, user_id: str, role: str,
    customer_id: str | None = None,
) -> bool:
    if role not in {"customer", "service", "approver", "admin"}:
        return False
    if (role == "customer") != bool(customer_id):
        return False
    with closing(connect(database_path)) as connection:
        with connection:
            permitted = connection.execute(
                """SELECT 1 FROM tenant_users WHERE tenant_id = ? AND user_id = ?
                   AND role = 'admin' AND is_active = 1""",
                (admin.tenant_id, admin.user_id),
            ).fetchone()
            if permitted is None:
                return False
            if customer_id is not None and connection.execute(
                "SELECT 1 FROM customers WHERE tenant_id = ? AND customer_id = ? AND is_active = 1",
                (admin.tenant_id, customer_id),
            ).fetchone() is None:
                return False
            if role != "approver" and connection.execute(
                """SELECT 1 FROM approval_tasks WHERE tenant_id = ? AND approver_id = ?
                   AND status = 'pending' LIMIT 1""",
                (admin.tenant_id, user_id),
            ).fetchone() is not None:
                return False
            cursor = connection.execute(
                """UPDATE tenant_users SET role = ?, customer_id = ?
                   WHERE tenant_id = ? AND user_id = ?""",
                (role, customer_id, admin.tenant_id, user_id),
            )
    return cursor.rowcount == 1


def set_service_customer_grant(
    database_path: Path, admin: Any, service_user_id: str,
    customer_id: str, *, allowed: bool,
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            roles = connection.execute(
                """SELECT user_id, role FROM tenant_users WHERE tenant_id = ?
                   AND user_id IN (?, ?) AND is_active = 1""",
                (admin.tenant_id, admin.user_id, service_user_id),
            ).fetchall()
            role_map = {row["user_id"]: row["role"] for row in roles}
            if role_map.get(admin.user_id) != "admin" or role_map.get(service_user_id) != "service":
                return False
            if connection.execute(
                "SELECT 1 FROM customers WHERE tenant_id = ? AND customer_id = ? AND is_active = 1",
                (admin.tenant_id, customer_id),
            ).fetchone() is None:
                return False
            if allowed:
                connection.execute(
                    """INSERT INTO service_customer_grants
                       (tenant_id, service_user_id, customer_id, granted_by, created_at)
                       VALUES (?, ?, ?, ?, ?)
                       ON CONFLICT(tenant_id, service_user_id, customer_id)
                       DO UPDATE SET is_active = 1, granted_by = excluded.granted_by""",
                    (admin.tenant_id, service_user_id, customer_id, admin.user_id, now),
                )
                return True
            cursor = connection.execute(
                """UPDATE service_customer_grants SET is_active = 0
                   WHERE tenant_id = ? AND service_user_id = ? AND customer_id = ?""",
                (admin.tenant_id, service_user_id, customer_id),
            )
    return cursor.rowcount == 1

def fetch_order(database_path: Path, order_id: str, identity: Any) -> dict[str, Any] | None:
    """Return only an order covered by the caller's persisted tenant authorization."""
    role = {"requester": "customer"}.get(identity.role, identity.role)
    with closing(connect(database_path)) as connection:
        if role == "customer" and identity.customer_id:
            row = connection.execute(
                """SELECT o.*, own.customer_id AS owner_customer_id FROM orders AS o
                   JOIN order_customer_ownership AS own
                     ON own.tenant_id = o.tenant_id AND own.order_id = o.order_id
                    AND own.source = 'sqlite' AND own.store_id = '' AND own.is_active = 1
                   JOIN tenant_users AS tu
                     ON tu.tenant_id = o.tenant_id AND tu.user_id = ?
                    AND tu.role = 'customer' AND tu.customer_id = own.customer_id
                    AND tu.is_active = 1
                   WHERE o.order_id = ? AND o.tenant_id = ?""",
                (identity.user_id, order_id, identity.tenant_id),
            ).fetchone()
        elif role == "service":
            row = connection.execute(
                """SELECT o.*, own.customer_id AS owner_customer_id FROM orders AS o
                   JOIN order_customer_ownership AS own
                     ON own.tenant_id = o.tenant_id AND own.order_id = o.order_id
                    AND own.source = 'sqlite' AND own.store_id = '' AND own.is_active = 1
                   JOIN service_customer_grants AS grant
                     ON grant.tenant_id = own.tenant_id AND grant.customer_id = own.customer_id
                    AND grant.service_user_id = ? AND grant.is_active = 1
                   JOIN tenant_users AS tu
                     ON tu.tenant_id = o.tenant_id AND tu.user_id = grant.service_user_id
                    AND tu.role = 'service' AND tu.is_active = 1
                   WHERE o.order_id = ? AND o.tenant_id = ?""",
                (identity.user_id, order_id, identity.tenant_id),
            ).fetchone()
        else:
            row = None
    return dict(row) if row else None


def create_approval_task(
    database_path: Path, *, task_id: str, tenant_id: str, order_id: str,
    customer_id: str, requester_id: str, actor_id: str, approver_id: str,
    thread_id: str,
) -> dict[str, Any]:
    """Persist a demo assignment; caller must have already used a scoped order read."""
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            # Recheck every principal and order relation inside the write transaction.
            principals = connection.execute(
                """SELECT user_id, role, customer_id FROM tenant_users WHERE tenant_id = ?
                   AND user_id IN (?, ?, ?) AND is_active = 1""",
                (tenant_id, requester_id, actor_id, approver_id),
            ).fetchall()
            memberships = {row["user_id"]: dict(row) for row in principals}
            roles = {user_id: row["role"] for user_id, row in memberships.items()}
            if roles.get(approver_id) != "approver":
                raise PermissionError("assigned approver is not active in this tenant")
            if roles.get(actor_id) not in {"customer", "service"}:
                raise PermissionError("only customer or service can request approval")
            if requester_id == approver_id or actor_id == approver_id:
                raise PermissionError("self approval is not allowed")
            requester = memberships.get(requester_id)
            actor = memberships.get(actor_id)
            if requester is None or requester["role"] != "customer" or requester["customer_id"] != customer_id:
                raise PermissionError("requesting customer does not own the requested order")
            if actor["role"] == "customer" and actor["customer_id"] != customer_id:
                raise PermissionError("customer cannot request another customer's approval")
            if actor["role"] == "service":
                grant = connection.execute(
                    """SELECT 1 FROM service_customer_grants WHERE tenant_id = ?
                       AND service_user_id = ? AND customer_id = ? AND is_active = 1""",
                    (tenant_id, actor_id, customer_id),
                ).fetchone()
                if grant is None:
                    raise PermissionError("service user lacks customer grant")
            ownership = connection.execute(
                """SELECT 1 FROM order_customer_ownership WHERE tenant_id = ?
                   AND source = 'sqlite' AND store_id = '' AND order_id = ?
                   AND customer_id = ? AND is_active = 1""",
                (tenant_id, order_id, customer_id),
            ).fetchone()
            if ownership is None:
                raise PermissionError("order ownership is not authorized")
            existing = connection.execute(
                "SELECT * FROM approval_tasks WHERE thread_id = ? AND tenant_id = ?",
                (thread_id, tenant_id),
            ).fetchone()
            if existing:
                return dict(existing)
            connection.execute(
                """INSERT INTO approval_tasks
                   (task_id, tenant_id, source, store_id, order_id, customer_id,
                    requester_id, actor_id, approver_id, thread_id, status,
                    created_at, updated_at)
                   VALUES (?, ?, 'sqlite', '', ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (task_id, tenant_id, order_id, customer_id, requester_id,
                 actor_id, approver_id, thread_id, now, now),
            )
            connection.execute(
                """INSERT INTO approval_task_events
                   (event_id, task_id, tenant_id, actor_id, event_type, created_at)
                   VALUES (?, ?, ?, ?, 'assigned', ?)""",
                (uuid4().hex, task_id, tenant_id, actor_id, now),
            )
            row = connection.execute(
                "SELECT * FROM approval_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
    return dict(row)


def fetch_approval_task_for_identity(
    database_path: Path, thread_id: str, identity: Any
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT t.* FROM approval_tasks AS t
               JOIN tenant_users AS u ON u.tenant_id = t.tenant_id
                AND u.user_id = ? AND u.is_active = 1
               WHERE t.thread_id = ? AND t.tenant_id = ?
                 AND (t.approver_id = ? OR t.requester_id = ? OR t.actor_id = ?)""",
            (identity.user_id, thread_id, identity.tenant_id, identity.user_id,
             identity.user_id, identity.user_id),
        ).fetchone()
    return dict(row) if row else None


def list_assigned_approval_tasks(
    database_path: Path, identity: Any
) -> list[dict[str, Any]]:
    if identity.role != "approver":
        return []
    with closing(connect(database_path)) as connection:
        rows = connection.execute(
            """SELECT t.task_id, t.tenant_id, t.order_id, t.customer_id,
                      t.requester_id, t.actor_id, t.status, t.created_at, t.thread_id
               FROM approval_tasks AS t JOIN tenant_users AS u
                ON u.tenant_id = t.tenant_id AND u.user_id = t.approver_id
                AND u.role = 'approver' AND u.is_active = 1
               WHERE t.tenant_id = ? AND t.approver_id = ? AND t.status = 'pending'
               ORDER BY t.created_at""",
            (identity.tenant_id, identity.user_id),
        ).fetchall()
    return [dict(row) for row in rows]


def decide_approval_task(
    database_path: Path, task_id: str, identity: Any, *, approved: bool
) -> dict[str, Any] | None:
    """Atomically consume one pending task assigned to the current approver."""
    status = "approved_demo" if approved else "rejected"
    decision = "approve" if approved else "reject"
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            row = connection.execute(
                """SELECT t.* FROM approval_tasks AS t JOIN tenant_users AS u
                   ON u.tenant_id = t.tenant_id AND u.user_id = ?
                   AND u.role = 'approver' AND u.is_active = 1
                   WHERE t.task_id = ? AND t.tenant_id = ? AND t.approver_id = ?
                     AND t.status = 'pending' AND t.requester_id <> ? AND t.actor_id <> ?""",
                (identity.user_id, task_id, identity.tenant_id, identity.user_id,
                 identity.user_id, identity.user_id),
            ).fetchone()
            if row is None:
                return None
            cursor = connection.execute(
                """UPDATE approval_tasks SET status = ?, decision = ?, decision_by = ?,
                   decision_at = ?, updated_at = ? WHERE task_id = ? AND tenant_id = ?
                   AND approver_id = ? AND status = 'pending'""",
                (status, decision, identity.user_id, now, now, task_id,
                 identity.tenant_id, identity.user_id),
            )
            if cursor.rowcount != 1:
                return None
            connection.execute(
                """INSERT INTO approval_task_events
                   (event_id, task_id, tenant_id, actor_id, event_type, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (uuid4().hex, task_id, identity.tenant_id, identity.user_id,
                 "approved" if approved else "rejected", now),
            )
            result = connection.execute(
                "SELECT * FROM approval_tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
    return dict(result)


def assign_approval_task(
    database_path: Path, task_id: str, admin: Any, approver_id: str
) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            admin_row = connection.execute(
                """SELECT 1 FROM tenant_users WHERE tenant_id = ? AND user_id = ?
                   AND role = 'admin' AND is_active = 1""",
                (admin.tenant_id, admin.user_id),
            ).fetchone()
            approver = connection.execute(
                """SELECT 1 FROM tenant_users WHERE tenant_id = ? AND user_id = ?
                   AND role = 'approver' AND is_active = 1""",
                (admin.tenant_id, approver_id),
            ).fetchone()
            if admin_row is None or approver is None:
                return False
            cursor = connection.execute(
                """UPDATE approval_tasks SET approver_id = ?, updated_at = ?
                   WHERE task_id = ? AND tenant_id = ? AND status = 'pending'
                     AND requester_id <> ? AND actor_id <> ?""",
                (approver_id, now, task_id, admin.tenant_id, approver_id, approver_id),
            )
            if cursor.rowcount != 1:
                return False
            connection.execute(
                """INSERT INTO approval_task_events
                   (event_id, task_id, tenant_id, actor_id, event_type, created_at, details_json)
                   VALUES (?, ?, ?, ?, 'assigned', ?, ?)""",
                (uuid4().hex, task_id, admin.tenant_id, admin.user_id, now,
                 json.dumps({"approver_id": approver_id})),
            )
    return True


def create_agent_run(
    database_path: Path, run_id: str, trace_id: str, user_id: str, tenant_id: str
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            connection.execute(
                """INSERT INTO agent_runs
                   (run_id, trace_id, user_id, tenant_id, status, started_at)
                   VALUES (?, ?, ?, ?, 'running', ?)""",
                (run_id, trace_id, user_id, tenant_id, now),
            )


def update_agent_run(
    database_path: Path,
    run_id: str,
    identity: Any,
    *,
    status: str,
    intent: str | None = None,
    error_type: str | None = None,
) -> bool:
    if status not in {"running", "pending", "completed", "failed"}:
        raise ValueError("invalid demo run status")
    finished_at = None if status == "running" else datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """UPDATE agent_runs SET status = ?, intent = COALESCE(?, intent),
                   error_type = ?, finished_at = ?
                   WHERE run_id = ? AND tenant_id = ? AND user_id = ?""",
                (status, intent, error_type, finished_at, run_id,
                 identity.tenant_id, identity.user_id),
            )
    return cursor.rowcount == 1


def update_agent_run_system(
    database_path: Path, run_id: str, tenant_id: str, *, status: str,
    intent: str | None = None, error_type: str | None = None,
) -> bool:
    """Trusted workflow callback; never accept identity data from an API payload."""
    if status not in {"running", "pending", "completed", "failed"}:
        raise ValueError("invalid demo run status")
    finished_at = None if status == "running" else datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """UPDATE agent_runs SET status = ?, intent = COALESCE(?, intent),
                   error_type = ?, finished_at = ? WHERE run_id = ? AND tenant_id = ?""",
                (status, intent, error_type, finished_at, run_id, tenant_id),
            )
    return cursor.rowcount == 1


def fetch_agent_run(
    database_path: Path, run_id: str, identity: Any
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            "SELECT * FROM agent_runs WHERE run_id = ? AND tenant_id = ? AND user_id = ?",
            (run_id, identity.tenant_id, identity.user_id),
        ).fetchone()
    return dict(row) if row else None


def delete_agent_run(database_path: Path, run_id: str, tenant_id: str) -> bool:
    """Tenant-scoped cleanup for demo/test runs; never exposed as an API route."""
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM agent_runs WHERE run_id = ? AND tenant_id = ? AND is_demo = 1",
                (run_id, tenant_id),
            )
    return cursor.rowcount == 1


def reserve_aftersale_request(
    database_path: Path,
    *,
    request_id: str,
    tenant_id: str,
    user_id: str,
    actor_id: str,
    customer_id: str,
    order_id: str,
    platform: str,
    reason: str,
    idempotency_key: str,
) -> tuple[dict[str, Any], bool]:
    """Create a tenant-scoped intent once; return (record, created_now)."""
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO aftersale_requests
                   (request_id, tenant_id, user_id, actor_id, customer_id, order_id, platform, reason,
                    idempotency_key, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitting', ?, ?)""",
                (request_id, tenant_id, user_id, actor_id, customer_id, order_id, platform, reason,
                 idempotency_key, now, now),
            )
            created_now = cursor.rowcount == 1
            row = connection.execute(
                """SELECT * FROM aftersale_requests
                   WHERE tenant_id = ? AND idempotency_key = ?""",
                (tenant_id, idempotency_key),
            ).fetchone()
    if row is None:
        raise RuntimeError("aftersale request reservation failed")
    result = dict(row)
    # Older rows predate actor/customer audit columns. Their NULL means
    # "unknown historically", not a conflicting value for a retry.
    strict_fields = {
        "user_id": user_id,
        "order_id": order_id,
        "platform": platform,
        "reason": reason,
    }
    nullable_audit_fields = {
        "actor_id": actor_id,
        "customer_id": customer_id,
    }
    conflicts = any(result[field] != value for field, value in strict_fields.items())
    conflicts = conflicts or any(
        result[field] is not None and result[field] != value
        for field, value in nullable_audit_fields.items()
    )
    if conflicts:
        raise AftersaleIdempotencyConflict("Idempotency key already used for another request")
    return result, created_now


def update_aftersale_request(
    database_path: Path,
    request_id: str,
    identity: Any,
    *,
    status: str,
    platform_aftersale_id: str | None = None,
) -> bool:
    if status not in {"submitting", "pending_demo", "failed"}:
        raise ValueError("invalid demo aftersale status")
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            cursor = connection.execute(
                """UPDATE aftersale_requests SET status = ?,
                   platform_aftersale_id = COALESCE(?, platform_aftersale_id), updated_at = ?
                   WHERE request_id = ? AND tenant_id = ? AND actor_id = ?""",
                (status, platform_aftersale_id, now, request_id,
                 identity.tenant_id, identity.user_id),
            )
    return cursor.rowcount == 1


def fetch_aftersale_request(
    database_path: Path, request_id: str, identity: Any
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT r.* FROM aftersale_requests AS r
               JOIN tenant_users AS u ON u.tenant_id = r.tenant_id
                AND u.user_id = ? AND u.is_active = 1
               WHERE r.request_id = ? AND r.tenant_id = ? AND (
                 r.user_id = ? OR
                 (u.role = 'customer' AND u.customer_id = r.customer_id) OR
                 (u.role = 'service' AND EXISTS (
                    SELECT 1 FROM service_customer_grants AS g
                    WHERE g.tenant_id = r.tenant_id AND g.service_user_id = u.user_id
                      AND g.customer_id = r.customer_id AND g.is_active = 1
                 ))
               )""",
            (identity.user_id, request_id, identity.tenant_id, identity.user_id),
        ).fetchone()
    return dict(row) if row else None


def process_mockshop_webhook(
    database_path: Path,
    *,
    event_id: str,
    event_type: str,
    tenant_id: str,
    store_id: str,
    order_id: str,
    customer_id: str,
    platform_status: str,
    occurred_at: str,
    payload_sha256: str,
) -> tuple[dict[str, Any], bool]:
    """Atomically deduplicate an event and update the latest normalized source state."""
    now = datetime.now(timezone.utc).isoformat()
    with closing(connect(database_path)) as connection:
        with connection:
            existing = connection.execute(
                "SELECT * FROM webhook_events WHERE platform = 'mock-shop' AND event_id = ?",
                (event_id,),
            ).fetchone()
            if existing:
                if existing["payload_sha256"] != payload_sha256:
                    raise WebhookEventConflict("Event id was already used for a different payload")
                state = connection.execute(
                    "SELECT * FROM platform_order_states WHERE platform = 'mock-shop' AND order_id = ?",
                    (order_id,),
                ).fetchone()
                return (dict(state) if state else dict(existing)), False
            connection.execute(
                """INSERT INTO webhook_events
                   (platform, event_id, event_type, tenant_id, store_id, order_id,
                    payload_sha256, status, received_at)
                   VALUES ('mock-shop', ?, ?, ?, ?, ?, ?, 'processed', ?)""",
                (event_id, event_type, tenant_id, store_id, order_id, payload_sha256, now),
            )
            connection.execute(
                """INSERT INTO platform_order_states
                   (platform, order_id, tenant_id, store_id, customer_id,
                    platform_status, source_event_id, occurred_at, updated_at)
                   VALUES ('mock-shop', ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(platform, order_id) DO UPDATE SET
                     tenant_id=excluded.tenant_id, store_id=excluded.store_id,
                     customer_id=excluded.customer_id, platform_status=excluded.platform_status,
                     source_event_id=excluded.source_event_id, occurred_at=excluded.occurred_at,
                     updated_at=excluded.updated_at
                   WHERE excluded.occurred_at >= platform_order_states.occurred_at""",
                (order_id, tenant_id, store_id, customer_id, platform_status,
                 event_id, occurred_at, now),
            )
            state = connection.execute(
                "SELECT * FROM platform_order_states WHERE platform = 'mock-shop' AND order_id = ?",
                (order_id,),
            ).fetchone()
            return dict(state), True


def fetch_platform_order_state(
    database_path: Path, order_id: str, tenant_id: str
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            """SELECT * FROM platform_order_states
               WHERE platform = 'mock-shop' AND order_id = ? AND tenant_id = ?""",
            (order_id, tenant_id),
        ).fetchone()
    return dict(row) if row else None


def fetch_webhook_event(
    database_path: Path, event_id: str, tenant_id: str
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            "SELECT * FROM webhook_events WHERE platform = 'mock-shop' AND event_id = ? AND tenant_id = ?",
            (event_id, tenant_id),
        ).fetchone()
    return dict(row) if row else None
