from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv()  # 从 CWD 向上找 .env：源码布局与容器 WORKDIR 均可命中
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")


def _resolve_env_path(env_name: str, default: str) -> Path:
    """解析相对路径配置：相对 CWD 解析，源码布局下回退项目根。

    pip 安装后 Path(__file__).parents[2] 指向 site-packages，
    不能再作为相对路径基准（否则容器里会在 /usr/local/lib 下
    新建一个空库）；因此相对路径优先按 CWD 解析。
    """
    raw_path = Path(os.getenv(env_name, default))
    if raw_path.is_absolute():
        return raw_path
    cwd_based = Path.cwd() / raw_path
    if cwd_based.parent.exists():
        return cwd_based
    return PROJECT_ROOT / raw_path


@dataclass(frozen=True)
class Settings:
    database_path: Path
    demo_token_demo_a: str = "demo-a-local-token"
    demo_token_demo_b: str = "demo-b-local-token"
    demo_token_demo_a_approver: str = "demo-a-approver-local-token"
    demo_token_demo_a_approver_alt: str = "demo-a-approver-alt-local-token"
    demo_token_demo_a_service: str = "demo-a-service-local-token"
    demo_token_demo_a_admin: str = "demo-a-admin-local-token"
    demo_token_legacy: str = "legacy-demo-local-token"
    logistics_api_base_url: str = "http://127.0.0.1:8091"
    logistics_api_key: str = "demo-logistics-local-key"
    logistics_timeout_seconds: float = 3.0
    mock_shop_api_base_url: str = "http://127.0.0.1:8092"
    mock_shop_api_key: str = "demo-shop-local-key"
    mock_shop_webhook_secret: str = "demo-shop-webhook-secret"
    checkpoint_path: Path = PROJECT_ROOT / "data" / "checkpoints.sqlite"
    log_level: str = "INFO"
    siliconflow_api_key: str | None = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_embedding_model: str = "BAAI/bge-large-zh-v1.5"
    siliconflow_chat_model: str = "Qwen/Qwen2.5-7B-Instruct"
    vector_store_path: Path = PROJECT_ROOT / "data" / "vector_store"
    rag_chunk_size: int = 400
    rag_chunk_overlap: int = 0
    rag_top_k: int = 4


def get_settings() -> Settings:
    database_path = _resolve_env_path("DATABASE_PATH", "data/support_agent.db")
    vector_store_path = _resolve_env_path("VECTOR_STORE_PATH", "data/vector_store")
    checkpoint_path = _resolve_env_path("CHECKPOINT_DB_PATH", "data/checkpoints.sqlite")
    chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "400"))
    chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "0"))
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("RAG chunk size must be positive and overlap must be smaller than size")
    top_k = int(os.getenv("RAG_TOP_K", "4"))
    if top_k < 1:
        raise ValueError("RAG_TOP_K must be at least 1")
    demo_tokens = (
        os.getenv("DEMO_TOKEN_DEMO_A", "demo-a-local-token"),
        os.getenv("DEMO_TOKEN_DEMO_B", "demo-b-local-token"),
        os.getenv("DEMO_TOKEN_DEMO_A_APPROVER", "demo-a-approver-local-token"),
        os.getenv("DEMO_TOKEN_DEMO_A_APPROVER_ALT", "demo-a-approver-alt-local-token"),
        os.getenv("DEMO_TOKEN_DEMO_A_SERVICE", "demo-a-service-local-token"),
        os.getenv("DEMO_TOKEN_DEMO_A_ADMIN", "demo-a-admin-local-token"),
        os.getenv("DEMO_TOKEN_LEGACY", "legacy-demo-local-token"),
    )
    if len(set(demo_tokens)) != len(demo_tokens):
        raise ValueError("Each demo persona must use a distinct token")
    logistics_timeout = float(os.getenv("LOGISTICS_TIMEOUT_SECONDS", "3"))
    if logistics_timeout <= 0:
        raise ValueError("LOGISTICS_TIMEOUT_SECONDS must be positive")
    return Settings(
        database_path=database_path,
        demo_token_demo_a=os.getenv("DEMO_TOKEN_DEMO_A", "demo-a-local-token"),
        demo_token_demo_b=os.getenv("DEMO_TOKEN_DEMO_B", "demo-b-local-token"),
        demo_token_demo_a_approver=os.getenv(
            "DEMO_TOKEN_DEMO_A_APPROVER", "demo-a-approver-local-token"
        ),
        demo_token_demo_a_approver_alt=os.getenv(
            "DEMO_TOKEN_DEMO_A_APPROVER_ALT", "demo-a-approver-alt-local-token"
        ),
        demo_token_demo_a_service=os.getenv(
            "DEMO_TOKEN_DEMO_A_SERVICE", "demo-a-service-local-token"
        ),
        demo_token_demo_a_admin=os.getenv(
            "DEMO_TOKEN_DEMO_A_ADMIN", "demo-a-admin-local-token"
        ),
        demo_token_legacy=os.getenv("DEMO_TOKEN_LEGACY", "legacy-demo-local-token"),
        logistics_api_base_url=os.getenv(
            "LOGISTICS_API_BASE_URL", "http://127.0.0.1:8091"
        ).rstrip("/"),
        logistics_api_key=os.getenv(
            "MOCK_LOGISTICS_API_KEY", "demo-logistics-local-key"
        ),
        logistics_timeout_seconds=logistics_timeout,
        mock_shop_api_base_url=os.getenv(
            "MOCK_SHOP_API_BASE_URL", "http://127.0.0.1:8092"
        ).rstrip("/"),
        mock_shop_api_key=os.getenv("MOCK_SHOP_API_KEY", "demo-shop-local-key"),
        mock_shop_webhook_secret=os.getenv(
            "MOCK_SHOP_WEBHOOK_SECRET", "demo-shop-webhook-secret"
        ),
        checkpoint_path=checkpoint_path,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        siliconflow_api_key=os.getenv("SILICONFLOW_API_KEY") or None,
        siliconflow_base_url=os.getenv(
            "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"
        ),
        siliconflow_embedding_model=os.getenv(
            "SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"
        ),
        siliconflow_chat_model=os.getenv(
            "SILICONFLOW_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct"
        ),
        vector_store_path=vector_store_path,
        rag_chunk_size=chunk_size,
        rag_chunk_overlap=chunk_overlap,
        rag_top_k=top_k,
    )
