import json
import logging
import sqlite3
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
"""


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
            connection.executemany(
                "INSERT OR IGNORE INTO tenants (tenant_id, display_name, is_demo) VALUES (?, ?, 1)",
                [("legacy-demo", "V1 imported demo tenant"), ("demo-a", "Fixed V2 demo tenant")],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO demo_users (user_id, tenant_id, display_name, is_demo) VALUES (?, ?, ?, 1)",
                [
                    ("user-demo-a", "demo-a", "Demo Customer A"),
                    ("user-legacy-demo", "legacy-demo", "Legacy Demo User"),
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
                "order_id": "1001",
                "tenant_id": "demo-a",
                "customer_id": "demo-a",
                "product": "定制商品",
                "product_type": "customized",
                "is_customized": True,
                "quantity": 1,
                "amount_cents": None,
                "currency": "CNY",
                "status": "已完成",
                "created_date": "2026-11-01",
                "paid_date": "2026-11-01",
                "shipped_date": None,
                "received_date": "2026-11-01",
                "feedback_date": "2026-11-11",
                "issue_description": "质量问题",
                "refund_started_date": None,
                "refund_completed_date": None,
                "is_demo": True,
            })


def fetch_order(database_path: Path, order_id: str, tenant_id: str) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            "SELECT * FROM orders WHERE order_id = ? AND tenant_id = ?",
            (order_id, tenant_id),
        ).fetchone()
    return dict(row) if row else None


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
    tenant_id: str,
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
                   error_type = ?, finished_at = ? WHERE run_id = ? AND tenant_id = ?""",
                (status, intent, error_type, finished_at, run_id, tenant_id),
            )
    return cursor.rowcount == 1


def fetch_agent_run(
    database_path: Path, run_id: str, tenant_id: str
) -> dict[str, Any] | None:
    with closing(connect(database_path)) as connection:
        row = connection.execute(
            "SELECT * FROM agent_runs WHERE run_id = ? AND tenant_id = ?",
            (run_id, tenant_id),
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
