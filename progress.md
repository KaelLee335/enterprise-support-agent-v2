# 工作进度

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

- 用户确认从 WSL `/opt/project2` 构建成功，容器 `project2-support-agent-1` 为 `Up (healthy)`；`/health` 返回 200，`GET /orders/1001` 与 `POST /chat` 全链路成功，订单只读回答返回“已完成”。
- 用户确认在 `/mnt/d` 构建遇到 BuildKit 权限限制，因此改用 `/opt/project2` 作为构建上下文；`/mnt/d/project_2/data:/app/data` 绝对 bind mount 仍指向 Windows D 盘数据。
- 用户修复并同步 `main.py` 的 seed 路径三级回退，处理 site-packages 安装布局启动失败。
- 用户实测 pytest 33 项通过；后续本地修复中文紧邻订单号解析，并在 Windows 项目全量回归 35 项通过。Compose YAML 已解析验证。
- 当前容器实测版本早于最后的 `ORDER_ID_PATTERN` 和 D 盘绝对挂载变更，需要同步最新 `src/support_agent/agent/nodes.py`、`compose.yaml` 到 `/opt/project2` 并 `docker compose up --build -d` 后，验证“查询订单1001”及 `healthy`。

### 最终 Docker 验收（用户实测）

- 用户已将订单号路由修复和 D 盘绝对 bind mount 同步到 `/opt/project2` 并重建；无空格输入“查询订单1001”命中 `order_lookup`。
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
- 将 `scripts/verify_phase6.sh` 改为断言式验收：health 非 200、intent 不符、回答缺少预期文本或 POL-06 引用无效时会失败；README 已补运行命令。需在 WSL `/opt/project2` 同步脚本并运行，以验收脚本自身和当前服务。
- 用户已在 `/opt/project2` 运行断言式验收脚本，7 项健康/安全/回归检查全部 PASS，EXIT=0。WSL 只读状态：`pgrep -a dockerd` 为 PID 11；`systemctl is-active docker` 为空，`is-enabled docker` 为 `enabled`。这确认 daemon 当前运行，但不足以证明 systemd 正在管理或重启后会自启；没有修改 WSL 启动配置。服务演示期间保持 `inbox` WSL 会话运行。
- 使用项目本机 `.env` 对同一 RAG 标注集完成 Top-2/4/6/8 对比：Hit@k 分别为 97.2/100/100/100%，平均 Recall@k 为 77.3/86.6/89.4/99.1%，完整证据率为 58.3/72.2/77.8/97.2%。Top-2/6/8 报告分别为 `data/evaluation/v2_retrieval_top2.json`、`data/evaluation/v2_retrieval_top6.json`、`data/evaluation/v2_retrieval_top8.json`。默认 `RAG_TOP_K=4` 暂不更改，需结合 LLM 答案语义质量与延迟/token 成本再决策。
- 用户明确授权后，已对 14 条答案要点明确的政策 QA 用例分别生成 Top-4/Top-8 答案并以 Qwen 同模型作探索性评分，完整报告 `data/evaluation/v2_rag_answers.json`。引用编号静态检查均为 100%；LLM judge 要点覆盖率 76.9%/71.8%，grounded/引用支持 92.9%/92.9%。人工抽样发现 judge 误判 KB-04 Top-4，并发现 KB-04 Top-8 出现与 POL-04 冲突的表述；这些自动分数不能视为准确率，默认 Top-4 保持不变。更换 Top-k 前需更可靠的独立语义评审与成本分析。
- 按用户要求建立根目录 `AGENTS.md` 和 `docs/project_status.md`，将项目边界、已验收状态、未完成事项、接续规则写入。另新增 `docs/rag_answer_manual_review.md`，逐例记录 14 组 Top-4/Top-8 答案的遗漏和事实问题。
- Prompt-only 实验结果记录：多条长规则导致矛盾输出，保存在 `data/evaluation/v2_rag_answers_prompt_v2_top4.json`；短规则 4 例定向运行超时中断，未形成完整报告；后续两条规则在 KB-04 输出没有再直接否认排除条款，但引入未经证据支持的替代路线，MVP-KB-BOUNDARY 仍未分清质量问题/无理由退货。输出见 `data/evaluation/v2_rag_answers_prompt_v4_targeted_top4.json` 与 `v2_rag_answers_prompt_v5_targeted_top4.json`。所有试验 Prompt 已撤回，`answer.py` 保持用户验收的原版本。
- 因单纯 Prompt 调整不稳，新增 `docs/rag_grounding_hardening_plan.md`，建议以版本化、可审计约束层解决政策排除/条件遗漏；实现前需用户决定是否扩大项目范围，备选是保留演示限制。
- 用户确认继续实现约束层。本机 `answer_constraints.py` 加入规则：POL-04 进液排除和 POL-02 质量问题退货分流为确定性兜底；POL-02 退货条件、POL-05 运费/指引、POL-06 两阶段退款、POL-09 发票隐私/范围约束按需补充。命中/执行约束 ID 加入答案结果、评估文件和 `rag_answer_constraints` 结构日志。原始 Prompt 未改，`RAG_TOP_K` 仍为 4。
- 约束层 14 案例 Top-4/Top-8 全量评估完成：28 条输出引用检查 28/28 有效；每档匹配 11 条约束，分别 6/7 条执行补充/兜底。跳过已知不可靠的同模型 judge，并人工审阅关键兜底输出。报告 `data/evaluation/v2_rag_answers_constraints_v3.json`。
- 新版本仅在 Windows 工作区完成评估；尚未同步至 `/opt/project2`，也未重建/重验 WSL Docker。下一步需用户在其 WSL 会话同步本次应用源文件、重建容器并运行 `scripts/verify_phase6.sh`。
- 为减少 WSL 手工同步错误，新增 `scripts/update_wsl_and_verify.sh`：会复制 `answer.py`、新约束模块、`nodes.py` 和扩充后的验收脚本；执行 `docker compose up --build -d`、轮询容器 `healthy` 与 `/health`，再运行阶段 6 全集检查。脚本已按 `/mnt/d/project_2` → `/opt/project2` 的既定路径写好，但尚未在 WSL 运行。
- 截图复核：WSL 的 POL-06 回答包含退款处理 1–3 个工作日、到账 1–5 个工作日、取决于支付渠道及“具体到账时间无法保证”，并引用 POL-06；内容符合规则。失败点仅为 WSL 上旧版 `verify_phase6.sh` 的措辞白名单遗漏该同义句。检查确认 D 盘脚本当前已接受“具体到账时间无法保证”。下一步只需将该脚本复制到 `/opt/project2/scripts/verify_phase6.sh` 并重跑，不需重建容器；等待用户回报复验结果。
- 用户随后确认已同步脚本并重跑：健康检查通过，11 个业务用例全部 PASS，EXIT=0；其中此前失败的 POL-06 退款两阶段时限检查现已通过，POL-04 进液排除、POL-02 质量故障路由及 POL-09 发票隐私边界也全部通过。扩充版阶段 6 验收完成，无需重建容器。剩余可选项是 WSL daemon 生命周期只读诊断；生产化能力不在演示验收范围。
- 用户提供 Docker 启动恢复实测：Ubuntu WSL 原为 `Stopped`，触发 `Start-ScheduledTask` 后日志显示 `dockerd ready`，Docker 容器 `project2-support-agent-1` 为 `Up (healthy)`，health 返回 200。结合 `/proc/1/comm` 为 `init`、`systemctl is-active docker` 无输出、`is-enabled` 为 enabled，结论是已验证计划任务可从停止的发行版恢复 Docker 与项目；不能据此推断 Windows 完整重启后会自动触发。记录更新在 `docs/wsl_docker_lifecycle.md`，无需改 systemd 或 WSL 配置。
- 按阶段计划完成最终交付文档核对：修正 README、Evaluation 和 RAG 人工复核报告中“约束层尚未部署/验收”的过期说明；更新 AGENTS 接续状态；findings 中保留原始历史记录并明确标注已被后续实测取代。原计划阶段 0–6 均已完成，目前无待执行的必选阶段；剩余的是可选 Windows 开机计划任务设置核查，以及用户此前暂缓的学习问答。
- 阶段 7（发布就绪/可复现交接）开始：检查发现 Dockerfile 直接 `COPY data/vector_store`，但该本机生成目录在 `.gitignore` 中排除，会使全新克隆无法构建；Compose 又把数据路径写死为 `/mnt/d/project_2/data`。已移除 Docker 镜像对向量目录的构建依赖（运行时由持久化挂载目录读取）、通过 `PROJECT_DATA_DIR` 参数化数据路径并保留当前 D 盘默认、完善 `.gitignore`/`.dockerignore`、更新 `.env.example` 和 README，新增 `docs/release_readiness.md`。已在缺少 `.git` 时初始化本地 Git 仓库，未提交/推送。初始化后工具环境多次返回 `setup refresh had errors`，因此暂未完成 `git status`/ignore 审查和 Compose YAML 检查；这些需先恢复命令行再完成。随后需要用户在 WSL 同步 Dockerfile/Compose/忽略规则，构建并跑扩充版验收。
- 阶段 7 验收完成（用户实测）：`git status --short` 仅列出预期项目文件/目录；`.env`、虚拟环境、pytest 临时目录、数据库/WAL、向量库和 egg-info 等 7 项均命中 `.gitignore`，`.env.example` 未忽略。用户已同步 Dockerfile、Compose、`.dockerignore` 至 `/opt/project2`；镜像成功构建，容器 recreated/started 并为 `healthy`。`docker inspect` 确认唯一数据挂载 `/mnt/d/project_2/data -> /app/data`；`verify_phase6.sh` 11 用例全通过、EXIT=0。首次构建期间的 curl 56 是容器尚处于 health: starting 时的瞬态请求，容器就绪后复跑验收全绿。未提交或推送 GitHub；该结果已更新至 `docs/release_readiness.md`、`task_plan.md` 和 `docs/project_status.md`。
- 阶段 8 本地发布准备完成：GitHub 连接已可用，本地终端经命令级 `safe.directory` 参数恢复；审阅 93 个待提交文件，确认 `.env`、本机数据库/WAL、向量库、虚拟环境、测试缓存和 egg-info 均不在清单中。已知 token 格式扫描无命中，`.env.example` 的 API Key 留空。Compose YAML 解析成功，数据挂载模板为 `/mnt/d/project_2/data -> /app/data`。初始本地提交 `e68a1cea3bc6f31cb7704c709f6273aae900ee04` 已创建，使用 GitHub noreply 邮箱保护本机个人邮箱；当前无 remote。GitHub 工具未提供创建仓库操作，待用户创建空白公开仓库 `enterprise-support-agent-v2` 并提供 URL 后推送。没有输出或提交任何凭据。
- GitHub 公开仓库已通过本机 Git Credential Manager 认证创建：`https://github.com/KaelLee335/enterprise-support-agent-v2`，visibility=public，空白初始化（无 README/license/gitignore）。未输出令牌。下一步添加 origin 并推送本地 `main` 上的首个提交，再核对远端分支与文件清单。
- 最终发布验收：本机 push 成功，GitHub API 确认仓库 public、默认分支 `main`；`git ls-remote` 返回 HEAD `04503a162aabaf671d90bbe7d3859100cd0162cc`，本地状态为 `main...origin/main`。远端树 105 项且未截断，含 README、`src/`、`tests/`，未出现 `.env`、数据库/WAL、`data/vector_store`、虚拟环境、缓存或 egg-info 路径。虚拟网卡只读检查显示 WLAN、WSL、Mihomo、VMware 适配器在线；未更改网卡或路由设置。
- 阶段 9 主机启动只读审查：发现 `\\WSL-Dockerd-Autostart` 执行 `wsl.exe -d Ubuntu -u root -- /usr/local/bin/start-dockerd.sh`，由当前用户以 Interactive/ Limited 运行；触发器是已启用 Logon，不是 Startup。任务 State=Running；最近执行时间 2026-11-16 09:58:58，结果代码 267009。该检查只读取任务设置，没有触发或修改任务、Docker daemon、WSL/systemd 或虚拟网卡。README、`docs/wsl_docker_lifecycle.md`、`docs/project_status.md`、`task_plan.md` 和 `AGENTS.md` 已记录该边界。若用户需要登录前的开机自启，需先确定并授权系统任务变更。
- 用户澄清“开机触发”是指 Windows 用户登录时触发；截图确认 `WSL-Dockerd-Autostart` 配置本来就是 Logon trigger，与只读检查一致。用户选择保留现状，无需修改。阶段 9 完成；未验证 Windows 重启后的自动触发行为。

