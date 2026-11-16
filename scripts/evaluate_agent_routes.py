"""Score deterministic Agent routing and extracted order parameters on V1 labels."""

import json
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from pydantic import ValidationError

from support_agent.agent.nodes import lookup_order, route_request
from support_agent.config import PROJECT_ROOT
from support_agent.db import connect, initialize_database
from support_agent.schemas import ChatRequest


EXPECTED_INTENTS = {
    "else_llm_policy_answer": {"policy_qa"},
    "insufficient_evidence_reply": {"policy_qa"},
    "order_lookup": {"order_lookup"},
    "order_reply": {"order_lookup"},
    "clarify_or_safe_fallback": {"clarify", "request_rejected"},
    "clarify_order_intent": {"clarify"},
    "clarify_multiple_order_ids": {"clarify"},
    "clarify_invalid_order_id": {"clarify"},
    "clarify_or_split_topics": {"clarify", "policy_qa"},
    "read_only_refusal": {"write_request", "approval_required"},
    "direct": {"write_request", "approval_required"},
    "privacy_refusal": {"write_request", "policy_qa"},
    "prompt_injection_refusal": {"write_request", "policy_qa"},
    "safe_read_only_lookup_or_reject": {"order_lookup", "write_request"},
}


def evaluate(cases: list[dict]) -> dict:
    route_rows = []
    parameter_rows = []
    expected_tool_cases = [case for case in cases if case.get("expected", {}).get("tool") == "order_lookup"]
    tool_rows = []
    outcome_rows = []
    business_field_rows = []
    unscored = []
    for case in cases:
        expected = case.get("expected", {})
        expected_route = expected.get("route")
        query = case.get("query", "")
        if not query.strip():
            try:
                ChatRequest(question=query)
            except ValidationError:
                result = {"intent": "request_rejected", "order_id": None}
            else:
                result = route_request({"question": query})
        else:
            result = route_request({"question": query})
        allowed = EXPECTED_INTENTS.get(expected_route)
        if allowed:
            route_rows.append({
                "case_id": case["id"],
                "expected_route": expected_route,
                "allowed_intents": sorted(allowed),
                "actual_intent": result["intent"],
                "passed": result["intent"] in allowed,
            })
        elif expected_route:
            unscored.append({"case_id": case["id"], "reason": f"unmapped expected route: {expected_route}"})
        elif expected.get("tool_args"):
            unscored.append({"case_id": case["id"], "reason": "no route label; exact parameter checked separately"})

        tool_args = expected.get("tool_args")
        if expected.get("tool") == "order_lookup" and tool_args and "order_id" in tool_args:
            expected_id = str(tool_args["order_id"])
            parameter_rows.append({
                "case_id": case["id"],
                "expected_order_id": expected_id,
                "actual_order_id": result.get("order_id"),
                "actual_intent": result["intent"],
                "passed": result["intent"] == "order_lookup" and result.get("order_id") == expected_id,
            })

    seed_path = PROJECT_ROOT / "data/seed/v1_orders.json"
    with TemporaryDirectory(prefix="agent-route-eval-", dir=PROJECT_ROOT / "data/evaluation") as temp_dir:
        database_path = Path(temp_dir) / "orders.sqlite"
        initialize_database(database_path, seed_path)
        with closing(connect(database_path)) as connection:
            before = [tuple(row) for row in connection.execute("SELECT * FROM orders ORDER BY order_id")]

        for case in expected_tool_cases:
            routed = route_request({"question": case.get("query", "")})
            if routed["intent"] != "order_lookup" or not routed.get("order_id"):
                tool_rows.append({"case_id": case["id"], "called": False, "passed": False})
                continue
            tool_result = lookup_order({
                "order_id": routed["order_id"],
                "tenant_id": "legacy-demo",
                "database_path": str(database_path),
            })
            call_passed = tool_result.get("error") is None
            tool_rows.append({
                "case_id": case["id"], "called": True,
                "order_id": routed["order_id"], "error": tool_result.get("error"),
                "passed": call_passed,
            })
            expected_outcome = case.get("expected", {}).get("order_outcome")
            if expected_outcome:
                actual_outcome = "found" if tool_result.get("order") is not None else "not_found"
                outcome_rows.append({
                    "case_id": case["id"], "expected": expected_outcome,
                    "actual": actual_outcome, "passed": actual_outcome == expected_outcome,
                })
            expected_order = case.get("expected", {}).get("expected_order")
            if expected_order:
                mismatched_fields = [
                    key for key, value in expected_order.items()
                    if tool_result.get("order", {}).get(key) != value
                ]
                business_field_rows.append({
                    "case_id": case["id"],
                    "expected_field_count": len(expected_order),
                    "mismatched_fields": mismatched_fields,
                    "passed": not mismatched_fields,
                })

        with closing(connect(database_path)) as connection:
            after = [tuple(row) for row in connection.execute("SELECT * FROM orders ORDER BY order_id")]
        database_unchanged = before == after

    route_passed = sum(row["passed"] for row in route_rows)
    parameter_passed = sum(row["passed"] for row in parameter_rows)
    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": "v1_eval_cases.json",
        "evaluation": "deterministic_route_and_order_id_extraction",
        "total_cases": len(cases),
        "route_scored": len(route_rows),
        "route_passed": route_passed,
        "route_accuracy": route_passed / len(route_rows) if route_rows else 0,
        "route_by_expected_label": {
            label: {
                "scored": len(rows),
                "passed": sum(row["passed"] for row in rows),
                "accuracy": sum(row["passed"] for row in rows) / len(rows),
            }
            for label in sorted({row["expected_route"] for row in route_rows})
            for rows in [[row for row in route_rows if row["expected_route"] == label]]
        },
        "order_parameter_scored": len(parameter_rows),
        "order_parameter_passed": parameter_passed,
        "order_parameter_accuracy": parameter_passed / len(parameter_rows) if parameter_rows else 0,
        "route_failures": [row for row in route_rows if not row["passed"]],
        "parameter_failures": [row for row in parameter_rows if not row["passed"]],
        "expected_tool_calls": len(expected_tool_cases),
        "tool_calls_succeeded": sum(row["passed"] for row in tool_rows),
        "tool_call_success_rate": sum(row["passed"] for row in tool_rows) / len(tool_rows) if tool_rows else 0,
        "tool_outcomes_scored": len(outcome_rows),
        "tool_outcomes_passed": sum(row["passed"] for row in outcome_rows),
        "tool_outcome_accuracy": sum(row["passed"] for row in outcome_rows) / len(outcome_rows) if outcome_rows else 0,
        "business_order_cases_scored": len(business_field_rows),
        "business_order_cases_passed": sum(row["passed"] for row in business_field_rows),
        "business_order_field_accuracy": (
            sum(row["expected_field_count"] - len(row["mismatched_fields"]) for row in business_field_rows)
            / sum(row["expected_field_count"] for row in business_field_rows)
            if business_field_rows else 0
        ),
        "read_only_database_unchanged": database_unchanged,
        "tool_cases": tool_rows,
        "tool_outcomes": outcome_rows,
        "business_order_fields": business_field_rows,
        "unscored": {
            "route_case_count": len(cases) - len(route_rows),
            "route_case_ids": [case["id"] for case in cases if case.get("expected", {}).get("route") is None],
            "order_parameter_case_count": len(cases) - len(parameter_rows),
            "task_success_and_answer_semantics": "not automatically scored; require rubric/manual evaluation",
            "unmapped_route_labels": unscored,
        },
        "routes_seen": dict(Counter(row["actual_intent"] for row in route_rows)),
    }


def main() -> None:
    dataset = json.loads((PROJECT_ROOT / "data/evaluation/v1_eval_cases.json").read_text(encoding="utf-8"))
    report = evaluate(dataset["cases"])
    output_path = PROJECT_ROOT / "data/evaluation/v2_agent_routes.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Route accuracy: {report['route_passed']}/{report['route_scored']} "
        f"({report['route_accuracy']:.1%}); order ID parameters: "
        f"{report['order_parameter_passed']}/{report['order_parameter_scored']} "
        f"({report['order_parameter_accuracy']:.1%})"
    )
    print(
        f"Tool outcomes: {report['tool_outcomes_passed']}/{report['tool_outcomes_scored']}; "
        f"business order cases: {report['business_order_cases_passed']}/{report['business_order_cases_scored']}; "
        f"DB unchanged: {report['read_only_database_unchanged']}"
    )
    print(f"Detailed results: {output_path}")


if __name__ == "__main__":
    main()
