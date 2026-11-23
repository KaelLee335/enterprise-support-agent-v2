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
    fetch_platform_order_state,
    fetch_webhook_event,
    initialize_database,
    process_mockshop_webhook,
    WebhookEventConflict,
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
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1


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


def test_database_upgrade_rebuilds_webhook_tables_and_preserves_rows(tmp_path):
    db_path = tmp_path / "legacy-webhook.db"
    seed_path = tmp_path / "orders.json"
    seed_path.write_text('{"orders": []}', encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE tenants (
                tenant_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                is_demo INTEGER NOT NULL DEFAULT 1
            );
            INSERT INTO tenants VALUES ('demo-a', 'Demo A', 1);
            CREATE TABLE webhook_events (
                platform TEXT NOT NULL, event_id TEXT NOT NULL, event_type TEXT NOT NULL,
                tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id), store_id TEXT NOT NULL,
                order_id TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('processed','rejected')),
                received_at TEXT NOT NULL, PRIMARY KEY (platform, event_id)
            );
            CREATE INDEX idx_webhook_events_tenant ON webhook_events(tenant_id, received_at);
            CREATE TABLE platform_order_states (
                platform TEXT NOT NULL, order_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id), store_id TEXT NOT NULL,
                customer_id TEXT NOT NULL, platform_status TEXT NOT NULL,
                source_event_id TEXT NOT NULL, occurred_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY (platform, order_id)
            );
            INSERT INTO webhook_events VALUES
                ('mock-shop','legacy-event-001','order.shipped','demo-a','shop-a','legacy-order-001','hash','processed','2026-11-20T00:00:00Z');
            INSERT INTO platform_order_states VALUES
                ('mock-shop','legacy-order-001','demo-a','shop-a','customer-a','WAIT_BUYER_RECEIVE','legacy-event-001','2026-11-20T00:00:00Z','2026-11-20T00:00:01Z');
        """)

    initialize_database(db_path, seed_path)
    initialize_database(db_path, seed_path)

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        event_pk = tuple(row[1] for row in sorted(
            (row for row in connection.execute("PRAGMA table_info(webhook_events)") if row[5]),
            key=lambda row: row[5],
        ))
        state_pk = tuple(row[1] for row in sorted(
            (row for row in connection.execute("PRAGMA table_info(platform_order_states)") if row[5]),
            key=lambda row: row[5],
        ))
        assert event_pk == ("platform", "tenant_id", "store_id", "event_id")
        assert state_pk == ("platform", "tenant_id", "store_id", "order_id")
        assert connection.execute("SELECT COUNT(*) FROM webhook_events").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM platform_order_states").fetchone()[0] == 1


def test_database_migration_failure_rolls_back_table_rebuild(tmp_path):
    db_path = tmp_path / "broken-legacy.db"
    seed_path = tmp_path / "orders.json"
    seed_path.write_text('{"orders": []}', encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            CREATE TABLE tenants (
                tenant_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
                is_demo INTEGER NOT NULL DEFAULT 1
            );
            INSERT INTO tenants VALUES ('demo-a', 'Demo A', 1);
            CREATE TABLE webhook_events (
                platform TEXT NOT NULL, event_id TEXT NOT NULL, event_type TEXT NOT NULL,
                tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id), store_id TEXT NOT NULL,
                order_id TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
                status TEXT NOT NULL, received_at TEXT NOT NULL,
                PRIMARY KEY (platform, event_id)
            );
            CREATE TABLE platform_order_states (
                platform TEXT NOT NULL, order_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id), store_id TEXT NOT NULL,
                customer_id TEXT NOT NULL, platform_status TEXT NOT NULL,
                source_event_id TEXT NOT NULL, occurred_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY (platform, order_id)
            );
            INSERT INTO webhook_events VALUES
                ('mock-shop','orphan-event-001','order.shipped','missing-tenant','shop-a','order-a','hash','processed','2026-11-20T00:00:00Z');
        """)

    with pytest.raises(sqlite3.IntegrityError):
        initialize_database(db_path, seed_path)

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM webhook_events").fetchone()[0] == 1
        pk_columns = tuple(row[1] for row in sorted(
            (row for row in connection.execute("PRAGMA table_info(webhook_events)") if row[5]),
            key=lambda row: row[5],
        ))
        assert pk_columns == ("platform", "event_id")
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='webhook_events_v1'"
        ).fetchone()[0] == 0


def test_database_rejects_newer_schema_without_initializing_tables(tmp_path):
    db_path = tmp_path / "future.db"
    seed_path = tmp_path / "orders.json"
    seed_path.write_text('{"orders": []}', encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA user_version = 99")

    with pytest.raises(RuntimeError, match="newer than supported"):
        initialize_database(db_path, seed_path)

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 99
        assert connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        ).fetchone()[0] == 0


def test_webhook_event_and_order_ids_are_store_scoped_and_idempotent(tmp_path):
    seed_path = tmp_path / "orders.json"
    seed_path.write_text('{"orders": []}', encoding="utf-8")
    db_path = tmp_path / "store-scope.db"
    initialize_database(db_path, seed_path)
    common = {
        "event_id": "event-shared-0001",
        "event_type": "order.shipped",
        "tenant_id": "demo-a",
        "order_id": "order-shared-0001",
        "customer_id": "customer-demo-a",
        "occurred_at": "2026-11-20T00:00:00+00:00",
    }
    first, created_first = process_mockshop_webhook(
        db_path, **common, store_id="shop-a-1", platform_status="WAIT_BUYER_RECEIVE",
        payload_sha256="payload-a",
    )
    second, created_second = process_mockshop_webhook(
        db_path, **common, store_id="shop-a-2", platform_status="TRADE_SUCCESS",
        payload_sha256="payload-b",
    )
    duplicate, created_duplicate = process_mockshop_webhook(
        db_path, **common, store_id="shop-a-1", platform_status="WAIT_BUYER_RECEIVE",
        payload_sha256="payload-a",
    )

    assert created_first is True and created_second is True
    assert created_duplicate is False
    assert first["platform_status"] == duplicate["platform_status"]
    assert first["store_id"] == "shop-a-1"
    assert second["store_id"] == "shop-a-2"
    assert fetch_platform_order_state(db_path, common["order_id"], "demo-a", "shop-a-1")["platform_status"] == "WAIT_BUYER_RECEIVE"
    assert fetch_platform_order_state(db_path, common["order_id"], "demo-a", "shop-a-2")["platform_status"] == "TRADE_SUCCESS"
    assert fetch_webhook_event(db_path, common["event_id"], "demo-a", "shop-a-1")["payload_sha256"] == "payload-a"
    assert fetch_webhook_event(db_path, common["event_id"], "demo-a", "shop-a-2")["payload_sha256"] == "payload-b"
    with pytest.raises(WebhookEventConflict):
        process_mockshop_webhook(
            db_path, **common, store_id="shop-a-1", platform_status="TRADE_SUCCESS",
            payload_sha256="conflicting-payload",
        )
