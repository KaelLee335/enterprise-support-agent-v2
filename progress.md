# 工作进度

## 2026-11-22 — Phase 3 Bad Case 闭环本机完成

- 用户要求后续阶段自动继续到需要其验收的节点。本阶段为 OOS runner 增加可机读 Bad Case ledger，收录期望/实际回答、证据、引用异常、自动初筛，以及待人工填写的根因、修复和回归测试字段。
- 初筛假设与人工根因分离；允许的人工分类为 DATA/CHUNK/RETRIEVAL/GENERATION/BUSINESS/ABSTENTION。生成 Markdown 同时提示分类仍需人工复核。
- OOS 单元测试 **5 passed**；全量 pytest **117 passed / 20.70s**。没有真实 OOS 调用、没有重写历史指标/报告、没有数据库或 WSL 操作。
- 后续离线证据边界核验已在同日完成，结果见紧随其后的 Phase 3 记录。

## 2026-11-22 — RAG 离线证据边界初查（随后已补直接冲突保护）

- 新增三个特征测试：无关证据带合法引用、矛盾证据无显式冲突状态、假模型按证据内指令作出错误承诺但引用检查通过。它们只刻画当前结构限制，不冒充真实模型攻击评估。
- 本机全量 pytest 后续达到 **123 passed / 19.41s**。离线阶段未调用聊天模型或刷新 OOS 指标。
- README 和 ARCHITECTURE 已从旧的 93 passed/“WSL 待部署”状态更新到现行 123 passed 与用户报告的 Phase 2/WSL 验收；RAG 报告的日期与证据级别保持明确。
- 经用户批准完成真实 Embedding 距离校准（见下方记录）；当前停在行为变化验收点。

## 2026-11-22 — Embedding 距离校准与显式冲突处理

- 新增 `scripts/calibrate_rag_distance.py`，用 12 条目标政策明确的合成可回答问题和 12 条合成无答案问题，经已配置 SiliconFlow `BAAI/bge-large-zh-v1.5` 对既有 12-chunk Chroma 计算全部政策排序距离。
- 真实调用仅为 Embedding；没有 Qwen/chat 调用，没有写入 Chroma、SQLite、没有重建索引或刷新 OOS 报告。
- 报告：`data/evaluation/oos/embedding_distance_calibration_v1.md`。12/12 可回答目标进入 Top-4；目标距离范围 0.6516–1.1380，无答案最近距离范围 0.9072–1.1817，存在较大重叠。该样本不支持安全的全局阈值，不能据此改变拒答策略。
- 用户批准只处理明确的直接矛盾，不添加全局阈值。新增 `src/support_agent/rag/evidence_conflicts.py`：仅当两条检索句子在移除显式“不/没/未”标记后完全一致、且一条有否定一条没有否定，并与用户问题共享已知主题锚点时，才标为冲突。
- 冲突触发时跳过聊天模型，返回带来源引用的“资料存在相反表述，请人工核验”；答案审计记录加入冲突计数。明确测试了直接对立会短路、普通商品/定制商品范围例外不会误报、退款发起与到账两个阶段不会误报、“无理由”中的“无”不是否定词、与提问无关的主题不拦截。
- 更新 `scripts/update_wsl_and_verify.sh` 同步 RAG answer/constraints/冲突模块，并加入容器内直接矛盾/范围例外 smoke。全量 pytest **126 passed / 20.28s**；没有调用 Qwen、没有改 Chroma/SQLite，也未在本会话操作 WSL。
- 当前停止点为实机验收：请用户执行 WSL 同步/重建与 `verify_phase6`、`verify_v21`，并反馈结果。

## 2026-11-22 — Phase 2 实机验收闭环并暂停（用户实测）

- 用户报告已备份 SQLite（`support_agent.db.bak-20261122`）、同步并重建 WSL 部署；三个容器 healthy，`verify_phase6.sh` 与 `verify_v21.sh` 全 PASS，EXIT=0。
- 用户确认 2026-11-18 的真实存量 `actor_id=NULL` 行重试后返回同一申请，legacy NULL 幂等兼容修复在持久数据上生效。
- Phase 2 权限模型实机验收完成。按用户要求结束并暂停，不自动启动下一阶段；运行结果为用户提供，本会话未操作 WSL。

## 2026-11-22 — 修复旧售后行的幂等兼容

- 用户报告：更新后的 `verify_phase6.sh` self-application 用例通过；WSL 首次运行 `verify_v21` 失败。根因为迁移新增的 `actor_id/customer_id` 在旧行中为 NULL，严格比较把 NULL 和新请求身份误判为幂等键冲突。
- 选择保留 NULL 的“历史未知”语义，不批量回填真实记录；在 `reserve_aftersale_request` 中跳过旧 NULL 审计字段比较，同时继续严格校验 user/order/platform/reason 和所有已有非空审计字段。
- 新增 legacy NULL API 重试回归：相同请求复用原申请、不再次调用模拟平台；变更 reason 仍返回 409。定向测试 2 passed / 4.19s，全量 pytest **115 passed / 20.29s**。
- 修复需同步至 `/opt/project2` 并重建容器后，重跑 `verify_phase6.sh` 与 `verify_v21.sh`；当前尚无该轮 WSL 结果。

## 2026-11-22 — 修正 Phase 2 WSL verifier 旧断言

- 用户报告：SQLite 迁移成功、三容器 healthy，验收前 17 项通过；唯一失败是审批人自批用例仍使用旧流程预期。
- 现行代码在审批人提交申请时已由角色守卫提前拒绝，chat 返回 `approval_status=forbidden_role`，不会创建待审批任务。更新 `scripts/verify_phase6.sh`，直接断言此 chat 状态；业务实现未改。
- 等待将更新后的 verifier 同步到 WSL 后重跑完整验收。此前的 17 项 WSL PASS 和迁移成功来自用户报告；本轮未操作 WSL。

## 2026-11-22 — Phase 2 权限模型本地实施完成（等待 WSL 验收）

- 用户批准四角色权限模型后，完成 Customer 所有权、Service 客户授权、Approver 任务分配与自批阻止、Admin 同租户管理、订单和 AgentRun Repository 范围、售后 actor/customer 审计拆分，以及 MockShop 先授权后取详情。
- 审批任务以 SQL 条件更新防止重复/并发审批；Graph interrupt 恢复前从当前身份和持久任务重新验证分配关系。
- 完整本机 pytest：**114 passed / 20.47s**。迁移兼容仅在测试临时库验证；未启动 WSL/Compose，未改持久 SQLite/Chroma，未提交或推送。
- 迁移影响、旧权限断言的修订原因和剩余风险记录在 `docs/phase2_permission_model_and_migration_proposal.md`。部署前需用户先备份持久 SQLite，然后运行既定 WSL 同步/验收流程；实机验收后本阶段暂停。

## 2026-11-18 — WSL V2.1 重复验收通过（用户实测）

- 用户在已部署提交 `43adc60` 后连续两次运行 `update_wsl_and_verify.sh`；两次均未重启 `mock-shop`，且订单 2003 已有售后申请记录。
- 两次均为三容器 healthy，`verify_phase6.sh` 与 `verify_v21.sh` 全 PASS，EXIT=0。
- 这验证 `verify_v21.sh` 可处理 fixture 已有售后记录的重复运行状态；WSL 结果来自用户实测，本会话未直接操作容器。
- V2.1 MockShop 集成部署验收完成。远程 CI 状态未在本次会话查询；项目代码提交已推送到 GitHub main（前序推送结果）。

## 2026-11-18 — V2.1 电商集成本机交付收尾

- 修复店铺 B 测试触发的 tenant 外键缺口：新增固定 `demo-b` tenant、`user-demo-b` 身份映射和 customer/store scope。新增正向读取断言，确认店铺 B 能读自己的订单与 webhook 事件；店铺 A 仍得到 404。
- 扩展 Vue：显示平台订单、物流、资格结果；支持店铺 A/B 身份切换；售后操作拆为“检查资格”和“确认创建演示申请”两个动作，并显式呈现 `pending_demo`。
- 新增 `docs/api_reference_v2_1.md`、`docs/evaluation_v2_1.md`、`docs/interview_guide_v2_1.md`；更新 README、ARCHITECTURE、task plan、AGENTS 和项目状态。
- 全量 pytest：**93 passed / 12.26 秒**；Vue production build 通过；`docker compose config --quiet` 通过；Python compileall 通过。
- 重新运行 `scripts/evaluate_agent_routes.py`：route 35/35 (100%)、订单参数 8/8 (100%)、工具 outcome 6/6、业务订单子集 5/5、SQLite unchanged。报告产物为 `data/evaluation/v2_agent_routes.json`。
- 更新 `scripts/update_wsl_and_verify.sh`：同步新增 `mock_shop_api.py` 和全部 integration modules，随后执行既有 phase 6 verifier 及新增 `verify_v21.sh`。新 verifier 覆盖两店铺隔离、资格检查、明确确认申请、幂等重试、HMAC Webhook、重复事件、状态同步、无效签名和跨租户事件隐藏。
- CI smoke 增加店铺 B 正向查询、跨租户拒绝及 pending demo 申请；CI paths 纳入根目录架构和计划记录。
- 最终静态检查：Compose config、GitHub Actions YAML 与嵌入 Python 语法、Python compileall 通过；本机未执行 Docker `up` 或 GitHub CI。
- 未启动 Compose、未操作 WSL、未调用外部模型/真实平台。待用户在 WSL `/opt/project2` 执行更新脚本并提供容器验收结果。

### 2026-11-16：依照完整项目说明扩展阶段路线

