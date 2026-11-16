# 阶段 0：项目与 V1 资产盘点

检查日期：2026-11-14。此次只读检查 V1；没有修改 V1 文件。V1 Git 工作区有一项既存修改，见下方。

## 当前 V2 状态

- 工程：Python 3.12，`pyproject.toml` 声明 FastAPI、Uvicorn；开发依赖为 pytest、httpx。
- 已有 API：`GET /health`、`GET /orders/{order_id}`；订单端点要求 `X-Tenant-ID`。
- 已有 SQLite 表：`tenants`、`orders`，含租户索引；启动时导入 20 条 V1 订单并幂等插入订单 `1001`。
- 已有基本 logging、Pydantic 响应模型及 6 个 API/数据库测试。
- 尚无 `POST /chat`、LangChain、LangGraph、RAG、Agent 执行记录、身份认证、checkpoint 或 HITL 审批实现。因此阶段 1 核心骨架已在，但不能将整个 Agent 项目描述为已完成。
- Dockerfile、Compose 和 `.dockerignore` 已存在；README 有 Docker/WSL 启动说明。当前项目没有在本轮启动或验证。
- 阶段 0 检查时当前 PowerShell Python 为 3.12.10；全局解释器没有 FastAPI、LangChain、LangGraph，pytest 9.1.1 与 pyproject 的 `pytest<9` 约束不一致。阶段 1 随后创建 `.venv` 并按项目约束安装依赖；该环境测试通过。
- Windows 会话找不到 `docker` 命令；`wsl.exe --status` 返回不可读状态且退出码 -1。用户说明 Docker Desktop 已由桌面的 `启动dify.bat` 启动；本轮未连接或检查该服务，也未将“Dify 已启动”视为 V2 容器已运行。

## V1 位置和可复用资产

V1 仓库位于 `D:\python_project\enterprise-support-agent`。V1 目录可读，当前分支为 `main`。只读 Git 检查发现：

- V1 有既存未提交修改：`.env.example` 中 `DIFY_API_KEY` 从占位文本改为空值。不要覆盖、还原或清理该修改。
- V1 其余工作区状态未报告修改。V2 没有可用 Git 元数据（当前目录并非 Git 仓库）。
- V1 `data/knowledge/` 有 POL-01 至 POL-10；V2 `data/policies/` 的这十份文件 SHA-256 全部相同。
- V1 `data/orders.json` 含 20 条订单；V2 `data/seed/v1_orders.json` 与之逐字节一致。导入时将历史订单归入 `legacy-demo`，不根据缺失资料猜客户或商品属性。
- V1 `data/eval_cases.json` 有 45 条用例；V2 `data/evaluation/v1_eval_cases.json` 与之逐字节一致。用例包含 route、工具参数、预期证据、断言和判分说明；Dify route 名需映射到 V2 轨迹语义，不能冒称真实 LangGraph 路由。
- V1 `docs/architecture.md`、`README.md`、`reports/evaluation_results.json` 分别与 V2 的 `docs/v1_architecture.md`、`docs/v1_README.md`、`data/evaluation/v1_results/evaluation_results.json` 逐字节一致。
- V1 提供 Dify Chatflow DSL (`dify/support-agent.yml`)、知识库设置说明、评估脚本和历史报告。DSL 可供流程参考；文档说明导入 DSL 不会带上 Dify 知识库文件或索引。未发现可移植的向量库索引/实际 embedding 导出文件。
- 评估数据存在记录口径差异：Markdown 汇总写 127 条；结果 JSON 元数据显示 `captured_run_count=127`、`actual_saved_run_count=125`。迁移时保留来源口径并标注，不能把 127 直接描述成 125 条实际保存记录。

## 规则一致性边界

- RET-01 与 QUA-01 是 V2 固定业务事实，并非 V1 原文规则。V1 POL-02 没有定制商品例外；V1 POL-03 有 15 日质量换货申请与人工检测，但没有本项目明确的凭证要求、普通/定制统一申请范围和审核措辞。
- 迁移时继续保留 POL-01 至 POL-10 原文，单独维护 RET-01/QUA-01；评估中标注来源和版本差异。案例 `1001` 的正确结论是：不能按 7 日无理由退货，但可在签收后 15 日内提交质量售后申请，需凭证、人工审核；不得承诺退款或审核通过。

