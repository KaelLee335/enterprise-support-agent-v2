# 项目推进计划

## 2026-11-22：Phase 3 Bad Case 闭环

### 2026-11-23 后续回归完成

- [x] 用户复核通过后完成政策边界修复、必要证据标签收窄、检查器同义项优化与请求超时/进度机制。
- [x] 全量 pytest **137 passed / 18.14s**；真实 OOS-v2 回归指标 Hit@4 100%、Macro Recall@4 100%、答案/拒答/引用规则筛查均 100%，Bad Case 0。
- [x] 本地交付提交经 amend 为 `48cd754` 并推送；用户报告 WSL 三容器 healthy，`verify_phase6` 和 `verify_v21` 全 PASS（EXIT=0）。
- [x] 排查 GitHub Actions 红叉：确认是 pytest collection 导入 `scripts`/`tests` 失败，与 API Key 无关；补充 package markers，本机全量 pytest **137 passed / 18.46s**。
- [x] CI 导入修复提交 `793f259` 已推送；GitHub Actions run `45163773462` 成功。
- [x] 只读检查 SQLite 备份和当前库：两者完整性均 `ok`；备份为迁移前结构且未纳入 Git。

### 本机实施与验收

- [x] 保留 Phase 2 实机验收结论；按用户新指示继续后续阶段，不再在每个普通阶段完成后停下来等待。
- [x] OOS runner 增加机器可读 Bad Case ledger：记录案例、期望/实际回答、证据、自动筛查类别与原因，并预留人工根因复核和修复回归字段。
- [x] 明确允许的人工根因类别 DATA/CHUNK/RETRIEVAL/GENERATION/BUSINESS/ABSTENTION；自动筛查不冒充人工定因。
- [x] Mock 评估器单测 5 passed；全量 pytest **117 passed / 20.70s**。没有运行真实 OOS、调用模型、修改政策数据、数据库或容器。
- [x] 初始新增离线特征测试：无关证据合法引用、互相冲突的政策内容、证据内指令样式文本。初始假模型用例只记录当时结构缺口，不视为安全通过；后续经确认补上窄范围直接冲突保护。
- [x] 更新 README/ARCHITECTURE 的过期状态、权限模型和已报告的 WSL 验收；未提交或推送。
- [x] 经用户批准，以已配置的 SiliconFlow Embedding 对 12 份虚构政策和 24 条合成相关/无关探针计算距离；未调用聊天模型、未修改索引/数据库/业务行为；报告见 `data/evaluation/oos/embedding_distance_calibration_v1.md`。
- [x] 校准观察：12/12 可回答探针目标政策进入 Top-4；可回答目标距离 0.6516–1.1380，无答案最近距离 0.9072–1.1817，区间明显重叠，不能安全设定统一距离阈值。
- [x] 用户批准仅处理明确冲突：相同命题在检索证据中一处明确肯定、一处明确否定时，生成前停止并给出带引用的人工核验答复；不引入全局距离阈值。
- [x] 增加冲突短路测试、范围例外/不同退款阶段/无关主题不误报测试、无理由词组识别测试；全量 pytest **126 passed / 20.28s**。
- [x] 更新 WSL 同步脚本，包含新的冲突识别模块、答案约束和答案入口，并在容器内验证直接矛盾短路及范围例外不误报。
- [x] 用户报告较早的“直接冲突/范围例外”版本已在 WSL 通过新增容器 smoke 与 phase6/V2.1 verifier（EXIT=0）。此证据不覆盖本轮新增的复合查询扩展。
- [x] 当前本机查询扩展回归 OOS-v1：Hit@4 15/15、Macro Recall@4 100%；答案规则初筛、拒答边界、引用标签匹配均 15/15。OOS-05 已参与调优，结果仅作回归，不是盲测。
- [x] 用户审核通过 OOS-v2 的 15 个问题、预期行为和证据编号；扩展独立 runner 的 `--dataset` 参数，报告与 Bad Case ledger 按数据集分开输出。HOLDOUT-04 专门测试已观察到的凭证格式边界，因此不宣称整套是完全盲测。
- [x] 用户另行授权向 SiliconFlow/Qwen 发送 OOS-v2 问题、检索证据及答复；真实运行完成，报告和 ledger 分别写入 `rag_oos_v2_holdout_report.md` 与 `rag_oos_v2_holdout_bad_cases.json`。
- [ ] 等用户之后复核 Codex 对 12 个候选 Bad Case 的初步分诊，再确认真实失败、检查器误报及证据标注范围；复核前不据词面筛查指标调整 Prompt/约束层。
- [x] Codex 已完成逐案初步分诊，标注 3 个明确生成问题候选、2 个无依据细节候选、4 个检查器误报、2 个证据标注争议和 1 个回答不完整候选；详见 `rag_oos_v2_manual_triage.md`。根因 ledger 保持待用户复核。
- [x] 用户复核通过后，修复拆修保修、凭证格式、发票金额、缺货、未寄回退款计时和付款次日发货推测；扩充等价短语检查。全量 pytest **137 passed / 18.09s**。
- [ ] 更新后的真实 OOS-v2 回归未能完成；报告顶部标明仍是更早的成功快照，不能视为当前代码/修订标签的最新指标。重跑需要排查 SiliconFlow 请求挂起。
- [ ] 本轮代码尚未提交或部署。按用户说明保持 WSL 部署状态不变；提交后由用户同步，再报告新版本实机验收。


## 2026-11-22：Phase 2 业务权限模型

