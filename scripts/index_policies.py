from support_agent.config import PROJECT_ROOT, get_settings
from support_agent.rag.policies import load_policy_documents, split_policy_documents
from support_agent.rag.index import index_policy_documents
from support_agent.rag.retrieval import create_siliconflow_embeddings


def main() -> None:
    settings = get_settings()
    policy_dir = PROJECT_ROOT / "data" / "policies"
    source_documents = load_policy_documents(policy_dir)
    chunks = split_policy_documents(
        source_documents,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
    store, changed_count = index_policy_documents(
        chunks,
        settings.vector_store_path,
        create_siliconflow_embeddings(settings),
        embedding_model=settings.siliconflow_embedding_model,
    )
    stored_count = len(store.get(include=["metadatas"])["ids"])
    print(
        f"Loaded {len(source_documents)} policies into {stored_count} chunks; "
        f"embedded {changed_count} changed chunks."
    )


if __name__ == "__main__":
    main()
