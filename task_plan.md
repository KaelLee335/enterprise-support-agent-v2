# 项目推进计划

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
| 15 | 可选生产化：真实身份认证、审批 RBAC/审计、多实例存储、韧性和安全运营 | 非 Demo 范围；需单独定范围与批准 |

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

- [x] 阶段 7.1：文档、忽略规则和 Docker 构建输入审查；用户 WSL build 成功证实 Compose 可解析。
- [x] 阶段 7.2：本地 Git 仓库文件清单和敏感/生成路径忽略规则由用户在 WSL 核查；`.env.example` 可跟踪，尚未提交。
- [x] 阶段 7.3：用户在 WSL `the WSL project directory` 同步发布就绪改动、重建并运行 11 项阶段 6 验收，数据挂载正确。

- [x] 逐例审查 Top-4/Top-8 生成答案；`docs/rag_answer_manual_review.md` 已记录全部 14 组。
- [x] 政策约束层 v1 已实现并完成 14 案例 Top-4/Top-8 评估；28/28 引用 ID 校验有效，重点 Bad Case 输出已人工审阅。
- [x] 用户在 `inbox` WSL 会话同步修正后的 `verify_phase6.sh` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0；退款两阶段时限用例已通过。
- [x] 最终交付文档收尾：README、RAG 人工评审、Evaluation、项目状态和接续说明均与 WSL 最新部署/验收结果对齐；历史记录保留并明确标注为已被后续结果取代。
- [x] 阶段 10：完成需求追踪矩阵，逐条标为已实现、部分实现、未实现、未验证或不适用，并附证据位置与建议优先级；未运行测试。
- [x] 阶段 11：完成 LangChain、LangGraph、RAG、SQL、FastAPI 五章代码绑定中文手册，位于 docs/learning/；GitHub tree 已确认五章存在。
- [x] 阶段 12：本地 Demo 身份、租户权限、最小运行记录和 12 项故障库完成；用户报告全量 51 项和 WSL 11/11 通过，并报告新增 not_found 与 fake timeout 两条定向测试 2/2 通过。Checkpoint 损坏、Compose 缺 Key 仍列为未验证，不等同本阶段验收通过。
- [x] 阶段 13：用户报告 D 盘全新 clone、venv/pip 安装、53 项 pytest 通过（18.39s）；API health 200、Bearer 订单 1001 查询 200、无 token 401。此次无 .env、无 API Key、无 WSL/Docker。
- [x] 阶段 14：已核对 README、项目故事、面试包、演示手册、需求追踪、故障库和项目状态；按用户报告更新 53 项测试及 clean clone API smoke，并保留未验证边界。WSL/Docker 主机记录采用不含机器路径和网络参数的概括描述。
- [ ] 阶段 15 生产化待单独定范围；学习/面试演练在用户参与阶段逐步开展。

## 本轮范围

阶段 0–6 的原始版本、Docker 功能验收、演示手册和完整面试材料均已完成。阶段 7 发布就绪与可复现交接也已完成：Git 忽略规则与待跟踪清单已审阅，Docker 新克隆构建成功，D 盘数据挂载正确，11 项验收全过。RAG 约束层在本机评估并部署到 WSL；Ubuntu WSL 停止后通过计划任务触发已恢复 Docker 容器并健康；Windows 完整重启后的触发仍未验证。原始需求的学习问答由用户要求暂缓，之后统一处理。

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
| 当前会话无法调用 Docker CLI，`wsl.exe` 命令输出不可读 | PowerShell 检查 Docker，随后检查 WSL 命令 | 用户随后在 WSL Docker 中完成构建、健康、订单、审批与 RAG 全链路验收，最终结果记录于 `progress.md` |
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


## 阶段 15 预案：生产化评估（未开始，需单独定范围）

本地 Demo 的阶段 0–14 已交付。生产化会改变身份、数据和部署边界，因此本阶段只先列路线，不默认动代码、接入真实用户数据或改变主机运行配置。

1. **范围与威胁模型**：确认目标用户、部署环境、数据等级、服务可用性要求和责任人；明确 Demo token 与模拟数据不能用于生产。
2. **身份与授权**：选定可信身份提供方，定义用户/租户映射、审批人角色、凭据轮换与审计要求。
3. **数据与状态**：确定数据库部署、迁移/备份/恢复策略、运行记录保留期、checkpoint 隔离和恢复目标。
4. **模型与 RAG 韧性**：定义超时、重试、限流、降级与供应商切换策略；补足真实 API 429/超时、检索失败和 checkpoint 损坏的隔离验证；重新评估语义正确性后才考虑改变默认 Top-K。
5. **部署与运维**：选择运行平台，制定密钥管理、日志脱敏、健康检查、监控告警、回滚和灾难恢复流程。
6. **验收门槛**：完成威胁建模、端到端权限测试、故障演练、备份恢复演练、部署复现及用户验收；明确每项证据和未覆盖风险。

**启动门槛**：需要用户确认该项目是否继续保持个人本地 Demo，或进入真实环境生产化。若选择生产化，还需提供部署环境、身份系统和数据合规要求；未明确前保持当前模拟身份、虚构数据和不执行真实退款的边界。

## 用户待办（下一次接续）

### 必做：同步最新文档
在本机项目目录执行：

```powershell
git pull --ff-only origin main
```

### 可选：决定是否进入生产化
当前本地 Demo 已完成阶段 0–14。只有你希望项目用于真实用户/真实业务时，才需要决定启动阶段 15。若启动，请补充部署环境、身份认证系统和数据合规要求；否则保持 Demo，不需要额外操作。

### 暂不需要你做
- 不需要重建或重启 WSL/Docker。
- 不需要再次配置 API Key。
- 不需要重跑已由你报告通过的 53 项测试和 API 首次启动验收。
- 不需要处理 checkpoint 损坏、真实供应商限流、Compose 缺 Key/路径等未验证项，除非你决定继续做这些故障验证。

