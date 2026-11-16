# 原始项目要求追踪矩阵

审计日期：2026-11-16  
依据：用户提供的《Enterprise Support Agent V2 — Python Full-stack Agent Engineering》完整项目说明。  
审计范围：当前仓库代码、测试、评估与说明文档，以及此前记录的 WSL/Docker 验收。本轮只读检查，没有运行测试、调用模型或修改业务代码。

## 状态说明

- **已实现/有证据**：仓库或用户实测记录能直接支持该结论。
- **部分实现**：具备 Demo 版本，但原要求的一部分、学习目标或验证范围仍缺失。
- **未实现/明确不做**：当前没有该能力，且属于生产化或明确超出 Demo 的内容。
- **未验证**：代码/文档提示存在，但没有找到足够的直接验收证据。

## 项目定位、V1 资产与固定业务事实

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| 代码化重构 Dify 售后 Agent，覆盖请求、业务处理、Agent、存储、评估和部署 | 已实现/有证据 | `README.md`、`docs/project_story.md`、FastAPI/SQLite/LangChain/LangGraph 代码、WSL 11 项验收记录。V2 运行不依赖 Dify。 |
| 复用 V1 政策、20 条订单、45 条评估规格、架构/README 资产 | 已实现/有证据 | `docs/migration.md` 与阶段 0 `findings.md` 记录文件比对；V1 原始文件未修改。 |
| RET-01/QUA-01 与 V1 差异保持透明 | 已实现/有证据 | `data/policies/RET-01.md`、`data/policies/QUA-01.md` 标记 V2 来源，`docs/migration.md` 说明 V1 覆盖差异。 |
| 固定订单 1001：demo-a、定制商品、签收/反馈日期、质量问题 | 已实现/有证据 | `data/seed/v1_orders.json`、`tests/test_db.py::test_initialization_imports_v1_and_fixed_order`、`docs/migration.md`。 |
| 1001 的正确业务结论：无理由退货不适用，但可在 15 日内申请质量售后，需凭证并人工审核，不承诺退款/通过 | 已实现，端到端证据部分 | RET-01/QUA-01 原文与 `docs/migration.md` 有完整规则；RAG/WSL 边界用例已验收。但没有发现一个单独的端到端断言同时锁定订单日期、两条规则和所有禁止承诺项。 |
| 只用模拟数据，不执行真实退款/改址/删除 | 已实现/有证据 | Agent 写请求拒绝；退款审批只写 `approved_demo`；`tests/test_api.py` 对查询前后订单状态作断言；没有真实业务写工具。 |

## Python、FastAPI 与 SQL

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| Python 包结构、类型注解、异常处理、配置和环境变量 | 已实现/有证据 | `src/support_agent/` 包、TypedDict/Pydantic 类型、`config.py`、API/节点异常安全返回。 |
| Pydantic 请求/响应验证、GET/POST、HTTP 状态、Swagger/接口说明 | 已实现/有证据 | `src/support_agent/schemas.py`、`src/support_agent/main.py`、`tests/test_api.py::test_health_and_swagger_routes` 与 body validation；`docs/demo_runbook.md`。 |
| FastAPI 依赖注入基础 | 部分实现 | `Header(...)` 由 FastAPI 注入租户 Header；没有 `Depends` 风格的可复用认证/服务依赖。对当前单机 Demo 足够，教学点仍可在阶段 11 说明。 |
| 必要 async/await | 部分实现 | 应用 lifespan/middleware 使用异步接口，业务路由是同步函数；尚无异步业务调用链或 I/O 对照练习。 |
| SQLite、租户/订单表、主外键、索引、参数化查询和初始化 | 已实现/有证据 | `src/support_agent/db.py` 建有 `tenants`、`orders`、外键和租户索引；订单查询用参数化 `WHERE order_id = ? AND tenant_id = ?`。 |
| JOIN、事务、UPDATE/DELETE 原理与安全边界实践 | 部分实现/未作为功能使用 | 现有业务只需订单查询和幂等 seed 插入；没有 JOIN、订单 UPDATE/DELETE 路径，也没有专门的 SQL 事务学习记录。不能为学习项引入无必要业务写操作。 |
| 用户身份表或 Agent 任务表 | 未实现/明确 Demo 边界 | 当前没有 `users` 表或持久化 Agent 执行记录表；轨迹进入脱敏结构化日志，审批状态在 SQLite checkpoint。见 `docs/interview_kit.md`、`docs/langgraph_design.md`。 |

