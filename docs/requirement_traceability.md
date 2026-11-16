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
| FastAPI 依赖注入基础 | 已实现/有证据 | `auth.py` 的 `require_demo_identity` 由 `Depends()` 注入 Bearer 身份；`main.py` 的业务路由据此取得可信 user/tenant。测试覆盖缺 token、无效 token 和伪造 `X-Tenant-ID`。 |
| 必要 async/await | 部分实现 | 应用 lifespan/middleware 使用异步接口，业务路由是同步函数；尚无异步业务调用链或 I/O 对照练习。 |
| SQLite、租户/订单表、主外键、索引、参数化查询和初始化 | 已实现/有证据 | `src/support_agent/db.py` 建有 `tenants`、`orders`、外键和租户索引；订单查询用参数化 `WHERE order_id = ? AND tenant_id = ?`。 |
| JOIN、事务、UPDATE/DELETE 原理与安全边界实践 | 部分实现/未作为功能使用 | Agent run 插入/更新使用 SQLite 事务上下文；订单业务仍只读。JOIN 和订单 UPDATE/DELETE 不属于必要功能，不为学习清单添加无用写操作。 |
| 用户身份表或 Agent 任务表 | Demo 实现并验收；非生产认证 | Bearer demo token 映射固定用户/租户；`demo_users` 和 `agent_runs` 存于 SQLite，执行记录不保存原始问题。用户报告干净克隆 53 项 pytest 通过；另有 WSL 11 项验收通过。实现位置 `src/support_agent/auth.py`、`src/support_agent/db.py`、`src/support_agent/main.py`。 |

## LangChain、RAG 与 LangGraph

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| LangChain Chat Model、Prompt、Document、Splitter、Embeddings、Vector Store、Retriever | 已实现/有证据 | `src/support_agent/rag/answer.py`、`policies.py`、`retrieval.py`、`index.py`；索引/检索有本机测试与真实评估记录。 |
| LCEL 与 Output Parser | 已实现/有证据 | `answer.py` 使用 `ANSWER_PROMPT | chat_model | StrOutputParser()`；`docs/interview_kit.md` 已有组件职责说明。 |
| LangChain Tool 定义/调用 | 部分实现 | 业务“工具调用”是确定性 LangGraph 节点/普通 Python 服务函数，代码没有 `@tool`、`bind_tools` 或模型工具选择。安全路由刻意不用 LLM 决定授权；学习材料解释该边界，不为了技术覆盖强行添加 Tool。 |
| RAG 完整链路：加载、分块、Embedding、Chroma、检索、上下文、生成、引用检查 | 已实现/有证据 | `src/support_agent/rag/`；12 个政策源一源一块；36 条有证据标签的检索评估、14 条 Top-4/Top-8 人工审阅和约束层评估均有记录。 |
| 无可靠证据时拒答，防止引用伪造 | 已实现/有证据 | 空召回不调模型的测试、检索/生成错误安全答复、引用编号校验、`answer_constraints.py`、WSL policy QA 验收。引用 ID 有效不等于语义必然正确。 |
| 语义 grounding/最终回答事实正确性自动评估 | 部分实现 | 有 14 条逐例人工审阅和规则约束评估；同模型 LLM judge 被明确标为探索性且存在误判。尚无独立裁判或成熟事实级自动指标。 |
| State、Node、Edge、条件路由、checkpoint、interrupt/resume、单 Agent 执行轨迹 | 已实现/有证据 | `src/support_agent/agent/state.py`、`graph.py`、`nodes.py`；`docs/langgraph_design.md`；审批跨应用重启恢复测试与 WSL 验收。 |
| Tool 权限、身份与租户授权 | Demo 范围已验收；生产 RBAC 不适用 | 本地演示身份固定映射租户，后端 SQL 强制租户条件；用户报告身份边界测试及 WSL 11 项验收通过。公开 Demo token 不是生产认证，审批接口没有真实审批人 RBAC。 |
| LangChain/LangGraph 学习材料 | 已完成 | `docs/learning/` 含 LangChain、LangGraph、RAG、SQL、FastAPI 五章；中文材料链接实际代码，包含流程图、示例、重点和自测题。互动问答由用户安排后再开展。 |