### 实施与验收（已完成；按用户要求暂停）

- [x] 只读检查 User/Tenant/Order/After-sale/Approval/AgentRun/Webhook、FastAPI、Repository、MockShop 与 LangGraph checkpoint。
- [x] 输出当前角色关系、越权面、代码入口和分层测试矩阵：`docs/phase2_permission_model_and_migration_proposal.md`。
- [x] 用户批准迁移提案；新增 schema 只在 pytest 临时库验证，未触碰现有 D 盘/WSL 业务库。
- [x] 实现 Customer owner、Service grants、Approver task assignment、自批阻止、Admin tenant 边界及 MockShop 先授权后读取。
- [x] 新增/修订权限回归；全量 pytest **115 passed / 20.29s**，保留测试，只窄修订过时权限期望。
- [x] 更新 README、演示手册、阶段状态、迁移与审计说明。
- [x] 用户报告已备份并迁移持久 SQLite；三个容器 healthy，`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0）。真实存量 NULL 审计字段重试返回同一申请。
- [x] Phase 2 实机验收闭环；按用户要求结束并暂停，不自动进入下一阶段。

### 当前暂停边界

- 新版启动会为现有 DB 增量建表并仅在缺列时新增售后审计字段；本会话未操作持久 SQLite/Chroma。用户已报告在 WSL 备份并迁移成功。
- 本次不启动 Compose、不更改 WSL、不提交或推送。
- Phase 2 验收后暂停，等待用户明确确认，不自动进入其他阶段。

## 2026-11-22：工程质量与开源竞争力优化（阶段 1 历史记录；后续 Phase 2 已获批准并完成本地实现）

### 阶段 1：工程审计（已完成；核心业务代码未修改）

- [x] 盘点当前工作区变更，区分上一轮 OOS 改进与本轮审计产物；不覆盖未提交内容。
- [x] 按实际代码核对 API、租户与订单权限、RAG 检索/引用/拒答、LangGraph 状态/路由/审批恢复、评估数据与指标、测试、Compose、CI、README。
- [x] 对每项标记：已实现且有测试、部分实现或风险，并列出源码与测试证据。
- [x] 运行当前全量 pytest：**105 passed / 17.99s**；未触碰数据库、Chroma 或容器。
- [x] 新建 `docs/engineering_audit_2026-11-22.md`，含架构图、核验矩阵、风险优先级与预计修改文件。
- [x] 同步更新本计划、`findings.md`、`progress.md`、`AGENTS.md` 与 `docs/project_status.md`。
- [x] 先汇报审计；核心权限/schema/RAG 业务修复待用户确认，不自动进入修改。

### 审计后续建议（原计划，已由下方 Phase 2 实施记录取代）

1. P0 核心可靠性：先由用户确认请求人/审批人访问语义和订单 owner schema，再改权限隔离；随后提交 RAG 无关证据/冲突/注入测试与最小拒答方案供确认。
2. P1 OOS：把现有 15 条作为开发回归集；定义并由用户审核新的 blind holdout，再补 Macro/Micro 与答案人工标注指标。
3. P2 Bad Case 闭环：统一归因类别、证据、根因复核、修复和回归。
4. P3 工程与部署：评估 schema migration、CI、Compose、日志追踪和本地性能基准；不从 Windows checkout 启动 Compose。
5. GitHub 展示：核心审计与指标口径确认后更新 README/架构图/复现方式/限制；不自动提交或推送。

### 阶段 1 当时边界（历史记录）

- 本轮只读检查核心实现；可新增审计/计划文档，不改核心权限、SQL、RAG、Graph 或业务规则。
- 不删除/覆盖数据库和 Chroma，不改 Git 历史，不提交或推送。
- 现有 OOS 改进有未提交工作区变更；保持原样，核对后仅在审计中记录。

## 2026-11-18：V2.1 电商集成扩展（当前任务）

> 新需求按增量项目处理：保留现有 V2 售后 Agent、模拟物流服务、Demo 身份、SQLite、LangGraph 和前端；新增一条 MockShop Adapter 集成链。所有店铺、订单、用户和物流事件均为虚构数据。本轮不能标记真实平台接入。

### Phase 0：现状盘点（已完成）

- [x] 检查仓库结构、API、Agent/Graph、数据库、身份、测试、Docker/Compose 和 README。
- [x] 跑基线测试并记录环境限制。
- [x] 输出复用项、新增项、顺序、风险和最小交付边界（见 `ARCHITECTURE.md`）。

基线：项目虚拟环境 `pytest` 为 **71 passed**；pytest cache 写入受 ACL 阻止产生 1 条 warning。`uv run` 不能初始化全局 uv cache（拒绝访问），改用 `.venv` Python 并指定新的项目内 basetemp 后成功。原 `.pytest-tmp` / `.pytest_cache` 保持未触碰。

### 增量架构结论

- **复用**：FastAPI 生命周期/请求追踪、Bearer DemoIdentity 的 user/tenant、SQLite `orders`、确定性 LangGraph 路由、现有 RAG 政策问答、已有物流 typed HTTP client、Pydantic、pytest、Compose/CI。
- **扩展**：订单数据模型补充店铺与平台标识（保持 V1 字段及规则）；权限服务按身份 scope 做 order/store 校验；Graph State/节点增加售后查询与申请流程；日志记录工具/平台调用的安全元数据；前端展示订单/物流/售后处理步骤。
- **新增**：`integrations/` 统一领域模型、协议、registry 与 MockShop Adapter/HTTP client；独立 Mock 电商 API；售后资格与申请的模拟服务及 SQLite 持久层；签名验证、webhook inbox 幂等记录与订单状态更新；扩展评估与 API/Adapter/Agent/Webhook 权限回归。

### 实施顺序

1. Mock 电商 API 与统一领域 Schema/基础 Adapter（本机代码与单元测试已完成；Compose/API 集成待做）。
2. Adapter/registry 及平台异常、状态映射；订单查询改为经 Adapter，逐步移除 Agent 对平台原始结构的依赖（当前进行中）。
3. 售后资格规则和模拟申请持久化；新增 LangGraph 分支与明确确认/权限检查，不触及真实退款。
4. Agent 对外暴露安全的售后工具/服务接口，补参数校验、租户/店铺权限、日志和异常映射。
5. Webhook 签名校验、SQLite 事件 inbox、event_id 幂等、状态映射与安全重试结果。
6. 扩充测试/评估，前端最小流程展示，更新 README、ARCHITECTURE/API/EVALUATION/INTERVIEW 文档。
7. Docker Compose 与 CI/WSL 验收；先做静态和离线检查，再按已确立的 WSL 部署流程提醒用户执行真实容器更新。

### 最小可交付版本（MVP）

一个 MockShop、固定虚构店铺/客户/订单，支持租户和用户范围的订单/物流查询、政策 RAG、售后资格检查；满足条件后仅创建 `pending_demo` 模拟售后申请并返回申请 ID，不宣称退款完成；Webhook 只处理签名正确且 event_id 未重复的模拟订单/售后事件。至少有 API/Adapter/Agent/Webhook/权限/幂等测试、Compose 启动说明和真实运行证据。真实平台、真实客户、真实退款、Redis/Kafka/微服务集群均不在范围。

### 当前风险/错误记录

| 项 | 证据/影响 | 处理 |
|---|---|---|
| uv cache 权限 | `uv run --locked pytest` 在启动前失败，D:\\caches\\uv 拒绝访问 | 继续使用项目 `.venv`，必要时指定项目内新 basetemp；不改 ACL |
| pytest 缓存 ACL | 基线为 71 passed，但 cache provider 写入 `.pytest_cache` 被拒，1 条 warning | 验收可加 `-p no:cacheprovider`；不删除或更改既有目录权限 |
| 现有订单数据缺少店铺/平台键 | V2 按 tenant_id 隔离，暂不能表达多店铺及平台原始订单状态 | 用向前兼容 schema 增量列/新表与显式 demo 映射，保留旧查询行为 |
| V2 写操作边界 | 当前只有退款人工演示审批，不做实际写回 | 新售后申请独立标为 demo request，增加确认和权限；不得改订单为“已退款” |
| Compose 运行副本 | WSL `/opt/project2` 已占 8000，Windows checkout Compose 会冲突 | Codex 不对 Windows checkout 执行 `compose up`；Docker 集成部署留到用户 WSL 流程 |

### 实施状态（2026-11-18）

- [x] Phase 0 现状盘点：基线 71 passed；确认此前没有平台 Adapter、售后资格接口、售后申请 API 或 Webhook。
- [x] Phase 1 Mock API 与领域契约：本机完成。独立 FastAPI 模块有固定虚构订单、物流、资格/申请/状态 API；API 与 Adapter 测试通过；Compose source 已配置服务。
- [x] Phase 2 Adapter 基础：业务协议、registry、typed client、字段/状态映射、HTTP/timeout/JSON 错误归一、Demo identity→store/customer 授权已完成；完整 Agent/Compose runtime 联调继续进行。
- [x] Phase 3 REST/SQLite 售后骨架：FastAPI 增加平台订单、物流、资格、申请、申请状态 endpoint；主 SQLite 保存幂等申请状态；写操作需 requester + 显式 confirmed；同一请求重试返回同一记录。
- [x] Phase 3/4 Graph Agent 首版：可识别显式“平台订单”提问，调用绑定当前 DemoIdentity 的 LangChain StructuredTools 查订单/物流/资格；售后路径复用现有 RAG 后补资格检查说明；Agent 不会代替用户确认提交。
- [x] Phase 4 UI 与申请状态展示：平台订单/物流/资格卡片，店铺 A/B 身份切换，先资格检查再明确确认创建演示申请。
- [x] Phase 5 Webhook：raw-body HMAC、schema、SQLite event inbox、event_id 幂等、冲突/过期事件处理及 tenant-scoped 状态查询。
- [x] Phase 6 本机测试/评估/文档：全量 93 passed，Vue production build 通过；新增 API、评估、面试文档。
- [x] Phase 7 CI/Compose/WSL 运行验收：用户报告提交 `43adc60` 后，未重启 mock-shop 连续两次执行 WSL 同步/验收；三容器 healthy，phase 6 与 V2.1 全部 PASS（EXIT=0）。

> 记忆更新：2026-11-16，采用用户最新的《Python Full-stack Agent Engineering — Autonomous Development & Interview Preparation》提示词。阶段 0–10 已结束；旧的“用户先设计、Codex 等待批准”流程已被新分工取代。Codex 自主负责技术方案与主力实现，用户通过代码讲解和学习材料理解项目。

## 总路线图

| 阶段 | 目标 | 状态 |
|---|---|---|
| 0 | 盘点 V1/V2 资产、依赖和运行环境 | 已完成 |
| 1 | FastAPI、SQLite、租户范围订单查询和结构化日志 | 已完成 |
| 2 | 云端 Embedding、政策索引、RAG 检索与基础评估 | 已完成 |
| 3 | LangGraph 单 Agent 路由及 `/chat` 接入 | 已完成 |
| 4 | SQLite checkpoint 与退款人工审批演示（不执行真实退款） | 已完成 |
| 5 | 评估、追踪、Bad Case 修复、检索/回答比较和政策约束层 | 已完成 |
| 6 | WSL Docker 运行验收与安全边界验证 | 已完成 |
| 7 | 新环境部署文档、忽略规则和数据目录持久化 | 已完成 |
| 8 | GitHub 公开发布与文件清单复核 | 已完成 |
| 9 | WSL Docker 用户登录触发配置只读审查；用户确认保留现状 | 已完成 |
| 10 | 将原始要求拆成可追踪清单，对照代码、测试、文档和实测证据做差距盘点 | 已完成；见 `docs/requirement_traceability.md` |
| 11 | 按 LangChain → LangGraph → RAG → SQL → FastAPI 次序完善代码绑定的中文学习手册 | 已完成；五章均已推送到 docs/learning/ |
| 12 | 补齐 P0 演示能力与受控故障注入 | 已完成（用户报告 2 条新增回归通过；部分故障边界继续透明标注未验证） |
| 13 | 从公开仓库干净克隆，复现 README 首次运行流程 | 已完成（用户报告依赖安装、53 项 pytest、health 200、订单 1001 为 200、无 token 为 401） |
| 14 | 校验架构/流程/SQL/权限/RAG/评估图文、演示记录和面试材料均与真实实现一致 | 已完成（阶段 13 首次启动证据和故障测试状态已对齐） |
| 15 | 主链路后的可靠性加固：自动测试、checkpoint 保护、Compose、容器及故障边界 | 已完成：CI 55 项、WSL 12/12（用户报告）、本机四条离线回归 4/4；Compose 缺 `.env` 与错误 bind 路径均完成隔离验收 |
| 16 | 可选真实生产化 | 当前用户明确选择“不做生产化”，本阶段暂停；不得接真实 IdP/云服务/商业物流或真实客户数据 |
| 17 | Vue 本地演示前端 | 首版完成：用户报告实机真实 API 链路成功，本机 Vite 构建通过 |
| 18 | V2.1 Demo 工程加固 | 本地四阶段和 WSL 两容器集成验收均完成（WSL 验收由用户报告） |

### 路线图边界

- 每个阶段推进一个可验收的小主题；Codex 作为技术负责人自主选取简单可维护方案，完成实现、测试和文档，再进入下一阶段。
- 进入每个学习主题前，Codex 先介绍模块在系统中的位置和当前代码，再边开发边写中文学习材料；用户无需先设计架构或编写核心代码。
- 阶段 10 只做需求追踪与差距盘点；不得把文档上写的要求自动算作实现完成，状态必须链接到代码、测试、评估或用户实测证据。
- 任何需要新增云端调用、暴露/复制 API Key、执行长时间安装构建、或改变 WSL Docker 运行状态的步骤，应在到达依赖点时说明并等待用户操作/确认。
- 按新版优先级先完成 P0；不为 P1/P2 延误交付，不引入多 Agent、Redis、PostgreSQL、Kubernetes、真实客户数据或真实退款。

## 目标

按用户给出的 Enterprise Support Agent V2 说明，小步完成本地可运行、可演示、可测试、可评估和可复现部署的项目；复用并保持 V1 业务规则一致，不覆盖 V1。

## 阶段

- [x] 阶段 0：盘点当前 V2、V1 资产、依赖和环境；给出迁移方案及最小结构。
- [x] 阶段 1：FastAPI、SQLite、日志、租户隔离和订单 API 已在项目虚拟环境通过测试及本地 HTTP 验收。
- [x] 阶段 2：真实向量索引、36 条有标注用例 Recall@4、SiliconFlow Qwen RAG CLI 回答链和来源引用检查已完成。
- [x] 阶段 3：经用户确认单轮 State 方案后，已实现 LangGraph 单 Agent 路由并接入 FastAPI `POST /chat`。
- [x] 阶段 4：SQLite checkpoint、租户范围审批状态、LangGraph interrupt/resume 演示完成；批准不产生业务写入。
- [x] 阶段 5：复用 V1 评估集建立 RAG/Agent 路由、工具参数/结果指标；加入 JSON 追踪、故障注入及 Bad Case 修复前后对照；完成 Top-2/4/6/8 检索对照、14 条 Top-4/Top-8 生成对照、逐例人工复核及本机政策约束层评估。
- [x] 阶段 6：用户确认最新路由加固在 WSL Docker 中通过；health、订单/无空格路由、异常/隐私/提示注入拒答、退款审批、POL-06 RAG、D 盘挂载及节点日志均已验收。
- [x] 阶段 7：发布就绪与可复现交接：修复全新克隆缺少未跟踪向量库时的 Docker 构建依赖；参数化数据目录且保留此设备默认路径；补全 Git/Docker 忽略项；更新首次部署文档并在 WSL 构建验证。
- [x] 部署收尾只读诊断：`systemctl is-active` 为空、`is-enabled` 为 `enabled`，systemd active 未证实。用户随后实测 Ubuntu WSL 为 Stopped 时触发 `Start-ScheduledTask`，`dockerd` ready、项目容器 healthy、health 200；计划任务恢复路径已验证，Windows 完整重启触发仍未验证，主机级配置未改动。
- [x] 阶段 6 验收脚本已在 WSL `the WSL project directory` 运行，全部检查通过，EXIT=0。

## 当前剩余工作

### 独立 RAG 样本外评估（2026-11-21）

- [x] 检查原 45 条 RAG 案例、现有检索评估、Chroma Retriever/Top-K 配置及已有 Bad Case 记录；不改原开发集和业务链路。
- [x] 新建 15 条 OOS 案例，覆盖口语表达、同义表达、组合条件、多意图、无答案/范围边界和模糊澄清；每题带预期、证据来源、预期行为、分类和人工可审的规则项。
- [x] 新增独立模块 `tests.oos`，复用现有 Chroma、Embedding、Qwen、Prompt 与约束层，默认 Top-K=4；命令为 `python -m tests.oos.run_oos`。
- [x] 首次生成 OOS 报告并保留基线 `rag_oos_v1_report_before_style.md`；定位机械话术、约束编号伪引用、运费边界过度补充与无关追问。
- [x] 加固回答 Prompt/政策约束；模糊退货资格先澄清；运费、退款、发货和超范围问题改为与问题相关的短答。Top-K 与业务 API 不变。
- [x] 最新真实 OOS 报告（2026-11-21 11:42 UTC）：Hit@4 100.0%、Macro Recall@4 95.6%、答案规则项 93.3%、拒答/范围边界 100%、引用标签匹配 100%；剩余 OOS-05 为 Top-4 未召回 RET-01/QUA-01。部分检查规则和一项证据标注有修正，前后比例不是严格同口径准确率。
- [x] 全量 pytest 105 passed / 15.00s；真实 OOS 复跑成功；发货时效约束合并文本并明确回应“明天能否到”。
- [x] 用户报告新版 WSL 三容器 healthy，`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0）；演示页已验证 OOS-05 修复生效。部署验收单独记录，不改写独立 OOS 评测快照。
- [ ] 用户审阅 OOS-05 的证据缺口，确认是否进一步改善召回；不自动提升 Top-K。