## LangChain、RAG 与 LangGraph

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| LangChain Chat Model、Prompt、Document、Splitter、Embeddings、Vector Store、Retriever | 已实现/有证据 | `src/support_agent/rag/answer.py`、`policies.py`、`retrieval.py`、`index.py`；索引/检索有本机测试与真实评估记录。 |
| LCEL 与 Output Parser | 已实现/有证据 | `answer.py` 使用 `ANSWER_PROMPT | chat_model | StrOutputParser()`；`docs/interview_kit.md` 已有组件职责说明。 |
| LangChain Tool 定义/调用 | 部分实现 | 业务“工具调用”是确定性 LangGraph 节点/普通 Python 服务函数，代码没有 `@tool`、`bind_tools` 或模型工具选择。安全路由刻意不用 LLM 决定授权；阶段 11 应先比较“显式 LangChain Tool”和当前节点函数的职责，不能为了技术覆盖强行添加。 |
| RAG 完整链路：加载、分块、Embedding、Chroma、检索、上下文、生成、引用检查 | 已实现/有证据 | `src/support_agent/rag/`；12 个政策源一源一块；36 条有证据标签的检索评估、14 条 Top-4/Top-8 人工审阅和约束层评估均有记录。 |
| 无可靠证据时拒答，防止引用伪造 | 已实现/有证据 | 空召回不调模型的测试、检索/生成错误安全答复、引用编号校验、`answer_constraints.py`、WSL policy QA 验收。引用 ID 有效不等于语义必然正确。 |
| 语义 grounding/最终回答事实正确性自动评估 | 部分实现 | 有 14 条逐例人工审阅和规则约束评估；同模型 LLM judge 被明确标为探索性且存在误判。尚无独立裁判或成熟事实级自动指标。 |
| State、Node、Edge、条件路由、checkpoint、interrupt/resume、单 Agent 执行轨迹 | 已实现/有证据 | `src/support_agent/agent/state.py`、`graph.py`、`nodes.py`；`docs/langgraph_design.md`；审批跨应用重启恢复测试与 WSL 验收。 |
| Tool 权限、身份与租户授权 | 部分实现 | 租户条件由后端 SQL 强制并有跨租户测试；`X-Tenant-ID` 是客户端演示范围选择，不是身份认证。审批接口没有真实审批人 RBAC。 |
| LangChain/LangGraph 架构理解由用户参与 | 尚未完成 | 代码和讲解材料已存在；用户参与式学习/设计确认尚未开始。已排入阶段 11，顺序 LangChain → LangGraph。 |