## 评估、追踪与故障注入

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| Logging/Tracing 记录路由、节点、订单工具、RAG 来源、耗时、错误并脱敏 | 已实现/有证据 | `src/support_agent/observability.py`、`main.py`、`docs/evaluation_and_observability.md`；WSL 容器日志字段由用户验收。 |
| RAG Hit@K/Recall@K/完整证据率 | 已实现/有证据 | Top-2/4/6/8 对照；36 条有标签案例，Top-4 Hit 100%、平均 Recall 86.6%、完整证据率 72.2%。 |
| Agent 路由、参数、工具结果、业务断言与 Bad Case 前后对照 | 已实现/有证据 | 35/35 路由、8/8 参数、9/9 工具调用、6/6 outcome、5/5 订单字段；修复前后记录与定义见 `docs/evaluation_and_observability.md`、`docs/interview_kit.md`。各分母不可合并成整体成功率。 |
| 故障：缺订单号、跨租户 | 已实现/有证据 | `tests/test_agent.py`、`test_api.py`、`test_db.py`。 |
| 故障：RAG 空召回/无可靠来源 | 已实现/有证据 | `tests/test_rag.py::test_rag_answer_does_not_call_model_when_retrieval_is_empty` 和 WSL 断言式验收。 |
| 故障：错误政策排序或回答违反政策 | 部分实现 | Top-8 冲突在人工审查中发现，约束层已修复高影响规则；尚无完整、独立的语义蕴含自动测试套件。 |
| 故障：工具 not_found | 部分实现 | 已新增 `tests/test_api.py::test_random_missing_order_is_not_found_for_authenticated_tenant`，尚未运行；原有评估也区分 found/not_found。 |
| 故障：错误分支/提示注入/隐私索取 | 已实现/有证据 | 路由/API 单测与 WSL 11 项断言验收覆盖多类恶意/异常输入。 |
| 故障：数据库连接失败 | 已实现/有证据 | `tests/test_api.py::test_order_database_failure_returns_safe_error`。 |
| 故障：模型 API 不可用/真实超时/限流 | 部分实现 | Embedding/检索错误可注入并返回安全答复；fake Chat Model timeout 节点单测已添加但尚未运行；429 与 checkpoint 损坏仍待注入测试。统一 12 类场景索引见 `docs/troubleshooting/fault_cases.md`。 |
| 故障：checkpoint 恢复失败或状态损坏 | 部分实现 | 正常应用重启恢复和重复审批冲突有测试；损坏文件仍待隔离注入，见 `docs/troubleshooting/fault_cases.md`。 |
| 故障：Docker 环境变量缺失 | 部分覆盖 | 单测确认缺少 SiliconFlow Key 时构造 Embedding 会报错；Compose 缺变量的启动/健康行为仍未端到端验证，已列入 `docs/troubleshooting/fault_cases.md`。 |
| 延迟基线、P50/P95 | 未实现 | 有单次节点时延日志；`docs/evaluation_and_observability.md` 记录尚无稳定统计基线。 |

## Docker、交付物与学习机制

| 要求 | 状态 | 证据与边界 |
|---|---|---|
| Dockerfile、Compose、环境配置、数据持久化和 WSL 部署 | 已实现/有证据 | `Dockerfile`、`compose.yaml`、README；D 盘数据 bind mount 与 11 项容器验收由用户实测。 |
| 从 GitHub 干净克隆复现 | 用户报告已通过 | 用户在 D 盘干净 clone，venv/pip 安装成功、53 项 pytest 通过，并验收 health 200、Bearer 订单查询 200、无 token 401。 |
| 架构图与流程图 | 部分实现 | `docs/project_story.md`、`docs/langgraph_design.md` 含 Mermaid 图；仓库中未发现独立 PNG/SVG 图像资产。Mermaid 可作为源码图，不代表已交付渲染图。 |
| 演示记录/运行证据 | 部分实现 | `docs/demo_runbook.md`、项目状态和 WSL 实测文字记录完整；没有发现整理进仓库的正式演示截图/视频包。 |
| Bad Case 分析、架构取舍、面试包 | 已实现/有证据 | `docs/rag_answer_manual_review.md`、`docs/evaluation_and_observability.md`、`docs/project_story.md`、`docs/interview_kit.md`（含 3/10 分钟讲解、20 问、5 个故障案例）。材料未来仍需阶段 14 按最新代码复核。 |
| 自主开发与代码学习 | 学习材料已完成；互动练习待用户参与 | 新提示词由 Codex 主导设计和实现、用户通过代码学习。五章学习材料已发布；在用户安排学习时间后可进行复盘，不作为功能验收阻塞。 |

