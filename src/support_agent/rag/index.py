from hashlib import sha256
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

COLLECTION_NAME = "support_agent_policies"


def policy_collection_name(embedding_model: str | None = None) -> str:
    if embedding_model is None:
        return COLLECTION_NAME
    model_suffix = sha256(embedding_model.encode("utf-8")).hexdigest()[:12]
    return f"{COLLECTION_NAME}_{model_suffix}"


def open_policy_store(
    persist_directory: Path,
    embeddings: Embeddings,
    *,
    embedding_model: str | None = None,
) -> Chroma:
    return Chroma(
        collection_name=policy_collection_name(embedding_model),
        embedding_function=embeddings,
        persist_directory=str(persist_directory),
    )


def index_policy_documents(
    documents: list[Document],
    persist_directory: Path,
    embeddings: Embeddings,
    *,
    embedding_model: str | None = None,
) -> tuple[Chroma, int]:
    """Upsert changed chunks and remove stale IDs without re-embedding unchanged text."""
    if not documents:
        raise ValueError("No policy chunks found; refusing to clear the existing policy index")
    store = open_policy_store(
        persist_directory, embeddings, embedding_model=embedding_model
    )
    existing = store.get(include=["metadatas"])
    existing_hashes = {
        doc_id: (metadata or {}).get("chunk_hash")
        for doc_id, metadata in zip(existing["ids"], existing["metadatas"])
    }
    desired_ids = [str(document.metadata["chunk_id"]) for document in documents]
    desired_set = set(desired_ids)
    stale_ids = [doc_id for doc_id in existing_hashes if doc_id not in desired_set]
    changed = [
        (doc_id, document)
        for doc_id, document in zip(desired_ids, documents)
        if existing_hashes.get(doc_id) != document.metadata["chunk_hash"]
    ]
    if changed:
        store.add_documents(
            documents=[document for _, document in changed],
            ids=[doc_id for doc_id, _ in changed],
        )
    if stale_ids:
        store.delete(ids=stale_ids)
    return store, len(changed)
