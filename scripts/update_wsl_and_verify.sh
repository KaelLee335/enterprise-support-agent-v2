#!/usr/bin/env bash
# Sync the reviewed V2.1/RAG source and verifier files to WSL, rebuild, and verify.
set -euo pipefail

SOURCE_ROOT="/mnt/d/project_2"
TARGET_ROOT="/opt/project2"

if [[ ! -d "$SOURCE_ROOT" || ! -f "$SOURCE_ROOT/compose.yaml" ]]; then
  echo "Source project not found at $SOURCE_ROOT" >&2
  exit 1
fi
if [[ ! -d "$TARGET_ROOT" || ! -f "$TARGET_ROOT/compose.yaml" ]]; then
  echo "WSL deployment project not found at $TARGET_ROOT" >&2
  exit 1
fi

FILES=(
  "Dockerfile"
  "compose.yaml"
  "pyproject.toml"
  "uv.lock"
  "src/support_agent/main.py"
  "src/support_agent/auth.py"
  "src/support_agent/config.py"
  "src/support_agent/db.py"
  "src/support_agent/schemas.py"
  "src/support_agent/mock_shop_api.py"
  "src/support_agent/logistics.py"
  "src/support_agent/mock_logistics.py"
  "src/support_agent/agent/nodes.py"
  "src/support_agent/agent/graph.py"
  "src/support_agent/agent/state.py"
  "src/support_agent/rag/answer.py"
  "src/support_agent/rag/answer_constraints.py"
  "src/support_agent/rag/evidence_conflicts.py"
  "src/support_agent/rag/retrieval.py"
  "src/support_agent/rag/query_expansion.py"
  "scripts/verify_phase6.sh"
  "scripts/verify_v21.sh"
)

for relative_path in "$SOURCE_ROOT"/src/support_agent/integrations/*.py; do
  [[ -f "$relative_path" ]] || continue
  FILES+=("${relative_path#"$SOURCE_ROOT"/}")
done

for relative_path in "${FILES[@]}"; do
  source_file="$SOURCE_ROOT/$relative_path"
  target_file="$TARGET_ROOT/$relative_path"
  if [[ ! -f "$source_file" ]]; then
    echo "Missing source file: $source_file" >&2
    exit 1
  fi
  install -D -m 0644 -- "$source_file" "$target_file"
  echo "Synced $relative_path"
done

cd "$TARGET_ROOT"
docker compose up --build -d
docker compose ps

ready=0
for attempt in $(seq 1 60); do
  container_id=$(docker compose ps -q support-agent)
  if [[ -n "$container_id" ]]; then
    container_health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")
    status=$(curl -sS --max-time 3 -o /dev/null -w '%{http_code}' http://localhost:8000/health || true)
    if [[ "$container_health" == "healthy" && "$status" == "200" ]]; then
      ready=1
      break
    fi
  fi
  sleep 2
done
if [[ "$ready" != "1" ]]; then
  echo "Service did not become healthy at http://localhost:8000/health" >&2
  docker compose logs --tail=80
  exit 1
fi

echo "Verifying the persistent SQLite schema..."
docker compose exec -T support-agent /app/.venv/bin/python - <<'PY'
import sqlite3

from support_agent.config import get_settings
from support_agent.db import SCHEMA_VERSION

database_path = get_settings().database_path.resolve()
uri = f"{database_path.as_uri()}?mode=ro"
with sqlite3.connect(uri, uri=True) as connection:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    expected = {
        "webhook_events": ("platform", "tenant_id", "store_id", "event_id"),
        "platform_order_states": ("platform", "tenant_id", "store_id", "order_id"),
    }
    actual = {}
    for table in expected:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        actual[table] = tuple(
            row[1]
            for row in sorted(rows, key=lambda row: row[5])
            if row[5]
        )

assert integrity == "ok", f"SQLite integrity check failed: {integrity}"
assert version == SCHEMA_VERSION, (
    f"SQLite schema version is {version}; expected {SCHEMA_VERSION}"
)
for table, primary_key in expected.items():
    assert actual[table] == primary_key, (
        f"{table} primary key is {actual[table]}; expected {primary_key}"
    )
print(f"PASS SQLite integrity and schema version {version}")
print("PASS webhook and order-state tenant/store primary keys")
PY

docker compose exec -T support-agent /app/.venv/bin/python - <<'PY'
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from support_agent.rag.answer import generate_answer_from_evidence
from support_agent.rag.retrieval import RetrievedPolicy
from support_agent.config import get_settings
from support_agent.rag.retrieval import open_configured_policy_store, retrieve_policies

direct_conflict = generate_answer_from_evidence(
    "退款多久到账？",
    evidence=[
        RetrievedPolicy("POL-06", "退款时效", "退款保证24小时内到账。", 0.1),
        RetrievedPolicy("POL-12", "退款时效补充", "退款不保证24小时内到账。", 0.2),
    ],
    chat_model=FakeListChatModel(responses=[]),
)
assert "相反表述" in direct_conflict.answer
assert direct_conflict.citation_check_passed
assert direct_conflict.constraint_ids == ["EXPLICIT_EVIDENCE_CONFLICT"]
print("PASS rag direct-conflict abstention")

scoped_exception = generate_answer_from_evidence(
    "定制商品无理由退货可以吗？",
    evidence=[
        RetrievedPolicy("POL-02", "无理由退货", "普通商品在签收后7日内可以申请无理由退货。", 0.1),
        RetrievedPolicy("RET-01", "定制商品例外", "定制商品不适用7日无理由退货。", 0.2),
    ],
    chat_model=FakeListChatModel(responses=["定制商品不适用7日无理由退货。[RET-01]"]),
)
assert not scoped_exception.conflicts_detected
assert "不适用7日无理由退货" in scoped_exception.answer
print("PASS rag scoped-exception handling")

settings = get_settings()
store = open_configured_policy_store(settings=settings)
compound = retrieve_policies(
    "键盘是定制配色，签收第4天发现按键坏了，能不能处理，邮费谁出？",
    store=store,
    top_k=settings.rag_top_k,
)
sources = {item.source_id for item in compound}
required = {"RET-01", "QUA-01", "POL-05"}
assert required.issubset(sources), f"compound retrieval missed {sorted(required - sources)}: {sorted(sources)}"
print("PASS rag compound-policy retrieval")
PY

bash scripts/verify_phase6.sh
# 用容器内的 venv 解释器取 webhook secret：裸 python 是系统解释器，
# import support_agent 会 ModuleNotFoundError，输出空串会把
# MOCK_SHOP_WEBHOOK_SECRET 覆盖为空，导致 verify_v21 签名全错。
export MOCK_SHOP_WEBHOOK_SECRET="$(docker compose exec -T support-agent /app/.venv/bin/python -c 'from support_agent.config import get_settings; print(get_settings().mock_shop_webhook_secret)')"
bash scripts/verify_v21.sh