### V2.1 Demo 工程加固（本轮只做模拟，不做生产化）

- [x] 建立 `docs/v2_1_demo_reinforcement_plan.md`：范围限定虚构客户/订单、本地模拟身份和本地模拟物流 API；明确不接真实身份服务、商业物流 API、生产数据库或真实退款。
- [x] 阶段 1：README/材料与代码、测试证据对齐；CI 覆盖 `data/seed/`、`data/policies/`、`frontend/`、`scripts/`、`docs/`；添加 `uv.lock`，CI 用 `--locked` 校验，Dockerfile 用 `--frozen` 按锁安装；记录路由修复前后 30/35 → 35/35 的 Bad Case 证据。
- [x] 阶段 2：固定模拟 requester/approver persona，只有 approver 可决策；同租户自批 403、跨租户 404、重复决策 409，订单不变回归通过。
- [x] 阶段 3：LangGraph 物流意图 → typed HTTP client → 本地模拟 HTTP API；覆盖服务标记、JSON 校验、超时/服务错误和 Mock transport。容器间 HTTP 烟雾验收已由用户在 WSL 报告通过。
- [x] 阶段 4：Vue 演示、README/演示手册/项目故事/面试和学习材料已同步；生产迁移仅作为文档边界，不搭生产基础设施。
- [x] WSL 集成验收：用户报告 `update_wsl_and_verify.sh` 已同步并重建 `/opt/project2`；两容器 healthy，扩展 `scripts/verify_phase6.sh` 中阶段 6 与 V2.1 新增用例全部 PASS。此项是用户提供的运行结果，本会话未操作 WSL。
- [x] 前端角色切换修复：requester/approver 分离对话历史，审批任务单独跨角色保留，决定结果同步回请求人会话；Vue production build 通过。
- [x] 自然退款申请表达修复：`帮我申请订单 1001 退款` 等说法创建 `pending` 审批，而不是进入只读订单查询；审批人空状态新增引导。定向测试与前端构建通过。
- [x] WSL 集成回归：用户报告已运行 `bash /mnt/d/project_2/scripts/update_wsl_and_verify.sh`；后端路由及更新验收脚本已同步至 `/opt/project2`，双容器 healthy，扩展 verifier 全 PASS（EXIT=0），截图中的申请表达已正确生效。
- [x] 审批任务 UI 可见范围：任务卡和决定按钮限定为审批人页面；请求人仅保留自己的待审批答复。Vue production build 通过。
- [x] 用户浏览器验收：请求人/审批人页面隔离及审批卡仅审批人可见，用户确认通过。
- [x] 发布后图示建议复核：V2.1 交付一致性、模拟身份/审批人、本地物流 API、演示迁移说明均已完成；项目看板中的旧阶段状态已校准。
- **验收边界：**所有身份、物流和客户信息均为虚构；不触发真实外部 API，不把公开 Demo token 描述为认证；保留 `RAG_TOP_K=4` 和只读订单/演示审批边界。