- 重读用户提供的《Enterprise Support Agent V2 — Python Full-stack Agent Engineering》。按当前用户要求将它作为本项目的工作标准；文档末尾“现在执行阶段 0”属于原始启动指令，阶段 0–9 已完成，不重新执行。
- 总计划扩展为阶段 10 需求追踪审计、阶段 11 用户参与的核心模块理解/设计确认、阶段 12 经确认的缺口修复和故障注入、阶段 13 干净克隆复现、阶段 14 最终交付/面试材料核对、阶段 15 可选生产化。
- 下一阶段只读盘点，计划建立 `docs/requirement_traceability.md`；本轮没有改业务代码、运行测试或发起新云端调用。
- 初步核实已存在 Mermaid LangGraph 路由图和面试材料；租户 Header 非身份认证、没有 users 表；故障注入完整覆盖状态待逐项确认。这些都写入 `findings.md`，最终状态以阶段 10 的逐项证据为准。
- 用户确定阶段 11 学习顺序为 LangChain、LangGraph、RAG、SQL、FastAPI，并要求每次进入主题前先由 Codex 介绍现有架构和设计问题、引导用户给思路；用户负责核心构想与学习，Codex 在设计对齐后协助实现。已加入路线图和接续说明。
- 按新提示词更新公开介绍：README 项目定位、项目故事/协作方式、面试包中的 3 分钟自我介绍；GitHub About 描述已更新为端到端 Python Agent 工程学习项目，并明确模拟数据/Demo 边界。实际实现指标未改写，阶段 10 需求追踪尚未开始。
- 阶段 10 原始要求追踪完成，产物 `docs/requirement_traceability.md`：覆盖定位与 V1 复用、固定案例、Python/FastAPI/SQL、LangChain/RAG/LangGraph、身份/租户权限、评估/追踪、逐项故障注入、Docker、交付物和学习机制。严格区分已实现、部分实现、未实现和未验证；本轮只读，没有运行测试、改业务代码或调用模型。
- 阶段 11 已开启第一个主题 LangChain。已向用户介绍当前链路边界：RAG 生成链 `PromptTemplate → Chat Model → StrOutputParser`；LangGraph 管理业务状态分支；当前订单节点不是 LangChain `@tool`。待用户先提出设计思路，再决定解释/改造，不会为了技术栈清单自动新增工具封装。
- 用户提供新版自主开发提示词并要求更新项目记忆：Codex 现在担任技术负责人/主力开发者，用户为学习者；不再要求用户先设计架构或逐模块批准。保留其学习顺序 LangChain → LangGraph → RAG → SQL → FastAPI。每章需写中文代码绑定学习材料（代码位置、数据流图、示例、重点分级、5–10 个问题）。新版 P0 新增 Demo 身份/权限、必要任务记录、受控 CRUD/事务和统一故障案例库；将以模拟身份与隔离数据补齐，不触及真实业务写操作。已更新 `AGENTS.md`、`task_plan.md`、`docs/project_status.md`、追踪矩阵及公开项目介绍。下一步继续阶段 11 LangChain，由 Codex 主动写学习章和相应验证，不等待用户先给设计方案。

### 2026-11-16：整理项目总路线及阶段 10 计划

- 阶段 0–9 已完成状态重新汇总；阶段 9 保留用户确认的 Windows 用户登录触发设置。
- 下一阶段建议为阶段 10「公开仓库全新克隆复现」：在隔离目录从 GitHub `main` 克隆，检查 README 首次运行、配置模板、政策索引/密钥边界和数据持久化要求，不影响运行中的 WSL Docker 服务。
- 本轮只建立了总体路线图和阶段 10 的执行步骤、验收条件及需用户操作的暂停点；尚未开始克隆或执行验证。
- 阶段 11 演示迭代、阶段 12 生产化及学习问答仍为候选/暂缓，避免扩大本轮范围。

## 2026-11-14

- 开始阶段 0；已读取用户提供的项目范围、工程目标和阶段要求。
- 已初始化 `task_plan.md`、`findings.md` 和 `progress.md`。
- 确认 V1 路径 `[本机路径]`，并核对 10 份政策、20 条订单、45 条评估规格、README、架构说明和结果 JSON 的 V2 副本哈希；各副本均与来源一致。
- 确认 V1 自带 Dify DSL、配置指南、评估脚本和历史报告；DSL 不包含可直接迁移的向量索引。V1 的 `.env.example` 有用户既存修改，已保持不动。
- 记录 RET-01/QUA-01 是 V2 补充事实，不应声称为 V1 原规则；记录评估 JSON 的 127 captured 与 125 actual saved 口径差异。
- 当前阶段 0 完成；未运行测试或启动服务。阶段 1 基础 API/SQLite 代码已存在但尚未在本轮运行验证。工作区既有 Docker 配置尚未验证；用户告知 Dify 由桌面 `启动dify.bat` 启动，本轮没有将其等同于 V2 服务。
- V1 首次 Git 状态检查遇到 safe.directory 所有权拦截；改用单次 `git -c safe.directory=...` 只读查询成功，没有更改全局 Git 配置。WSL CLI 在当前会话仍返回异常，记录为未核实环境项。
- 阶段 1：在工作区创建 `.venv` 并按 `pyproject.toml` 安装项目和开发依赖。测试最终 6 passed；pytest 默认用户临时目录及项目 `.pytest-tmp` 在本会话不可写，因此使用授权的可视化输出目录作为 basetemp、禁用 pytest cache 后通过。
- 本地启动 Uvicorn 完成 HTTP 验收：`GET /docs` 200；`GET /health` 返回 `ok`；`demo-a` 查询订单 1001 成功；`legacy-demo` 查询同订单返回 404。测试服务已停止，数据库建于本地输出目录，不污染演示数据。
- 官方 SiliconFlow 文档核查：支持 OpenAI 风格 API 接入，`https://api.siliconflow.cn/v1` 为文档示例 Base URL，官方托管文档给出 `BAAI/bge-large-zh-v1.5` Embedding 示例；模型可用性以账户目录为准。用户已确认 SiliconFlow。
- 用户确认每份政策一个块；12 份政策目前约 160–370 字符。
- 阶段 2 本地代码已实现：政策加载和来源元数据、递归切分器（当前文档保持整块）、SiliconFlow OpenAI 兼容 Embedding client 配置、Chroma 本地持久向量索引、稳定 ID/哈希增量更新、模型隔离 collection、检索证据输出、索引/搜索 CLI 和 README/RAG 设计说明。
- 新增配置只从本地 `.env` 读取 key；缺 key 时在发网络请求前报清晰错误。空文档索引被阻止，生成索引目录加入 `.gitignore`。
- 安装 LangChain 依赖后测试 11 passed。测试使用确定性假 Embeddings，不调用云 API；覆盖来源元数据、检索结果、增量索引、空查询及空索引防护。
- 用户补充确认 SiliconFlow `.env` 已配置，免费账户的 `BAAI/bge-large-zh-v1.5` Key 验证通过；真实索引 12 文档/12 chunks 已由用户在允许联网的环境完成。项目已存在 `data/vector_store/chroma.sqlite3`，用户确认 POL-03/POL-06 检索正常。
- `scripts/verify_sf_key.py` 曾硬编码真实 Key，已改为从本地设置读取且只输出模型名/维度，不显示 Key。无论免费与否，源码和日志中均不保留凭据。
- 新增 `scripts/evaluate_retrieval.py`，批量嵌入 V1 45 个评估 query（仅计分 36 个有 `required_evidence` 标签的案例），输出逐案例召回、Hit@K、Recall@K 和指标 JSON。
- 在用户提供的已配置 `.env` 下获准运行真实检索评估：36/45 scored，Hit@4 100.0%，mean Recall@4 86.6%，全部必要 evidence 均召回率 72.2%。报告 `data/evaluation/v2_retrieval_20261114T092303Z.json`。
- 多证据漏召回集中在 no-answer 和 security_request，常见遗漏是 POL-10；全量已标注案例都至少命中一份预期政策。后续先检查 k 值和补证据策略；Reranker 可改善排序，不能弥补召回候选集合本身缺失。
- 最近重跑 pytest 时，旧 basetemp 清理失败；改用全新 basetemp 后全套 13 passed。
- 用户选择 SiliconFlow Chat 模型 `Qwen/Qwen2.5-7B-Instruct`。新增 LangChain LCEL RAG 回答链：政策检索、证据上下文、中文回答 prompt、StrOutputParser、引用 ID 对照检查；新增 `scripts/ask_policy.py`。
- `ask_policy.py` 使用真实 SiliconFlow API 对“定制商品出现质量问题怎么办？”完成一次调用，召回 QUA-01、RET-01、POL-03、POL-10，输出引用检查通过且引用 QUA-01。当前执行工具的 Windows 控制台中文输出编码异常，但 HTTP 请求成功且 source id/citation 结果可见。
- 增加假 ChatModel 测试：合法引用、未检索引用被标记、无检索证据时不调用模型。全套回归测试 16 passed。
- 用户确认第一版使用单轮 State，不加 `chat_history` 或 checkpoint。
- 阶段 3 实现完成：新增 TypedDict `SupportState`、确定性 `route_request`、租户过滤只读 `lookup_order`、写请求 `refuse_write_request`、缺参 `clarify_request`、`retrieve_policy` 与 `generate_policy_answer` 节点和条件边；FastAPI 新增 `POST /chat`。
- 路由将写操作意图置于订单解析前，并区分“退款进度查询”和“执行退款”；只有只读查询进入 SQLite。跨租户查不到订单时不泄露订单存在性；Header 缺失/请求体为空由 FastAPI 返回 422。
- 新增 API 和路由回归后，全套测试 25 passed。测试覆盖 OpenAPI、请求校验、订单租户隔离、写操作拒绝、订单号澄清和退款进度只读路由；政策模型调用使用既有单独 RAG 真实验收，不在测试中连外网。
- `/chat` 已通过 TestClient 测试；尚未在外部服务环境用 HTTP 做真实 `/chat`+模型端到端检查。`X-Tenant-ID` 仍是演示范围标识，不是身份认证；State 无 checkpoint。

### 阶段 4–5 更新

- HITL 按用户确认实现：退款请求进入待审批；批准只标记 `approved_demo`，不修改订单、不执行真实退款。SQLite checkpoint 跨应用重启恢复；跨租户不可见、重复决定返回 409。
- API 为请求返回 `X-Trace-ID`，`/chat` 另返回 `trace_id`；JSON 日志串联 HTTP、Agent 路由和检索事件，不记录问题正文或模型答案。
- 新增 `scripts/evaluate_agent_safety.py` 复用 V1 确定性 no-write 用例。SEC-01 初次暴露“把订单改成已退款”未识别为写请求，已补规则；当前 4/4 通过，报告 `data/evaluation/v2_agent_safety.json`。
- 新增数据库与 Embedding 故障注入测试。当前全量 33 项测试通过，`compileall` 成功。
- Bad Case 与评估口径见 `docs/evaluation_and_observability.md`。有限安全规则评估不代表完整 Agent 任务成功率；RAG 多证据漏召回仍有 POL-10/NA-03 等案例。
- 阶段 5 完成时，阶段 6 尚待 WSL 验收；后续结果见下方阶段 6 最终验收记录。

