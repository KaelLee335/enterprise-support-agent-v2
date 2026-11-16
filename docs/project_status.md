# 项目状态

更新日期：2026-11-16

## 已完成并验收

- GitHub About、README、项目故事和面试材料已按最新项目定位更新：强调从 Dify 向代码级 Python Agent 工程学习、端到端链路及模拟数据边界。协作模式现按新版提示词为 Codex 技术负责人/主力开发者、用户学习理解者。
- 阶段 0–6：V1 资产盘点、API/SQLite、云端 Embedding 与 Chroma RAG、LangGraph 路由、退款审批中断/恢复、评估与追踪、Docker 部署。
- 用户在 WSL Docker 实测：`/health` 200；订单号查询（含无空格形式）；异常/多订单号澄清；隐私和提示注入拒答；退款审批 `pending`；POL-06 政策回答引用有效；日志无 ERROR。
- 最新扩充版 `scripts/verify_phase6.sh` 已同步至 `the WSL project directory` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0。新增退款两阶段时限、进液保修排除、质量故障退货分流和发票隐私边界均通过。D 盘 `data/` 通过绝对路径 bind mount 持久化。
- 本机 Agent 路由评估：35/35；标注订单参数 8/8；工具调用 9/9；标注 outcome 6/6；订单字段 5/5。此前本机 pytest 47 项通过。上述是已记录结果，本轮没有重跑测试。
- RAG 召回对照（36 条有证据标签的案例）：Top-2/4/6/8 平均 Recall 分别为 77.3%/86.6%/89.4%/99.1%；完整证据率为 58.3%/72.2%/77.8%/97.2%。报告位于 `data/evaluation/`。
- Top-4/Top-8 对 14 条政策问题的生成与同模型 LLM 评分已执行；答案与来源记录在 `data/evaluation/v2_rag_answers.json`。
- 上述 28 条回答已逐例人工核查；发现 Top-4 的若干条件遗漏，以及 Top-8 的 POL-04 事实冲突。逐条记录在 `docs/rag_answer_manual_review.md`。
- 用户确认继续后已实现本地政策约束层，覆盖 POL-04 进液排除、POL-02 质量故障分流/退货条件、POL-05 退货指引、POL-06 分阶段退款时限、POL-09 发票隐私和未知范围。Top-4/Top-8 14 案例报告：`data/evaluation/v2_rag_answers_constraints_v3.json`；28/28 引用 ID 校验有效，重点回答已逐条核查。

## 当前配置和已知限制

- 用户选择保持 `RAG_TOP_K=4`。Top-8 提升证据召回，但基线评估未证明最终回答更好；约束层评估也没有因 Top-8 而切换默认值。
- LLM judge 指标仅作探索性筛查，不能当作答案准确率。引用 ID 有效也不代表回答的事实都被证据支持。
- systemd 的 `docker` unit 未报告 active（enabled 标记存在）。用户已实测 Ubuntu WSL 为 `Stopped` 时触发任务后 `dockerd ready`、容器 healthy、health 200。2026-11-16 本机只读检查发现 `the existing scheduled task` 任务是当前用户的交互式 Logon 触发器，不是 Startup 触发器；因此不能保证用户登录前恢复。没有修改计划任务或虚拟网卡。
- 学习/面试问答按用户要求暂存。

## 尚未完成 / 后续计划

1. 阶段 0–11 已完成。用户截图报告演示 Bearer 身份/租户隔离、最小运行记录、51 项 pytest 和 WSL 11/11 验收通过。阶段 12 已按用户报告验收：两条新增 not_found 与假模型 timeout 测试通过（2/2）；12 类故障库已建立。Checkpoint 损坏/Compose 缺 Key 仍记录为未验证边界。
2. 阶段 11 学习手册已完成并推送：LangChain、LangGraph、RAG、SQL、FastAPI 五章位于 `docs/learning/`；每章包括代码入口、数据流图、示例、重点和自测题。
3. 阶段 13 已完成：用户报告 D 盘干净克隆依赖安装成功、全量 53 项 pytest 通过，并完成 API health/order 首次启动验收。
4. 阶段 14 已完成：复核 README、项目故事、面试包、演示手册、需求追踪、故障库和 WSL 生命周期说明；过期待验收状态已修正，主机级配置仅以概括形式记录。
5. 阶段 15 生产化（真实认证、RBAC、多实例、运营安全）不在本地 Demo 范围，单独规划，不默认开展。

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
- 阶段 13 干净克隆复现已完成（用户报告）；阶段 14 正在做最终材料一致性核查。


## Clean clone 与 pip 镜像记录（2026-11-16）

- 用户报告 D 盘干净克隆后同步到最新 main，pytest 53 passed / 18.39s / exit 0；这是用户提供的结果，本会话未复跑。
- 用户遇到全局 TUNA pip simple 返回 403（pip User-Agent 请求），临时加阿里云 `-i https://mirrors.aliyun.com/pypi/simple` 后安装成功。README 已加入单次安装的镜像 fallback。
- Dockerfile 的 TUNA 源风险记录为下次 Dockerfile 调整事项；本轮未改 Dockerfile，也未触碰 WSL/Docker。
- 用户随后报告该 clean clone 的 health 返回 {"status":"ok"}，带 Bearer 的 GET /orders/1001 返回 200 且租户/虚构数据正确，无 token 返回 401。至此首次启动链路已由用户验收；health 200、带 Bearer 的订单查询 200、无 token 401 均来自用户截图。本会话没有自行运行本地进程。阶段 14 文档一致性复核已完成。