## 建议后续顺序

1. **阶段 14：最终材料一致性核对。** 校验 README、项目故事、面试包、演示手册、追踪矩阵与当前代码和用户验收结果一致；清除旧的 47 项/待复验/旧 Header 说法。
2. 保留案例库中 checkpoint 损坏、Compose Key/路径等未验证边界，不扩大阶段 12 的测试通过结论。
3. 生产化身份、审批 RBAC、多实例与运行安全不属于本地 Demo 验收，只有用户另行授权时才规划。

> 验收证据：用户报告干净 clone 全量 pytest 53 passed（18.39 秒），health 200、Bearer 订单 1001 查询 200、无 token 401；此前用户另报告 WSL health 200、11 项 verifier 全过。上述结果来自不同环境与验收步骤。

## 2026-11-16 更新提示词的新增/变更要求

用户提供了 `Python Full-stack Agent Engineering — Autonomous Development & Interview Preparation` 版本，明确取代早期的开发分工与优先级。以下变更并入后续路线：

| 新版要求/变化 | 当前状态 | 后续处理 |
|---|---|---|
| Codex 是技术负责人和主力开发者；用户主要学习理解，不应等待用户先交架构/代码 | 已更新 `AGENTS.md`、`task_plan.md` 与公开介绍 | 按自主开发继续；仅在真实密钥、外部授权、不可逆操作或缺少业务信息时停下询问 |
| 学习材料与真实项目同步，需中文、代码位置、数据流图、可运行示例、重点分级及每章 5–10 个问题 | 已完成 | `docs/learning/` 已发布五章，内容依当前源码说明职责/数据流、提供示例、重点和自测题。 |
| 模拟用户身份/本地演示认证、用户与租户数据、必要执行记录 | 已实现代码，待测试和 WSL 验收 | 静态公开 Demo token 映射固定 user/tenant；agent_runs 记录 trace、intent、状态和异常类型，不存原始问题；不声称生产认证 |
| 适度 CRUD 与事务基础 | 订单数据目前以 seed 插入和只读查询为主，真实订单更新/删除刻意禁止 | 阶段 12 只为安全的模拟任务/审批记录评估受限状态更新与事务；绝不添加真实退款、改址、删除 |
| 12 项故障案例库，记录现象/层次/根因/日志线索/定位/修复/防复发 | 案例库已完成；验证部分待补 | `docs/troubleshooting/fault_cases.md` 列出 12 类现象、定位、修复和防复发；random not_found、Chat Model timeout、checkpoint 损坏、Compose 缺 Key 等状态明确标为部分覆盖/待验证。 |
| P0/P1/P2 交付优先级、每阶段测试与自动进入下一阶段 | 已更新长期工作纪律；整体功能已交付，后续是 P0 缺口收尾 | 不被 Web UI、Langfuse/Phoenix、性能统计等 P1 和 Kubernetes/多 Agent 等 P2 拖延 |
| README 新环境复现、GitHub、面试材料均需完成 | GitHub/学习章节/面试材料已发布；干净克隆未验证 | 下一步阶段 13 隔离 clone，随后阶段 14 核对材料与验收一致性。 |

该新版提示词变更了阶段 11 的互动门槛：不再要求用户先提出架构；Codex 需要主动完成设计和开发并同步讲解。此前旧提示词的“用户先给设计方案后再实现”已废止。
