from collections.abc import Sequence

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


def score_retrieved_sources(
    expected_sources: Sequence[str], retrieved_sources: Sequence[str]
) -> dict[str, float | bool | int]:
    expected = set(expected_sources)
    retrieved = set(retrieved_sources)
    if not expected:
        raise ValueError("expected_sources must contain at least one policy ID")
    found = expected & retrieved
    recall = len(found) / len(expected)
    return {
        "expected_count": len(expected),
        "found_count": len(found),
        "hit": bool(found),
        "recall": recall,
        "all_expected_found": found == expected,
    }


def evaluate_cases(
    cases: list[dict],
    *,
    store: Chroma,
    embeddings: Embeddings,
    top_k: int,
) -> tuple[list[dict], dict[str, int | float]]:
    """Batch-embed marked queries and compare retrieved policy IDs with the rubric."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    scored_cases = [case for case in cases if case.get("required_evidence")]
    if not scored_cases:
        raise ValueError("No evaluation cases have required_evidence labels")

    queries = [case["query"] for case in scored_cases]
    vectors = embeddings.embed_documents(queries)
    if len(vectors) != len(scored_cases):
        raise ValueError("Embedding API returned a different number of query vectors")

    records: list[dict] = []
    for case, vector in zip(scored_cases, vectors):
        matches = store.similarity_search_by_vector_with_relevance_scores(vector, k=top_k)
        retrieved = [str(doc.metadata.get("source_id", "unknown")) for doc, _ in matches]
        score = score_retrieved_sources(case["required_evidence"], retrieved)
        records.append({
            "case_id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "required_evidence": case["required_evidence"],
            "retrieved_source_ids": retrieved,
            "retrieved": [
                {
                    "source_id": str(doc.metadata.get("source_id", "unknown")),
                    "title": str(doc.metadata.get("title", "")),
                    "relevance_score": float(score_value),
                }
                for doc, score_value in matches
            ],
            "hit_at_k": score["hit"],
            "recall_at_k": score["recall"],
            "all_expected_found": score["all_expected_found"],
        })

    summary = {
        "scored_cases": len(records),
        "hit_at_k": sum(record["hit_at_k"] for record in records) / len(records),
        "mean_recall_at_k": sum(record["recall_at_k"] for record in records) / len(records),
        "all_expected_found_rate": sum(
            record["all_expected_found"] for record in records
        ) / len(records),
    }
    return records, summary
