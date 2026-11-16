# Enterprise Support Agent V2 — Python Agent Engineering

这是我从 Dify 低代码 Agent 开发转向 Python 代码级 Agent 工程的学习项目。我用一个企业售后场景，把用户请求、FastAPI、SQLite、LangChain RAG、LangGraph 状态编排、评估追踪和 Docker 部署连成一条可运行、可检查的工程链路。

项目重视真实理解与工程取舍，不堆叠技术：核心架构问题由我参与思考和决策，Codex 协助常规实现、调试和验证。当前是使用模拟数据的本地演示项目，不是生产客服系统；它不执行真实退款、改址或删除操作。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn support_agent.main:app --reload --app-dir src
```

打开 <http://127.0.0.1:8000/docs>。健康检查为 `GET /health`；订单查询为 `GET /orders/{order_id}`；Agent 对话为 `POST /chat`，请求头需提供 `X-Tenant-ID`。V1 导入订单使用 `legacy-demo`；固定案例 `1001` 使用 `demo-a`。

SQLite 默认写入 `data/support_agent.db`。删除该文件会重建演示数据库；它是本地运行数据，不应提交到 Git。

## 测试

```powershell
pytest
```

## 政策检索（阶段 2）

复制 `.env.example` 为 `.env`，在本机 `.env` 中填写 SiliconFlow API Key；不要把真实 Key 发到聊天或提交到 Git。Windows + WSL 用户可保持 `PROJECT_DATA_DIR` 留空，默认使用本项目的 `/mnt/d/project_2/data`；其他环境在 `.env` 中将其设置为项目内的数据路径，例如 `PROJECT_DATA_DIR=./data`。然后在项目虚拟环境运行：

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# 编辑 .env，填写 SILICONFLOW_API_KEY
\.venv\Scripts\Activate.ps1
python scripts/index_policies.py
python scripts/search_policies.py "定制商品出现质量问题怎么办？"
python scripts/ask_policy.py "定制商品出现质量问题怎么办？"
```

当前政策较短，第一版每个政策文件形成一个检索块；向量索引保存在 `data/vector_store/`。`ask_policy.py` 和 `POST /chat` 会把召回证据传给配置的聊天模型并检查引用是否来自本次检索结果；引用检查不是完整事实核验，仍需结合评估集检查回答是否被证据支持。

## 人工审批（阶段 4）

退款请求会暂停并保存在 `data/checkpoints.sqlite`，等待显式批准或拒绝。批准只写入 `approved_demo` 状态，不修改订单、不执行退款。`POST /chat` 返回待审批 `thread_id` 后，可通过 Swagger 查看状态并调用 `POST /approvals/{thread_id}/decision` 恢复流程。审批路由仅供本地演示，没有真实审批人认证。

## 评估与追踪（阶段 5）

运行 `python scripts/evaluate_agent_routes.py` 评估标注路由、订单参数和临时数据库工具结果；运行 `python scripts/evaluate_agent_safety.py` 检查写操作边界；`pytest` 执行故障注入和 API 回归。RAG 评估使用 `python scripts/evaluate_retrieval.py`，需本机配置 SiliconFlow Key。评估口径、已知 Bad Case 和追踪字段见 [`docs/evaluation_and_observability.md`](docs/evaluation_and_observability.md)。每个 API 响应均带 `X-Trace-ID`，日志为 JSON 并输出到标准输出。

RAG 答案层增加了可审计的政策约束规则，详细人工复核和 Top-4/Top-8 输出见 [`docs/rag_answer_manual_review.md`](docs/rag_answer_manual_review.md) 与 `data/evaluation/v2_rag_answers_constraints_v3.json`。约束层当前仅在 Windows 工作区完成评估；需同步到 WSL 并重建后才进入 Docker 验收版本。

## 端到端演示

启动、验证订单/租户隔离、政策引用和退款审批的完整步骤见 [`docs/demo_runbook.md`](docs/demo_runbook.md)。当前 WSL Docker 部署已完成用户实测验收。

## 项目架构与讲解

