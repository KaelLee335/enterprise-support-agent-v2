# 项目状态

更新日期：2026-11-17

## 当前阶段：V2.1 本地演示加固（WSL 集成验收完成）

- 新增同租户独立 requester/approver 演示身份；requester 自批 403、跨租户审批读取 404、独立 approver 可记录 `approved_demo`。仍是公开 Demo token，不是真实认证。
- 新增 LangGraph 物流查询分支；先按 tenant 从 SQLite 确认订单，再经带演示服务标记的 HTTP client 请求静态 mock 服务。只含虚构单号与轨迹，不访问商业快递 API。
- 新增 `uv.lock`；CI 用 `uv sync --locked` 检查锁文件一致性，Dockerfile 用 `uv sync --frozen` 按锁文件安装，避免构建时受 Aliyun 索引元数据重新解析影响。CI 触发路径已包含政策、seed、前端、脚本和文档，并添加 Vue 构建及 Compose 内物流 API smoke。
- 本机验收：65 项 pytest 通过；Vue `npm run build` 通过；`docker compose config --quiet` 通过；Python 源码编译通过。此前本机 Docker 镜像构建曾在拉取阶段返回 `unexpected EOF`；之后用户在 WSL 完成同步和重建，该结果已由下条实机验收覆盖。
- WSL 部署由用户报告已完成：更新脚本同步 `uv.lock` 与源码到 `/opt/project2`，两容器 healthy，阶段 6 与 V2.1 新增 verifier 用例全部 PASS。此为用户提供的实机结果，本会话没有操作 WSL。
- 发布后的 GitHub Actions run 19（commit `46d089a`）已通过：锁文件安装、Python 全量测试、Vue 构建、无密钥 Compose 校验、Docker 镜像构建和无 Key 容器烟测。
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
- 用户已明确无需生产化，阶段 16 暂停。V2.1 四阶段实现与 WSL 集成验收均已完成（WSL 结果由用户报告）；实现已由 `c8879bf` 推送到 `origin/main`。完整方案见 [`docs/v2_1_demo_reinforcement_plan.md`](v2_1_demo_reinforcement_plan.md)。

- 用户最新 WSL 验收报告：同步 `Dockerfile`、Compose、`main.py`、API 回归测试和 verifier 后，镜像重建、容器重建启动成功，health 200；`verify_phase6.sh` 12/12 PASS，EXIT=0。该项包括此前新增的 auth/clarify/refund/policy 用例。结果来自用户截图，本会话未直接操作 WSL。

- 用户选择保持 `RAG_TOP_K=4`。Top-8 提升证据召回，但基线评估未证明最终回答更好；约束层评估也没有因 Top-8 而切换默认值。
- LLM judge 指标仅作探索性筛查，不能当作答案准确率。引用 ID 有效也不代表回答的事实都被证据支持。
- systemd 的 `docker` unit 未报告 active（enabled 标记存在）。用户已实测 Ubuntu WSL 为 `Stopped` 时触发任务后 `dockerd ready`、容器 healthy、health 200。2026-11-16 本机只读检查发现 `the existing scheduled task` 任务是当前用户的交互式 Logon 触发器，不是 Startup 触发器；因此不能保证用户登录前恢复。没有修改计划任务或虚拟网卡。
- 学习/面试问答按用户要求暂存。

## 尚未完成 / 后续计划

1. 阶段 0–14 已完成。阶段 15 现有 CI 为 55 passed，WSL 12/12 验收由用户报告；本机阶段 15 四条离线回归也已复核通过（4/4，3.35 秒：timeout 安全答复、无 Embedding Key、checkpoint 损坏保护、无 Key API 降级）。2026-11-17 隔离 Compose 检查确认缺少 `.env` 会明确配置失败；错误数据路径在 `config` 阶段不创建。`compose.yaml` 使用 `create_host_path: false`；临时服务的运行态错误挂载验收也通过。真实供应商 429/timeout 未验证，暂不属于当前本地 Demo 验收范围。
2. 阶段 11 学习手册已完成并推送：LangChain、LangGraph、RAG、SQL、FastAPI 五章位于 `docs/learning/`；每章包括代码入口、数据流图、示例、重点和自测题。
3. 阶段 13 已完成：用户报告 D 盘干净克隆依赖安装成功、全量 53 项 pytest 通过，并完成 API health/order 首次启动验收。
4. 阶段 14 已完成：复核 README、项目故事、面试包、演示手册、需求追踪、故障库和 WSL 生命周期说明；过期待验收状态已修正，主机级配置仅以概括形式记录。
5. 阶段 15 离线加固已完成；缺少 `.env` 的配置错误、错误 bind 路径防误建和运行态失败均已隔离验证。阶段 16 生产化依用户指示暂停；V2.1 只推进本地 persona、演示审批角色、模拟物流 API 和交付一致性。

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

V2.1 本地实现及 WSL 集成验收均已完成（部署/验收结果由用户报告）。不要配置真实 API Key、外部身份服务或云资源；也不需要重跑已验收的 53 项 clean-clone 测试/API smoke。阶段 15 的 55 项结果来自 GitHub Actions。

## 当前优先级

用户确认先完成主要业务链路，再回头做加固。主链路已由用户验收。阶段 15 可靠性加固现已开始：已新增 GitHub Actions，在干净 Python 3.12 环境全量运行 pytest；新增 checkpoint 损坏预检，损坏文件安全阻止启动且不覆盖原文件。

GitHub Actions 最新报告 55 passed in 3.99s；Compose 模板解析、阿里云源 Docker 构建、临时容器 health/订单/无 Key RAG 安全降级均通过。WSL 部署与 12 项验收已由用户报告通过；本会话没有操作 WSL。2026-11-17 Compose v2.39.1 临时配置检查：无 `.env` 时 `config` 非零退出并报告文件缺失；错误数据目录配置可解析且配置命令不会创建目录。Compose 短格式 bind mount 默认会自动创建缺失源目录，因此 `compose.yaml` 已改成长语法并设置 `create_host_path: false`。桥接恢复后，唯一临时 Compose 项目验证不存在路径会使服务启动失败，daemon 明确返回 `bind source path does not exist`，宿主路径未创建；资源已清理且原项目容器仍 healthy。真实供应商限流、延迟统计和生产化暂缓。
