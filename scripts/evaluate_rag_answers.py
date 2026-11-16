"""Compare generated policy answers at multiple retrieval depths with an LLM rubric judge."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from support_agent.config import PROJECT_ROOT, get_settings
from support_agent.rag.answer_constraints import match_answer_constraints
from support_agent.rag.answer import (
    generate_answer_from_evidence,
)
from support_agent.rag.retrieval import (
    open_configured_policy_store,
    retrieve_policies,
)


JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是严格的中文政策问答评估员。只能依据给定的政策证据和评分标准评分，"
        "不得引入外部知识。逐项判断答案是否覆盖必答要点、是否出现禁答内容、"
        "每个事实结论是否有证据支持、引用是否指向给定证据。"
        "回答必须是 JSON 对象，不要输出 Markdown。",
    ),
    (
        "human",
        "问题：{question}\n必答要点（逐条原样评估语义覆盖）：{points}\n"
        "禁答内容：{forbidden}\n政策证据：\n{evidence}\n"
        "助手答案：\n{answer}\n\n"
        "输出 JSON，键为 point_coverage（布尔数组，与要点顺序一致）、"
        "forbidden_violations（字符串数组）、grounded（布尔值）、"
        "citation_supported（布尔值）、brief_reason（简短中文字符串）。",
    ),
])


def parse_json_object(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise ValueError("judge response did not contain a JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("judge response JSON was not an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, nargs="+", default=[4, 8])
    parser.add_argument("--limit", type=int, default=None, help="Optional case limit for a smoke run.")
    parser.add_argument(
        "--case-id", action="append", default=None,
        help="Evaluate only the specified case ID; may be repeated.",
    )
    parser.add_argument(
        "--skip-judge", action="store_true",
        help="Skip the slow same-model judge; save answers and constraint application for manual review.",
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="Per-call model timeout in seconds.")
    parser.add_argument("--resume", action="store_true", help="Resume missing case/top-k records from an existing partial report.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if any(k < 1 for k in args.top_k):
        raise SystemExit("Each --top-k value must be at least 1")

    settings = get_settings()
    dataset = json.loads((PROJECT_ROOT / "data/evaluation/v1_eval_cases.json").read_text(encoding="utf-8"))
    cases = [
        case for case in dataset["cases"]
        if case.get("required_evidence")
        and case.get("expected", {}).get("route") == "else_llm_policy_answer"
        and case.get("expected", {}).get("answer_points")
    ]
    if args.case_id:
        wanted = set(args.case_id)
        cases = [case for case in cases if case["id"] in wanted]
        missing = wanted - {case["id"] for case in cases}
        if missing:
            raise SystemExit(f"Unknown or ineligible case IDs: {', '.join(sorted(missing))}")
    if args.limit is not None:
        cases = cases[:args.limit]

    output_path = args.output or PROJECT_ROOT / "data/evaluation/v2_rag_answers.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    store = open_configured_policy_store(settings=settings)
    if not settings.siliconflow_api_key:
        raise SystemExit("SILICONFLOW_API_KEY is missing from the local .env file")
    chat_model = ChatOpenAI(
        model=settings.siliconflow_chat_model,
        api_key=settings.siliconflow_api_key,
        base_url=settings.siliconflow_base_url,
        temperature=0,
        timeout=args.timeout,
        max_retries=0,
    )
    judge_chain = None if args.skip_judge else JUDGE_PROMPT | chat_model | StrOutputParser()
    records = []
    if args.resume and output_path.exists():
        previous = json.loads(output_path.read_text(encoding="utf-8"))
        if previous.get("top_k_values") != args.top_k:
            raise SystemExit("Cannot resume: --top-k does not match the existing report")
        records = previous.get("records", [])
        print(f"Resuming from {len(records)} saved answer records", flush=True)

    def save_report(status: str) -> None:
        output = {
            "status": status,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "judge_enabled": not args.skip_judge,
            "judge_model": settings.siliconflow_chat_model if not args.skip_judge else None,
            "generator_model": settings.siliconflow_chat_model,
            "embedding_model": settings.siliconflow_embedding_model,
            "top_k_values": args.top_k,
            "case_count": len(cases),
            "record_count": len(records),
            "summary_by_top_k": summarize(records, args.top_k) if args.skip_judge else {},
            "records": records,
        }
        output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    save_report("in_progress")
    completed = {(record["case_id"], record["top_k"]) for record in records}

    for case in cases:
        ranked_evidence = retrieve_policies(case["query"], store=store, top_k=max(args.top_k))
        for top_k in args.top_k:
            if (case["id"], top_k) in completed:
                continue
            selected_evidence = ranked_evidence[:top_k]
            selected_constraints = match_answer_constraints(case["query"], selected_evidence)
            try:
                answer = generate_answer_from_evidence(
                    case["query"], evidence=selected_evidence, chat_model=chat_model
                )
            except Exception as exc:
                records.append({
                    "case_id": case["id"],
                    "category": case.get("category"),
                    "top_k": top_k,
                    "question": case["query"],
                    "answer": None,
                    "answer_error": type(exc).__name__,
                    "sources": [
                        {"source_id": item.source_id, "distance": item.distance}
                        for item in selected_evidence
                    ],
                    "citations": [],
                    "citation_check_passed": False,
                    "unknown_citations": [],
                    "constraint_ids": [item.constraint_id for item in selected_constraints],
                    "enforced_constraint_ids": [],
                    "judge": None,
                    "judge_error": None,
                })
                save_report("in_progress")
                print(f"{case['id']} top_k={top_k} ERROR={type(exc).__name__}", flush=True)
                continue
            evidence_text = "\n\n".join(
                f"[{item.source_id}] {item.title}\n{item.content}"
                for item in answer.evidence
            )
            expected = case["expected"]
            judge = None
            judge_error = None
            if judge_chain is not None:
                judge_raw = judge_chain.invoke({
                    "question": case["query"],
                    "points": json.dumps(expected.get("answer_points", []), ensure_ascii=False),
                    "forbidden": json.dumps(expected.get("forbidden", []), ensure_ascii=False),
                    "evidence": evidence_text,
                    "answer": answer.answer,
                })
                try:
                    judge = parse_json_object(judge_raw)
                except (ValueError, json.JSONDecodeError) as exc:
                    judge_error = str(exc)
            records.append({
                "case_id": case["id"],
                "category": case.get("category"),
                "top_k": top_k,
                "question": case["query"],
                "answer": answer.answer,
                "sources": [
                    {"source_id": item.source_id, "distance": item.distance}
                    for item in answer.evidence
                ],
                "citations": answer.citations,
                "citation_check_passed": answer.citation_check_passed,
                "unknown_citations": answer.unknown_citations,
                "constraint_ids": answer.constraint_ids,
                "enforced_constraint_ids": answer.enforced_constraint_ids,
                "judge": judge,
                "judge_error": judge_error,
            })
            save_report("in_progress")
            print(f"{case['id']} top_k={top_k} citation_valid={answer.citation_check_passed}", flush=True)

    summary_by_k = summarize(records, args.top_k)
    output = {
        "status": "complete",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "judge_enabled": not args.skip_judge,
        "judge_model": settings.siliconflow_chat_model if not args.skip_judge else None,
        "generator_model": settings.siliconflow_chat_model,
        "embedding_model": settings.siliconflow_embedding_model,
        "top_k_values": args.top_k,
        "case_count": len(cases),
        "record_count": len(records),
        "summary_by_top_k": summary_by_k,
        "records": records,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary_by_k, ensure_ascii=False, indent=2))
    print(f"Detailed results: {output_path}")


def summarize(records: list[dict], top_k_values: list[int]) -> dict:
    summary = {}
    for k in top_k_values:
        group = [record for record in records if record["top_k"] == k]
        summary[str(k)] = {
            "answers": len(group),
            "citation_valid_rate": (
                sum(record["citation_check_passed"] for record in group) / len(group) if group else None
            ),
            "answers_with_constraints": sum(bool(record["constraint_ids"]) for record in group),
            "answers_with_enforced_constraints": sum(
                bool(record["enforced_constraint_ids"]) for record in group
            ),
        }
    return summary


if __name__ == "__main__":
    main()
