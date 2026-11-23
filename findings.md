# 阶段 0：项目与 V1 资产盘点

## 2026-11-22 Phase 3 OOS 回归更新

- OOS-05 暴露复合查询 Top-4 证据遗漏。新增仅在定制商品、质量问题、寄回/运费三个信号共现时启用的检索查询扩展；测试实际 Chroma Top-4 命中 QUA-01、RET-01、POL-02、POL-05。Top-K 仍为 4，用户原问题仍传给生成模型。
- OOS-v1 复测为 Hit@4 100%、Macro Recall@4 100%、答案规则筛查 100%、拒答边界 100%、引用标签匹配 100%、筛查 Bad Case 0。OOS-05 参与调优，必须标注为回归，不能作为 blind 成绩或语义准确率。
- 人工复核发现 OOS-05 答案额外提出照片/视频格式，而政策只要求质量问题凭证，没有指定介质；当前规则检查未捕捉这一无依据细节。
- OOS-v2 15 条案例已由用户于 2026-11-23 审核通过；独立 runner 已支持 `--dataset` 并为该数据集生成独立报告和 Bad Case ledger。HOLDOUT-04 目标来自此前观察到的凭证格式无依据追问，故该集合不是完全盲测。外部模型调用需单独授权，获得授权前不运行真实评估。用户报告早前冲突保护版本 WSL 验收通过，但当前复合查询扩展未部署，待用户提交后同步。
- 用户授权后真实评估完成：Hit@4 15/15、Macro Recall@4 93.3%、答案规则初筛 3/15、拒答词面初筛 0/6、引用标签匹配 15/15；12 个自动筛查案例（GENERATION 10、RETRIEVAL 2）。拒答短语检查可能误报，不能把筛查通过率解释为语义准确度；HOLDOUT-04 输出确有未被规则检查发现的具体凭证格式幻觉。人工复核前不做 Prompt/约束调整。
- 已对 12 个候选项逐例对照原政策，完成 Codex 初步分诊，详见 `data/evaluation/oos/rag_oos_v2_manual_triage.md`。发现 HOLDOUT-03/04/12 的明确答复偏差；HOLDOUT-02/06/13/15 多为词面检查误报；HOLDOUT-08/10 的标注必要性值得复核。该分诊不是用户最终裁定，Bad Case ledger 中人工根因字段保持 pending。

## 2026-11-22 Phase 3 Bad Case 评估闭环

- OOS Markdown 报告已有问题、期望/实际回答、召回来源、自动可能原因和建议；此前缺少结构化机器可读记录及人工根因、修复和回归追踪字段。
- 新 ledger 将初筛类别/原因标记为未确认假设；人工根因类别限制为 DATA、CHUNK、RETRIEVAL、GENERATION、BUSINESS、ABSTENTION，修复/回归证据以独立字段记录。
- runner 改动仅影响评估输出，不修改 RAG 生成、检索阈值或既有报告。真实 OOS 运行可以写入该 ledger，但本阶段尚未运行模型或刷新任何 OOS 指标。
- 三个离线特征测试确认：非空无关证据仍可让带合法 source ID 的答复通过引用白名单；矛盾证据没有专门冲突标记；FakeListChatModel 返回指令诱导的承诺时引用编号检查仍可能为真。这些测试描述结构局限，不代表真实 LLM 行为。
- 已由用户批准完成 SiliconFlow Embedding-only 校准，详细原始探针、排序和距离见 `data/evaluation/oos/embedding_distance_calibration_v1.md`。12 条可回答探针的目标均进入 Top-4；但可回答目标距离范围 0.6516–1.1380 与无答案最近距离 0.9072–1.1817 明显重叠。该样本不支持安全的全局低相关阈值。
- 校准阶段没有改变 Chroma/SQLite 或回答行为。用户随后批准了窄范围实现：仅针对检索句子在去掉显式“不/没/未”后完全相同、否定极性相反、且与当前问题共享具体业务主题锚点的情况。冲突会在生成前短路为带引用的人工核验答复；不同条件、例外范围、退款不同阶段及无关主题不自动认作冲突。它不能覆盖语义改写式冲突，不能当作通用矛盾检测。

## 2026-11-22 Phase 2 权限实施发现

- 权限事实现在由服务端 tenant membership、Customer 所属关系、Service grants 和 approval task 分配共同决定；Demo token 只选择固定虚构主体，客户端 user/tenant/role/approver 字段不作为身份来源。
- SQLite 订单查询在 SQL 中同时约束租户与客户/授权关系；MockShop 先读取最小 scope 标识并完成授权，再获取订单详情。旧导入订单没有可靠 owner 的，不猜测回填，默认对 Customer/Service 不可见。
- 审批状态以持久任务表为准，比较并交换更新覆盖重复/并发决策；恢复 LangGraph checkpoint 时仍要使用当前认证身份校验 assignee。
- schema 是增量的：新增权限表，并仅在旧 after-sale 表缺列时添加可空 `actor_id/customer_id`；旧记录无自动回填。本会话只在 pytest 临时数据库验证；用户报告已备份持久库并通过 WSL 流程执行首次迁移。
- 完整测试 115 passed / 20.29s。剩余重要风险：approval SQLite 与 LangGraph checkpoint 不同库，写入决策后若 Graph 恢复失败，可能需要人工对账；这不触发真实退款。
- WSL 验收后续发现：旧版 `aftersale_requests` 迁移加列后，存量行的 `actor_id/customer_id` 为 NULL。幂等重试将这两个字段视作未知，不参与冲突比较；`user_id/order_id/platform/reason` 继续严格比较，非空审计字段也必须匹配。修复通过 legacy-row API 回归和全量 pytest 115 passed / 20.29s；用户报告 WSL 重建后 phase6 与 v21 全通过，并在真实 2026-11-18 存量行上确认重试复用原申请。

