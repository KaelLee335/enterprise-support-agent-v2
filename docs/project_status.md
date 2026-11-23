# 当前状态（2026-11-23）：V2.1 电商集成、RAG 样本外评估与权限模型

## 当前推进阶段（2026-11-23）：Phase 4 SQLite 事件身份与迁移（已完成）

- 用户已于 2026-11-23 接受 Phase 3，阶段关闭。Phase 4 实现、持久库迁移与 WSL 部署已在用户授权后完成。
- Phase 4 实现提交 `d15d6f3` 已推送；全量 pytest **142 passed / 17.52s**，Actions run `45169866834` 成功。持久库迁移前通过 SQLite 在线备份 API 创建 `data/support_agent.db.bak-20261123-200521-pre-phase4`，完整性 `ok`、版本 0；备份保留本地且不提交。
- 最终部署验收：三容器 healthy，`verify_phase6.sh` 与 `verify_v21.sh` 全 PASS。运行库完整性 `ok`、`user_version=1`；webhook event 和 platform order state 的主键包含 platform/tenant/store。首次发现旧 verifier 缺少 `store_id`，修正并重跑后通过。
- 验收脚本与阶段记录已在 `fe1aeb2` 提交并推送；GitHub Actions run `45172043824` 全成功（pytest、Vue build、Compose 配置、Docker build、无 Key smoke）。无需再次迁移数据库。
- Phase 5 已完成：WSL 更新脚本新增 SQLite 只读后置核验（完整性、代码 schema version、tenant/store 复合主键），CI 检查 shell 语法。当前三容器全流程复跑通过，未执行新迁移或写数据库。提交 `20e954e` 的 GitHub Actions run `45180300306` 全成功。详见 [`Phase 5 迁移后置核验`](phase5_migration_verification.md)。
- 最新 OOS-v2 实跑（2026-11-23 13:50 UTC）：15 条全量回答/证据已归档；Hit@4、Macro Recall@4、答案要点、拒答要点和引用来源规则筛查均 100%，机器筛查 Bad Case 0。用户确认旧分诊后，逐案回看发现 HOLDOUT-07 旧答复有矛盾拒答，已加 POL-06 窄规则和筛查回归。WSL 实际部署后健康检查、schema/RAG smoke、Phase 6/V2.1 全通过；认证 `/chat` 实测回答与 POL-06 一致。筛查 100% 不是语义准确率；完整答复见 `data/evaluation/oos/rag_oos_v2_holdout_answers.json`。
- SiliconFlow Chat/Embedding 请求设置 30 秒超时和一次重试，OOS 逐案例显示进度，避免长时间无反馈。
- Phase 3 交付提交 `48cd754` 已推送；用户报告 WSL 三容器 healthy，`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0）。
- GitHub Actions 的 pytest 收集错误已在 `793f259` 修复：新增 `scripts/__init__.py`、`tests/__init__.py`。本机全量 pytest **137 passed / 18.46s**，远端 Actions run `45163773462` 成功。该修复只影响仓库测试导入，不改变容器应用代码。
- SQLite 备份 `data/support_agent.db.bak-20261122` 与当前库均通过只读 integrity check；备份为 Phase 2 迁移前快照，未提交或推送。

- Phase 2 权限模型已按用户报告完成 WSL 迁移和验收；详情见下方阶段记录。
- Phase 3 已为 OOS runner 增加机器可读 Bad Case ledger，并完成 24 条合成探针的 Embedding 距离校准；距离分布重叠，不设统一拒答阈值。
- 本机全量 pytest **130 passed / 17.01s**。2026-11-22 使用既有虚构 OOS-v1 做了真实回归复测；OOS-05 已用于改进，因此结果不是 blind holdout。
- 已新增 RAG 无关证据、冲突证据和证据内指令的离线特征测试；FakeListChatModel 证明直接相反句会在调用模型前安全澄清，并检查例外范围、多阶段规则和无关主题不误报。引用 ID 检查仍不能证明事实正确。
- 真实 Embedding 校准：12/12 可回答目标进入 Top-4，但可回答距离与无答案最近距离大幅重叠，不建议应用全局距离阈值。报告：`data/evaluation/oos/embedding_distance_calibration_v1.md`。校准本身未写入 Chroma/SQLite；随后经用户批准加入了窄范围答复保护。
- OOS-v1 回归复测 15 条：Hit@4、Macro Recall@4、答案规则初筛、拒答初筛、引用标签匹配均 100%，Bad Case 0。真实语义仍需人工复核；OOS-05 一次人工检查发现模型问了政策未规定的“照片或视频”格式。
- 新增定制商品+质量问题+运费的专门检索查询扩展，Top-K 保持 4。用户报告更早的显式冲突版本 WSL smoke 与双 verifier 全 PASS，但明确要求本轮最终部署状态等提交后再同步；查询扩展还未部署。
- OOS-v2 15 题已由用户于 2026-11-23 审核通过并授权真实运行，位于 `data/evaluation/oos/rag_oos_v2_holdout.json`。其中 HOLDOUT-04 针对已知边界，因此不是完全盲测；整套现已成为已观察数据。
- 用户已授权真实运行：Hit@4 100%、Macro Recall@4 93.3%、答案规则初筛 20%、拒答/范围词面初筛 0/6、引用标签匹配 100%；12 个候选 Bad Case（10 GENERATION、2 RETRIEVAL）待人工逐例判定。这些词面筛查率不是语义准确率；详见独立报告和 ledger。
- 用户已确认 `data/evaluation/oos/rag_oos_v2_manual_triage.md` 中逐案分诊并授权继续。经归档的逐案检查新增发现 HOLDOUT-07 漏检，已修复并重跑 OOS-v2；部署等待现有 WSL 验收流程。
- 历史中间状态（已被 2026-11-23 后续结果取代）：当时一次真实 OOS 重跑未完成，报告保留为旧快照。当前结果见本页顶部的最新状态和独立报告。
- 已补 SiliconFlow 请求超时与逐案例进度显示（30 秒、最多 1 次重试）；后续真实 OOS-v2 报告已刷新，见顶部状态。

## 最新阶段（2026-11-22）：Phase 2 权限模型实施

- Customer 订单所有权、Service 客户 grant、Approver 任务分配/自批阻止、Admin 同租户管理边界已实现。
- SQLite Repository 以 tenant + customer/grant/user/task 范围过滤；MockShop 在读取详情前先做 scope 授权；售后记录分开保存 requester、actor、customer。
- 审批任务持久化并通过条件更新防重复；Graph 恢复前按当前身份重验任务分配。
- 全量本机 pytest：**115 passed / 20.29s**，包括临时数据库的旧 schema 追加列、不回填检查及 legacy NULL 售后幂等重试。
- 固定 Demo fixture 有显式 owner 映射；V1 owner 不明的历史订单默认拒绝。没有修改 D 盘/WSL 持久 DB/Chroma。
- 用户报告已备份持久 SQLite 并完成 WSL 实机验收：三容器 healthy，`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0）；2026-11-18 的 `actor_id/customer_id=NULL` 存量行重试返回原申请。Phase 2 闭环，按要求暂停。

