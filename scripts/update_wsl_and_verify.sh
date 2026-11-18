#!/usr/bin/env bash
# Sync the reviewed V2.1 source and verifier files to WSL, rebuild, and verify.
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

bash scripts/verify_phase6.sh
# 用容器内的 venv 解释器取 webhook secret：裸 python 是系统解释器，
# import support_agent 会 ModuleNotFoundError，输出空串会把
# MOCK_SHOP_WEBHOOK_SECRET 覆盖为空，导致 verify_v21 签名全错。
export MOCK_SHOP_WEBHOOK_SECRET="$(docker compose exec -T support-agent /app/.venv/bin/python -c 'from support_agent.config import get_settings; print(get_settings().mock_shop_webhook_secret)')"
bash scripts/verify_v21.sh
