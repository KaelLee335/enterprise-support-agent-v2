# 项目推进计划

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
- [x] 阶段 6 验收脚本已在 WSL `/opt/project2` 运行，全部检查通过，EXIT=0。

## 当前剩余工作

- [x] 阶段 7.1：文档、忽略规则和 Docker 构建输入审查；用户 WSL build 成功证实 Compose 可解析。
- [x] 阶段 7.2：本地 Git 仓库文件清单和敏感/生成路径忽略规则由用户在 WSL 核查；`.env.example` 可跟踪，尚未提交。
- [x] 阶段 7.3：用户在 WSL `/opt/project2` 同步发布就绪改动、重建并运行 11 项阶段 6 验收，数据挂载正确。

- [x] 逐例审查 Top-4/Top-8 生成答案；`docs/rag_answer_manual_review.md` 已记录全部 14 组。
- [x] 政策约束层 v1 已实现并完成 14 案例 Top-4/Top-8 评估；28/28 引用 ID 校验有效，重点 Bad Case 输出已人工审阅。
- [x] 用户在 `inbox` WSL 会话同步修正后的 `verify_phase6.sh` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0；退款两阶段时限用例已通过。
- [x] 最终交付文档收尾：README、RAG 人工评审、Evaluation、项目状态和接续说明均与 WSL 最新部署/验收结果对齐；历史记录保留并明确标注为已被后续结果取代。
- [ ] （可选运维）若需保证 Windows 开机后自动恢复，检查 `Start-ScheduledTask` 对应任务的触发器、运行账户及“用户未登录时运行”设置；目前已验证 Ubuntu Stopped 时手动触发任务可恢复 Docker 与项目容器。不要停止或重复启动 daemon。
- [ ] 生产化能力（真实身份认证、审批人 RBAC/审计、多实例持久化、超时/限流/重试）不属于当前演示范围。
- [ ] 学习/面试问答按用户要求暂缓。

## 本轮范围

阶段 0–6 的原始版本、Docker 功能验收、演示手册和完整面试材料均已完成。阶段 7 发布就绪与可复现交接也已完成：Git 忽略规则与待跟踪清单已审阅，Docker 新克隆构建成功，D 盘数据挂载正确，11 项验收全过。RAG 约束层在本机评估并部署到 WSL；Ubuntu WSL 停止后通过计划任务触发已恢复 Docker 容器并健康；Windows 完整重启后的触发仍未验证。原始需求的学习问答由用户要求暂缓，之后统一处理。

## 阶段 8：GitHub 公开交付（已完成；下方为历史记录）

- [x] 用户选择新建公开仓库。
- [x] 发布前最终密钥/运行数据检查并审阅首次提交文件清单。
- [x] 完成公开前忽略规则、文件清单、令牌格式和 `.env.example` 检查；创建本地初始提交 `e68a1cea3bc6f31cb7704c709f6273aae900ee04`，作者使用 GitHub noreply 地址。
- [x] 在 GitHub 创建空白公开仓库 `https://github.com/KaelLee335/enterprise-support-agent-v2`，未初始化额外文件。
- [x] 添加 origin、推送 `main` 并核对远端仓库可见性、文件树和 README/source/tests 内容。
- [x] 验证远端默认分支、README/source/tests 展示并提供仓库链接。

## 阶段 9：Windows/WSL Docker 启动可靠性（只读审查完成，等待用户决定是否改设置）

- [x] 只读检查 `WSL-Dockerd-Autostart` 任务的命令、触发器、运行账户和最近结果。
- [x] 确认任务当前以 `LAPTOP-08OK88SN\\17488` 交互式账户运行，触发器为已启用的 Logon（用户登录），不是 Startup（系统启动）。
- [ ] 若用户需要登录前开机自启，先取得确认，再评估改为 Startup/服务账户运行的安全性、WSL 启动行为及脚本权限；确认前不修改计划任务、不启动/停止 Docker、不改 WSL/systemd/网卡设置。
- [ ] 经授权后才验证系统重启/登录前行为；不得用停止当前 daemon 的方式做试验。

当前检查只读取任务属性：任务状态 Running，最近执行时间 2026-11-16 09:58:58，结果代码 267009；未触发或修改任务。此前用户已验证手动触发可从 Ubuntu Stopped 状态恢复到容器 healthy 和 health 200，这与“开机登录前自动恢复”是不同场景。

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
