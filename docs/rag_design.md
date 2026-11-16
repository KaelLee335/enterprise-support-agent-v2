# 政策 RAG：第一版设计

## 流程

```text
data/policies/*.md
  → 每个文件加载为一个 LangChain Document
  → RecursiveCharacterTextSplitter（当前文件少于 400 字符时保持整篇）
  → SiliconFlow Embedding API 生成向量
  → 本地持久 Chroma 索引
  → 用户问题向量化并按相似度取 Top-K
  → 检查政策编号、原文证据和 Chroma distance
```

## 关键输入与输出

- `Document.page_content` 保存政策原文；metadata 保存 `source_id`、源文件、标题、来源版本、chunk 起始位置及内容哈希。
- RET-01/QUA-01 的来源版本为 V2，其余 POL-01 至 POL-10 标为 V1，避免把两版本规则混为一谈。
- Chroma 保存向量、原文块和 metadata 到 `data/vector_store/`。根据 Embedding 模型名隔离 collection，避免更换模型后把旧向量和新查询向量混用。
- `scripts/search_policies.py` 返回每条检索证据及距离。Chroma distance 是距离值，通常越低越相似；当前不做硬阈值拒答，阈值需通过评估集校准。
- `scripts/index_policies.py` 根据稳定块 ID 和内容哈希只更新变更块，避免重复计算所有政策 Embedding。数据源不变时重复运行不会重算向量。

## 边界和后续评估

- 当前实现包含文档加载、切分、云端 Embedding、向量存储、可观察检索、CLI RAG 回答链，以及由 LangGraph 调用的 FastAPI `/chat` 政策问答路径。
- 引用检查只确认答案引用的政策编号属于本次检索来源，不等于证明每个自然语言结论都被证据支持；结论正确性仍靠评估用例人工/规则审核。
- 初始参数：`RAG_CHUNK_SIZE=400`、`RAG_CHUNK_OVERLAP=0`、`RAG_TOP_K=4`。由于现有政策只有约 160–370 字符，第一版每文件仍是一块；如果加长政策，再基于标题/段落边界调整并用召回结果对照。
- 复用 V1 用例的 `required_evidence` 作为目标来源 ID。已在相同的 36 条有标签用例上比较 Top-2/4/6/8；指标及限制见 `docs/evaluation_and_observability.md`。Top-8 完整证据召回较高，但答案质量未证明优于 Top-4，因此默认仍为 4。
- SiliconFlow key 只放在本机 `.env`。任何日志和评估文件都不得记录密钥。
