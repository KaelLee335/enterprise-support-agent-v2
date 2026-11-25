"""One-shot live Langfuse smoke using fictional policy data and isolated SQLite.

Run only after configuring the local backend .env and explicitly authorizing a
real trace check: `python scripts/verify_langfuse_trace.py --send`.
This makes one `/chat` request (including the existing model/embedding calls),
uses a temporary business/checkpoint database, and prints only observation
names/types/counts. It never prints credentials, prompts, answers, or evidence.
"""
from __future__ import annotations

import argparse
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient
from langfuse import get_client

from support_agent import main
from support_agent.langfuse_observability import langfuse_status


def main_cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send", action="store_true", help="send one fictional policy query to the configured model and Langfuse")
    args = parser.parse_args()
    if not args.send:
        parser.error("pass --send only after confirming the local .env and telemetry data scope")

    status = langfuse_status(main.settings)
    if not status["enabled"]:
        print(f"FAIL Langfuse not configured ({status['reason']})")
        return 2
    if not main.settings.siliconflow_api_key:
        print("FAIL configured chat/embedding provider key is missing")
        return 2
    if not main.settings.vector_store_path.exists():
        print("FAIL configured Chroma directory is missing")
        return 2

    with tempfile.TemporaryDirectory(prefix="support-agent-langfuse-") as temp_dir:
        temporary_root = Path(temp_dir)
        original = main.settings
        main.settings = replace(
            original,
            database_path=temporary_root / "isolated.db",
            checkpoint_path=temporary_root / "isolated-checkpoint.sqlite",
        )
        try:
            with TestClient(main.app) as client:
                response = client.post(
                    "/chat",
                    json={"question": "退款申请通过审核后，通常还需要多久能到账？"},
                    headers={"Authorization": "Bearer demo-a-local-token"},
                )
            if response.status_code != 200:
                print(f"FAIL fictional /chat returned HTTP {response.status_code}")
                return 3
            payload = response.json()
            if payload.get("intent") != "policy_qa" or not payload.get("trace_id"):
                print("FAIL request did not route through policy QA with a trace id")
                return 3
            get_client().flush()
            observations = []
            has_root = has_graph = has_generation = False
            for _ in range(20):
                result = get_client().api.observations.get_many(
                    trace_id=payload["trace_id"], limit=100
                )
                observations = getattr(result, "data", []) or []
                names = {
                    getattr(item, "name", "") or ""
                    for item in observations
                    if getattr(item, "name", None)
                }
                has_root = "support-agent-request" in names
                has_graph = any(name.startswith("graph.") for name in names)
                has_generation = any(
                    "generation" in str(getattr(item, "type", "")).lower()
                    for item in observations
                )
                if has_root and has_graph and has_generation:
                    break
                time.sleep(1)
            names = sorted({getattr(item, "name", "") or "" for item in observations if getattr(item, "name", None)})
            types = sorted({str(getattr(item, "type", "")) for item in observations})
            print(f"Langfuse Trace ID: {payload['trace_id']}")
            print(f"Observations: {len(observations)}; types: {', '.join(types) or '(none)'}")
            print(f"Node names: {', '.join(names) or '(none)'}")
            print(f"Checks: root={has_root}, graph_nodes={has_graph}, generation={has_generation}")
            if not (has_root and has_graph and has_generation):
                return 4
            return 0
        finally:
            main.settings = original


if __name__ == "__main__":
    raise SystemExit(main_cli())
