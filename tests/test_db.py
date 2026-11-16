import json
import sqlite3

from support_agent.db import (
    create_agent_run,
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

    old_order = fetch_order(db_path, "OLD-1", "legacy-demo")
    assert old_order is not None
    assert old_order["product"] == "V1 item"
    assert old_order["received_date"] is None

    fixed_order = fetch_order(db_path, "1001", "demo-a")
    assert fixed_order is not None
    assert fixed_order["is_customized"] == 1
    assert fixed_order["received_date"] == "2026-11-01"
    assert fixed_order["feedback_date"] == "2026-11-11"


def test_order_query_is_scoped_to_tenant(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "test.db"
    initialize_database(db_path, seed)

    assert fetch_order(db_path, "1001", "legacy-demo") is None


def test_seed_is_idempotent(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "test.db"
    initialize_database(db_path, seed)
    initialize_database(db_path, seed)

    with sqlite3.connect(db_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 1


def test_agent_run_create_read_update_delete_is_tenant_scoped(tmp_path):
    seed = tmp_path / "orders.json"
    seed.write_text(json.dumps({"orders": []}), encoding="utf-8")
    db_path = tmp_path / "runs.db"
    initialize_database(db_path, seed)

    create_agent_run(db_path, "run-1", "trace-1", "user-demo-a", "demo-a")
    assert fetch_agent_run(db_path, "run-1", "legacy-demo") is None
    assert update_agent_run(db_path, "run-1", "legacy-demo", status="failed") is False
    assert update_agent_run(
        db_path, "run-1", "demo-a", status="completed", intent="order_lookup"
    ) is True
    run = fetch_agent_run(db_path, "run-1", "demo-a")
    assert run["status"] == "completed"
    assert run["intent"] == "order_lookup"
    assert delete_agent_run(db_path, "run-1", "legacy-demo") is False
    assert delete_agent_run(db_path, "run-1", "demo-a") is True
    assert fetch_agent_run(db_path, "run-1", "demo-a") is None
