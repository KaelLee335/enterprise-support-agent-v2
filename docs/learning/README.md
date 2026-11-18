# 项目学习手册

本手册跟随真实项目代码，按用户指定的顺序学习。每一章包含系统位置、项目数据流、真实代码入口、示例、重点和自测题。

基础五章已齐备；随每次功能扩展继续核对代码入口和本机验证结果。V2.1 电商 Adapter 追加章节按当前工作树实现编写，WSL 容器验收完成后再补充运行结果。

## 路线

1. [LangChain：政策问答链路](langchain.md) — Prompt、Runnable、Chat Model、Parser、Retriever 与 LangGraph 的分工。
2. [LangGraph：售后请求状态图](langgraph.md) — State、Node、Edge、路由和暂停/恢复。
3. [RAG：从政策文件到有据可查的答案](rag.md) — 文档、切分、Embedding、Chroma 检索、引用和答案约束。
4. [SQL：SQLite 数据、租户范围与事务](sql.md) — 表关系、参数化查询、租户过滤、事务与运行记录。
5. [FastAPI：HTTP API、身份依赖与响应模型](fastapi.md) — 路由、Schema、依赖注入、Bearer 演示身份、错误响应和 API 测试。

基础五章之后的扩展专题：[V2.1 电商 Integration Layer、Adapter、LangChain Tools、Webhook 与售后申请边界](ecommerce_integration.md)。

每章完成后补充当前测试证据；代码变化时更新对应章节。学习材料不意味着生产级认证或生产可用性。
