import argparse

from support_agent.config import get_settings
from support_agent.rag.retrieval import open_configured_policy_store, retrieve_policies


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect relevant policy evidence.")
    parser.add_argument("query", help="Question to search in the policy corpus")
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    store = open_configured_policy_store(settings=settings)
    results = retrieve_policies(
        args.query,
        store=store,
        top_k=args.top_k if args.top_k is not None else settings.rag_top_k,
    )
    if not results:
        print("No policy evidence retrieved.")
        return
    for rank, result in enumerate(results, start=1):
        print(f"[{rank}] {result.source_id} — {result.title} (distance={result.distance:.4f})")
        print(result.content)
        print()


if __name__ == "__main__":
    main()