### 阶段 6 准备

- 检查发现 Dockerfile 原先未复制政策源文件和 Chroma 向量库；现已补齐。Compose 通过 `.env` 读取本机 Key、挂载 `data/` 保留订单库/审批 checkpoint/向量数据，并加 `/health` 健康检查。
- `compose.yaml` 已用本机 YAML 解析器成功解析；更新后 33 项测试通过。
- 容器尚未构建或运行：本会话 PowerShell 找不到 Docker CLI，`wsl.exe` 的 stdout 返回不可读字符。需要在用户已启动的 WSL Docker 环境完成实际验收。

### 阶段 6 首轮 Docker 验收（用户实测）

- 用户确认从 WSL `WSL 项目目录` 构建成功，容器 `project2-support-agent-1` 为 `Up (healthy)`；`/health` 返回 200，`GET /orders/1001` 与 `POST /chat` 全链路成功，订单只读回答返回“已完成”。
- 用户确认在 `本机 Windows 挂载目录` 构建遇到 BuildKit 权限限制，因此改用 `WSL 项目目录` 作为构建上下文；`本机持久化数据目录:/app/data` 绝对 bind mount 仍指向 Windows D 盘数据。
- 用户修复并同步 `main.py` 的 seed 路径三级回退，处理 site-packages 安装布局启动失败。
- 用户实测 pytest 33 项通过；后续本地修复中文紧邻订单号解析，并在 Windows 项目全量回归 35 项通过。Compose YAML 已解析验证。
- 当前容器实测版本早于最后的 `ORDER_ID_PATTERN` 和 D 盘绝对挂载变更，需要同步最新 `src/support_agent/agent/nodes.py`、`compose.yaml` 到 `WSL 项目目录` 并 `docker compose up --build -d` 后，验证“查询订单1001”及 `healthy`。

### 最终 Docker 验收（用户实测）

- 用户已将订单号路由修复和 D 盘绝对 bind mount 同步到 `WSL 项目目录` 并重建；无空格输入“查询订单1001”命中 `order_lookup`。
- 用户发现 pip 安装后相对数据路径错误指向 `site-packages`，已修改 `config.py` 为基于当前工作目录解析相对路径，并将 DATABASE/CHECKPOINT/VECTOR_STORE 统一使用 `_resolve_env_path`。seed 路径使用三级回退。
- 最终验收全绿：`/health` 200、订单查询、无空格订单号查询、退款进入审批 `pending`、政策问答引用 POL-06 且 `citations_valid=True`、容器日志 0 error；pytest 35 passed。
- 阶段 0–6 完成，Docker 结果由用户在 WSL 环境实测确认。
- 新增 `docs/demo_runbook.md` 端到端演示手册，覆盖启动/健康、订单号识别、租户隔离、POL-06 引用、写操作拒绝、退款审批及验收清单；同步修正旧版 LangGraph 设计说明与 README 中过时的阶段状态。
- 新增 `docs/project_story.md` 系统架构图、可核验指标、关键技术取舍、约一分钟讲解稿、常见追问和已知限制；修正 RAG 设计文档中“`/chat` 尚未接入”的过时描述。
- 根据最初项目需求，新增 `docs/interview_kit.md`：3 分钟介绍、10 分钟架构讲解、20 个技术问题与参考回答、5 个故障案例及 LangChain/LangGraph 分工、未使用多 Agent/Redis/Kubernetes 的解释。
- 补齐结构化观测：HTTP/Node 开始结束耗时、路由/订单工具参数与结果摘要、RAG 来源 ID 和 distance、引用/审批状态；记录限长且脱敏的用户输入预览。预期 interrupt 记录为 `node_pause` INFO，不会报 ERROR。
- 观测日志脱敏/耗时、审批暂停非错误均加入测试；本机 pytest 39 passed。当时容器尚未包含这批代码；该状态现已由下方“结构化追踪最终容器验收”更新并解决。
- 新增 Agent 离线路由/工具评估 `scripts/evaluate_agent_routes.py`：复用 V1 标签，35 个可映射路由 35/35、标注参数 8/8、临时 SQLite 工具调用 9/9、预期 outcome 6/6、结构字段 5/5；查询前后数据库相同。报告 `data/evaluation/v2_agent_routes.json`，修复前对照 `data/evaluation/v2_agent_routes_before_fixes.json`（路由 30/35）。
- 评估暴露空输入、多个/格式错误订单号、索要个人联系方式和提示注入四类分流问题；空输入由 Pydantic 在 API 层拒绝，其余增加澄清/拒答规则及 API 回归。更新后 pytest 47 passed，RAG/安全评估各自仍保留独立指标和分母。
- 最新结果复跑确认：Agent routes 35/35，order parameters 8/8，模拟工具调用 9/9，outcomes 6/6，业务订单字段 5/5，临时 DB 未变化；安全路由 4/4；pytest 47 passed。修复前路由报告保留为 `data/evaluation/v2_agent_routes_before_fixes.json`，路由 30/35。
- 用户已将 `nodes.py`/`state.py` 同步到 WSL 并重建，验收脚本 `scripts/verify_phase6.sh` 与 Swagger 均通过：格式错误/多订单号澄清、个人信息/提示注入拒答，以及正常订单查询和 POL-06 RAG 回归。
- 用户指出当前 `dockerd` 不自启，由会话持有。Docker 容器与功能已完成验收；daemon 跨发行版关闭/Windows 重启后的生命周期还未核实。新增 `docs/wsl_docker_lifecycle.md` 记录只读检查与避免重复启动 daemon 的注意事项。
- 将 `scripts/verify_phase6.sh` 改为断言式验收：health 非 200、intent 不符、回答缺少预期文本或 POL-06 引用无效时会失败；README 已补运行命令。需在 WSL `WSL 项目目录` 同步脚本并运行，以验收脚本自身和当前服务。
- 用户已在 `WSL 项目目录` 运行断言式验收脚本，7 项健康/安全/回归检查全部 PASS，EXIT=0。WSL 只读状态：`pgrep -a dockerd` 为 PID 11；`systemctl is-active docker` 为空，`is-enabled docker` 为 `enabled`。这确认 daemon 当前运行，但不足以证明 systemd 正在管理或重启后会自启；没有修改 WSL 启动配置。服务演示期间保持 `inbox` WSL 会话运行。
- 使用项目本机 `.env` 对同一 RAG 标注集完成 Top-2/4/6/8 对比：Hit@k 分别为 97.2/100/100/100%，平均 Recall@k 为 77.3/86.6/89.4/99.1%，完整证据率为 58.3/72.2/77.8/97.2%。Top-2/6/8 报告分别为 `data/evaluation/v2_retrieval_top2.json`、`data/evaluation/v2_retrieval_top6.json`、`data/evaluation/v2_retrieval_top8.json`。默认 `RAG_TOP_K=4` 暂不更改，需结合 LLM 答案语义质量与延迟/token 成本再决策。
- 用户明确授权后，已对 14 条答案要点明确的政策 QA 用例分别生成 Top-4/Top-8 答案并以 Qwen 同模型作探索性评分，完整报告 `data/evaluation/v2_rag_answers.json`。引用编号静态检查均为 100%；LLM judge 要点覆盖率 76.9%/71.8%，grounded/引用支持 92.9%/92.9%。人工抽样发现 judge 误判 KB-04 Top-4，并发现 KB-04 Top-8 出现与 POL-04 冲突的表述；这些自动分数不能视为准确率，默认 Top-4 保持不变。更换 Top-k 前需更可靠的独立语义评审与成本分析。
- 按用户要求建立根目录 `AGENTS.md` 和 `docs/project_status.md`，将项目边界、已验收状态、未完成事项、接续规则写入。另新增 `docs/rag_answer_manual_review.md`，逐例记录 14 组 Top-4/Top-8 答案的遗漏和事实问题。
- Prompt-only 实验结果记录：多条长规则导致矛盾输出，保存在 `data/evaluation/v2_rag_answers_prompt_v2_top4.json`；短规则 4 例定向运行超时中断，未形成完整报告；后续两条规则在 KB-04 输出没有再直接否认排除条款，但引入未经证据支持的替代路线，MVP-KB-BOUNDARY 仍未分清质量问题/无理由退货。输出见 `data/evaluation/v2_rag_answers_prompt_v4_targeted_top4.json` 与 `v2_rag_answers_prompt_v5_targeted_top4.json`。所有试验 Prompt 已撤回，`answer.py` 保持用户验收的原版本。
- 因单纯 Prompt 调整不稳，新增 `docs/rag_grounding_hardening_plan.md`，建议以版本化、可审计约束层解决政策排除/条件遗漏；实现前需用户决定是否扩大项目范围，备选是保留演示限制。
- 用户确认继续实现约束层。本机 `answer_constraints.py` 加入规则：POL-04 进液排除和 POL-02 质量问题退货分流为确定性兜底；POL-02 退货条件、POL-05 运费/指引、POL-06 两阶段退款、POL-09 发票隐私/范围约束按需补充。命中/执行约束 ID 加入答案结果、评估文件和 `rag_answer_constraints` 结构日志。原始 Prompt 未改，`RAG_TOP_K` 仍为 4。
- 约束层 14 案例 Top-4/Top-8 全量评估完成：28 条输出引用检查 28/28 有效；每档匹配 11 条约束，分别 6/7 条执行补充/兜底。跳过已知不可靠的同模型 judge，并人工审阅关键兜底输出。报告 `data/evaluation/v2_rag_answers_constraints_v3.json`。
- 新版本仅在 Windows 工作区完成评估；尚未同步至 `WSL 项目目录`，也未重建/重验 WSL Docker。下一步需用户在其 WSL 会话同步本次应用源文件、重建容器并运行 `scripts/verify_phase6.sh`。
- 为减少 WSL 手工同步错误，新增 `scripts/update_wsl_and_verify.sh`：会复制 `answer.py`、新约束模块、`nodes.py` 和扩充后的验收脚本；执行 `docker compose up --build -d`、轮询容器 `healthy` 与 `/health`，再运行阶段 6 全集检查。脚本已按 `本机数据目录` → `WSL 项目目录` 的既定路径写好，但尚未在 WSL 运行。
- 截图复核：WSL 的 POL-06 回答包含退款处理 1–3 个工作日、到账 1–5 个工作日、取决于支付渠道及“具体到账时间无法保证”，并引用 POL-06；内容符合规则。失败点仅为 WSL 上旧版 `verify_phase6.sh` 的措辞白名单遗漏该同义句。检查确认 D 盘脚本当前已接受“具体到账时间无法保证”。下一步只需将该脚本复制到 `WSL 项目目录/scripts/verify_phase6.sh` 并重跑，不需重建容器；等待用户回报复验结果。
- 用户随后确认已同步脚本并重跑：健康检查通过，11 个业务用例全部 PASS，EXIT=0；其中此前失败的 POL-06 退款两阶段时限检查现已通过，POL-04 进液排除、POL-02 质量故障路由及 POL-09 发票隐私边界也全部通过。扩充版阶段 6 验收完成，无需重建容器。剩余可选项是 WSL daemon 生命周期只读诊断；生产化能力不在演示验收范围。
- 用户提供 Docker 启动恢复实测：Ubuntu WSL 原为 `Stopped`，触发 `Start-ScheduledTask` 后日志显示 `dockerd ready`，Docker 容器 `project2-support-agent-1` 为 `Up (healthy)`，health 返回 200。结合 `/proc/1/comm` 为 `init`、`systemctl is-active docker` 无输出、`is-enabled` 为 enabled，结论是已验证计划任务可从停止的发行版恢复 Docker 与项目；不能据此推断 Windows 完整重启后会自动触发。记录更新在 `docs/wsl_docker_lifecycle.md`，无需改 systemd 或 WSL 配置。
- 按阶段计划完成最终交付文档核对：修正 README、Evaluation 和 RAG 人工复核报告中“约束层尚未部署/验收”的过期说明；更新 AGENTS 接续状态；findings 中保留原始历史记录并明确标注已被后续实测取代。原计划阶段 0–6 均已完成，目前无待执行的必选阶段；剩余的是可选 Windows 开机计划任务设置核查，以及用户此前暂缓的学习问答。
- 阶段 7（发布就绪/可复现交接）开始：检查发现 Dockerfile 直接 `COPY data/vector_store`，但该本机生成目录在 `.gitignore` 中排除，会使全新克隆无法构建；Compose 又把数据路径写死为 `本机持久化数据目录`。已移除 Docker 镜像对向量目录的构建依赖（运行时由持久化挂载目录读取）、通过 `PROJECT_DATA_DIR` 参数化数据路径并保留当前 D 盘默认、完善 `.gitignore`/`.dockerignore`、更新 `.env.example` 和 README，新增 `docs/release_readiness.md`。已在缺少 `.git` 时初始化本地 Git 仓库，未提交/推送。初始化后工具环境多次返回 `setup refresh had errors`，因此暂未完成 `git status`/ignore 审查和 Compose YAML 检查；这些需先恢复命令行再完成。随后需要用户在 WSL 同步 Dockerfile/Compose/忽略规则，构建并跑扩充版验收。
- 阶段 7 验收完成（用户实测）：`git status --short` 仅列出预期项目文件/目录；`.env`、虚拟环境、pytest 临时目录、数据库/WAL、向量库和 egg-info 等 7 项均命中 `.gitignore`，`.env.example` 未忽略。用户已同步 Dockerfile、Compose、`.dockerignore` 至 `WSL 项目目录`；镜像成功构建，容器 recreated/started 并为 `healthy`。`docker inspect` 确认唯一数据挂载 `本机持久化数据目录 -> /app/data`；`verify_phase6.sh` 11 用例全通过、EXIT=0。首次构建期间的 curl 56 是容器尚处于 health: starting 时的瞬态请求，容器就绪后复跑验收全绿。未提交或推送 GitHub；该结果已更新至 `docs/release_readiness.md`、`task_plan.md` 和 `docs/project_status.md`。
- 阶段 8 本地发布准备完成：GitHub 连接已可用，本地终端经命令级 `safe.directory` 参数恢复；审阅 93 个待提交文件，确认 `.env`、本机数据库/WAL、向量库、虚拟环境、测试缓存和 egg-info 均不在清单中。已知 token 格式扫描无命中，`.env.example` 的 API Key 留空。Compose YAML 解析成功，数据挂载模板为 `本机持久化数据目录 -> /app/data`。初始本地提交 `e68a1cea3bc6f31cb7704c709f6273aae900ee04` 已创建，使用 GitHub noreply 邮箱保护本机个人邮箱；当前无 remote。GitHub 工具未提供创建仓库操作，待用户创建空白公开仓库 `enterprise-support-agent-v2` 并提供 URL 后推送。没有输出或提交任何凭据。
- GitHub 公开仓库已通过本机 Git Credential Manager 认证创建：`https://github.com/KaelLee335/enterprise-support-agent-v2`，visibility=public，空白初始化（无 README/license/gitignore）。未输出令牌。下一步添加 origin 并推送本地 `main` 上的首个提交，再核对远端分支与文件清单。
- 最终发布验收：本机 push 成功，GitHub API 确认仓库 public、默认分支 `main`；`git ls-remote` 返回 HEAD `04503a162aabaf671d90bbe7d3859100cd0162cc`，本地状态为 `main...origin/main`。远端树 105 项且未截断，含 README、`src/`、`tests/`，未出现 `.env`、数据库/WAL、`data/vector_store`、虚拟环境、缓存或 egg-info 路径。虚拟网卡只读检查显示 WLAN、WSL、Mihomo、VMware 适配器在线；未更改网卡或路由设置。
- 阶段 9 主机启动只读审查：发现 `\\现有启动任务` 执行 `wsl.exe -d Ubuntu -u root -- /usr/local/bin/Docker 启动脚本`，由当前用户以 Interactive/ Limited 运行；触发器是已启用 Logon，不是 Startup。任务 State=Running；最近执行时间 2026-11-16 09:58:58，结果代码 267009。该检查只读取任务设置，没有触发或修改任务、Docker daemon、WSL/systemd 或虚拟网卡。README、`docs/wsl_docker_lifecycle.md`、`docs/project_status.md`、`task_plan.md` 和 `AGENTS.md` 已记录该边界。若用户需要登录前的开机自启，需先确定并授权系统任务变更。
- 用户澄清“开机触发”是指 Windows 用户登录时触发；截图确认 `现有启动任务` 配置本来就是 Logon trigger，与只读检查一致。用户选择保留现状，无需修改。阶段 9 完成；未验证 Windows 重启后的自动触发行为。

