import json
import sqlite3
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest

from support_agent.db import (
    assign_approval_task,
    create_approval_task,
    create_agent_run,
    decide_approval_task,
    delete_agent_run,
    fetch_agent_run,
    fetch_order,
    initialize_database,
    update_agent_run,
)


def test_initialization_imports_v1_and_fixed_order(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": [{
        "order_id": "OLD-1", "product": "V1 item", "quantity": 1,
        "amount_cents": 100, "currency": "CNY", "status": "已完成",
        "is_demo": True,
    }]}), encoding="utf-8")
    db_path = tmp_path / "test.db"

    initialize_database(db_path, seed)

    customer_a = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a", role="customer", customer_id="customer-demo-a")
    old_order = fetch_order(db_path, "OLD-1", SimpleNamespace(tenant_id="legacy-demo", user_id="user-legacy-demo", role="customer", customer_id="customer-legacy-unmapped"))
    # The legacy seed has no verified owner, so it must remain inaccessible.
    assert old_order is None

    fixed_order = fetch_order(db_path, "1001", customer_a)
    assert fixed_order is not None
    assert fixed_order["is_customized"] == 1
    assert fixed_order["received_date"] == "2026-11-01"
    assert fixed_order["feedback_date"] == "2026-11-11"


def test_order_query_is_scoped_to_tenant(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "test.db"
    initialize_database(db_path, seed)

    assert fetch_order(db_path, "1001", SimpleNamespace(tenant_id="legacy-demo", user_id="user-legacy-demo", role="customer", customer_id="customer-legacy-unmapped")) is None
    assert fetch_order(db_path, "1001", SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-approver", role="approver")) is None


def test_seed_is_idempotent(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "test.db"
    initialize_database(db_path, seed)
    initialize_database(db_path, seed)

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 1


def test_initialize_adds_aftersale_audit_columns_without_backfilling_legacy_rows(tmp_path):
    db_path = tmp_path / "legacy.db"
    seed = tmp_path / "orders.json"
    seed.write_text('{"orders": []}', encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE tenants (tenant_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
                                  is_demo INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE demo_users (user_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL,
                                     display_name TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, customer_id TEXT,
                product TEXT NOT NULL, product_type TEXT, is_customized INTEGER NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 1, amount_cents INTEGER,
                currency TEXT NOT NULL DEFAULT 'CNY', status TEXT NOT NULL,
                created_date TEXT, paid_date TEXT, shipped_date TEXT, received_date TEXT,
                feedback_date TEXT, issue_description TEXT, refund_started_date TEXT,
                refund_completed_date TEXT, is_demo INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE aftersale_requests (
                request_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
                order_id TEXT NOT NULL, platform TEXT NOT NULL, platform_aftersale_id TEXT,
                reason TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            INSERT INTO aftersale_requests VALUES
                ('old-request','legacy-demo','user-legacy-demo','OLD-1','mock-shop',NULL,
                 'old reason','old-key','pending_demo','2026-01-01','2026-01-01');
        """)

    initialize_database(db_path, seed)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        record = connection.execute(
            "SELECT user_id, actor_id, customer_id FROM aftersale_requests WHERE request_id='old-request'"
        ).fetchone()
    assert record["user_id"] == "user-legacy-demo"
    assert record["actor_id"] is None
    assert record["customer_id"] is None


def test_agent_run_create_read_update_delete_is_user_and_tenant_scoped(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "runs.db"
    initialize_database(db_path, seed)

    create_agent_run(db_path, "run-1", "trace-1", "user-demo-a", "demo-a")
    owner = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a")
    other = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-b")
    foreign = SimpleNamespace(tenant_id="legacy-demo", user_id="user-legacy-demo")
    assert fetch_agent_run(db_path, "run-1", foreign) is None
    assert fetch_agent_run(db_path, "run-1", other) is None
    assert update_agent_run(db_path, "run-1", foreign, status="failed") is False
    assert update_agent_run(
        db_path, "run-1", owner, status="completed", intent="order_lookup"
    ) is True
    run = fetch_agent_run(db_path, "run-1", owner)
    assert run["status"] == "completed"
    assert run["intent"] == "order_lookup"
    assert delete_agent_run(db_path, "run-1", "legacy-demo") is False
    assert delete_agent_run(db_path, "run-1", "demo-a") is True
    assert fetch_agent_run(db_path, "run-1", owner) is None


def test_role_scoped_orders_service_grants_and_approver_minimum_scope(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text('{"orders": []}', encoding="utf-8")
    db_path = tmp_path / "roles.db"
    initialize_database(db_path, seed)
    customer = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a", role="customer", customer_id="customer-demo-a")
    service = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-service", role="service", customer_id=None)
    approver = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-approver", role="approver", customer_id=None)
    admin = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-admin", role="admin", customer_id=None)
    assert fetch_order(db_path, "1001", customer) is not None
    assert fetch_order(db_path, "1001", service) is not None
    assert fetch_order(db_path, "1001", approver) is None
    assert fetch_order(db_path, "1001", admin) is None


def test_approval_assignment_is_atomic_assignee_scoped_and_self_approval_denied(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text('{"orders": []}', encoding="utf-8")
    db_path = tmp_path / "approval.db"
    initialize_database(db_path, seed)
    customer = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a", role="customer")
    first_approver = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-approver", role="approver")
    second_approver = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-approver-alt", role="approver")
    admin = SimpleNamespace(tenant_id="demo-a", user_id="user-demo-a-admin", role="admin")
    task = create_approval_task(
        db_path, task_id="task-1", tenant_id="demo-a", order_id="1001",
        customer_id="customer-demo-a", requester_id="user-demo-a", actor_id="user-demo-a",
        approver_id=first_approver.user_id, thread_id="thread-1",
    )
    assert task["status"] == "pending"
    assert decide_approval_task(db_path, "task-1", second_approver, approved=True) is None
    assert assign_approval_task(db_path, "task-1", admin, second_approver.user_id)
    result = decide_approval_task(db_path, "task-1", second_approver, approved=True)
    assert result["status"] == "approved_demo"
    assert result["decision_by"] == second_approver.user_id
    assert decide_approval_task(db_path, "task-1", second_approver, approved=False) is None
    assert not assign_approval_task(db_path, "task-1", admin, customer.user_id)

    with pytest.raises((PermissionError, sqlite3.IntegrityError)):
        create_approval_task(
            db_path, task_id="task-self", tenant_id="demo-a", order_id="1001",
            customer_id="customer-demo-a", requester_id=first_approver.user_id,
            actor_id=first_approver.user_id, approver_id=first_approver.user_id,
            thread_id="thread-self",
        )


def test_concurrent_approval_decisions_only_consume_pending_once(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text('{"orders": []}', encoding="utf-8")
    db_path = tmp_path / "approval-race.db"
    initialize_database(db_path, seed)
    create_approval_task(
        db_path, task_id="task-race", tenant_id="demo-a", order_id="1001",
        customer_id="customer-demo-a", requester_id="user-demo-a", actor_id="user-demo-a",
        approver_id="user-demo-a-approver", thread_id="thread-race",
    )
    approver = SimpleNamespace(
        tenant_id="demo-a", user_id="user-demo-a-approver", role="approver"
    )
    barrier = Barrier(2)

    def decide(approved):
        barrier.wait()
        return decide_approval_task(db_path, "task-race", approver, approved=approved)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(decide, (True, False)))
    assert sum(result is not None for result in results) == 1
