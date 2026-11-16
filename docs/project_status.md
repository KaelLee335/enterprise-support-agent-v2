# 项目状态

更新日期：2026-11-16

## 已完成并验收

- 阶段 0–6：V1 资产盘点、API/SQLite、云端 Embedding 与 Chroma RAG、LangGraph 路由、退款审批中断/恢复、评估与追踪、Docker 部署。
- 用户在 WSL Docker 实测：`/health` 200；订单号查询（含无空格形式）；异常/多订单号澄清；隐私和提示注入拒答；退款审批 `pending`；POL-06 政策回答引用有效；日志无 ERROR。
- 最新扩充版 `scripts/verify_phase6.sh` 已同步至 `/opt/project2` 并重跑：健康检查通过，11 个用例全部 PASS，EXIT=0。新增退款两阶段时限、进液保修排除、质量故障退货分流和发票隐私边界均通过。D 盘 `data/` 通过绝对路径 bind mount 持久化。
- 本机 Agent 路由评估：35/35；标注订单参数 8/8；工具调用 9/9；标注 outcome 6/6；订单字段 5/5。此前本机 pytest 47 项通过。上述是已记录结果，本轮没有重跑测试。
- RAG 召回对照（36 条有证据标签的案例）：Top-2/4/6/8 平均 Recall 分别为 77.3%/86.6%/89.4%/99.1%；完整证据率为 58.3%/72.2%/77.8%/97.2%。报告位于 `data/evaluation/`。
- Top-4/Top-8 对 14 条政策问题的生成与同模型 LLM 评分已执行；答案与来源记录在 `data/evaluation/v2_rag_answers.json`。
- 上述 28 条回答已逐例人工核查；发现 Top-4 的若干条件遗漏，以及 Top-8 的 POL-04 事实冲突。逐条记录在 `docs/rag_answer_manual_review.md`。
- 用户确认继续后已实现本地政策约束层，覆盖 POL-04 进液排除、POL-02 质量故障分流/退货条件、POL-05 退货指引、POL-06 分阶段退款时限、POL-09 发票隐私和未知范围。Top-4/Top-8 14 案例报告：`data/evaluation/v2_rag_answers_constraints_v3.json`；28/28 引用 ID 校验有效，重点回答已逐条核查。

## 当前配置和已知限制

- 用户选择保持 `RAG_TOP_K=4`。Top-8 提升证据召回，但基线评估未证明最终回答更好；约束层评估也没有因 Top-8 而切换默认值。
- LLM judge 指标仅作探索性筛查，不能当作答案准确率。引用 ID 有效也不代表回答的事实都被证据支持。
- systemd 的 `docker` unit 未报告 active（enabled 标记存在）。用户已实测 Ubuntu WSL 为 `Stopped` 时触发 `Start-ScheduledTask` 后 `dockerd ready`、`project2-support-agent-1 Up (healthy)`、health 200。该发行版停止后的恢复已验证；Windows 完整重启后的任务触发条件尚未核实。
- 学习/面试问答按用户要求暂存。

## 尚未完成 / 后续计划

1. 阶段 7（进行中）：全新克隆/构建可复现性与 GitHub 发布前整理。修复完成后需在 WSL `/opt/project2` 重建并运行 11 项验收；不会自动发布到 GitHub。
2. （可选运维）若需验证 Windows 开机自启，检查计划任务触发器、运行账户及用户未登录时的行为。Ubuntu 停止后的计划任务恢复已实测成功。
3. （生产化，不属于当前演示验收）真实认证与 tenant 授权、审批人 RBAC/审计、多实例持久化、模型超时/限流/重试与安全监控。

## 阶段 7：发布就绪与可复现交接（已完成）

- Dockerfile、Compose、`.gitignore`、`.dockerignore`、`.env.example` 和 README 已按全新克隆场景调整；本地 Git 仓库已初始化。
- 用户核查 `git status` 和忽略规则：7 个密钥/生成路径均被忽略，`.env.example` 保持可跟踪，待跟踪列表为预期项目文件。
- 用户在 WSL 成功重建镜像，容器 `healthy`；`docker inspect` 确认 `/mnt/d/project_2/data -> /app/data`；11 个阶段 6 验收用例全部 PASS，EXIT=0。没有提交或推送。

## 阶段 8：GitHub 公开交付（待连接）

- 用户已选择新建公开仓库，建议名称 `enterprise-support-agent-v2`。
- 发布前需要再次确认待提交清单与凭据扫描；尚未创建远端或提交代码。
- 已选择创建新的公开仓库 `enterprise-support-agent-v2`。首次提交内容已完成忽略规则检查和本地令牌格式扫描；等待空白远端仓库 URL 后推送。不要将本机 `.env`、数据库或向量库纳入版本控制。

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