### 结构化追踪最终容器验收（用户实测）

- 最新 `observability.py`、`agent/graph.py`、`main.py` 已同步至 `WSL 项目目录` 并重建，构建耗时约 1 分 33 秒。
- 用户为降低重复构建时间并处理 pip 超时，将 Dockerfile 改为先安装依赖、再安装本地源码的缓存分层，并切换到 TUNA pip 源、延长下载超时；该 Dockerfile 已同步在 Windows 工作区。
- 订单日志实际包含 `question_preview`、`node_start/end` 和 `duration_ms`（route 约 0.5ms、lookup 约 16.9ms）。政策问答日志包含检索来源及距离，POL-06 distance=0.625 为此次最相似来源，生成节点约 756ms、`citation_valid=true`。退款审批暂停记录为 INFO `node_pause`，状态 `pending`。
- 全程无 ERROR；本机日志脱敏/耗时等回归 39 项通过。用户要求将学习理解问题留到之后统一处理，本轮不追加答题问题。
# 2026-11-16 — 快速执行通道恢复尝试

- 用户要求快速完成项目，并要求明确写出需要其操作的部分。
- Windows 执行通道在 `git status`、`git diff --check` 等只读调用开始前报错：`helper_unknown_error: setup refresh had errors`；多次重试仍未恢复。
- 新增 `docs/learning/fast_mode_handoff.md`，列出用户只需恢复 Codex 项目执行通道并回复“继续”，以及恢复后自动执行的代码审查、全量测试、文档更新和 WSL 验收流程。
- 最近已知测试记录仅为定向 API/DB 测试 26 项通过；本轮没有运行完整测试，没有同步/重建/验收 WSL。
- 下一步：恢复执行工具后立即检查真实工作树和完整差异，勿根据摘要猜测待同步文件。


# 2026-11-16 — 执行通道交接恢复（WorkBuddy 代执行）

- Codex 执行通道 `setup refresh had errors` 期间，交接清单由 WorkBuddy 代为执行完成。
- Git 状态：`safe.directory` 已加入全局配置（仓库属主为 CodexSandboxOffline）；工作树 15 个修改文件 + `src/support_agent/auth.py`、`docs/learning/` 两个未跟踪项，全部为 Codex 的身份认证与运行记录改动。
- 忽略规则复核：`.env`/`.venv`/`.pytest-tmp`/`data/*.db`/`data/*.sqlite*`/`data/vector_store`/`*.egg-info` 全部命中；`.env.example` 未被忽略，可入库。
- API 身份映射与租户隔离审查：Bearer token → 固定 DemoIdentity（user-demo-a→demo-a、user-legacy-demo→legacy-demo）；`X-Tenant-ID` header 已全线移除，伪造 header 被忽略；`agent_runs` 表带 tenant 外键与状态 CHECK，所有查询 `WHERE run_id AND tenant_id`，运行记录不含 question 明文；故障用例已补齐（缺失 token 401、无效 token 401、伪造 header、跨租户 run 404）。
- 全量 pytest：**51 passed, 267s**（此前定向测试 26 项），唯一警告为 `.pytest_cache` 权限（已知无害）。`PYTEST_EXIT=0`。
- WSL 同步与验收：auth.py 等 7 个源码/测试文件同步至 `WSL 项目目录`，`DEMO_TOKEN_*` 追加至 WSL `.env`，容器重建后 health 200、verify_phase6.sh 11 用例全 PASS。
# 2026-11-16 — 接收本地与 WSL 验收记录

- 用户截图报告：身份映射/租户隔离审查通过；全量 pytest 51 passed（267 秒）；`progress.md`、`findings.md`、`docs/project_status.md` 已记录实测；WSL 容器重建后 health 200 且 `verify_phase6.sh` 11/11 PASS。
- 截图另报告 WSL 重启后的 Docker NAT 网段冲突及用户已完成的 daemon `bip` 调整、备份与启动等待逻辑。此为用户主机级变更；本会话不再触碰 WSL、daemon 或网卡配置。
- 本会话仍无法启动本机命令执行器（`setup refresh had errors`），故以上均按用户截图记录，未独立复跑或核对文件差异。
- 本会话已将截图中的状态与边界补记到 `AGENTS.md`。GitHub 远端仍是最后读取的旧提交 `6a2c132`；公开仓库是否已接收截图中这批 15+ 文件变更未知，需在本机执行通道恢复后再核查，避免直接通过网页 API 覆盖未审查文件。
- 下一步：执行通道恢复后核实工作树、确认 51 项测试和文档的真实内容，再决定 GitHub 同步；学习阶段继续 LangChain → LangGraph → RAG → SQL → FastAPI。