## 工程质量审计（2026-11-22）

- 阶段 1 审计报告：[`工程审计报告`](engineering_audit_2026-11-22.md)。审计时基线为 105 passed / 17.99s；不是权限修复后的结果。
- 用户随后批准了 Phase 2 权限模型实施。当前代码与测试结果见本页顶部及 [`Phase 2 权限模型与迁移提案`](phase2_permission_model_and_migration_proposal.md)。
- 审计报告保留为历史快照；其中“等待确认/未改核心代码”的状态已被后续实施取代。

## 工程质量审计（2026-11-22）

- 新需求阶段 1 只读审计完成：[`工程审计报告`](engineering_audit_2026-11-22.md)。本机全量 pytest **105 passed / 17.99s**。
- 用户报告新版 WSL 三容器 healthy，阶段 6/V2.1 verifier 全 PASS；本次审计没有操作容器。
- 核心权限和 SQL 当前只按租户做旧订单/运行记录范围；同租户用户所有权语义尚待确认。MockShop 用户映射测试通过，但读取 adapter 对象后才检查权限。
- OOS-v1 的 15 条在迭代过程中参与过回答/检查规则调优；应按回归集看待，未参与开发的新 holdout 尚未建立。
- GitHub Actions 最新公开 run 29 对 `43adc60` 成功；本地未提交改动不包含在该远端结果中。README 与架构阶段状态存在过期描述。
- 本轮未改核心业务代码/数据、未改数据库或向量库、未提交推送；下一步先由用户确认订单/运行记录的请求人和审批人访问规则。