- [x] 阶段 7.1：文档、忽略规则和 Docker 构建输入审查；用户 WSL build 成功证实 Compose 可解析。
- [x] 阶段 7.2：本地 Git 仓库文件清单和敏感/生成路径忽略规则由用户在 WSL 核查；`.env.example` 可跟踪，密钥与运行数据排除在公开提交之外。
- [x] 阶段 7.3：用户在 WSL `the WSL project directory` 同步发布就绪改动、重建并运行 11 项阶段 6 验收，数据挂载正确。

- [x] 逐例审查 Top-4/Top-8 生成答案；`docs/rag_answer_manual_review.md` 已记录全部 14 组。
- [x] 政策约束层 v1 已实现并完成 14 案例 Top-4/Top-8 评估；28/28 引用 ID 校验有效，重点 Bad Case 输出已人工审阅。
- [x] 用户在 `inbox` WSL 会话同步修正后的 `verify_phase6.sh` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0；退款两阶段时限用例已通过。
- [x] 最终交付文档收尾：README、RAG 人工评审、Evaluation、项目状态和接续说明均与 WSL 最新部署/验收结果对齐；历史记录保留并明确标注为已被后续结果取代。
- [x] 阶段 10：完成需求追踪矩阵，逐条标为已实现、部分实现、未实现、未验证或不适用，并附证据位置与建议优先级；未运行测试。
- [x] 阶段 11：完成 LangChain、LangGraph、RAG、SQL、FastAPI 五章代码绑定中文手册，位于 docs/learning/；GitHub tree 已确认五章存在。
- [x] 阶段 12：本地 Demo 身份、租户权限、最小运行记录和 12 项故障库完成；用户报告全量 51 项和 WSL 11/11 通过，并报告新增 not_found 与 fake timeout 两条定向测试 2/2 通过。checkpoint 随机损坏文件已在阶段 15 隔离测试中验证为 fail-fast 且原文件不变；真实供应商 429/超时仍待验证；空 Key 配置已在隔离容器中验证安全降级。
- [x] 阶段 13：用户报告 D 盘全新 clone、venv/pip 安装、53 项 pytest 通过（18.39s）；API health 200、Bearer 订单 1001 查询 200、无 token 401。此次无 .env、无 API Key、无 WSL/Docker。
- [x] 阶段 14：已核对 README、项目故事、面试包、演示手册、需求追踪、故障库和项目状态；按用户报告更新 53 项测试及 clean clone API smoke，并保留未验证边界。WSL/Docker 主机记录采用不含机器路径和网络参数的概括描述。
- [x] 阶段 15 离线加固第一轮：GitHub Actions 55 项通过；临时 checkpoint 损坏 fail-fast/保留文件测试通过；Compose 模板检查、阿里云源 Docker 镜像构建、空 Key 容器的 health/order/RAG safe fallback smoke 全通过。无 Key 和演示数据仅用于 CI 临时环境。
- [x] 阶段 15 四条本机离线回归复核：使用项目虚拟环境和项目内 pytest 临时目录，4/4 通过（3.35 秒）；没有调用模型或操作 WSL/Docker。
- [x] 阶段 15 Compose 隔离配置检查：缺少 `.env` 时 `docker compose config` 返回非零并指出文件不存在；不存在的数据路径在配置解析阶段不会被创建。
- [x] 阶段 15 bind mount 防误建：将短语法改为长语法并设置 `bind.create_host_path: false`；Compose v2.39.1 的临时配置解析通过，目标仍为 `/app/data`。
- [x] 阶段 17 Vue 前端首版：用户报告安装和真实 `/api/chat` 演示成功；本机会话 Vite production build 通过。
- [x] 阶段 15 Compose 错误挂载运行态验收：临时项目使用唯一名称、BusyBox 本地镜像、无端口和 `network_mode: none`；不存在的 bind source 导致服务启动失败，错误明确报告 `bind source path does not exist`，宿主目录未创建；临时 Compose 资源已清理，原项目容器仍 healthy。
- [ ] 阶段 16 真实生产化：按用户最新指示暂停，不纳入 V2.1 执行。

