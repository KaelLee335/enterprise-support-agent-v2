import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from support_agent.config import PROJECT_ROOT, get_settings
from support_agent.rag.evaluation import evaluate_cases
from support_agent.rag.retrieval import (
    create_siliconflow_embeddings,
    open_configured_policy_store,
)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Evaluate policy retrieval against V1 labels.")
    parser.add_argument("--top-k", type=int, default=settings.rag_top_k)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path (defaults to a timestamped V2 result).",
    )
    args = parser.parse_args()

    source_path = PROJECT_ROOT / "data" / "evaluation" / "v1_eval_cases.json"
    dataset = json.loads(source_path.read_text(encoding="utf-8"))
    cases = dataset["cases"]
    scored_count = sum(bool(case.get("required_evidence")) for case in cases)
    if scored_count == 0:
        raise SystemExit("No cases have required_evidence labels.")

    embeddings = create_siliconflow_embeddings(settings)
    store = open_configured_policy_store(settings=settings)
    records, summary = evaluate_cases(
        cases,
        store=store,
        embeddings=embeddings,
        top_k=args.top_k,
    )
    output_path = args.output or (
        PROJECT_ROOT / "data" / "evaluation" /
        f"v2_retrieval_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    )
    output = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "source_dataset": "v1_eval_cases.json",
        "embedding_model": settings.siliconflow_embedding_model,
        "top_k": args.top_k,
        "total_cases": len(cases),
        "scored_cases": len(records),
        "unscored_cases": len(cases) - len(records),
        "summary": summary,
        "cases": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Scored {len(records)}/{len(cases)} cases at k={args.top_k}: "
        f"Hit@k={summary['hit_at_k']:.1%}, "
        f"mean Recall@k={summary['mean_recall_at_k']:.1%}, "
        f"all expected={summary['all_expected_found_rate']:.1%}"
    )
    print(f"Detailed results: {output_path}")


if __name__ == "__main__":
    main()
