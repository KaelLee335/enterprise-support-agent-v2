from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from support_agent.config import Settings
from support_agent.rag.index import index_policy_documents
from support_agent.rag.policies import load_policy_documents, split_policy_documents
from support_agent.rag.evaluation import evaluate_cases, score_retrieved_sources
from support_agent.rag.answer import answer_policy_question
from langchain_chroma import Chroma
from support_agent.rag.retrieval import (
    create_siliconflow_embeddings,
    retrieve_policies,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class KeywordEmbeddings(Embeddings):
    """Small deterministic test embedder; it never calls a network API."""

    labels = ("质量", "退货", "退款", "定制")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(label in text) for label in self.labels]


def policy_chunks() -> list:
    documents = load_policy_documents(PROJECT_ROOT / "data" / "policies")
    return split_policy_documents(documents, chunk_size=400, chunk_overlap=0)


def test_policy_loader_preserves_one_source_per_current_chunk():
    chunks = policy_chunks()

    assert len(chunks) == 12
    assert {chunk.metadata["source_id"] for chunk in chunks} >= {"POL-02", "QUA-01", "RET-01"}
    assert all(chunk.metadata["source_id"] in chunk.metadata["chunk_id"] for chunk in chunks)
    assert next(chunk for chunk in chunks if chunk.metadata["source_id"] == "QUA-01").metadata[
        "source_version"
    ] == "V2"


def test_policy_index_upserts_only_changed_chunks_and_returns_evidence(tmp_path):
    chunks = policy_chunks()
    embeddings = KeywordEmbeddings()

    store, first_indexed = index_policy_documents(chunks, tmp_path / "chroma", embeddings)
    same_store, second_indexed = index_policy_documents(chunks, tmp_path / "chroma", embeddings)
    results = retrieve_policies("定制商品质量问题", store=same_store, top_k=4)

    assert first_indexed == 12
    assert second_indexed == 0
    assert len(results) == 4
    assert {result.source_id for result in results} & {"QUA-01", "POL-03"}
    assert all(result.content and result.title for result in results)


def test_empty_index_input_does_not_clear_existing_collection(tmp_path):
    with pytest.raises(ValueError, match="refusing to clear"):
        index_policy_documents([], tmp_path / "chroma", KeywordEmbeddings())


def test_retrieval_rejects_empty_queries(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())

    with pytest.raises(ValueError, match="query must not be empty"):
        retrieve_policies("  ", store=store)


def test_siliconflow_embedding_requires_local_api_key():
    settings = Settings(database_path=PROJECT_ROOT / "data" / "test.db")

    with pytest.raises(RuntimeError, match="SILICONFLOW_API_KEY is missing"):
        create_siliconflow_embeddings(settings)


def test_retrieval_evidence_scoring_counts_partial_recall():
    score = score_retrieved_sources(["POL-02", "POL-03"], ["POL-03", "POL-04"])

    assert score["hit"] is True
    assert score["recall"] == 0.5
    assert score["all_expected_found"] is False


def test_evaluation_ignores_cases_without_evidence_labels(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    cases = [
        {"id": "scored", "category": "qa", "query": "质量", "required_evidence": ["POL-03"]},
        {"id": "unscored", "category": "safe", "query": "修改地址", "required_evidence": []},
    ]

    records, summary = evaluate_cases(
        cases, store=store, embeddings=KeywordEmbeddings(), top_k=3
    )

    assert len(records) == 1
    assert summary["scored_cases"] == 1
    assert 0.0 <= summary["mean_recall_at_k"] <= 1.0


def test_rag_answer_checks_citations_against_retrieved_evidence(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    chat = FakeListChatModel(responses=["定制商品仍可提交质量售后申请，需提供凭证并由人工审核。[QUA-01]"])

    result = answer_policy_question(
        "定制商品有质量问题怎么办？", store=store, chat_model=chat, top_k=4
    )

    assert "[QUA-01]" in {f"[{citation}]" for citation in result.citations}
    assert result.citation_check_passed is True
    assert result.unknown_citations == []


def test_rag_answer_flags_citations_not_in_retrieved_evidence(tmp_path):
    store, _ = index_policy_documents(policy_chunks(), tmp_path / "chroma", KeywordEmbeddings())
    chat = FakeListChatModel(responses=["可申请处理。[POL-09]"])

    result = answer_policy_question(
        "定制商品质量问题", store=store, chat_model=chat, top_k=1
    )

    assert result.citation_check_passed is False
    assert result.unknown_citations == ["POL-09"]


def test_rag_answer_does_not_call_model_when_retrieval_is_empty(tmp_path):
    store = Chroma(
        collection_name="empty_policy_test",
        embedding_function=KeywordEmbeddings(),
        persist_directory=str(tmp_path / "empty-chroma"),
    )
    chat = FakeListChatModel(responses=["should not be used"])

    result = answer_policy_question("陌生主题", store=store, chat_model=chat)

    assert result.evidence == []
    assert "无法确认" in result.answer