## 本轮范围

阶段 0–15 与阶段 17 首版已完成。阶段 16 真实生产化依用户指示暂停；当前只执行阶段 18 的 V2.1 本地模拟改进，不接真实外部服务、不使用真实客户数据。

## 阶段 8：GitHub 公开交付（已完成；下方为历史记录）

- [x] 用户选择新建公开仓库。
- [x] 发布前最终密钥/运行数据检查并审阅首次提交文件清单。
- [x] 完成公开前忽略规则、文件清单、令牌格式和 `.env.example` 检查；创建本地初始提交 `e68a1cea3bc6f31cb7704c709f6273aae900ee04`，作者使用 GitHub noreply 地址。
- [x] 在 GitHub 创建空白公开仓库 `https://github.com/KaelLee335/enterprise-support-agent-v2`，未初始化额外文件。
- [x] 添加 origin、推送 `main` 并核对远端仓库可见性、文件树和 README/source/tests 内容。
- [x] 验证远端默认分支、README/source/tests 展示并提供仓库链接。

## 阶段 9：Docker 启动可靠性只读检查（已完成）

- 用户确认当前 Windows 用户登录触发符合预期，保持现状，不变更启动任务。
- 用户报告从 WSL 停止状态触发启动后，Docker 容器恢复健康；完整 Windows 重启后的自动恢复仍未验证。
- 本项目不因阶段推进而重启 WSL、停止 daemon、启动第二个 daemon、修改 systemd 或调整网络。