## 评估、追踪与故障注入

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| Logging/Tracing 记录路由、节点、订单工具、RAG 来源、耗时、错误并脱敏 | 已实现/有证据 | `src/support_agent/observability.py`、`main.py`、`docs/evaluation_and_observability.md`；WSL 容器日志字段由用户验收。 |
| RAG Hit@K/Recall@K/完整证据率 | 已实现/有证据 | Top-2/4/6/8 对照；36 条有标签案例，Top-4 Hit 100%、平均 Recall 86.6%、完整证据率 72.2%。 |
| Agent 路由、参数、工具结果、业务断言与 Bad Case 前后对照 | 已实现/有证据 | 35/35 路由、8/8 参数、9/9 工具调用、6/6 outcome、5/5 订单字段；修复前后记录与定义见 `docs/evaluation_and_observability.md`、`docs/interview_kit.md`。各分母不可合并成整体成功率。 |
| 故障：缺订单号、跨租户 | 已实现/有证据 | `tests/test_agent.py`、`test_api.py`、`test_db.py`。 |
| 故障：RAG 空召回/无可靠来源 | 已实现/有证据 | `tests/test_rag.py::test_rag_answer_does_not_call_model_when_retrieval_is_empty` 和 WSL 断言式验收。 |
| 故障：错误政策排序或回答违反政策 | 部分实现 | Top-8 冲突在人工审查中发现，约束层已修复高影响规则；尚无完整、独立的语义蕴含自动测试套件。 |
| 故障：工具 not_found | 部分实现 | 代码及 Agent 离线评估区分 `found/not_found`，但未找到明确的 API 端到端 not_found 故障注入用例。 |
| 故障：错误分支/提示注入/隐私索取 | 已实现/有证据 | 路由/API 单测与 WSL 11 项断言验收覆盖多类恶意/异常输入。 |
| 故障：数据库连接失败 | 已实现/有证据 | `tests/test_api.py::test_order_database_failure_returns_safe_error`。 |
| 故障：模型 API 不可用/真实超时/限流 | 部分实现 | Embedding/检索错误可注入并返回安全答复；真实聊天模型超时、限流和重试没有完整演练。 |
| 故障：checkpoint 恢复失败或状态损坏 | 部分实现 | 正常应用重启恢复和重复审批冲突有测试；损坏文件、缺字段或恢复异常没有专门注入验证。 |
| 故障：Docker 环境变量缺失 | 未验证 | 单测确认缺少 SiliconFlow Key 时构造 Embedding 会报错；没有找到 Compose 缺变量的启动/健康验收。 |
| 延迟基线、P50/P95 | 未实现 | 有单次节点时延日志；`docs/evaluation_and_observability.md` 记录尚无稳定统计基线。 |

## Docker、交付物与学习机制

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| Dockerfile、Compose、环境配置、数据持久化和 WSL 部署 | 已实现/有证据 | `Dockerfile`、`compose.yaml`、README；D 盘数据 bind mount 与 11 项容器验收由用户实测。 |
| 从 GitHub 干净克隆复现 | 未验证 | 当前已做 WSL 工作副本重建和公开发布；尚未从远端全新 clone 独立复现。排在阶段 13。 |
| 架构图与流程图 | 部分实现 | `docs/project_story.md`、`docs/langgraph_design.md` 含 Mermaid 图；仓库中未发现独立 PNG/SVG 图像资产。Mermaid 可作为源码图，不代表已交付渲染图。 |
| 演示记录/运行证据 | 部分实现 | `docs/demo_runbook.md`、项目状态和 WSL 实测文字记录完整；没有发现整理进仓库的正式演示截图/视频包。 |
| Bad Case 分析、架构取舍、面试包 | 已实现/有证据 | `docs/rag_answer_manual_review.md`、`docs/evaluation_and_observability.md`、`docs/project_story.md`、`docs/interview_kit.md`（含 3/10 分钟讲解、20 问、5 个故障案例）。材料未来仍需阶段 14 按最新代码复核。 |
| 让用户参与核心设计并在故障后定位/复盘 | 尚未完成 | 用户已指定学习顺序 LangChain → LangGraph → RAG → SQL → FastAPI，并要求每次先做架构介绍和设计引导。互动学习循环与受控故障判断尚未开始，排入阶段 11/12。 |

## 建议后续顺序

1. **阶段 11：LangChain 设计引导。** 先解释当前 `Prompt → Chat Model → StrOutputParser`、Retriever/RAG 边界与普通 Python/LangGraph 节点的区别，再让用户提出期望架构；核心模块未对齐前不改代码。
2. **阶段 11：LangGraph 设计引导。** 以实际 State、节点、条件边、checkpoint、interrupt 为图，优先请用户解释路由与恢复方案，再补充比较。
3. **阶段 12：确认 Demo 范围内需要补的验证。** 首选清单中尚缺的 not_found、聊天模型故障、checkpoint 损坏、Docker 缺 Key 等隔离故障；先用假模型/临时目录，不打真实服务、不碰正式容器。
4. **阶段 13：全新克隆复现。** 从 GitHub `main` 克隆到隔离路径；达到模型 Key 或 WSL 运行状态依赖时暂停并提示用户。
5. **阶段 14：核对介绍/演示交付。** 保证图示、面试数据和说明均与实际实现、实际验收范围一致。

阶段 10 证据只读核查完成；本轮没有运行测试、没有新增云端调用，也没有修改业务代码。建议指标只表示路线优先级，不是用户已批准开始生产化。
