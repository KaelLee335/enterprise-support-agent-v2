import argparse

from support_agent.config import get_settings
from support_agent.rag.answer import configured_policy_answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question grounded in retrieved policies.")
    parser.add_argument("question", help="After-sales policy question")
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    result = configured_policy_answer(args.question, top_k=args.top_k, settings=settings)
    print(result.answer)
    print(f"Citation check: {'passed' if result.citation_check_passed else 'failed'}")
    if result.unknown_citations:
        print(f"Unknown citations: {', '.join(result.unknown_citations)}")
    print("Retrieved evidence:")
    for item in result.evidence:
        print(f"- {item.source_id} — {item.title} (distance={item.distance:.4f})")


if __name__ == "__main__":
    main()