## 阶段 10：原始需求追踪与差距盘点（已完成）

### 目标

将附件中的核心要求逐项映射到当前仓库，区分实现与证据，找出真正缺口并形成用户可审阅的优先级建议。本阶段只读，不改业务代码、不执行测试，也不开始面试问答。结果见 `docs/requirement_traceability.md`。

### 执行步骤

1. 拆解附件中项目定位、固定业务事实、安全边界、技术能力、评估项、故障注入、交付物、用户/Codex 分工和工作纪律。
2. 对照现有 `src/`、`tests/`、`scripts/`、`docs/`、README 和已记录 WSL 验收，分别收集代码证据、测试证据、评估结果和运行证据。
3. 明确检查真实但未必已覆盖的要求：固定订单 1001 的 RET-01/QUA-01 事实一致性、后端强制租户边界、缺失用户认证的演示限制、故障注入清单覆盖度、架构图/演示记录/面试材料与实际代码的一致性。
4. 为每条写状态、证据位置、用户影响、风险和建议（保留/补文档/补验证/改代码）；未知项标为未验证，不推测通过。
5. 产出 `docs/requirement_traceability.md`，列出建议下一步任务；同步总计划、状态和工作日志。
6. 阶段验收：主要要求按域和故障案例逐项记录状态及证据；区分 Demo 租户隔离与生产身份认证；没有把未实现能力描述成已实现；没有改业务代码、运行测试或发起新云端调用。

