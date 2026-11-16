# 工作进度

## 2026-11-14

- 开始阶段 0；已读取用户提供的项目范围、工程目标和阶段要求。
- 已初始化 `task_plan.md`、`findings.md` 和 `progress.md`。
- 确认 V1 路径 `D:\python_project\enterprise-support-agent`，并核对 10 份政策、20 条订单、45 条评估规格、README、架构说明和结果 JSON 的 V2 副本哈希；各副本均与来源一致。
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
- 阶段 8 执行核实：GitHub 连接已可用，本地终端经临时 `safe.directory` 参数恢复；审阅 93 个待提交文件，确认 `.env`、本机数据库/WAL、向量库、虚拟环境、测试缓存和 egg-info 均不在清单中。令牌格式扫描无命中，`.env.example` 的 API Key 留空。Compose YAML 解析成功，数据挂载模板为 `/mnt/d/project_2/data -> /app/data`。代码已暂存，等待空白公开远端 URL 后创建初始提交并推送；采用 GitHub noreply 邮箱避免公开本机个人邮箱。没有输出或提交任何凭据。

### 结构化追踪最终容器验收（用户实测）

- 最新 `observability.py`、`agent/graph.py`、`main.py` 已同步至 `/opt/project2` 并重建，构建耗时约 1 分 33 秒。
- 用户为降低重复构建时间并处理 pip 超时，将 Dockerfile 改为先安装依赖、再安装本地源码的缓存分层，并切换到 TUNA pip 源、延长下载超时；该 Dockerfile 已同步在 Windows 工作区。
- 订单日志实际包含 `question_preview`、`node_start/end` 和 `duration_ms`（route 约 0.5ms、lookup 约 16.9ms）。政策问答日志包含检索来源及距离，POL-06 distance=0.625 为此次最相似来源，生成节点约 756ms、`citation_valid=true`。退款审批暂停记录为 INFO `node_pause`，状态 `pending`。
- 全程无 ERROR；本机日志脱敏/耗时等回归 39 项通过。用户要求将学习理解问题留到之后统一处理，本轮不追加答题问题。