- 2026-11-16 补充：Codex 执行器仍不可用，`docs/learning/README.md` 与 `langchain.md` 由 WorkBuddy 对源码核实（6 条代码描述与 answer.py/retrieval.py/index.py/nodes.py 一致）后随身份认证改动一并提交；`dbab8af` 已推送 origin/main，远端与本地同步。
# 2026-11-16 — 阶段 11 LangGraph 学习材料

- 用户截图补充此前阻塞已解决：手册/代码逐项核对完成；提交 `dbab8af` 与 `12338a1` 已推送；工作树在截图时干净；51 项 pytest 与 WSL 11/11 验收完成。截图记录视作用户提供证据。
- 本会话通过 GitHub 只读接口独立确认 `main` 当前 HEAD 为 `12338a156975603bc4452e2fc1985100b312ad4c`，父提交为 `dbab8af...`，与截图一致。
- 已对照远端 `state.py`、`graph.py`、`nodes.py`、`main.py` 编写 `docs/learning/langgraph.md`，涵盖 State/节点/条件边、SQLite checkpoint、`interrupt`/`Command(resume)` 与租户边界；更新 `docs/learning/README.md`。
- 本会话仍无法启动 Windows 执行工具，故新增文档未能做本地链接/拼写检查、git diff 检查或提交推送；不得声称测试通过。要继续交付该文档，恢复本地终端后应先核对差异，再提交推送。
- 下一主题是 RAG，按顺序继续；代码讲解保持与远端/本地当前版本一致。

# 2026-11-16 — 阶段 11 后续模块材料初稿

- 已新增 `docs/learning/rag.md`、`sql.md`、`fastapi.md`，学习索引列出 LangChain → LangGraph → RAG → SQL → FastAPI 五章。
- 三章基于本会话通过 GitHub 只读接口读取的 `main=12338a1` 代码：RAG 的 policies/index/retrieval/answer/constraints/evaluation；SQL 的 schema、参数化 tenant 查询和 run 记录事务；FastAPI 的 Pydantic、Bearer 依赖、trace middleware、路由与测试。
- 章节说明了哪些命令会访问 SiliconFlow，并避免将个人信息放入示例；退款仍为 `approved_demo`，订单只读。
- 无本地执行器：无法从磁盘读回新增内容、做 Markdown 链接检查或推送。远端目前只读确认已有 `docs/learning/README.md`、`fast_mode_handoff.md`、`langchain.md`；LangGraph/RAG/SQL/FastAPI 四章尚未在远端目录看到。不能声称这些章节已发布。
- 项目功能测试已有用户截图报告 51 passed 与 WSL 11/11 PASS；本次只有学习材料变更，未运行测试或重建容器。


# 2026-11-16 — 学习手册完成与阶段 12 缺口收敛

- 用户截图报告四章学习材料和索引已推送，GitHub 当前 tree 确认 LangChain、LangGraph、RAG、SQL、FastAPI 五章存在。
- 更新 README 与状态/需求追踪文档：将用户报告的 51 项 pytest、WSL health 200/11 用例通过记录为用户提供证据；修正“待 WSL 验收”等过时文字。当前 WSL/docker/NAT 配置不作任何改动。
- 新增并发布 `docs/troubleshooting/fault_cases.md`：12 类故障的现象、层次、线索、处理和防复发，并明确哪些覆盖、部分覆盖或待验证。
- 更新 `AGENTS.md`、`task_plan.md`、`docs/project_status.md`、`docs/requirement_traceability.md`：阶段 11 完成；阶段 12 继续补随机 not_found、Chat Model timeout/429、checkpoint 损坏、Compose 缺 Key 的隔离验证；之后阶段 13 干净克隆。
- 本会话执行器仍不可用；上述本轮文档没有本地 diff 检查或测试运行。外部 GitHub 只读读取和已授权的文档发布可用。用户原报告的 51 pytest/WSL 11 项验收没有被当作本轮测试结果。


# 2026-11-16 — 阶段 12 两条离线回归已添加

- 新增 tests/test_api.py 随机订单 not_found 断言；新增 tests/test_agent.py 假 Chat Model TimeoutError 安全回答断言。两者均通过 GitHub 文件 API 提交，尚未运行。
- 更新 fault_cases、requirement_traceability、task_plan、project_status、AGENTS，将状态标为“已添加、待运行”；没有将其计入此前用户报告的 51 passed。
- 当前唯一需要用户现场操作的是把本机 [本机路径] 快进到公开 origin/main 并运行 pytest。运行结果回来后继续 checkpoint 隔离注入与阶段 13 干净克隆。


# 2026-11-16 — 阶段 12 验收与阶段 13 交接

- 用户截图报告 `git pull --ff-only origin main` 成功；两条新增定向测试 PASS：随机订单 not_found 和 Chat Model timeout 安全答复，2 passed in 4.61s。未重跑此前全量 51 项，也未触碰 WSL/Docker。
- 按用户确认关闭阶段 12；checkpoint 损坏与 Compose 缺 Key/路径仍在 `docs/troubleshooting/fault_cases.md` 明确标注为部分覆盖/未验证。
- 公开 README、案例库、追踪矩阵、task plan、project status、AGENTS、progress、findings 已通过 GitHub 文档更新反映当前阶段；文档变更未修改业务运行代码。
- 阶段 13 干净克隆静态预检：GitHub tree 包含五章学习手册和故障库；未包含 .env、数据库、向量库或虚拟环境。
- 当前本会话本机执行器仍返回 `setup refresh had errors`，因此不能替用户克隆/安装/运行。下一步需在 D 盘隔离目录完成 README 复现；不覆盖现有项目、密钥、数据或 WSL 服务。


# 2026-11-16 — 干净克隆测试结果

- 用户提供截图：D 盘克隆 GitHub HEAD 9caa363；创建新 venv、安装依赖成功；全量 pytest 53 passed in 18.39s，exit 0。包括原 51 项和两条阶段 12 回归。此为用户报告，本会话未复跑。
- 安装阶段发现全局 TUNA pip simple 对 pip User-Agent 返回 403；临时指定 Aliyun mirror 安装成功。README 已加单次镜像覆盖说明；Dockerfile 暂未更改，未来 Dockerfile 修改时再换源或做回退。
- 【历史待办，已由后续验收取代】阶段 13 API smoke 已由用户报告通过：health 200、Bearer 查询 demo 订单 1001 为 200、无 token 为 401。
- 无 WSL/Docker 操作；未运行索引，没有发生新的云端调用。


# 2026-11-16 — 干净克隆首次启动验收与阶段 14 收尾

- 用户截图报告干净克隆 API 冒烟通过：`GET /health` 无认证返回 `{"status":"ok"}`；使用 `Bearer demo-a-local-token` 查询 `/orders/1001` 返回 200 和 demo-a 虚构订单；缺少 token 返回 401。结合此前用户报告的 venv/依赖安装和 53 项 pytest（18.39 秒）通过，阶段 13 首次启动复现完成。以上均为用户报告，本会话未自行启动进程或重跑测试。
- 同步修正需求追踪矩阵和故障库中两条回归仍写“尚未运行/待运行”的旧状态：用户报告的 53 项全量测试包含随机订单 not_found 404 与 fake Chat Model timeout 安全答复测试；真实 429、checkpoint 损坏和 Compose 缺 Key/路径仍保持未验证/部分覆盖。
- 复核并更新 README（无过期测试数）、项目故事、面试材料、演示手册、需求追踪、故障库、项目状态、AGENTS、task_plan 与 WSL 生命周期说明。WSL NAT 修复内容仅按用户报告记录；未运行 WSL/Docker、未改主机配置。
- 阶段 14 文档一致性核查完成。阶段 15 生产化仍为另行定范围的非 Demo 工作；当前项目阶段可交接。

# 2026-11-16 — 优先完成主链路，暂缓加固

- 用户决定先完成主要业务链路，再回头做加固。对照需求追踪与用户验收，主链路已由演示身份/租户校验、FastAPI、LangGraph 路由、订单只读查询/政策 RAG/退款审批演示、答复与运行记录组成；现有 WSL、clean-clone 测试及 API smoke 证据分别记录，不混为一个指标。
- 已在 `task_plan.md`、`docs/project_status.md` 和 `AGENTS.md` 记录该优先级。真实供应商限流、checkpoint 损坏、Compose 缺配置、延迟统计和生产化暂缓；不扩展真实订单写操作或退款。


# 2026-11-16 — 阶段 15 第一步：自动测试与 checkpoint 损坏保护

- 新增 GitHub Actions 工作流 `.github/workflows/tests.yml`，在 push、pull request 和手动触发时使用 Python 3.12 安装项目及 dev 依赖并运行全量 pytest；不使用 `.env`、API Key 或真实模型调用。
- 在应用启动时对 checkpoint SQLite 文件运行只读 `PRAGMA quick_check`。若损坏/不可读则 fail-fast；先校验 checkpoint，再初始化业务订单数据库，避免覆盖损坏文件或留下误导性的新 DB。
- 新增 `tests/test_api.py::test_corrupt_checkpoint_fails_startup_without_overwriting`，使用 tmp_path 隔离坏文件，断言启动失败、文件字节不变、业务数据库未创建。
- GitHub Actions 在 Python 3.12 下全量结果为 54 passed in 2.98s。运行链接：https://github.com/KaelLee335/enterprise-support-agent-v2/actions/runs/43855982263。本会话没有触碰 WSL/Docker。
- 下一步：在 CI 用 `.env.example` 验证 Compose 配置可解析，再评估缺 Key 时的预期行为。真实供应商 429/超时仍后置。

# 2026-11-16 — 阶段 15 离线容器链路验收