## 迁移方案

1. 以当前 V2 为唯一写入目标；V1 仓库和来源记录只读保留，绝不在 V1 上做重构。
2. 阶段 1 沿用当前 FastAPI/SQLite 代码，补充并验证运行环境，不另起工程；以订单 1001 和跨租户拒绝为首个演示验收。
3. RAG 先用 V1 的 10 份 Markdown + V2 明确规则构建小型、可本地重建的索引；索引/嵌入配置作为生成物或可复现配置处理，不假定可从 DSL 还原。保留来源 ID 和可检查召回片段。
4. 在实现 LangGraph 前先与用户共同确认 State、节点、分支和工具边界；由确定性后端完成租户过滤、参数校验与只读限制，LLM 不负责授权。
5. 复用 45 条用例，先把 V1 的 route 与 evidence 语义映射成 V2 评估字段；将 125 实存/127 捕获的历史运行口径、版本、遗漏遥测和人工判分限制如实保留。新增固定订单 1001 用例，但不混淆 V1/V2 数据。
6. 逐阶段实现 checkpoint/HITL、故障注入与 Docker；Docker 使用 WSL/Docker Desktop 时由该环境实际启动并查看日志，当前工作区已有的配置需在阶段 6 验收时验证。

## 建议的最小结构

```text
src/support_agent/
├── main.py                 # FastAPI 应用和 lifespan
├── api/                    # chat、orders、health 路由（逐步拆出）
├── schemas/                 # 请求/响应 Pydantic 模型
├── config.py                # 环境配置
├── db/                      # SQLite 连接、schema、仓储
├── services/                # 权限与业务规则
├── rag/                     # 文档加载、分块、向量检索、证据返回
├── agent/                   # LangGraph state、nodes、edges、graph
├── tools/                   # 受权限服务保护的只读工具
└── observability/           # 结构化日志/执行记录
data/
├── policies/                # V1 政策只读副本 + 有来源标注的 V2 规则
├── seed/                    # 模拟订单
└── evaluation/              # 评估规格、历史来源结果、V2 运行记录
tests/                       # 单元、API、租户边界、Agent/RAG 评估
docs/                        # 架构、流程、State、权限、评估、Bad Case
```

这是目标分层，不建议一次性创建所有空目录。按阶段引入模块，避免为目录结构本身制造复杂度。

## 验收状态与待核实项

- 阶段 0 资产盘点完成；没有运行测试，因为本轮要求只做项目检查及迁移方案，当前解释器依赖也不满足项目约束。
- V2 API 运行、Docker 镜像构建、WSL Docker 命令和 Dify UI 中知识库实际配置均未在本轮验证。
- Dify DSL 和本地源文件均可读，但若后续要确认当前运行实例的知识库绑定/索引，需要在 Dify 已启动环境内核实；V2 运行不依赖 Dify。

## 阶段 1 验收更新（2026-11-14）

- 已建立项目 `.venv` 并安装 `pyproject.toml` 中项目及开发依赖；不要使用全局 pytest 9.x 替代项目虚拟环境中的 pytest 8.x。
- 回归测试：6 passed。pytest 默认 Windows 临时目录和工作区既有 `.pytest-tmp` 在当前会话拒绝访问；改用授权可写的 Codex 输出目录作为 `--basetemp`，并关闭 cache provider 后通过。
- Uvicorn 实际启动后验证 `/docs` HTTP 200、`/health` 返回 `ok`、租户 `demo-a` 查到订单 1001、`legacy-demo` 查同订单返回 404。临时服务已停止；SQLite 验收 DB 在 Codex 本地输出目录。
- 警告：当前新版本 Starlette 提示 `httpx` TestClient 集成后续弃用（建议迁移到 `httpx2`）；不影响本轮测试，但升级依赖时需重新核验。

## 云端 Embedding 准备