系统架构和指标摘要见 [`docs/project_story.md`](docs/project_story.md)；完整 3/10 分钟讲稿、20 个技术问题与 5 个故障案例见 [`docs/interview_kit.md`](docs/interview_kit.md)。

当前已完成/待推进事项见 [`docs/project_status.md`](docs/project_status.md)；项目代理接续说明与约束见根目录 [`AGENTS.md`](AGENTS.md)。

## Docker（WSL）

确保项目根目录已有本机 `.env`（SiliconFlow Key 不要写入镜像）。为避开 `/mnt/d` 上的 BuildKit 权限问题，在 WSL 中从 `/opt/project2` 构建；Compose 将数据目录绝对挂载到 Windows 同源的 `/mnt/d/project_2/data`：

```bash
cd /opt/project2
docker compose up --build -d
docker compose ps
```

首次 Docker 部署前，在项目虚拟环境中先运行一次 `python scripts/index_policies.py`，生成本机 `data/vector_store/`；该向量库被 Git 和 Docker 构建上下文排除，避免依赖未跟踪的本机文件。Compose 会从 `.env` 读取模型凭据和数据路径；订单库、审批 checkpoint 和 Chroma 向量库都保存在挂载的数据目录。等待容器状态为 `healthy` 后再打开 API 文档。

从 WSL `/opt/project2` 运行 `bash scripts/verify_phase6.sh` 可自动断言 health、订单/政策正常路径，以及异常订单号、隐私请求和提示注入处理；脚本失败时会返回非零状态。

政策约束层已同步到 WSL `/opt/project2` 并完成验收：健康检查通过，11 个业务用例全部 PASS，EXIT=0。验收覆盖 POL-06 退款两阶段时限、POL-04 进液保修排除、POL-02 质量故障路由和 POL-09 发票隐私边界。后续若 D 盘源码有改动，可在 `inbox` WSL 会话运行 `bash /mnt/d/project_2/scripts/update_wsl_and_verify.sh`，同步代码、重建 Compose 服务并重新验收；该操作会短暂重启服务，并保留 D 盘 `data/` 挂载。

Dockerfile 将依赖安装与本地源码安装分层，修改源码时可复用依赖缓存；pip 使用 TUNA 镜像并放宽下载超时。

API 地址为 <http://localhost:8000/docs>。订单数据库保存在宿主机 `data/support_agent.db`，容器重建后仍会保留。查看日志和停止服务：

```bash
docker compose logs -f
docker compose down
```

`/opt/project2` 中需放置与 Windows `D:\project_2` 同步的代码、Dockerfile、Compose 和政策文件。当前 WSL 配置默认将 `/mnt/d/project_2/data` 挂载到容器 `/app/data`；可用 `.env` 的 `PROJECT_DATA_DIR` 覆盖。订单库、审批 checkpoint 与 Chroma 索引均从此数据目录读取并保存。

容器中的相对路径配置（`DATABASE_PATH`、`CHECKPOINT_DB_PATH`、`VECTOR_STORE_PATH`）按工作目录 `/app` 解析，不依赖 pip 安装后 `site-packages` 中的源码位置。`.env` 从当前工作目录向上加载。

`systemctl is-active docker` 为空而 `is-enabled` 为 `enabled`，systemd 未报告 Docker unit 正在运行。用户实测 Ubuntu WSL 为 Stopped 时触发计划任务后，`dockerd` 就绪、容器 healthy、health 200。当前 Windows 计划任务配置为用户登录时触发，不能据此保证登录前自动恢复。详情见 [`docs/wsl_docker_lifecycle.md`](docs/wsl_docker_lifecycle.md)。

## 迁移说明

V1 资产来源、字段差异和 RET-01/QUA-01 对照见 [`docs/migration.md`](docs/migration.md)。新规则作为 V2 明确规则单独维护，不修改 V1 原始规则。

## 当前边界

`X-Tenant-ID` 仅用于本地租户隔离演示，不是登录身份或生产认证。退款审批只记录演示状态，不执行真实业务操作。Docker Compose 已在 WSL Docker 环境完成用户实测验收。