### 需要用户参与的方式

- 对核心设计冲突或存在多个合理路线时，先准备现状、候选方案、影响和建议，再请用户决定；不把用户变成重复敲代码的人。
- 每个主题开始前由 Codex 介绍其系统位置、现有代码和技术取舍，再结合实现提供学习材料；用户通过讲解和运行结果理解，不需要先给架构方案。默认顺序为 LangChain、LangGraph、RAG、SQL、FastAPI。
- 不请求用户粘贴任何 Key；涉及云端调用时先确认数据范围和服务商。

### 不在本阶段范围

- 不更改 `RAG_TOP_K=4`，不新增云端调用，不触碰真实用户数据。
- 不改现有 `the existing scheduled task` 登录触发配置。
- 不实现生产化身份认证、真实退款、审批 RBAC 或多实例部署。

## 阶段 11：LangChain → LangGraph → RAG → SQL → FastAPI 学习手册（已完成）

### 当前系统介绍

V2 中 LangChain 负责拼接政策回答链：`PromptTemplate → Chat Model → StrOutputParser`；同一 RAG 路径还使用 Document/Splitter、Embeddings、Chroma Vector Store 和 Retriever。LangGraph 负责更外层的业务状态与流程分支。当前订单处理走确定性 Python/LangGraph 节点，没有注册 LangChain `@tool`、没有 `bind_tools`，权限不由模型选择工具决定。

### 本阶段目标

- 由 Codex 根据实际源代码解释 LangChain 组件的职责、输入/输出和与 LangGraph 的边界。
- 在 `docs/learning/` 产出中文学习文档，覆盖项目代码位置、Mermaid 数据流、可运行示例、必须理解/了解即可和 5–10 个检查问题。
- 解释 RAG chain 与 Tool calling 的区别；是否需要显式 LangChain Tool 由实际架构需要决定，不为了清单添加无用封装。
- 与用户的既定学习顺序一致，先 LangChain，再 LangGraph、RAG、SQL、FastAPI。

### 验收

- 文档准确对应真实代码，示例可运行或明确标注为示意；相关自动化回归通过后记录测试结果。
- 学习材料完成后总结关键点并自动进入下一主题，不要求用户先给出架构方案。

## 错误记录

| 错误 | 尝试 | 处理 |
|---|---|---|
| 首次 WSL 命令返回异常/不可读状态 | 先前会话从 PowerShell 调用 `wsl.exe` | 本轮把 WSL/Docker 运行状态列为待核实环境信息，不据此声称 Docker 可用 |
| pytest 默认临时目录及 `.pytest-tmp` 均被拒绝访问 | 默认运行；随后指定项目内临时路径 | 使用授权的本地输出目录作为 `--basetemp` 并禁用 pytest cache provider，6 项测试全部通过 |
| 首次环境安装命令返回后 pytest 模块短暂不可用 | 直接运行 `python -m pytest` | 重新核验虚拟环境并完成 editable 安装后测试可运行 |
| LangChain 依赖安装期间 Windows `openai` 文件被占用 | 并发安装尝试导致虚拟环境安装互相冲突 | 识别并停止本轮启动的残留安装进程，单独顺序完成安装；最终依赖安装成功，RAG 全量测试通过 |
| 当前会话无法调用 Docker CLI，`wsl.exe` 命令输出不可读 | PowerShell 检查 Docker，随后检查 WSL 命令 | 后续用户配置 Windows Docker CLI loopback relay；当前通过完整路径执行只读 Docker/Compose 检查 |
# 阶段 8 最新状态（2026-11-16，覆盖下方旧的待连接记录）

- [x] 创建公开仓库：https://github.com/KaelLee335/enterprise-support-agent-v2
- [x] 推送本地 `main`，提交 `e68a1cea` 与 `04503a1` 均已发布。
- [x] 核对 GitHub API、远端分支和文件树：105 项；未包含 `.env`、数据库/WAL、向量库、虚拟环境、缓存或 egg-info。
- [x] 本机 `main` 与 `origin/main` 同步；发布期间未更改虚拟网卡或路由。

阶段 8 已完成。上方遗留的“待连接”小节标题为历史记录，当前状态以本节为准。
# 2026-11-16 快速执行状态补记