## 2026-11-18 V2.1 电商集成补充发现

- 第二个固定 MockShop 店铺 `shop-demo-b` 映射到独立 tenant `demo-b`。新增平台 API fixture 后，如果 SQLite 未初始化此租户，Webhook 写入会被 tenant 外键拒绝；已通过 seed `demo-b` tenant/user 和 user→customer 映射修复。
- 授权判断由服务端 `DemoIdentity` → tenant/store/customer 映射决定。平台 webhook 的租户从 `shop_id` 映射派生，不信任 event payload 的 tenant。订单和 webhook 事件均按 tenant 隔离；跨店返回 404。
- 售后创建是两步业务边界：资格查询只读；创建 endpoint 再验证 requester、订单范围、资格、显式 `confirmed` 和幂等键。返回 `pending_demo` 不代表审批通过或退款完成。
- HMAC 按 webhook 原始 body 计算；签名通过后才解析 schema。event_id 同 payload 重放视为 duplicate，不同 payload 冲突 409；旧事件不覆盖新状态。
- WSL 更新脚本之前没同步新增 `integrations/` 包和 mock-shop ASGI app；现已纳入同步清单，并在部署后运行专项 API 验收脚本。不要在 Windows checkout 执行 Compose `up`。
- 当前实证：全量 pytest 93 passed、Vue build、Compose static config、compileall 通过；Agent 路由 35/35、订单参数 8/8、工具 outcome 6/6、业务订单子集 5/5；WSL runtime 尚未验收。

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

V1 仓库位于 `[本机路径]`。V1 目录可读，当前分支为 `main`。只读 Git 检查发现：

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
- 用户报告 WSL Docker 阶段 6 首轮验收成功：容器健康、`/health` 200、订单查询和 `/chat` 成功；pytest 33 项通过。其容器使用 `the WSL project directory` 构建以绕过 `the local Windows-mounted directory` BuildKit 权限问题，以 `the local persistent data directory:/app/data` 保留 D 盘数据。
- 用户已将 `main.py` 的 seed path 三级回退同步回 Windows 项目，解决 site-packages 布局启动崩溃。
- 后续识别到订单号正则 `\b` 把“查询订单1001”误判为 clarify。已改为 ASCII token 边界判断，并新增无空格中英文混排 API/路由测试；Windows 工作区 35 项测试通过，安全路由评估 4/4。最终用户在 WSL 同步并重建后确认容器也已通过此用例（见下方最终验收结论）。

## 阶段 6 最终验收结论（覆盖此前待验证记录）