- GitHub Actions 已扩展为源码/测试/容器配置变更时运行全量测试、Compose 配置校验、Docker 镜像构建和临时容器 smoke；纯文档提交不触发镜像构建，另保留手动触发。
- 最新运行 `b797bda` 全部成功：55 passed in 3.99s；Compose config、阿里云源镜像构建、临时容器 health 200、带 Bearer 订单 1001 查询、空 API Key 政策请求安全降级均通过。
- checkpoint 损坏测试确认应用拒绝启动、坏文件字节不变、业务 DB 不先创建。CI 使用临时目录和虚构数据，无真实模型/API Key，也未操作用户 WSL/Docker。
- 需用户操作时：若要更新现有运行容器，请先拉取公开 main，再由用户按既有流程同步并重建 WSL 容器；本会话只验证 GitHub 临时容器。

# 2026-11-16 — 用户完成 WSL 同步与 12 项验收

- 用户截图报告已从公开 main 快进并将必要文件同步到 WSL 项目工作区；Docker 镜像重建、容器 Recreated/Started，health 200。
- 用户运行 `verify_phase6.sh`，12 个用例全部 PASS，EXIT=0。新验收包含 health、澄清/认证拒答、订单查询、policy QA、退款两阶段与政策边界用例。该结果为用户现场报告，本会话未运行或操作 WSL。
- 同步脚本曾因 CRLF 造成 `pipefail` 报错；用户报告去除行尾回车后通过，并已修改脚本避免重现。
- 阶段 15 当前已由 CI 和用户 WSL 两侧完成部署验收；剩余真实供应商故障、恢复和其他可选边界仍需隔离验证。

# 2026-11-16 — 阶段 15 本机离线回归复核

- 使用项目虚拟环境并将 pytest basetemp 指向项目内临时目录，复跑四项：模型 timeout 安全答复、缺少 Embedding Key、checkpoint 损坏保护、无 Key API 安全降级。
- 结果：4 passed in 3.35s。第一次使用系统 Python 因缺少 LangGraph/LangChain 依赖无法收集测试；随后改用项目虚拟环境。项目内临时目录避开了系统 Temp 权限问题，测试代码无失败。
- 未调用真实模型/API，未操作 WSL/Docker。Compose 缺少 `.env` 文件与错误挂载路径仍待隔离验证；工作树原有 `pyproject.toml` 修改未触碰。

# 2026-11-16 — 阶段 15 Compose 静态检查与真实 API 提醒

- 本机未发现 Docker/Docker Compose CLI，因此无法执行 Compose runtime failure injection。使用项目虚拟环境的 PyYAML 只读解析 `compose.yaml`：YAML 有效、服务声明 `.env` env_file、数据挂载采用 `PROJECT_DATA_DIR` 配置变量。
- 缺少 `.env` 和错误 bind mount 的实际 Docker 行为继续标为待验证，不将静态解析说成容器验收。
- 用户说明后续会配置真实 API 做演示。已在项目执行计划和 AGENTS 写明：首次配置凭据或发送请求前先提醒服务商、数据范围、费用/额度和本地 `.env` 操作；Key 不进入聊天。
# 2026-11-17 — Vue 演示前端首版

- 新增 `frontend/` Vue 3 + Vite 页面：聊天输入/历史、订单卡片、政策引用和证据、演示审批批准/拒绝、Demo Token 输入；Vite `/api` 代理转发至本地 FastAPI，不在前端配置云端 Key。
- 用户报告 npm install 成功、页面 200、`/api/chat` 经代理连接现有容器并收到 SiliconFlow 真实模型答复。此为用户现场验证；本机 `npm run build` 使用已安装依赖，Vite 6.4.6 构建通过（1.18 秒）。
- 增加全局 `node_modules/` 忽略；没有改动后端接口或重建容器。

# 2026-11-17 — 阶段 15 Compose 配置边界与 bind mount 防误建

- 在项目内随机临时目录复制 `compose.yaml` 做隔离验证；缺少 `.env` 时 `docker compose config --quiet` 返回退出码 1，并报告具体临时 `.env` 文件不存在。测试使用 `.env.example` 的模板副本，不读取或输出真实 `.env`。
- 使用不存在的临时 `PROJECT_DATA_DIR` 运行 Compose v2.39.1 `config`：退出码 0，命令不创建目录。进一步检查 `config --format json`：`true` 显式解析为 `bind.create_host_path: true`，`false` 解析为不带该字段（Compose 长格式的 false 默认值）。
- Docker 官方 Compose 文档说明短格式 bind mount 默认会在源路径不存在时创建目录；已将 `compose.yaml` 切换为长格式并设置 `bind.create_host_path: false`，避免错误路径静默建成空数据目录。README、演示手册和故障库已补充先决条件及排障方式。
- `docker compose version` 为 v2.39.1；访问 daemon 的 `docker ps` 与镜像查询均因 `127.0.0.1:2375` 连接被远端关闭而失败。未启动/停止容器、未重启 WSL、未触碰现有持久数据。错误挂载实际 `up` 失败提示仍待 daemon bridge 恢复后用临时 Compose 项目验证。
- 临时目录已删除。这里只运行了 Compose 配置验证，未运行 pytest 或构建镜像。

# 2026-11-17 — 阶段 15 Compose 错误挂载运行态验收

- 用户确认 Docker 桥接恢复后，先检查 `docker ps`：既有 `project2-support-agent-1` 为 healthy，BusyBox 镜像已本地存在。
- 在唯一临时目录创建独立 Compose 项目，使用 BusyBox、无端口映射和 `network_mode: none`，bind 到一个不存在的 `/mnt/d/project_2/.compose-runtime-<id>/missing-data` 路径，并保持 `create_host_path: false`。
- `docker compose up` 以退出码 1 失败；错误明确为 `invalid mount config for type "bind": bind source path does not exist: <临时路径>`。Windows 对应宿主路径仍不存在。
- `docker compose down --volumes --remove-orphans` 清理成功，临时项目目录删除。再次检查时仅看到原项目容器，仍为 healthy；端口 8000、WSL 设置和持久数据未触碰。
- 对真实项目目录运行 `docker compose config --quiet` 成功。`git diff --check` 通过；未运行 pytest、未重建镜像。

# 2026-11-17 — 阶段 16.0 模拟外部客户生产化规划

- 按用户要求以全虚构的两个租户、三类首批 persona（客户、客服、主管）规划可在本地完成的阶段；不使用真实姓名、电话、地址或真实账号，不调用模型服务。
- 对照当前代码确认身份来自固定 Demo token → user/tenant 映射；订单只按 tenant 查询；SQLite `demo_users` 无 role/membership；LangGraph 审批接口仅校验同租户，未做审批角色授权；run 记录查询也需要细化客户本人范围。
- 当时短暂新增 `docs/productionization_plan.md`；用户随后明确“无需生产化”，该文件已删除，生产化路线不再执行。后续只按 V2.1 本地模拟计划推进。
- 更新 task plan、project status 和 AGENTS。没有改业务代码、数据库、前端或外部服务；没有运行测试。

# 2026-11-17 — V2.1 Demo 工程加固计划

- 用户澄清“无需生产化”，并给出 V2.1 计划：交付一致性、审批身份边界、模拟物流 API 和面试迁移说明。
- 新建 `docs/v2_1_demo_reinforcement_plan.md`，将外部业务 API 限定为本地模拟 HTTP 服务；禁止真实商业物流 API、真实身份系统、生产数据库和真实退款。
- 当前工作树已有用户未提交修改（如 `.gitignore`、`pyproject.toml`、README、Compose、前端）；执行前将逐文件审阅，保留既有内容，不整体暂存或提交。
- 初步读码：Demo 身份目前只有 user/tenant，没有 role；审批 endpoint 验证 tenant 但没有 approver role；CI path filter 当前未覆盖政策/seed/frontend；Python 依赖为范围约束，尚无已识别的 Python lockfile；前端已有 `package-lock.json`。阶段 1 正式修改前继续核实锁文件工具与 README/Bad Case 证据。

## 2026-11-17 — V2.1 本地演示加固实现

- 阶段 1：生成 `uv.lock`，Python CI 与 Docker 安装改为 locked sync；固定 setuptools build backend；CI 覆盖 seed/policies/frontend/scripts/docs 并构建 Vue。Bad Case 文档明确保留路由修复前后 30/35 → 35/35，同时区分召回、引用 ID 与语义正确。
- 阶段 2：加入 `user-demo-a-approver` 模拟同租户审批身份；决策端点先做 tenant 404，再校验 approver role 和发起人不自批；审批日志记录 approver、requester、thread 与演示决定。SQLite `demo_users` 初始化新增虚构审批人。
- 阶段 3：加入 `logistics_lookup` LangGraph 分支、HTTPX/Pydantic typed client、固定虚构轨迹的本地 FastAPI mock service 和 Compose 服务依赖。节点先验证订单 tenant；服务标记、状态码、超时及错误 JSON 由 mock transport/服务测试覆盖。
- 阶段 4：Vue 增加 requester/approver 切换和模拟物流轨迹；README、runbook、项目故事、面试材料与 LangGraph/FastAPI 学习章节同步更新；WSL 同步脚本和阶段验收脚本扩展到新业务分支。
- 验收：`uv lock --check --offline` 成功；全量 `pytest` 65 passed；Vue production build 成功；`docker compose config --quiet` 和 Python compileall 成功。WSL 两容器实际 HTTP 集成仍需用户同步及重建。
- 本机 Docker 镜像构建尝试未完成，远端 daemon 在拉取阶段返回 `unexpected EOF`；之后用户报告已在 WSL 成功同步并重建，两容器 healthy，阶段 6 + V2.1 verifier 全 PASS，覆盖了本机无法完成的容器间集成验收。
- 未提交、未推送，保留已有工作树改动。

## 2026-11-17 — V2.1 发布完成

- 用户报告 WSL `/opt/project2` 已同步最新 `uv.lock`、源码并重建，两个容器 healthy；阶段 6 与 V2.1 新增 verifier 用例全部 PASS。此 WSL 结果由用户提供，本会话未直接操作 WSL。
- 审阅并提交 V2.1 全量交付（含 Dockerfile `uv sync --frozen` 修正、Vue 前端、物流模拟服务、独立演示审批角色、锁文件、CI、测试与文档），提交 `c8879bf`；推送到公开仓库 `origin/main` 成功。
- 发布前核对 `.env.example` 的 SiliconFlow Key 为空；`.env`、数据库、向量库、前端依赖/构建产物未纳入提交。发现 Vite 本地日志后已加入 `.gitignore` 并排除。
- 本地既有记录为 pytest 65 passed、Vue build 通过、Compose 静态配置与 Python 编译通过；本轮未重跑测试。远端最初查询曾遇到当前沙箱 Git 凭证不可用，后续获准 Git 推送成功。
- 推送后 GitHub Actions run 19（commit `46d089a`）完成并通过：锁文件安装、Python 测试、Vue build、无密钥 Compose 校验、Docker 镜像构建及无 Key 容器 smoke。