- 用户截图报告 P0 身份/运行记录实现、全量 51 项测试、WSL 重建与 11/11 验收已通过；此会话按用户证据记录，尚未能独立复核。
- 阶段 11：新增 LangChain 中文初稿 `docs/learning/langchain.md` 和学习路线索引 `docs/learning/README.md`。内容基于本会话可读的公开代码快照；需执行器恢复后对照本机身份改造后的实现、核验代码链接和示例，并补充 LangGraph → RAG → SQL → FastAPI 章节。
- GitHub 公开仓库最后可读 `main` 为 `6a2c132`，仍未看到本地截图中的 P0 源码或学习目录。待本地 Git 工具恢复后核对是否推送；目前不通过 API 直接发布未经差异审查的内容。
- 近期阻塞：Windows 执行工具未启动（`helper_unknown_error: setup refresh had errors`），无法检查工作树或重跑测试。不得重复修改 WSL DNS/daemon/网络配置。

## 2026-11-16 后续更新

- GitHub API 已确认截图中两次提交：当前 `origin/main` HEAD 为 `12338a156975603bc4452e2fc1985100b312ad4c`，父提交为 `dbab8af...`。此前“main 仍为 6a2c132”的判断已过期。
- 阶段 11 LangGraph：已按当前远端源码新增 `docs/learning/langgraph.md`，并将索引从 LangChain 延伸至 LangGraph。它尚未做本地 git diff/测试/推送，待终端恢复后先核对再发布。
- 后续顺序不变：RAG → SQL → FastAPI。每章包含源码映射、流程图、示例、重点与自测题；完成文档后继续后续阶段，不要求用户先给架构方案。


## 阶段 16 旧版生产化提纲（当前暂停）

以下内容保留为历史路线说明；用户最新明确要求无需生产化，因此不执行本节工作。V2.1 只做本地模拟能力。

1. **范围与威胁模型**：确认目标用户、部署环境、数据等级、服务可用性要求和责任人；明确 Demo token 与模拟数据不能用于生产。
2. **身份与授权**：选定可信身份提供方，定义用户/租户映射、审批人角色、凭据轮换与审计要求。
3. **数据与状态**：确定数据库部署、迁移/备份/恢复策略、运行记录保留期、checkpoint 隔离和恢复目标。
4. **模型与 RAG 韧性**：定义超时、重试、限流、降级与供应商切换策略；补足真实 API 429/超时、检索失败和 checkpoint 损坏的隔离验证；重新评估语义正确性后才考虑改变默认 Top-K。
5. **部署与运维**：选择运行平台，制定密钥管理、日志脱敏、健康检查、监控告警、回滚和灾难恢复流程。
6. **验收门槛**：完成威胁建模、端到端权限测试、故障演练、备份恢复演练、部署复现及用户验收；明确每项证据和未覆盖风险。

阶段 16 不在当前工作范围。模拟身份、权限、审批和物流 API 按 `docs/v2_1_demo_reinforcement_plan.md` 执行，不接真实服务。

## 用户待办（下一次接续）

### 当前：V2.1 模拟外部客户主链已完成
本地实现、文档、WSL 两容器集成验收均已完成；WSL 结果由用户报告。V2.1 改动已由 `c8879bf` 推送至 `origin/main`。无需配置真实账号、API Key、云服务或客户资料。

### 暂不需要你做
- 不需要重建或重启 WSL/Docker。
- 不需要再次配置 API Key。
- 不需要重跑已由你报告通过的 53 项测试和 API 首次启动验收。
- checkpoint 随机损坏文件、Compose 缺 `.env` 配置失败和错误 bind 路径均已完成隔离验证；真实供应商限流/超时仍未验证，留待以后有明确演示需求时处理。

### 真实 API 演示提醒

- 用户计划后续配置真实 API 用于演示。在首次需要配置真实服务凭据或发送演示请求前，Codex 必须主动提醒用户，并说明服务商、请求数据范围、费用/额度影响和本机 `.env` 配置方法。
- API Key 只保存在用户本机 `.env` 或受控密钥存储中，不在聊天中索取或输出；未经确认不向新的服务商或模型发送数据。

## 当前执行顺序（用户确认：主链路完成后进行加固）

### 主链路状态：已贯通，按用户验收记录

`Bearer 身份/租户校验 → FastAPI 请求 → LangGraph 意图路由 → 订单只读 SQL / 政策 RAG / 退款审批 interrupt → 安全答复与运行记录`

证据分别来自用户报告的 WSL 11/11 验收、干净克隆 53 项 pytest，以及 clean-clone API smoke（health 200、带 Bearer 订单查询 200、无 token 401）。这些证据来自不同环境与步骤，不合并成单一指标。本阶段不重做已验收链路。

### 当前：阶段 15 可靠性加固

主链路已按验收记录完成。阶段 15 已完成：CI 55 项通过、Compose 解析/镜像构建/无 Key 容器 smoke 通过、checkpoint 损坏保护通过；本机四条离线回归 4/4（3.35 秒）；WSL 新镜像部署与 health 200、`verify_phase6.sh` 12/12 由用户报告。2026-11-17 本机会话完成 Compose 缺 `.env` 配置错误和错误 bind 路径的临时运行态验收；错误路径返回 `bind source path does not exist`、宿主路径未创建，临时资源已清理，现有项目容器仍 healthy。真实供应商限流/超时和生产化继续后置。用户计划后续用真实 API 演示，首次真实凭据配置或发送请求前必须主动提醒。
- 稳定延迟基线、语义正确性自动评估和生产级身份/RBAC/运维。
- 当前 Demo 保持虚构数据、固定演示身份、只读订单和演示审批，不扩展真实业务写操作。

若用户指出主链路还有未覆盖的业务路径，先把该路径写成验收场景，再据此规划实现；不得用加固项替代核心功能。
