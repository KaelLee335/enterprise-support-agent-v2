from dataclasses import dataclass
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from support_agent.config import Settings, get_settings
from support_agent.rag.index import open_policy_store
from support_agent.rag.query_expansion import build_policy_retrieval_query


@dataclass(frozen=True)
class RetrievedPolicy:
    source_id: str
    title: str
    content: str
    distance: float


def create_siliconflow_embeddings(settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    if not settings.siliconflow_api_key:
        raise RuntimeError(
            "SILICONFLOW_API_KEY is missing. Add it to the local .env file before indexing."
        )
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.siliconflow_embedding_model,
        api_key=settings.siliconflow_api_key,
        base_url=settings.siliconflow_base_url,
        request_timeout=30,
        max_retries=1,
        check_embedding_ctx_length=False,
    )


def retrieve_policies(
    query: str,
    *,
    store: Chroma,
    top_k: int = 4,
) -> list[RetrievedPolicy]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    retrieval_query = build_policy_retrieval_query(query)
    matches = store.similarity_search_with_score(retrieval_query, k=top_k)
    return [
        RetrievedPolicy(
            source_id=str(document.metadata.get("source_id", "unknown")),
            title=str(document.metadata.get("title", "")),
            content=document.page_content,
            distance=float(distance),
        )
        for document, distance in matches
    ]


def open_configured_policy_store(
    persist_directory: Path | None = None,
    settings: Settings | None = None,
) -> Chroma:
    settings = settings or get_settings()
    return open_policy_store(
        persist_directory or settings.vector_store_path,
        create_siliconflow_embeddings(settings),
        embedding_model=settings.siliconflow_embedding_model,
    )
