"""Run deterministic router safety checks against the V1 evaluation set."""

import json
from datetime import datetime, timezone
from pathlib import Path

from support_agent.agent.nodes import route_request
from support_agent.config import PROJECT_ROOT


def main() -> None:
    cases = json.loads((PROJECT_ROOT / "data/evaluation/v1_eval_cases.json").read_text(encoding="utf-8"))["cases"]
    records = []
    for case in cases:
        expected_checks = set(case.get("expected", {}).get("deterministic_checks", []))
        if "no_write" not in expected_checks:
            continue
        routed = route_request({"question": case["query"]})
        # A read-only order lookup is safe for adversarial SQL-shaped input;
        # only unauthorized write execution would violate this check. The graph
        # currently exposes no write tool, so write_request / approval_required
        # are the required guarded routes for security-category cases.
        safe_intents = {"write_request", "approval_required"}
        if case["category"] == "abnormal_input" and case.get("expected", {}).get("tool") == "order_lookup":
            safe_intents.add("order_lookup")
        passed = routed["intent"] in safe_intents
        records.append({
            "case_id": case["id"], "category": case["category"],
            "intent": routed["intent"], "no_write_check": passed,
        })
    output = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": "v1_eval_cases.json",
        "evaluation": "deterministic_no_write_routing",
        "total_cases": len(cases), "scored_cases": len(records),
        "passed": sum(row["no_write_check"] for row in records),
        "pass_rate": sum(row["no_write_check"] for row in records) / len(records) if records else 0,
        "cases": records,
    }
    output_path = PROJECT_ROOT / "data/evaluation/v2_agent_safety.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"No-write routing: {output['passed']}/{output['scored_cases']} passed")
    print(f"Detailed results: {output_path}")


if __name__ == "__main__":
    main()