## 2026-11-17 — 前端角色会话隔离修复

- 用户反馈切换到审批人后仍看到请求人对话。根因是角色切换只更换 Demo token，没有切换会话列表。
- Vue 前端现在按 requester/approver 分别保留本次页面会话中的对话；未决审批以独立任务卡跨角色显示，批准/拒绝后清除任务卡并同步结果到请求人对话。角色切换期间若请求仍在处理中则禁止切换。
- `npm run build` 通过。未操作 WSL/Docker、未调用模型；页面需刷新后确认实际交互效果。

## 2026-11-17 — 退款申请路由与审批人空状态修复

- 用户截图显示输入“帮我申请订单 1001 退款”被误路由成 `order_lookup`，切换审批人后因此没有待办。原因是路由规则只识别“帮我给订单…直接退款”等写法，不识别“申请订单…退款”。
- 已扩展确定性规则，覆盖“帮我申请订单 1001 退款 / 申请订单1001退款 / 我要申请订单1001退款 / 给订单1001申请退款”；退款进度查询仍保持只读。审批人无会话且无待办时，现在会解释如何由请求人创建审批任务；已有 pending 时任务卡跨角色保留。
- 验收：`tests/test_agent.py` 19 passed；新增自然申请表达 API 测试 1 passed；Vue production build passed。首次混合运行 API 测试时受项目既有 `.pytest-tmp` ACL 阻挡；改用本任务专用临时目录后，目标 API 用例通过；临时测试 SQLite 已清理。
- 更新 `scripts/verify_phase6.sh`，让 WSL 验收直接覆盖用户截图中的退款申请表达。用户随后报告同步脚本已执行完成：双容器 healthy，verify 全 PASS（EXIT=0），路由修正生效。该 WSL 结果来自用户实机报告。

## 2026-11-17 — 审批任务仅向审批人显示

- 用户指出待审批卡片同时显示在请求人和审批人页面。原因是前端按共享 `pending` 状态渲染卡片，只在卡片内部区分按钮角色。
- 修改为整个任务卡仅在 `role=approver` 时渲染；请求人仍能在自己的助手答复和状态行看到 `pending`，不会看到审批任务卡或决定按钮。
- 纯前端修正，无需 WSL/Docker 后端重建；Vue production build 通过。
- 提交 `12aaf4d` 已推送；GitHub Actions run `44077476920` 最终状态为 success。
- 用户随后实际操作浏览器并确认通过：请求人与审批人看到各自对话，待审批任务只在审批人页面显示。

## 2026-11-17 — 图示建议收尾复核

- 对照 V2.1 工程加固图复核：交付一致性与锁文件/CI、模拟 requester/approver 边界、本地物流 HTTP API、演示/面试/迁移说明均已实现并验收；没有遗留在本地 Demo 范围内的功能项。
- 发现项目状态页仍把阶段 15 写成“刚开始”，并把若干已完成验收列在待办中。已修正当前阶段、V2.1/WSL/浏览器验收状态和建议后续顺序；保留生产化、真实供应商故障演练、事实级独立评估/延迟基线和学习互动为明确暂缓项。
- 看板校准提交 `d703155` 的 GitHub Actions run `44084457126` 通过。
## 2026-11-18 — 启动 V2.1 电商集成扩展

- 按用户的新项目 brief 开始增量扩展：目标包括 Mock 电商平台、统一 Adapter、售后资格/模拟申请、Agent 接入、签名 Webhook、隔离/幂等测试和文档；明确保持演示边界，不接真实平台与真实用户。
- 完成 Phase 0 仓库盘点：当前 API/身份/SQLite/LangGraph/RAG/物流/Docker Compose/CI 均可复用；新增 Adapter 和售后/Webhook 领域目前不存在。
- 基线测试第一次通过 `uv run --locked pytest -q` 未启动，因全局 uv cache `D:\\caches\\uv` 拒绝访问。通过 `.venv` Python 指定新的 `.pytest-tmp-v21` 成功：**71 passed, 9.25s**；仅 1 条 `.pytest_cache` 写权限 warning。没有更改 ACL 或清理受限目录。
- 已将新路线、MVP、风险和架构决策写入 `task_plan.md`、`findings.md`；下一步实现独立 MockShop API 与 Adapter 基础接口，并保持旧 API 和图路由回归。
- Phase 1/2 首批实施完成：新增 `mock_shop_api.py`、`integrations/{models,base,registry,mock_shop}.py` 和 7 条测试。MockShop endpoint 需要 demo service key，提供固定状态/物流/售后资格/售后申请/申请状态 API；Adapter 隐藏平台字段和状态映射。
- 验收：新增测试 7 passed（0.80s）；全量测试 78 passed（9.06s）。测试使用项目 `.venv`、自定义 basetemp 和 `-p no:cacheprovider`；没有改动用户 WSL/Docker、真实平台或用户数据。
- 下一步：完善平台异常映射和 Demo identity→store/customer 权限策略，再把新服务接入 FastAPI/Compose；售后业务写入必须由主 API SQLite 留痕并与“审批/退款执行”区分。
- 随后实现平台错误归一（404、认证失败、409、422、服务不可用、timeout、坏 JSON/Schema、未知状态）和用户/租户/店铺/客户范围策略；新增异常回归后全量 pytest 达 **81 passed / 8.94s**。
- 新增配置、FastAPI 电商 REST endpoint 和 SQLite `aftersale_requests` 表，覆盖 tenant/customer 权限、明确请求人确认、资格检查、申请幂等与状态查询；Compose 配置 mock-shop 私有网络服务，CI smoke 纳入订单读取和跨客户 404。
- 本轮验收：`tests/test_ecommerce_api.py` + `tests/test_db.py` 9 passed / 4.61s；最新全量 pytest **86 passed / 9.63s**；`docker compose config --quiet` exit 0。未启动/重建 Docker 容器，也未同步 WSL。
- 当前阶段状态：MockShop API、Adapter 与 FastAPI/SQLite 基础路径已经可测；Agent graph/RAG 串联、Webhook、Vue、完整文档和实际 Compose/WSL runtime 仍待实现。
- LangGraph 接入新增三类显式平台意图：订单、物流、售后资格。Agent 节点调用绑定当前 `DemoIdentity` 的 LangChain `StructuredTool`；平台归属不从用户 header 或模型参数推断。售后资格结果随后经过现有 RAG；如果权限/平台检查失败则 Graph 不会继续检索，避免对无权请求做额外调用。
- 售后申请仍由单独 FastAPI POST 操作承接，要求 requester、`confirmed=true`、订单授权及资格符合，并写本地 SQLite 幂等记录。Agent 仅检查资格与说明下一步，不会根据自然语言自行提交。
- 定向测试 `test_ecommerce_api.py`、`test_mock_shop_integration.py`、`test_agent.py`：37 passed / 5.13s；全量套件 **89 passed / 10.05s**。离线路由评估用既有 V1 标签直接运行 `evaluate()`，没有生成报告文件：明确路由标签 35/35、订单参数 8/8、数据库未变、0 route failures。
- Compose 静态解析通过；当前没有 `compose up/build`、WSL 同步或外部模型请求。WSL runtime 尚未部署新服务，Vue 尚未展示新字段。
# 2026-11-21 — 独立 RAG 样本外测试

- 先盘点原评估资产：45 条开发集位于 `data/evaluation/v1_eval_cases.json`；现有检索评分在 `src/support_agent/rag/evaluation.py`，实际检索经 Chroma `similarity_search_with_score`，默认 Top-K=4；生成链和政策约束复用 `src/support_agent/rag/answer.py`。Bad Case 既有人工审阅记录在 `docs/rag_answer_manual_review.md`。
- 新增 `data/evaluation/oos/rag_oos_v1.json` 的 15 条独立案例，覆盖口语/同义、组合条件、多意图、无答案、范围外和模糊澄清。测试代码与原 45 条隔离；未变更政策、业务流程、向量数据或默认 Top-K。
- 新增 `tests/oos/runner.py` 和模块入口 `python -m tests.oos.run_oos`。执行时复用配置好的 Chroma、SiliconFlow Embedding 与 Qwen、既有 Prompt/约束；按回答实际使用的证据计算检索指标。规则式答案检查仅作初筛，不使用 LLM judge。
- 已完成真实 OOS 运行并写入 `data/evaluation/oos/rag_oos_v1_report.md`：15 个案例 Hit@4 100.0%，Macro Recall@4 92.2%；答案规则项通过 66.7%（10/15），拒答/范围边界通过 75.0%（3/4），引用标签与来源匹配 93.3%（14/15）。5 个 Bad Case 为 OOS-01、04、05、07、11；两条证据召回不全，另外三条存在规则项遗漏或无效引用标签。报告保留实际答复、来源及文档标题，需用户人工审阅。
- OOS-05 实际答复含非政策编号 `[POL-05_SHIPPING_AND_GUIDANCE]`；新增评估检查会将不属于本次召回来源的方括号引用标签记录出来，但未改动现有回答实现。
- 新增 `tests/test_rag_oos.py`，覆盖检索计分、空标签、Mock 执行/报告、无效引用标记和案例独立性。最终全量 pytest **96 passed / 12.28s**。Mock 用例不纳入真实 OOS 指标。
- 结果限制：Hit@4=100% 只表示每题至少找到一个相关来源；Recall 是证据来源的标签匹配；规则项比例不代表事实正确率。OOS 指标与 45 条开发集历史结果不合并。未自动调整 Prompt/检索配置，也未变更现有业务 API。

## 2026-11-21 — RAG 答复自然度加固