- 用户最终确认已将改动同步到 `the WSL project directory` 并重建。容器健康，`/health` 返回 200；订单路由含“查询订单1001”无空格形式正确命中；退款请求进入 `pending`；政策问答引用 POL-06、`citations_valid=True`；日志 0 error；pytest 35 passed。
- `config.py` 使用 `_resolve_env_path` 为数据库、checkpoint、向量库解析环境路径：绝对路径原样使用，相对路径优先以运行 CWD 为基准，以避免 pip 安装布局把容器数据解析到 `site-packages`。Docker 工作目录为 `/app`，数据 bind mount 到 `/app/data`。
- `main.py` 的 seed 文件解析兼容源码、安装包和容器布局，并支持环境变量覆盖。
- 阶段 0–6 最终验收完成。前文中“需要用户重建以验证最新修复”的状态已由本节最终实测结果取代。
- 最新追踪代码已由用户同步到 WSL 并重建，订单、RAG 和审批节点均观测到预期字段，日志无 ERROR。订单节点示例耗时 route 约 0.5ms、lookup 约 16.9ms；本次政策回答中 POL-06 distance=0.625、生成节点约 756ms、citation_valid=true。
- WSL 构建期间 Dockerfile 已分离依赖与源码层以利用缓存，并改用 TUNA pip index 与 120 秒默认超时；当前 Windows 工作区 Dockerfile 与此优化一致。
- 补充 Agent 评估后，路由标签基线 30/35；坏例包括空输入、多个/非法订单号、个人信息索取和提示注入。修复并回归后可映射路由 35/35；准确订单参数 8/8、工具调用成功 9/9、标注结果 6/6、预期订单字段 5/5，临时数据库快照一致。完整报告和基线对照为 `data/evaluation/v2_agent_routes.json` 与 `data/evaluation/v2_agent_routes_before_fixes.json`。
- 最新 pytest 47 passed。评估仅覆盖有标签的确定性路由/工具结果；没有自动评判 LLM 答案语义，也没有给 10 个无 route 标签用例强行赋分。
- 用户最终确认最新 `nodes.py`/`state.py` 在 WSL 容器重建后通过异常订单号、多个订单号、隐私索取和提示注入用例，且正常订单与 POL-06 RAG 回归无误；断言式 `scripts/verify_phase6.sh` 在 `the WSL project directory` 全部通过，EXIT=0。
- WSL 只读检查：`dockerd` PID 11 存活、`systemctl is-active docker` 为空、`is-enabled docker` 为 `enabled`。只能确认 daemon 当前运行；systemd 管理状态和跨 WSL/Windows 重启后的自动恢复未证实。演示期间应保持 daemon 所在 `inbox` WSL 会话运行。尚未修改 WSL 启动配置，避免与当前手动 daemon 冲突。详见 `docs/wsl_docker_lifecycle.md`。
- 追加检索评估：同一 36 条有证据标签案例的 Top-2/4/6/8 Hit@k 分别 97.2/100/100/100%，平均 Recall@k 分别 77.3/86.6/89.4/99.1%，完整证据率分别 58.3/72.2/77.8/97.2%。Top-2/6/8 报告在 `data/evaluation/v2_retrieval_top2.json`、`data/evaluation/v2_retrieval_top6.json`、`data/evaluation/v2_retrieval_top8.json`。默认配置仍为 Top-4；调整前还应比较答案语义质量、延迟和 token 成本。
- Top-4/Top-8 14 条答案生成探索性对照在 `data/evaluation/v2_rag_answers.json`。同模型 Qwen judge 的要点覆盖率为 76.9%/71.8%，引用格式检查两档均 100%。judge 对 KB-04 Top-4 有误判；Top-8 KB-04 答案还把“进液”说成可申请非人为故障保修，与 POL-04 明文规则冲突。不可把同模型 judge 分数当最终准确率；维持 Top-4，后续人工/独立裁判复核。
- 对 14 组生成答案完成逐项人工审阅，详情在 `docs/rag_answer_manual_review.md`。除 Top-8 KB-04 明显违背 POL-04 外，还发现 KB-01 未提商品条件、KB-05 漏人工退货指引、Top-4 KB-06 漏 1–3 日发起阶段、发票回答未明确聊天内不收集抬头/税号、MVP-KB-BOUNDARY 未充分区分质量问题与无理由退货。
- 提示优化实验记录：长规则提示导致矛盾答案，已撤销；短规则尝试未能修复质量问题分流，且引入未经证据支持的替代路线，均已撤销。当前 `src/support_agent/rag/answer.py` 仍为用户验收的原提示。`docs/rag_grounding_hardening_plan.md` 提出版本化规则约束层方案。未来改动必须先以可重复的 Bad Case 评估确认有效，再提议同步到 WSL。
- 经用户批准实施后，政策约束层 v1 在本机完成：`src/support_agent/rag/answer_constraints.py` 包含 POL-04 进液排除、POL-02 质量/无理由边界与退货条件、POL-05 运费指引、POL-06 退款阶段、POL-09 发票隐私/资格边界。关键硬边界用固定政策回复，其余仅补充证据原文要点；执行 ID 进入结构化日志。Top-4/8 14 案例共 28 条答案均通过来源 ID 校验；输出在 `data/evaluation/v2_rag_answers_constraints_v3.json`。此评估没有 LLM judge，不能视为语义准确率。
- 约束层尚未同步到 WSL Docker；容器仍运行用户先前验收版本。已准备 `scripts/update_wsl_and_verify.sh`，从 `inbox` WSL 会话运行时会将应用源文件及扩充后的 `verify_phase6.sh` 从 D 盘复制到 `the WSL project directory`，重建后检查容器健康并运行全部断言。该部署脚本尚未由用户执行。
- 上条为历史状态，现已被后续实测取代：用户确认 D 盘源码已同步至 `the WSL project directory` 并重建容器，扩充版 `verify_phase6.sh` 的 health 检查和 11 个业务用例全部通过，EXIT=0。最新执行证据记录于 `progress.md`，当前状态见 `docs/project_status.md`。
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

## 2026-11-16：采用新版自主开发提示词

- 新版协作分工取代上一版：Codex 负责技术路线、架构和主力开发；用户是学习者，不需要先产出设计或代码。旧的阶段 11 用户设计 gate 已移除，保留用户指定的学习顺序。
- 新版 P0 明确要求本地模拟身份/权限、用户与租户数据、必要执行记录和基础 CRUD/事务；当前项目只实现租户 header 范围隔离和订单只读，真实身份不存在。这属于待补的 Demo 级 P0，不等于需要引入生产认证或开放订单写操作。
- 新版要求每个模块有 `docs/learning/` 中文材料（代码位置、数据流图、可运行示例、必懂/了解内容、5–10 题），并建立统一故障案例库；这些尚未系统完成，列为后续 P0 交付材料。
- 记忆已同步至 `AGENTS.md`、`task_plan.md`、`docs/project_status.md`、`docs/requirement_traceability.md`、README、项目故事和面试材料。当前阶段 11 LangChain 应由 Codex 主动产出讲解与学习章节，不等待用户架构方案。


## 2026-11-16：Demo 身份认证与运行记录落地（交接代执行确认）

- `auth.py` 用固定 Bearer token 映射两个演示身份，替代 `X-Tenant-ID` header；租户从 token 派生，客户端伪造 header 无效（有测试覆盖）。
- `agent_runs` 记录运行生命周期（running/pending/completed/failed），含 trace_id/user_id/tenant_id/intent/error_type；跨租户读取返回 404；不存 question 明文，与脱敏日志原则一致。
- 全量测试 51 项通过（原 26 项定向 + 新增认证/运行记录用例）；verify_phase6.sh 已改用 `Authorization: Bearer`，默认 token 与 config.py 内置默认一致。
- 遗留：demo token 为公开示例值（.env.example 注明非生产凭据）；生产化需换真实认证，属学习目标差距项。

## 2026-11-16：WSL 重启后容器构建 DNS 失效（已修复）

- 现象：`docker compose up --build` 报 `Temporary failure in name resolution`（buildkit 内解析 TUNA 失败），宿主 curl 正常。
- 根因：`wsl --shutdown` 后 WSL NAT 本次启动分到 `the WSL-assigned private subnet`，与 docker0 的 `the Docker bridge private subnet` 子网重叠，容器流量路由被搅乱；此前 NAT 网段未撞上所以长期未暴露。
- 修复：`the Docker daemon configuration file` 增加 `"bip": "a separate private Docker bridge range"`（原文件备份 a backup of the daemon configuration），docker0 迁出冲突段；`the Docker startup script` 增加启动前等待 eth0 就绪（最多 30s），避免 dockerd 在网络未就绪时创建网桥。
- 教训：inbox WSL 每次重启 NAT 网段可能变化，docker 固定子网必须与之隔离；带 `nohup dockerd &` 的 wsl.exe 会话退出会连 dockerd 一起回收，daemon 持有必须用不退出的会话（the Docker startup script 的 sleep infinity）。
# 2026-11-16 补充：验收截图与学习文档

