# 项目学习手册

本手册跟随真实项目代码，按用户指定的顺序学习。每一章包含系统位置、项目数据流、真实代码入口、示例、重点和自测题。

当前五个主题的章节草稿已齐备。LangChain 初稿由用户截图报告已逐项核对并随 `dbab8af` 推送；本会话新增的 LangGraph/RAG/SQL/FastAPI 章节是基于 GitHub `main` 的只读代码快照撰写，尚未通过本地执行器复核或推送。

## 路线

1. [LangChain：政策问答链路](langchain.md) — Prompt、Runnable、Chat Model、Parser、Retriever 与 LangGraph 的分工。
2. [LangGraph：售后请求状态图](langgraph.md) — State、Node、Edge、路由和暂停/恢复。
3. [RAG：从政策文件到有据可查的答案](rag.md) — 文档、切分、Embedding、Chroma 检索、引用和答案约束。
4. [SQL：SQLite 数据、租户范围与事务](sql.md) — 表关系、参数化查询、租户过滤、事务与运行记录。
5. [FastAPI：HTTP API、身份依赖与响应模型](fastapi.md) — 路由、Schema、依赖注入、Bearer 演示身份、错误响应和 API 测试。

每章完成后补充当前测试证据；代码变化时更新对应章节。学习材料不意味着生产级认证或生产可用性。