- 保存首版样本外报告为 `data/evaluation/oos/rag_oos_v1_report_before_style.md`。
- 更新回答 Prompt：先答核心、避免重复规则，不追问用户已提供信息；内部约束 ID 不再传入模型上下文。
- 调整政策边界：退货信息不足时先询问签收时间/原因/商品状态；只在问题相关时说明无理由退货运费；处理到付、退款双阶段及发货/送达时效；订单完成售后资格、维修时限和超范围问题采用短而有据的回答。
- OOS-11 仅需 POL-02 支持第一轮澄清；若用户下一轮确认质量故障，再检索 POL-03。该证据标签变更记录在 `labeling_note` 中；规则检查接纳“商品故障”作为“质量问题”的同义说法。
- 最新真实复测（11:42 UTC）：15 条，Hit@4 100.0%、Macro Recall@4 95.6%、答案规则项 93.3%、拒答/范围边界 100%、引用标签匹配 100%。当前只剩 OOS-05 的 Top-4 证据缺口（RET-01、QUA-01）。部分检查规则与一项标注有修正，指标变化仅作方向参考。
- 发货回答约束改为顺接成单段、避免重复政策编号，并在用户问“明天能否到”时清楚回答不能保证；检查器对中文数字间空格做归一化。
- 最新全量 pytest **105 passed / 15.00s**。只改了本机工作区；WSL 容器未同步重建，演示前需走既有 WSL 同步验收流程。
- 用户随后报告新版已同步 WSL 并重建三容器，全部 healthy；`verify_phase6` 和 `verify_v21` 全 PASS（EXIT=0），OOS-05 修复已在演示页生效。此为用户提供的部署验收证据。独立 OOS 报告仍保留 11:42 UTC 运行的一个 OOS-05 检索 Bad Case，二者指标含义不同，未据部署断言改写报告。
# 2026-11-22 — 工程质量与开源竞争力审计启动

- 收到新任务说明；按阶段 1 先只读盘点实际代码、测试和部署配置，报告完成后暂停核心逻辑改动等待用户确认。
- 起始工作区已有上一轮 OOS 改进的未提交源码、测试和文档变更；已记录并保留，不清理、不覆盖。本轮不运行 Compose、不改持久数据或向 GitHub 发布。

# 2026-11-22 — 工程质量与开源竞争力审计完成

- 新需求按阶段 1 执行；开始前确认工作树有上一轮 OOS 源码、数据/报告和测试未提交变更，全部保留。
- 审查了目录、FastAPI/身份、SQLite 查询、MockShop Adapter/权限、Webhook、LangGraph State/Node/Edge/checkpoint、RAG/Chroma/Prompt、45-case 开发集、15-case OOS、pytest、Dockerfile/Compose、CI、README 与架构文档。
- 本机全量测试：**105 passed / 17.99s**。公开 GitHub main 与本地 HEAD 是 `43adc60`；GitHub Actions run 29 成功，但本地 OOS 未提交变更未由远端 CI 验证。
- 用户已报告 WSL 新版三容器 healthy、阶段 6 与 V2.1 验收全 PASS；本轮没有启动或修改容器。
- 新增 `docs/engineering_audit_2026-11-22.md`。主要待确认项：同租户用户级订单/run 权限、MockShop 查询前授权、RAG 无关/冲突证据处理、OOS 集被调优后不再 blind、Webhook 状态键跨店铺冲突、README 状态过期。
- 阶段 1 完成后停在审计汇报；未修改核心业务逻辑/数据库 schema/业务规则，也未提交或推送。
# 2026-11-22 — Phase 2 权限模型审计与方案

- 依据用户明确的四角色业务规则，只读核查身份、Repository、API、Agent State/Node、MockShop Adapter/API、审批 interrupt/checkpoint 与 Webhook。
- 新增 `docs/phase2_permission_model_and_migration_proposal.md`：当前结构/关系、漏洞、拟议模型、SQLite DDL 草案、迁移影响/回滚、代码入口及测试矩阵。
- 审计发现现有公开 Demo token 仅映射 requester/approver；没有 Service/Admin 数据模型。订单和 AgentRun 的 SQLite 查询只按 tenant；MockShop 对象读取后才做客户校验；审批缺任务分配表和 current-assignee 约束；售后缺 actor/customer 分离。
- 没有修改代码或业务数据，没有执行 migration、全量测试、Compose、Git commit/push。上一轮 105 passed / 17.99s 仅作为既有基线引用。
- 当前状态：审计与方案完成，等待用户确认 migration proposal 和历史授权数据录入策略；获批后按先测试、后小范围实现推进。Phase 2 结束后暂停。

# 2026-11-22 — Phase 3 OOS 回归改进与待验收状态

- 2026-11-23 最终更新：定向检查扩展后全量 pytest **137 passed / 18.14s**；真实 OOS-v2 最新运行于 09:27 UTC 完成。Hit@4 100%、Macro Recall@4 100%、答案规则初筛 100%、拒答边界初筛 100%、引用标签匹配 100%、Bad Case 0。指标为规则筛查，不代表语义准确率；OOS-v2 已是 observed regression set。报告与 ledger 已刷新。
- 新增 SiliconFlow 客户端 30 秒请求超时、一次重试及逐案例进度日志。WSL 未操作，代码未提交/推送。

- 用户报告：较早的直接冲突识别版本已在 WSL 通过容器内冲突/范围例外 smoke、Phase 6 和 V2.1 全部验收（EXIT=0）。用户明确表示当前部署保持原样，待本机提交后再同步；本轮未操作 WSL/Compose。
- 为 OOS-05 的复合条件召回缺口实现有条件查询扩展，只影响“定制商品 + 质量问题 + 寄回/运费”同时出现的查询；原问题传给生成模型，Top-K 仍为 4。当前 Chroma 实际 Top-4 含 QUA-01、RET-01、POL-02、POL-05。
- 用真实 Embedding/Chroma/Qwen 执行 OOS-v1 回归（报告时间 2026-11-22 14:57 UTC）：Hit@4 15/15、Macro Recall@4 100%、答案规则初筛 15/15、拒答边界 15/15、引用标签匹配 15/15，筛查 Bad Case 0。由于 OOS-05 用于设计修复，这是调优回归结果，不能宣称 blind holdout 成绩或语义准确率。
- 人工检查 OOS-05 实际答复发现“照片或视频”格式追问没有政策依据；现有规则检查漏过该细节。记录为待人工决策的生成边界问题，未自行增加政策要求。
- 用户于 2026-11-23 审核通过 OOS-v2 的 15 个案例。将其定为独立 holdout 文件，扩展 OOS runner 支持显式 `--dataset`，并为每个数据集分别写 Markdown 报告与 Bad Case ledger。OOS-v1 默认路径与输出文件保持不变。
- 评估口径复核发现 HOLDOUT-04 明确针对 OOS-v1 人工复核时已见的“照片/视频凭证格式”无依据追问；因此 OOS-v2 是新的独立评估集，但不是完全盲测。已在数据元信息和文档中记录，避免夸大独立性。
- 真实 OOS-v2 调用仍等待用户单独确认是否把新问题、检索证据和模型回答发送到既有 SiliconFlow/Qwen；获确认前只做本地验证，不产生真实指标。
- 用户随后于 2026-11-23 授权外发并运行真实 OOS-v2。运行时间 2026-11-23 04:25 UTC；Hit@4 100%、Macro Recall@4 93.3%、答案规则初筛 20%、拒答/范围词面初筛 0/6、引用标签匹配 100%，共 12 个规则筛查案例（GENERATION 10、RETRIEVAL 2）。报告与 ledger 已独立保存。
- 初步人工抽查发现，HOLDOUT-04 将“需要质量问题凭证”扩大成“必须上传视频/购买凭证”，属于需要认真复核的无依据细节；另一方面，拒答短语初筛很可能对语义合格但措辞不同的答复误报。未修改 Prompt 或规则；下一步是逐条人工判读 12 项并确认哪些是实际 Bad Case。
- Codex 完成了 12 个候选 Bad Case 的逐例初步分诊，见 `data/evaluation/oos/rag_oos_v2_manual_triage.md`。初步识别 3 个明确生成偏差、2 个无依据附加细节候选、4 个词面检查误报、2 个证据标注可能过宽和 1 个回答不完整。只写分诊意见，没有更改数据集/报告/ledger 的 root cause 字段，也没有改 Prompt、规则或检索参数；等待用户之后复核。
- 用户复核通过后，新增定向政策约束，修复错误的“昨天付款但未发货”分支匹配，扩充等价短语评估规则；将 HOLDOUT-08/10 的必要证据标签收窄到直接支持答复的 POL-07/POL-08。完整 pytest **137 passed / 18.09s**。
- 使用更新后的代码和标签再次调用 SiliconFlow 的 OOS-v2 运行在等待期间无输出，最终执行会话结束且没有生成新报告；旧报告顶部已注明快照早于最新变更。当前运行结果不可作为最新验收证据，后续需解决外部请求挂起后再复跑。
- 排查确认 SiliconFlow Chat 与 Embedding 客户端未显式设置请求超时，且重试为 2 次；为避免静默长时间挂起，现改为 30 秒请求超时、1 次重试，并让 OOS runner 按案例输出进度。模型实例运行时参数已在本机锁定版本上核实支持。准备在受限时长下重跑真实评估。
- 本机完整 pytest：130 passed / 17.01s。WSL 运行未执行；查询扩展仍为本地未部署改动。未提交、未推送、未更改持久 DB/Chroma。

## 2026-11-23 — Phase 3 本地交付提交

- 用户开放本机文件权限后，创建本地提交 `64432c8`（`feat: enforce tenant permissions and harden RAG evaluation`），包含 54 个源码、测试、文档和 OOS 评估文件。
- 检查确认 `.env` 与 `data/support_agent.db.bak-20261122` 未进入提交；数据库备份继续留在工作区。未推送 GitHub，未运行 WSL/Compose。
- 已同步更新阶段计划、Agent 指引和项目状态。下一步等待用户按既有流程同步到 WSL 并回报容器验收结果。

## 2026-11-23 — GitHub Actions 导入问题修复

- 根据 Actions run `45150776269` 的 job 日志，失败点是 pytest collection：`tests/test_rag_distance_calibration.py` 找不到 `scripts`，`tests/test_rag_oos.py` 找不到 `tests`。CI 没有触发 SiliconFlow 请求，因此与 API Key 是否过期无关。
- 新增 `scripts/__init__.py` 与 `tests/__init__.py`，明确将目录声明为本项目包，避免与 runner 环境中的同名 `tests` 包冲突。
- 本机全量 pytest **137 passed / 18.46s**。改动仍未提交/推送；GitHub Actions 的旧失败记录不会自行变化，推送修复后应观察新 run。