### 结构化追踪最终容器验收（用户实测）

- 最新 `observability.py`、`agent/graph.py`、`main.py` 已同步至 `/opt/project2` 并重建，构建耗时约 1 分 33 秒。
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
- WSL 同步与验收：auth.py 等 7 个源码/测试文件同步至 `/opt/project2`，`DEMO_TOKEN_*` 追加至 WSL `.env`，容器重建后 health 200、verify_phase6.sh 11 用例全 PASS。
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
- 阶段 13 尚缺 clean clone 中的 API 进程 smoke：health 200 和 Authorization Bearer 查询虚构订单 1001。本会话尝试执行时仍报 setup refresh errors，因此需要用户在克隆目录启动并验证。
- 无 WSL/Docker 操作；未运行索引，没有发生新的云端调用。


# 2026-11-16 — 干净克隆首次启动验收与阶段 14 收尾

- 用户截图报告干净克隆 API 冒烟通过：`GET /health` 无认证返回 `{"status":"ok"}`；使用 `Bearer demo-a-local-token` 查询 `/orders/1001` 返回 200 和 demo-a 虚构订单；缺少 token 返回 401。结合此前用户报告的 venv/依赖安装和 53 项 pytest（18.39 秒）通过，阶段 13 首次启动复现完成。以上均为用户报告，本会话未自行启动进程或重跑测试。
- 同步修正需求追踪矩阵和故障库中两条回归仍写“尚未运行/待运行”的旧状态：用户报告的 53 项全量测试包含随机订单 not_found 404 与 fake Chat Model timeout 安全答复测试；真实 429、checkpoint 损坏和 Compose 缺 Key/路径仍保持未验证/部分覆盖。
- 复核并更新 README（无过期测试数）、项目故事、面试材料、演示手册、需求追踪、故障库、项目状态、AGENTS、task_plan 与 WSL 生命周期说明。WSL NAT 修复内容仅按用户报告记录；未运行 WSL/Docker、未改主机配置。
- 阶段 14 文档一致性核查完成。阶段 15 生产化仍为另行定范围的非 Demo 工作；当前项目阶段可交接。