- 用户提供截图报告身份与租户隔离检查通过、51 项全量 pytest 通过、WSL health 200 和 11/11 验收通过；另报告 WSL NAT 网段冲突已通过备份后的 daemon bridge IP 调整修复。该主机修改未经本会话独立检查，禁止继续改 WSL/网卡配置。
- 本会话只读检查工具仍报 `setup refresh had errors`。GitHub main 最后可读提交为 `6a2c132`；当时远端不存在 `docs/learning/`。因此实际源代码身份改造是否已提交/推送未知。
- 新增 `docs/learning/langchain.md` 与索引，参考远端可读的 RAG 源文件编写，覆盖 Prompt → Chat Model → StrOutputParser、Retriever、答案约束、引用检查及 LangChain/LangGraph 分工。待本机执行恢复后与实际本地实现对齐并运行示例/相关测试；云端示例仅由用户显式运行。

## 2026-11-16：远端交接已核实，继续学习手册

- 用户新截图纠正先前状态：提交 `dbab8af` 与 `12338a1` 已推送且当时工作树干净；GitHub 只读查询确认 `main` HEAD 为 `12338a156975603bc4452e2fc1985100b312ad4c`。此前“main 仍为 6a2c132”的判断已被取代。
- 基于当前远端源码新增 LangGraph、RAG、SQL、FastAPI 学习章节草稿，包含 Mermaid 数据流、代码入口、示例、重点和自测题。它们还没在 GitHub `main` 目录出现，当前发布状态为未推送。
- 此会话新增章节后没有运行测试；功能验收仍引用用户截图报告的 51 passed、WSL 11/11 PASS。公开源码快照不是本地工作树复核的替代品。



## 2026-11-16：阶段 12 故障库和验收记录

- 用户报告全量 pytest 51 passed、WSL health 200 / 11 项 verifier 通过；这些是用户截图证据，不代表后续新增故障用例已运行。
- 新增统一 12 类故障手册 `docs/troubleshooting/fault_cases.md`，清楚区分已有覆盖、部分覆盖和未验证。优先补随机 not_found、Chat Model timeout/429、checkpoint 损坏；Compose 空 Key/路径检查在干净克隆阶段验证。
- 已完成并推送的学习章节：`docs/learning/{langchain,langgraph,rag,sql,fastapi}.md`。GitHub API 确认这些文件存在。
- 公开 README 已据用户 WSL 验收更新；阶段计划保留未完项，不把干净克隆或故障注入错误标成完成。
- 当前下一步需在隔离环境跑有针对性的故障测试，再执行 GitHub 干净克隆。不要在当前 WSL 容器/数据上进行破坏性注入。


## 2026-11-16：阶段 12 定向测试通过

- 用户截图报告本地从 origin/main 快进后新增两条测试通过：订单随机 not_found 404 与 Chat Model timeout 安全响应；2 passed in 4.61s。此前全量 pytest 51 passed（267 秒）是独立、更早结果。
- 阶段 12 按用户明确验收关闭；未覆盖的 checkpoint 文件损坏及 Compose 配置错误继续标记未验证，不能因 2 条通过而扩大结论。
- 阶段 13 需要干净 clone 实际安装与运行。静态 GitHub tree 未包含 .env、运行数据库、Chroma 向量库或虚拟环境；首次 RAG/容器部署须本地生成索引，Key 只留在本机 .env。
- 当前 Codex 本地执行器无法启动；克隆、pytest 和 HTTP smoke test 等本地结果需要用户在隔离 D 盘目录运行后提供。WSL/Docker 不需参与此阶段。


## 2026-11-16：干净克隆与包镜像

- 用户截图报告公开 main 9caa363 干净克隆，Python venv 与依赖安装成功，53 项 pytest 全通过，18.39 秒。此为用户现场结果；未在当前会话重跑。
- 全局 pip.ini 的 TUNA simple endpoint 返回 HTTP 403（pip User-Agent）；本次临时添加 Aliyun 镜像选项后安装成功。README 已记录一次性 pip mirror override，避免要求改全局配置。
- Dockerfile 仍使用 TUNA；仅在之后必要的 Dockerfile 改动中切换 Aliyun 或实现双源回退。本轮没有重建容器。
- 干净克隆还需跑 health 和带 Bearer 的 /orders/1001 smoke，才能完整确认首次运行路径。当前本地执行工具失败，等待用户在 clone 中执行。


## 阶段 13、14 验收更新（用户报告）

用户报告：干净克隆安装依赖后全量 pytest 53 项通过（18.39 秒）；API 首次启动 health 200、带 Bearer 的 demo 订单查询 200、缺少 token 返回 401。文档一致性收尾完成；本会话没有重跑测试或 API。真实 429、checkpoint 损坏和 Compose 缺 Key/路径仍未验证。


## 2026-11-16：阶段 13 与 14 收尾

用户报告干净克隆安装依赖后，全量 pytest 53 项通过（18.39 秒）；health 200、带 Bearer 查询演示订单 200、无 token 返回 401。阶段 14 文档一致性核对已完成。本会话未重跑测试或 API。真实供应商 429、checkpoint 损坏及 Compose 缺 Key/路径仍未验证。


## 阶段 15 第一步：checkpoint SQLite 完整性预检