- 用户选择云端 API，并已确定使用 SiliconFlow。
- SiliconFlow 官方[快速上手文档](https://docs.siliconflow.cn/docs/userguide/quickstart)给出 OpenAI 风格接入和 `https://api.siliconflow.cn/v1` Base URL；其官方托管的[DB-GPT 接入示例](https://docs.siliconflow.cn/docs/usercases/use-siliconcloud-in-DB-GPT)示例使用 `BAAI/bge-large-zh-v1.5` 调用 `/v1/embeddings`。当前账户可用模型与价格须以服务商模型目录为准。
- 下一项用户操作：在本机安全配置 SiliconFlow API Key（不通过聊天发送）。

## 阶段 2 RAG 设计初步核查

- 用户已选择 SiliconFlow。该服务商的官方托管示例指向 `https://api.siliconflow.cn/v1/embeddings`，并举例使用 `BAAI/bge-large-zh-v1.5`；V1 DSL 自身也曾使用 SiliconFlow 插件（LLM 插件不等于已配置 Embedding）。
- 当前 12 份 Markdown 规则单份约 160–370 字符，很短。建议第一版每个政策文件作为一个向量文档（保留 `source_id`、标题/规则编号、版本/来源元数据），不把单条政策上下文切碎；后续若召回错误或证据过长，再用分隔符按规则小节切分并做对照评测。
- 初步链路：Markdown loader → 轻量 splitter/按文件成块 → SiliconFlow embeddings → 本地持久向量库 → top-k 检索与打印 source_id/原文片段。当前建议先做“只看检索结果”的可观察基线；带 LLM 生成的证据约束回答还要确认聊天模型接口/凭据，并且不能从最终文本推断召回内容。
- LangChain 当前集成包的 API 需依照官方新文档和锁定版本实现；旧 `python.langchain.com` 文档已提示内容过时，不能照搬旧 v0.3 示例。

## 阶段 2 实现状态（2026-11-14）

- 用户确认每份政策一个块。实现分块器时设置 400 字符上限、0 重叠；当前语料每份 160–370 字符，实际仍每份一块。长文未来可按 Markdown/段落分割。
- 使用 `OpenAIEmbeddings` 兼容 SiliconFlow embedding endpoint，并用 `langchain-chroma` 在 `data/vector_store/` 持久化；默认模型为 `BAAI/bge-large-zh-v1.5`，需以用户账号模型目录确认是否可用。
- 安装版本：langchain 1.5.0、langchain-openai 1.8.0、langchain-text-splitters 1.1.3、langchain-chroma 1.1.0、chromadb 1.5.9。
- 重复索引使用稳定 chunk ID 和内容 hash 跳过不变块；按 Embedding 模型名隔离 collection，避免模型切换后错误混用向量；空索引输入被阻止。
- 本地测试共 11 passed（含 6 个后端测试和 5 个检索测试），使用假 Embedding；这只验证程序逻辑，不代表真实模型接口可用或真实检索召回达标。
- 真实索引、真实查询和 Recall@K 仍需 SiliconFlow API Key。文档命令见 README；Key 只能保存在本机 `.env`，不能发到对话或提交仓库。
- 官方资料：LangChain Embeddings 接口说明 `embed_documents` / `embed_query` 见 [LangChain Embedding integrations](https://docs.langchain.com/oss/python/integrations/embeddings)；OpenAIEmbeddings 的 `base_url` 参数见 [LangChain OpenAIEmbeddings API reference](https://reference.langchain.com/python/langchain-openai/embeddings/base/OpenAIEmbeddings)；Chroma `persist_directory` 见 [LangChain Chroma reference](https://reference.langchain.com/python/langchain-chroma/vectorstores/Chroma)；SiliconFlow endpoint/model 接入示例见其[官方托管示例](https://docs.siliconflow.cn/docs/usercases/use-siliconcloud-in-DB-GPT)。

## 阶段 3 验收

- 用户确认先做单轮 State，不保存对话历史。状态保存 question、tenant_id、数据库路径（API 注入）、intent、order_id、订单、证据、答复、引用校验和错误摘要。
- LangGraph 条件流程：`route_request` → 订单只读查询 / 政策检索与生成 / 写请求拒绝 / 缺参澄清。订单查询始终用 tenant_id 过滤；写操作请求不会调用订单工具。
- `POST /chat` 已加入 FastAPI，返回意图、答案、订单或政策证据与引用检查状态。引用号检查不等价于语义证据校验。
- 更新后全套 25 项测试通过。当前未在 HTTP 下调用真实 Chat API；RAG CLI 单独已有一次真实 SiliconFlow 问答验证。
- 用户提供的真实运行结果：12 文档/12 chunks 已用 `BAAI/bge-large-zh-v1.5` 向量化，且 POL-03、POL-06 检索命中正常。Key 在本机 `.env`，此工作区未读取或输出 Key 值。
- 真实 retrieval evaluation：36 条有证据标签用例，Hit@4 100.0%、mean Recall@4 86.6%、完全召回全部标注证据的用例比例 72.2%；结果保存在 `data/evaluation/v2_retrieval_20261114T092303Z.json`。不计分的 9 条是无 required evidence 标注的案例。
- Bad case 初步分析：缺失证据集中于 `no_answer` 与 `security_request` 的多证据案例，`POL-10` 人工协助边界常未进入 Top-4；因此不能只看 Hit@4，完整证据召回率更能暴露问题。提高 Top-K 可能帮助；Reranker 只能重排已取回候选，不会补回未召回的 POL-10。

## 阶段 4–5 结果

- HITL 使用 `langgraph-checkpoint-sqlite` 的 `SqliteSaver` 做本机演示；暂停状态可跨应用重启恢复。审批 API 对 thread tenant 做范围检查。SqliteSaver 适合轻量演示，不视为生产多实例存储。
- 用户批准退款审批方案：审批通过仅记录 `approved_demo`，不调用退款系统、不写订单数据。
- JSON 日志输出到 stdout，响应增加 `X-Trace-ID`；当前记录有限事件元数据，不记录 prompt/answer。
- 阶段 5 安全路由复用 4 个明确 no-write 用例，4/4 通过；SEC-01 初始 Bad Case 已补充状态伪造识别。详细口径和局限见 `docs/evaluation_and_observability.md`。
- 故障注入覆盖数据库和 Embedding 服务失败；客户端看到安全提示和异常类型，具体异常栈只留服务端日志。
- 尚未完成 LLM 语义质量评分、真实模型端到端故障注入、top-k 调整对检索的对照。不要把有限规则评估描述为完整任务成功率。
- 阶段 6 静态准备：Dockerfile 补入 `data/policies` 和 `data/vector_store`；Compose 使用本地 `.env` 注入模型 Key、挂载 `data/` 并检查 `/health`。YAML 语法校验通过，但 Docker 镜像构建/容器健康/宿主持久化尚未验证。
- 用户报告 WSL Docker 阶段 6 首轮验收成功：容器健康、`/health` 200、订单查询和 `/chat` 成功；pytest 33 项通过。其容器使用 `/opt/project2` 构建以绕过 `/mnt/d` BuildKit 权限问题，以 `/mnt/d/project_2/data:/app/data` 保留 D 盘数据。
- 用户已将 `main.py` 的 seed path 三级回退同步回 Windows 项目，解决 site-packages 布局启动崩溃。
- 后续识别到订单号正则 `\b` 把“查询订单1001”误判为 clarify。已改为 ASCII token 边界判断，并新增无空格中英文混排 API/路由测试；Windows 工作区 35 项测试通过，安全路由评估 4/4。最终用户在 WSL 同步并重建后确认容器也已通过此用例（见下方最终验收结论）。

## 阶段 6 最终验收结论（覆盖此前待验证记录）

- 用户最终确认已将改动同步到 `/opt/project2` 并重建。容器健康，`/health` 返回 200；订单路由含“查询订单1001”无空格形式正确命中；退款请求进入 `pending`；政策问答引用 POL-06、`citations_valid=True`；日志 0 error；pytest 35 passed。
- `config.py` 使用 `_resolve_env_path` 为数据库、checkpoint、向量库解析环境路径：绝对路径原样使用，相对路径优先以运行 CWD 为基准，以避免 pip 安装布局把容器数据解析到 `site-packages`。Docker 工作目录为 `/app`，数据 bind mount 到 `/app/data`。
- `main.py` 的 seed 文件解析兼容源码、安装包和容器布局，并支持环境变量覆盖。
- 阶段 0–6 最终验收完成。前文中“需要用户重建以验证最新修复”的状态已由本节最终实测结果取代。
- 最新追踪代码已由用户同步到 WSL 并重建，订单、RAG 和审批节点均观测到预期字段，日志无 ERROR。订单节点示例耗时 route 约 0.5ms、lookup 约 16.9ms；本次政策回答中 POL-06 distance=0.625、生成节点约 756ms、citation_valid=true。
- WSL 构建期间 Dockerfile 已分离依赖与源码层以利用缓存，并改用 TUNA pip index 与 120 秒默认超时；当前 Windows 工作区 Dockerfile 与此优化一致。
- 补充 Agent 评估后，路由标签基线 30/35；坏例包括空输入、多个/非法订单号、个人信息索取和提示注入。修复并回归后可映射路由 35/35；准确订单参数 8/8、工具调用成功 9/9、标注结果 6/6、预期订单字段 5/5，临时数据库快照一致。完整报告和基线对照为 `data/evaluation/v2_agent_routes.json` 与 `data/evaluation/v2_agent_routes_before_fixes.json`。
- 最新 pytest 47 passed。评估仅覆盖有标签的确定性路由/工具结果；没有自动评判 LLM 答案语义，也没有给 10 个无 route 标签用例强行赋分。
- 用户最终确认最新 `nodes.py`/`state.py` 在 WSL 容器重建后通过异常订单号、多个订单号、隐私索取和提示注入用例，且正常订单与 POL-06 RAG 回归无误；断言式 `scripts/verify_phase6.sh` 在 `/opt/project2` 全部通过，EXIT=0。
- WSL 只读检查：`dockerd` PID 11 存活、`systemctl is-active docker` 为空、`is-enabled docker` 为 `enabled`。只能确认 daemon 当前运行；systemd 管理状态和跨 WSL/Windows 重启后的自动恢复未证实。演示期间应保持 daemon 所在 `inbox` WSL 会话运行。尚未修改 WSL 启动配置，避免与当前手动 daemon 冲突。详见 `docs/wsl_docker_lifecycle.md`。
- 追加检索评估：同一 36 条有证据标签案例的 Top-2/4/6/8 Hit@k 分别 97.2/100/100/100%，平均 Recall@k 分别 77.3/86.6/89.4/99.1%，完整证据率分别 58.3/72.2/77.8/97.2%。Top-2/6/8 报告在 `data/evaluation/v2_retrieval_top2.json`、`data/evaluation/v2_retrieval_top6.json`、`data/evaluation/v2_retrieval_top8.json`。默认配置仍为 Top-4；调整前还应比较答案语义质量、延迟和 token 成本。
- Top-4/Top-8 14 条答案生成探索性对照在 `data/evaluation/v2_rag_answers.json`。同模型 Qwen judge 的要点覆盖率为 76.9%/71.8%，引用格式检查两档均 100%。judge 对 KB-04 Top-4 有误判；Top-8 KB-04 答案还把“进液”说成可申请非人为故障保修，与 POL-04 明文规则冲突。不可把同模型 judge 分数当最终准确率；维持 Top-4，后续人工/独立裁判复核。
- 对 14 组生成答案完成逐项人工审阅，详情在 `docs/rag_answer_manual_review.md`。除 Top-8 KB-04 明显违背 POL-04 外，还发现 KB-01 未提商品条件、KB-05 漏人工退货指引、Top-4 KB-06 漏 1–3 日发起阶段、发票回答未明确聊天内不收集抬头/税号、MVP-KB-BOUNDARY 未充分区分质量问题与无理由退货。
- 提示优化实验记录：长规则提示导致矛盾答案，已撤销；短规则尝试未能修复质量问题分流，且引入未经证据支持的替代路线，均已撤销。当前 `src/support_agent/rag/answer.py` 仍为用户验收的原提示。`docs/rag_grounding_hardening_plan.md` 提出版本化规则约束层方案。未来改动必须先以可重复的 Bad Case 评估确认有效，再提议同步到 WSL。
- 经用户批准实施后，政策约束层 v1 在本机完成：`src/support_agent/rag/answer_constraints.py` 包含 POL-04 进液排除、POL-02 质量/无理由边界与退货条件、POL-05 运费指引、POL-06 退款阶段、POL-09 发票隐私/资格边界。关键硬边界用固定政策回复，其余仅补充证据原文要点；执行 ID 进入结构化日志。Top-4/8 14 案例共 28 条答案均通过来源 ID 校验；输出在 `data/evaluation/v2_rag_answers_constraints_v3.json`。此评估没有 LLM judge，不能视为语义准确率。
- 约束层尚未同步到 WSL Docker；容器仍运行用户先前验收版本。已准备 `scripts/update_wsl_and_verify.sh`，从 `inbox` WSL 会话运行时会将应用源文件及扩充后的 `verify_phase6.sh` 从 D 盘复制到 `/opt/project2`，重建后检查容器健康并运行全部断言。该部署脚本尚未由用户执行。
- 上条为历史状态，现已被后续实测取代：用户确认 D 盘源码已同步至 `/opt/project2` 并重建容器，扩充版 `verify_phase6.sh` 的 health 检查和 11 个业务用例全部通过，EXIT=0。最新执行证据记录于 `progress.md`，当前状态见 `docs/project_status.md`。
# 2026-11-16：原始项目要求与当前产物初步对照

- 仓库已有 `docs/langgraph_design.md` 的 Mermaid 路由图，以及 State、Checkpoint、租户隔离和单轮请求边界说明；`docs/interview_kit.md`、`docs/project_story.md` 已含架构讲解和面试材料。初步文件清单中未发现独立 PNG/SVG 架构图；后续追踪矩阵应区分可渲染 Mermaid 图与独立图片资产。
- 现有设计明确 `X-Tenant-ID` 只是演示租户范围参数，不是身份认证；订单查询通过 order ID 与 tenant ID 同时过滤。对照原始“用户身份/数据范围/工具权限”要求，应标记为 Demo 层租户隔离已实现、真实身份认证未实现，不能混为一项。
- 面试材料记录 SQLite 当前有 `tenants` 和 `orders` 表，没有 `users` 表或持久化 Agent 任务日志表；状态/轨迹目前分布在 SQLite checkpoint 与结构化日志。该差异需要纳入阶段 10 追踪，不自动增加新表。
- 原始要求的故障注入清单覆盖模型/数据库/Tool/Checkpoint/RAG/路由/Docker 配置等多个层次。当前测试文件已包含部分 Agent、RAG、API、DB 与日志测试，但完整清单的逐项证据尚未建立；阶段 10 应逐条核验而不是宣称全覆盖。
- 以上是阶段 10 正式逐项审计前的初步检查，不单独作为完整差距结论；后续完整审计见下节和 `docs/requirement_traceability.md`。

## 阶段 10 完整审计结论（2026-11-16）

- 完成了原始要求到仓库实现的逐项追踪，完整矩阵和故障注入清单见 `docs/requirement_traceability.md`。本阶段只读；未运行 pytest、WSL/Docker 验收或云端模型调用。
- 已证实的强边界：租户条件在订单查询 SQL 中强制，跨租户测试存在；`X-Tenant-ID` 仍不是用户认证；审批仍为 demo-only 状态转换。
- 重要部分实现项：业务节点是普通 Python/LangGraph Node，并非 LangChain `@tool`/`bind_tools`；Tool not_found 有离线评估但无直接 API E2E 用例；模型超时/限流、checkpoint 损坏和 Compose 缺 Key 仍缺独立故障演练。
- SQL 目前围绕 tenants/orders、seed 插入和只读查询；没有 users/agent-run 表，也没有 JOIN、订单 UPDATE/DELETE 业务路径。这是学习目标与当前轻量 Demo 的差距，不建议未经讨论添加无用写操作。
- 首先建议的用户学习主题是 LangChain：现有 RAG 生成链为 PromptTemplate → Chat Model → StrOutputParser；外层业务流程由 LangGraph 管理。设计是否需要形式化 Tool API，需在用户提出思路后讨论，不预设改造。