## 最新进展（2026-11-21）：RAG 样本外评估

- 新增独立 15 条 OOS 集与可单独运行的评估器；原 45 条开发集未修改。完整报告：[`rag_oos_v1_report.md`](../data/evaluation/oos/rag_oos_v1_report.md)。
- 自然度加固后最新真实运行（11:42 UTC）：Hit@4 **100.0%**、Macro Recall@4 **95.6%**、答案规则项 **93.3%**、拒答/范围边界 **100%**、引用标签匹配 **100%**。这些是检查指标，不是语义准确率；检查规则和一项证据标注经修正，前后比例仅作方向参考。
- OOS 报告最近一次真实运行时记录 OOS-05 的 Top-4 证据缺口（RET-01/QUA-01）。当时全量 pytest **105 passed / 15.00s**。用户随后报告新版同步到 WSL：三容器重建且 healthy，`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0），OOS-05 修复在演示页生效。此为部署验收，与独立 OOS 指标分开记录。

- Phase 0 盘点完成；架构与阶段结果见根目录 [`ARCHITECTURE.md`](../ARCHITECTURE.md)。
- 本机实现已包括 MockShop API/Adapter、FastAPI 电商查询与明确确认申请、SQLite 幂等、LangGraph + 绑定身份的 LangChain Tools、HMAC Webhook inbox 与租户状态同步。
- 店铺 A/B 使用不同虚构 tenant、用户、客户映射。测试确认各自可访问自有订单，跨店铺/跨租户访问 404；Webhook tenant 从可信 shop_id 派生。
- Vue 展示平台订单/物流/资格结果，并提供先检查资格、再显式提交 `pending_demo` 的侧栏操作；申请不代表审批或退款。
- 本机全量 pytest **93 passed / 12.26 秒**；Vue production build、Compose 静态配置、Python compileall 和 CI YAML parse 通过。更新后重新评估 Agent route **35/35**、订单参数 **8/8**、工具 outcome **6/6**、业务订单子集 **5/5**；数据库保持不变。详见 [`evaluation_v2_1.md`](evaluation_v2_1.md)。
- API、评估、面试和电商 Integration Layer 学习文档已新增。用户报告提交 `43adc60` 后在 WSL 连续运行两次 `update_wsl_and_verify.sh`，均未重启 mock-shop、且已有 2003 售后记录；两次 phase 6 与 V2.1 验收全 PASS（EXIT=0）。可重跑状态验证通过。
- 边界：全是虚构数据和 MockShop，不接真实平台、真实客户或真实退款；不做生产化。

# 历史项目状态快照（2026-11-17；当前进展见本页顶部）

更新日期：2026-11-17

## 当前阶段：V2.1 本地演示加固（已完成）

- 新增同租户独立 requester/approver 演示身份；requester 自批 403、跨租户审批读取 404、独立 approver 可记录 `approved_demo`。仍是公开 Demo token，不是真实认证。
- 新增 LangGraph 物流查询分支；先按 tenant 从 SQLite 确认订单，再经带演示服务标记的 HTTP client 请求静态 mock 服务。只含虚构单号与轨迹，不访问商业快递 API。
- 新增 `uv.lock`；CI 用 `uv sync --locked` 检查锁文件一致性，Dockerfile 用 `uv sync --frozen` 按锁文件安装，避免构建时受 Aliyun 索引元数据重新解析影响。CI 触发路径已包含政策、seed、前端、脚本和文档，并添加 Vue 构建及 Compose 内物流 API smoke。
- V2.1 初始本机验收：65 项 pytest 通过；Vue build、Compose 静态配置和 Python 编译通过。后续退款路由修复的定向回归通过，审批 UI 改动的 Vue build 通过。
- WSL 部署由用户报告已完成：更新脚本同步 `uv.lock` 与源码到 `/opt/project2`，两容器 healthy，阶段 6 与 V2.1 新增 verifier 用例全部 PASS。此为用户提供的实机结果，本会话没有操作 WSL。
- GitHub Actions run `44077476920`（代码提交 `12aaf4d`）已通过，涵盖 Python 测试、Vue 构建、Compose 配置、Docker 镜像构建和无 Key 容器 smoke。看板校准提交 `d703155` 的 run `44084457126` 也已通过。
- 请求人与审批人分开显示各自历史；待审批任务和决策按钮只在审批人页面显示；申请人只在本方对话看到待审批状态。用户已确认浏览器验收通过。
- `帮我申请订单 1001 退款` 已改为创建 `pending` 审批，而不是进入 `order_lookup`；19 项 router 测试和新增 API 审批回归通过。用户报告同步脚本执行后双容器 healthy、扩展 verifier 全 PASS（EXIT=0）。
- 最新浏览器验收确认请求人/审批人各自显示独立对话，待审批卡与决定按钮只显示在审批人页面。代码提交 `12aaf4d`，后续项目状态记录已推送。
- Dockerfile 使用 `uv sync --frozen` 避免构建时按 Aliyun 源重新解析；CI 使用 `uv sync --locked` 验证锁文件一致性。

## 已完成并验收

- GitHub About、README、项目故事和面试材料已按最新项目定位更新：强调从 Dify 向代码级 Python Agent 工程学习、端到端链路及模拟数据边界。协作模式现按新版提示词为 Codex 技术负责人/主力开发者、用户学习理解者。
- 阶段 0–6：V1 资产盘点、API/SQLite、云端 Embedding 与 Chroma RAG、LangGraph 路由、退款审批中断/恢复、评估与追踪、Docker 部署。
- 用户在 WSL Docker 实测：`/health` 200；订单号查询（含无空格形式）；异常/多订单号澄清；隐私和提示注入拒答；退款审批 `pending`；POL-06 政策回答引用有效；日志无 ERROR。
- 最新扩充版 `scripts/verify_phase6.sh` 已同步至 `the WSL project directory` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0。新增退款两阶段时限、进液保修排除、质量故障退货分流和发票隐私边界均通过。D 盘 `data/` 通过绝对路径 bind mount 持久化。
- 本机 Agent 路由评估：35/35；标注订单参数 8/8；工具调用 9/9；标注 outcome 6/6；订单字段 5/5。历史记录中早期版本 pytest 为 47 项；后续干净克隆公开版本为 53 项通过，两者对应不同代码版本，不合并为同一轮结果。此处为已记录结果，本轮没有重跑测试。
- RAG 召回对照（36 条有证据标签的案例）：Top-2/4/6/8 平均 Recall 分别为 77.3%/86.6%/89.4%/99.1%；完整证据率为 58.3%/72.2%/77.8%/97.2%。报告位于 `data/evaluation/`。
- Top-4/Top-8 对 14 条政策问题的生成与同模型 LLM 评分已执行；答案与来源记录在 `data/evaluation/v2_rag_answers.json`。
- 上述 28 条回答已逐例人工核查；发现 Top-4 的若干条件遗漏，以及 Top-8 的 POL-04 事实冲突。逐条记录在 `docs/rag_answer_manual_review.md`。
- 用户确认继续后已实现本地政策约束层，覆盖 POL-04 进液排除、POL-02 质量故障分流/退货条件、POL-05 退货指引、POL-06 分阶段退款时限、POL-09 发票隐私和未知范围。Top-4/Top-8 14 案例报告：`data/evaluation/v2_rag_answers_constraints_v3.json`；28/28 引用 ID 校验有效，重点回答已逐条核查。

## 当前配置和已知限制

- 阶段 15 可靠性加固已完成。阶段 17 Vue 前端首版完成；用户报告安装、页面和真实 `/api/chat` 链路通过，本机 production build 通过。
- 用户已明确无需生产化，阶段 16 暂停。V2.1 实现、WSL 集成和浏览器验收均已完成；代码与文档已推送至公开 `main`。完整方案见 [`docs/v2_1_demo_reinforcement_plan.md`](v2_1_demo_reinforcement_plan.md)。

- 用户最新 WSL 验收报告：同步 `Dockerfile`、Compose、`main.py`、API 回归测试和 verifier 后，镜像重建、容器重建启动成功，health 200；`verify_phase6.sh` 12/12 PASS，EXIT=0。该项包括此前新增的 auth/clarify/refund/policy 用例。结果来自用户截图，本会话未直接操作 WSL。

- 用户选择保持 `RAG_TOP_K=4`。Top-8 提升证据召回，但基线评估未证明最终回答更好；约束层评估也没有因 Top-8 而切换默认值。
- LLM judge 指标仅作探索性筛查，不能当作答案准确率。引用 ID 有效也不代表回答的事实都被证据支持。
- systemd 的 `docker` unit 未报告 active（enabled 标记存在）。用户已实测 Ubuntu WSL 为 `Stopped` 时触发任务后 `dockerd ready`、容器 healthy、health 200。2026-11-16 本机只读检查发现 `the existing scheduled task` 任务是当前用户的交互式 Logon 触发器，不是 Startup 触发器；因此不能保证用户登录前恢复。没有修改计划任务或虚拟网卡。
- 学习/面试问答按用户要求暂存。

## 暂缓项与明确边界

- 阶段 16 真实生产化按用户要求暂停，不属于当前交付；不接真实身份服务、真实客户数据、商业物流 API、真实退款或生产数据库。
- 真实模型供应商 429/timeout 尚未实测；没有明确演示需求时，不额外发送请求或触发额度消耗。
- 独立语义裁判、成熟事实级 grounding 自动指标、延迟 P50/P95 基线不在当前演示验收范围；保留人工 Bad Case 复核与明确的证据边界。
- 学习互动按用户时间安排；五章材料已完成，不主动开始测验。

## 阶段 7：发布就绪与可复现交接（已完成）

- Dockerfile、Compose、`.gitignore`、`.dockerignore`、`.env.example` 和 README 已按全新克隆场景调整；本地 Git 仓库已初始化。
- 历史阶段 7 验收时，用户核查 `git status` 和忽略规则：7 个密钥/生成路径均被忽略，`.env.example` 保持可跟踪，待跟踪列表为预期项目文件。
- 用户在 WSL 成功重建镜像，容器 `healthy`；`docker inspect` 确认 `the local persistent data directory -> /app/data`；11 个阶段 6 验收用例全部 PASS，EXIT=0。以上是 GitHub 发布前的历史状态；仓库之后已公开发布。

## 阶段 8：GitHub 公开交付（已完成）

- 用户已选择新建公开仓库，建议名称 `enterprise-support-agent-v2`。
- 发布前曾执行待提交清单与凭据扫描；该条为过时历史提示，后续已完成仓库创建和推送。
- 阶段 8 发布完成：[KaelLee335/enterprise-support-agent-v2](https://github.com/KaelLee335/enterprise-support-agent-v2)，公开 `main` 分支。远端文件树 105 项，README、源代码和测试可见；`.env`、数据库/WAL、向量库、虚拟环境、缓存和 egg-info 均未发布。本地 Git 状态已推送并与 `origin/main` 同步。

## 主要记录入口

- 总计划：`task_plan.md`
- 工作日志：`progress.md`
- 实施发现：`findings.md`
- RAG/Agent 指标与限制：`docs/evaluation_and_observability.md`
- RAG 答案逐例审阅：`docs/rag_answer_manual_review.md`
- 建议的 RAG grounding 加固方案：`docs/rag_grounding_hardening_plan.md`
- Docker/WSL 运行说明：`docs/wsl_docker_lifecycle.md`
- 演示步骤：`docs/demo_runbook.md`
- 项目执行约束和接续说明：`AGENTS.md`

## 2026-11-16 执行通道交接恢复记录

- Codex 执行通道故障期间，交接步骤（git 审查 → 认证/租户审查 → 全量测试 → 文档 → WSL 验收）由 WorkBuddy 代执行完成。
- 全量 pytest 51 passed；WSL 侧容器重建后 health 200，verify_phase6.sh 11 用例全 PASS。
- 当前 API 认证为 Demo Bearer token（demo-a-local-token / legacy-demo-local-token），非生产凭据。
## 最新验收与学习手册状态（2026-11-16）

- 用户截图报告本地身份/租户边界审查通过、全量 pytest 51 passed（267 秒），以及 WSL 重建后 health 200、`verify_phase6.sh` 11/11 PASS；本项目状态文件据此记录，本会话没有重跑业务测试。
- WSL 重启后出现 Docker NAT 网段冲突；用户截图称通过备份 daemon 配置、调整 Docker bridge CIDR 和启动等待逻辑修复。主机网络改动以用户报告为准，不在本会话继续更改。
- 用户截图报告 LangChain 源码映射已核对、四章学习材料与索引已推送；本会话读取 GitHub tree 确认 `docs/learning/` 有 README 与 LangChain、LangGraph、RAG、SQL、FastAPI 五章。
- README、状态、需求追踪、计划、代理说明、进度和发现文档已随公开仓库更新；本轮只改文档，没有变更业务代码或运行测试。
- 阶段 13 干净克隆复现已完成（用户报告）；阶段 14 最终材料一致性核查已完成。


## Clean clone 与 pip 镜像记录（2026-11-16）

- 用户报告 D 盘干净克隆后同步到最新 main，pytest 53 passed / 18.39s / exit 0；这是用户提供的结果，本会话未复跑。
- 用户遇到全局 TUNA pip simple 返回 403（pip User-Agent 请求），临时加阿里云 `-i https://mirrors.aliyun.com/pypi/simple` 后安装成功。README 已加入单次安装的镜像 fallback。
- Dockerfile 的 TUNA 源风险记录为下次 Dockerfile 调整事项；本轮未改 Dockerfile，也未触碰 WSL/Docker。
- 用户随后报告该 clean clone 的 health 返回 {"status":"ok"}，带 Bearer 的 GET /orders/1001 返回 200 且租户/虚构数据正确，无 token 返回 401。至此首次启动链路已由用户验收；health 200、带 Bearer 的订单查询 200、无 token 401 均来自用户截图。本会话没有自行运行本地进程。阶段 14 文档一致性复核已完成。

## 当前推进

图中列出的 V2.1 演示改进与用户验收均已完成。下一步若继续项目工作，应进入用户安排的 LangChain/LangGraph 学习复盘，或另行确定新的 Demo 改进目标；不把暂停的生产化事项自动纳入当前范围。
