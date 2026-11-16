from support_agent.config import get_settings
from support_agent.rag.retrieval import create_siliconflow_embeddings


def main() -> None:
    settings = get_settings()
    embeddings = create_siliconflow_embeddings(settings)
    vector = embeddings.embed_query("保修期内质量问题如何处理？")
    print(
        "SiliconFlow Embedding request succeeded: "
        f"model={settings.siliconflow_embedding_model}, dimensions={len(vector)}"
    )


if __name__ == "__main__":
    main()