`main.py` 在初始化订单数据库前打开 checkpoint 文件并执行 `PRAGMA quick_check`。异常或非 `ok` 结果会关闭连接并以清晰错误拒绝启动；不会删除、覆盖或自动新建替代 checkpoint。这保护了可能包含待审批状态的文件，恢复仍由操作者决定。新增临时文件回归测试验证原始坏文件字节保持不变，且订单数据库尚未初始化。GitHub Actions Python 3.12 全量套件 54 passed（2.98 秒）；没有真实 WSL/Docker 或模型 API 操作。

## 阶段 15 离线容器端到端 smoke

GitHub Actions `b797bda` 运行成功：Python 3.12 全量 pytest 55 passed in 3.99s；Compose 配置可解析；Dockerfile 使用阿里云 PyPI 源后镜像构建成功；在临时 Compose 容器中空 API Key 下 health 200、Bearer 查询演示订单成功，政策请求返回安全降级且不访问真实模型。容器只使用临时宿主目录和虚构 seed。该 CI 不等同用户 WSL 部署验收，当前运行容器未更新。

## 用户报告的 WSL 12 项验收

用户报告：同步最新公开 main 后，Docker 镜像重建、容器启动、health 200；`verify_phase6.sh` 12/12 PASS、EXIT=0。同步脚本的 CRLF 导致 pipefail 的问题经去除行尾回车修复。上述均是用户现场结果，本会话没有直接操作 WSL。

## 2026-11-17 — Compose bind mount 缺失源路径行为

