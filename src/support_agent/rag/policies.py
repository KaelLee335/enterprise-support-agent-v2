import hashlib
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_policy_documents(policy_dir: Path) -> list[Document]:
    """Load Markdown policies and attach stable source metadata."""
    documents: list[Document] = []
    for path in sorted(policy_dir.glob("*.md")):
        if path.name == ".gitkeep":
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        first_heading = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
        source_id = path.stem
        documents.append(Document(
            page_content=content,
            metadata={
                "source_id": source_id,
                "source_file": path.name,
                "title": first_heading.group(1) if first_heading else source_id,
                "source_version": "V2" if source_id in {"RET-01", "QUA-01"} else "V1",
            },
        ))
    return documents


def split_policy_documents(
    documents: list[Document], *, chunk_size: int = 400, chunk_overlap: int = 0
) -> list[Document]:
    """Split long policies while keeping the current short policies intact."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n", "。", "",],
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    for chunk_index, document in enumerate(chunks):
        source_id = document.metadata["source_id"]
        start_index = document.metadata.get("start_index", 0)
        document.metadata["chunk_id"] = f"{source_id}-{start_index}"
        document.metadata["chunk_hash"] = hashlib.sha256(
            document.page_content.encode("utf-8")
        ).hexdigest()
    return chunks