- Compose v2.39.1 的隔离配置观察：缺 `.env` 时 `docker compose config --quiet` 非零退出并报告 env_file 路径；错误 `PROJECT_DATA_DIR` 可通过配置解析，且 `config` 自身不创建宿主路径。
- Docker Compose 短格式 bind mount 的官方默认行为是源目录不存在时自动创建。项目短语法因此可能把拼错的数据路径变成新的空目录，导致应用读写错误的数据位置。
- 修复：`compose.yaml` 使用长格式 bind mount 并设置 `bind.create_host_path: false`。临时副本 `docker compose config` 成功，`--format json` 中显式 true 表现为 `create_host_path: true`，false 使用 Compose 的默认省略序列化；配置中源路径与 `/app/data` 目标正确。
- 限制：本会话 daemon bridge 的 `docker ps` 返回远端连接重置，无法运行临时容器并观察实际挂载错误文本。没有操作用户 WSL、既有容器或 D 盘数据。后续在 Docker bridge 可用后完成该运行态验收。
- 参考：[Docker Compose 服务 volumes 文档](https://docs.docker.com/reference/compose-file/services/)（bind 短语法与 `create_host_path`）。

### 运行态闭环（Docker bridge 恢复后）

- 用户报告 bridge 已恢复。独立临时 Compose 项目实际启动一个 BusyBox 探针容器，无端口映射，且 `network_mode: none`；不存在的 bind source 在启动前被 dockerd 拒绝，明确返回 `bind source path does not exist`。
- 探针退出码为 1；Windows 对应临时目录未创建。`down --volumes --remove-orphans` 成功，临时工作目录已删除；原 `project2-support-agent-1` 后续检查仍 healthy。
- 这项真实引擎验收与 `docker compose config` 静态解析分开记录。全程没有停止/重建项目容器，没有操作 WSL 配置或 D 盘持久目录。

## 2026-11-17 — 外部客户场景规划基线

- 当前 `auth.py` 只有固定 Demo token 到 user/tenant 的映射，身份类型没有 role/customer_id。`db.py` 有 `tenants`、`demo_users`、`orders.customer_id` 和 `agent_runs`，但订单查询仅按 `order_id + tenant_id`；现有 demo seed 中 `customer_id` 还复用 tenant ID，不能拿它代表真实客户关系。
- `main.py` 中审批状态读取/决定只校验 thread tenant 与当前 tenant；审批决定记录到日志但没有专门审批记录表或角色要求。运行记录有 user_id/tenant_id，但 API 读权限只按 tenant 查询。
- 因此第一批安全可做工作是新建纯模拟 persona/成员关系和权限上下文、增加 customer_id 级查询约束、主管审批授权与独立审计记录，并以同租户跨客户、跨租户及非主管审批作为回归。
- 模拟方案暂定：客户只读自己的订单并发起请求；客服读本租户订单、提交审批；主管审批本租户请求且不可自批；所有角色都不能产生真实退款/订单写入。正式业务规则需要上线前确认。
- 历史生产依赖决策（IdP、部署区、PostgreSQL/checkpointer、客户数据保留及外部模型共享）不属于当前任务；用户已明确不做生产化。V2.1 当前计划与实现见 `docs/v2_1_demo_reinforcement_plan.md`。

## 2026-11-17 — V2.1 Demo 工程加固初步基线

- `auth.py` 的 `DemoIdentity` 目前只有 `user_id` 和 `tenant_id`，无 role；审批路由按 checkpoint tenant 校验，未验证发起者/审批者角色。
- `.github/workflows/tests.yml` 的路径过滤包含 `src/`、`tests/`、Dockerfile、Compose、`pyproject.toml` 与示例 env，当前遗漏 `data/seed/`、`data/policies/` 和 `frontend/`；现有 workflow 没有前端构建 job。
- `pyproject.toml` 声明依赖版本范围；前端已有 `frontend/package-lock.json`。本机尚未确认 `uv`/`pip-compile` 工具，生成 Python lockfile 的方法待检查，避免引入未经验证的依赖升级。
- 当前 Router 由 `nodes.py` 的显式关键词/正则规则决定，适合确定的有限业务意图；文档应明确路由评估样本边界，避免描述为通用自然语言理解。
- 当前 RAG 引用检查只验证来源编号来自本次召回，事实级支持仍靠人工/评估；不要把 citation validity 描述成语义正确率。
- 模拟物流 API 计划必须是本地可控 endpoint/transport，只使用合成 tracking 数据和不可外用的模拟认证标记；网络异常用假 transport 覆盖，不接商业物流商。

## 2026-11-17 — V2.1 本地实现结果

- 依赖锁用 `uv.lock` 管理，CI 固定 uv 并执行 `uv sync --locked` 校验锁文件未过期；Dockerfile 在依赖层与项目源码层分别执行 `uv sync --frozen`，避免按 Aliyun 镜像元数据重新解析。`setuptools` build backend 也固定版本。
- 审批 checkpoint 已包含请求人的 `user_id`；决策 endpoint 先以 tenant 做 404 隐藏，再要求 `approver` 演示角色，并拒绝同一 user 自批。批准只恢复图到 `approved_demo`，不触发订单写入。
- mock logistics 为同 Compose 网络内独立 FastAPI 服务。Agent 先用 SQLite `(order_id, tenant_id)` 核验，再发送 HTTP GET 与 `X-Demo-Service-Key`；响应由 Pydantic 校验。固定轨迹是虚构的，本项目没有商业物流 endpoint。
- 路由规则是有限关键词/正则分支，不是通用 NLU；RAG citation ID 检查不是事实蕴含检测。使用既有可追踪评估文件说明 30/35 → 35/35，不为这次文档更新发送模型请求。
- 本机验收口径为 65 项 pytest、Vue build、Compose 静态配置和源码编译；此前 container-to-container smoke 尚待 WSL 同步重建。后续用户报告已完成 WSL 重建，两个容器 healthy 且扩展 verifier 全通过。Docker 镜像构建尝试遭遇 daemon `unexpected EOF`，但被用户报告的 WSL 成功构建结果 supersede；未由本会话改变服务生命周期。
- 用户随后报告已从 WSL 执行同步/更新脚本：`/opt/project2` 已有新锁文件和代码，两容器 healthy，阶段 6 + V2.1 扩展 verifier 全部通过。该实机验收由用户报告。
## 2026-11-18 — V2.1 电商集成 Phase 0 盘点

- 当前目录组织为 `src/support_agent/`。FastAPI 路由在 `main.py`；Demo Bearer 身份映射在 `auth.py`；SQLite schema/查询在 `db.py`；单一 LangGraph 工作流在 `agent/graph.py`、`state.py`、`nodes.py`；政策 RAG 在 `rag/`；现有模拟物流 API 和 HTTP client 分别在 `mock_logistics.py`、`logistics.py`。
- 当前 `GET /orders/{order_id}` 按 `tenant_id` 查 SQLite；没有 store_id/user_id 订单归属关系，也没有平台原始状态、售后申请表、webhook event inbox、平台 Adapter/registry。
- Agent 当前为确定性正则/关键词路由。它有只读订单、模拟物流、政策 RAG、拒绝普通写请求和退款审批演示；Agent 不直接使用 LangChain Tools。本次电商 Tools 应先在后端服务与 Adapter 上形成可信边界，不为技术清单改写已有 Graph。
- Compose 已运行两个模拟服务容器：support-agent 和 mock-logistics；现有无密钥 CI 会构建镜像并跑 smoke。新增独立 mock-shop 服务会涉及 Compose/CI/WSL 同步，须在离线测试充分后再部署。
- 基线在 `D:\\project_2\\.venv\\Scripts\\python.exe -m pytest -q --basetemp=.pytest-tmp-v21`：71 passed，9.25s，1 个 pytest cache ACL warning。`uv run --locked pytest -q` 因全局 `D:\\caches\\uv` 初始化权限失败，在 pytest 启动前退出；没有改全局 ACL 或旧 pytest 临时目录。
- MVP 采用单个 MockShop；HTTP API 的外部平台结构在 Adapter 边界转换为领域 DTO；Agent/业务服务只消费 DTO。售后资格是明确标注的本地演示规则，创建申请只产生 `pending_demo` 申请记录；最终退款/退货执行不在范围。

## 2026-11-18 — Phase 1 MockShop API 与 Adapter 基础实现

- 新增独立 FastAPI app `support_agent.mock_shop_api:app`，API 前缀 `/mock-shop`；固定演示订单使用平台状态（`WAIT_SELLER_SEND_GOODS`、`WAIT_BUYER_RECEIVE`、`TRADE_SUCCESS`、`AFTERSALE_PROCESSING`、`REFUND_SUCCESS`），全部响应包含 `is_demo=true`。
- 当前服务端仓库是进程内演示 fixture，覆盖待发货/运输中/已签收/已有售后/已退款/不可退货及第二家虚构店铺；售后申请为 `WAIT_REVIEW`，使用 idempotency key 去重。它尚未持久化，也尚未纳入 Compose。
- 新增 `integrations.models` 的平台无关 DTO、`ECommerceAdapter` Protocol、简单 `AdapterRegistry`、`MockShopAdapter` typed client。Adapter 负责平台状态与领域状态映射；`shop_id → tenant_id` 是明确的 Demo 映射表，不允许 Agent 直接依赖平台 JSON 字段。
- 7 个新测试覆盖 endpoint 鉴权、固定订单状态、物流/资格结果、售后申请幂等/冲突、状态映射和 registry。新增测试 7 passed / 0.80s；全量 pytest **78 passed / 9.06s**，`-p no:cacheprovider` 避免已知 `.pytest_cache` ACL warning。
- 当前限制：MockShop 的售后状态只存在进程内；后续 Agent API 必须在主 SQLite 持久化本系统的售后申请与幂等 key，Webhook inbox 也需 SQLite 唯一约束。跨重启的 MockShop 状态持久化按 Demo 最小范围评估，不冒充平台持久化。

## 2026-11-18 — API/SQLite 权限与售后申请首版

- `integrations.permissions.can_access_order()` 使用显式 Demo 映射：`user-demo-a` 仅看 `customer-demo-a`；demo-a approver 可看同租户 `shop-demo-a`；租户或店铺不匹配统一返回 404。MockShop 的 `shop_id → tenant_id` 映射配置不依赖用户提交 header。
- FastAPI 新增 `/ecommerce/orders/{id}`、`/logistics`、`/aftersale-eligibility`、`/aftersales`、`/ecommerce/aftersales/{request_id}`。平台 HTTP/超时/无效 JSON/未知状态由 adapter 转成安全错误类型；API 不回显上游内部错误文本。
- `POST .../aftersales` 只允许 requester，必须 `confirmed=true`，经过订单归属与资格检查后才创建。SQLite `aftersale_requests` 用 `(tenant_id, idempotency_key)` 唯一约束记录 `submitting/pending_demo/failed`；相同请求重试复用同一个本地申请及平台 id，变更请求内容复用 key 返回 409。响应明确说明不代表审批、退货或退款完成。
- MockShop 服务加入 Compose（内部 8092，不对宿主机发布），support-agent 通过 service key 调用，Compose 等待其 healthcheck；GitHub Actions container smoke 新增平台订单查询和跨客户 404。
- 新增 5 个 API 回归；Adapter 测试扩展后 integration 模块 10 passed；当前全量 pytest **86 passed / 9.63s**，`docker compose config --quiet` 通过。尚未执行 Compose up/build、WSL 同步或真实平台调用。
- 注：主 SQLite 是本系统申请审计记录；MockShop API 仍是进程内虚拟平台，重启后平台端申请状态会重置。演示状态查询当前读主 SQLite，不把本地申请误称平台退款执行。

## 2026-11-18 — LangGraph 与 LangChain Tool 接入首版

- 路由规则仅在用户明确说“平台订单/电商订单/店铺订单/MockShop”时选择新增平台分支；原 V2 订单查询样本和合法 4 位订单号的路径不变。
- `integrations/tools.py` 用 LangChain `StructuredTool` 暴露结构化查询与售后方法；构建时捕获服务器验证过的 `DemoIdentity`，工具 schema 不接受 tenant/store/user id，调用前检查订单归属。当前 LangGraph 节点由确定性路由选择并调用读/资格工具，没有把工具交给 LLM 自由挑选。
- 售后资格节点先完成身份/订单授权，再检查 MockShop 资格，然后复用当前政策 RAG；检索无证据或失败时保留“无法确认政策”的安全说明，但仍会清楚标记平台演示资格，不把资格当批准/退款。未授权或平台失败时 Graph 在此停止，不进入 RAG。
- 写工具在 Toolset 里要求 requester + `confirmed=true`，实际业务写入口仍是专门 FastAPI endpoint，由它完成 SQLite idempotency reservation 与状态留存；自然语言意图本身不作为确认。
- Graph 测试覆盖平台订单/物流路由和“质量问题想退货”资格+RAG失败安全路径；StructuredTool 测试覆盖 5 个工具、身份绑定、确认和越权拒绝。
- 验收：定向 37 passed / 5.13s；全量 **89 passed / 10.05s**；既有 V1 路由标签 **35/35**、订单参数 **8/8**、DB unchanged，0 failures。CI/Compose 文件已改，但 CI 未触发，WSL 与 Vue 尚未更新。
# 2026-11-21 — OOS 评估实现发现（首次运行快照，已被后续复测取代）

- 开发集是 45 条，但原文件的 category 汇总元数据合计 43；本轮没有编辑或修正原数据，OOS 目录与执行器单独存放。
- Retriever 的 Top-K 来自配置（默认 4），向量查询调用 Chroma similarity search。答案函数返回用于回答的 evidence；OOS runner 对这份实际 evidence 计算 Hit/Recall，避免评估与模型上下文不一致。
- 15 条 OOS 题的相关来源标注不等于“无答案题无依据”：无答案/边界题仍标记支持拒答边界的政策来源。若知识库未来真没有支持性来源，可将 relevant_document_ids 留空；此时不参与检索指标。
- 当前 5 个 Bad Case 中，OOS-05 和 OOS-11 是多证据未全召回；Hit@4 仍为 100%，说明 Hit 指标掩盖了证据完整性差异。OOS-01、OOS-04、OOS-07 的词面规则项未过，可能是语义遗漏，也可能是检查口径问题，需人工审阅。OOS-05 还出现 `[POL-05_SHIPPING_AND_GUIDANCE]`，这不是政策文档编号；新增 OOS 检查会把不属于召回来源的引用标签标出来。
- 失败归类自动化只判断可直接观察的差异（RETRIEVAL、GENERATION、ABSTENTION）；DATA、CHUNK、BUSINESS 等根因必须由人对照原文确认，不自动推断。
- 当前输出是一次真实模型/向量库运行快照；重新运行会覆盖 Markdown 报告。该测试会向已授权的 SiliconFlow/Qwen 发送本 OOS 问题及检索证据用于回答，不发送个人数据。

## 2026-11-21 — OOS 回答自然度复测

- 最新版本剩余 OOS-05 是真实证据召回缺口；Hit@4 100% 仍可能掩盖完整证据不足。OOS-11 只要求第一轮澄清，POL-02 足以支持所问字段；用户若确认质量问题，后续回答再检索 POL-03。
- Before-style 报告保留首版原始答复。评估器和一条案例来源标注后来修正，所以聚合分数变化仅是方向性比较，不能视为严格同分母准确率提升。
- 目前无效约束编号不再输入给生成模型；质量运费回答不再无条件附加无理由退货费用；不确定的退货资格会先澄清。
- 进一步处理机械感：确定性补充与模型答复合并为同一段，同一政策编号不重复追加；如果用户问明天能否送达，会明确说不能保证明天。OOS 规则项检查在去空格后比较，避免中文数字格式导致误报。
- 最终真实复测（2026-11-21 11:42 UTC）：Hit@4 100.0%、Macro Recall@4 95.6%、答案规则项 93.3%、拒答/范围边界 100%、引用标签匹配 100%，仅剩 OOS-05 检索失败。全量 pytest 105 passed / 15.00s。
- 用户报告随后的 WSL 部署三容器 healthy，阶段 6 与 V2.1 验收全 PASS，OOS-05 修复在演示页已生效。该 runtime 验收与 11:42 UTC 的独立 OOS 评测快照分开保留；若要更新 OOS 统计，需基于部署修复后的实际 OOS 运行结果。
# 2026-11-22 — 工程质量审计

- 审计基线：项目根目录 `D:\project_2`。开始时工作区已存在上一轮 OOS 改进变更（回答约束、OOS 测试/报告及说明文档）；本轮需与审计发现分开归档。
- 任务要求阶段 1 先交审计报告；涉及身份权限、订单 SQL、RAG、LangGraph 等核心逻辑的修复，报告后提供原因/影响/方案并等用户确认。

# 2026-11-22 — 工程质量与开源竞争力审计结果

- 当前审计报告：`docs/engineering_audit_2026-11-22.md`。本轮只读核对代码、测试、README、CI/Compose 与已有运行证据；未改核心业务代码、规则、数据库、Chroma 或容器。
- 全量 pytest 本机复跑 **105 passed / 17.99s**。GitHub 公开 main/本地 HEAD 为 `43adc60`，Actions run 29 为 success；本地 OOS 改动未提交，因此不包含在远端 CI 证据里。
- 权限边界：普通 SQLite 订单和 `agent_runs` 查询按 tenant 过滤，不按 user/order ownership；MockShop user/store 权限测试存在，但授权发生在 adapter 返回订单之后。需先定义请求人和审批人的访问语义，再批准 schema/API 改动。
- Webhook 的 inbox 对 event_id 幂等、签名与 stale 状态有测试；`platform_order_states` 使用 `(platform, order_id)` 主键，未来 order_id 若仅在店铺内唯一会有碰撞覆盖风险。当前 Mock fixture 尚未覆盖。
- RAG 引用检查仅验证引用 ID 属于召回来源，空召回/服务异常可安全降级；无相关性阈值、证据冲突检测或事实蕴含测试。当前共享 Chroma 仅含 Demo 公共政策，不支持租户私有知识隔离。
- 现有 15-case OOS 已被用于回答约束/判分规则迭代；文件独立，但过程不再是 blind holdout。应保留为回归集并另建未参与调优的集合。
- README 当前验证摘要与阶段描述落后于最新 105 项与用户报告的 WSL 三容器验收。GitHub Actions 运行完整，但最新远端 run 只验证 `43adc60`。
# 2026-11-22 — Phase 2 权限模型审计

- 按 Customer/Service/Approver/Admin 目标规则完成源码只读核对，细节和待审 DDL 见 `docs/phase2_permission_model_and_migration_proposal.md`。
- 当前 auth 是固定 Demo token→DemoIdentity 映射；数据库没有角色列/关系，Service 和 Admin 角色尚不存在。SQLite order 只 tenant scope，`customer_id` 可空且含义不一致；AgentRun 读/写也缺 user scope。
- MockShop order 先从 adapter 读取再检查 caller customer；approver 当前被视为可访问整个租户店铺。售后只存 `user_id`，无法分开 actor/customer。审批没有持久 task/assignee 表，checkpoint thread 的权限不能代表分配关系。
- 迁移提案新增 customers、tenant_users、service_customer_grants、order_customer_ownership、approval_tasks、approval_task_events。未运行 SQL；不回填历史所有权或 approver 分配。
- `orders.customer_id='demo-a'` 对应关系不明确，V1 seed orders 为 NULL；不能映射成 MockShop customer ID。未映射资源默认拒绝。
- 本轮没有代码/schema变动，没有重跑测试。引用上轮已记录基线 105 passed / 17.99s，不将其表述为新权限测试结果。

## Phase 4 deployment finding (2026-11-23)

- The first live verifier failure (`expected 404, got 422`) was caused by the verifier not supplying the newly required `store_id`, not by the API or migrated data. Supplying the caller's mapped store produces the intended isolation check: another tenant/store receives 404; the owning tenant/store receives the event.
- Online backup before migration is safer than copying the active SQLite file because it uses SQLite's backup API and accounts for WAL state. The retained pre-migration snapshot has `integrity_check=ok`, schema version 0; deployed DB has `integrity_check=ok`, version 1.
- Phase 4 runtime acceptance is complete. Keep the backup out of Git and do not downgrade the DB without a reviewed rollback plan.

## Phase 5: migration postcondition check (2026-11-23)

- Container health alone is insufficient evidence that the persistent SQLite schema matches the application version. The WSL update script now opens the configured DB read-only and checks integrity, schema version, and ordered composite primary-key columns before continuing to RAG/API acceptance.
- Full WSL update flow passed against the deployed database, and `bash -n` validated the update script. This verification is read-only; no migration was repeated and no business rows were modified.
