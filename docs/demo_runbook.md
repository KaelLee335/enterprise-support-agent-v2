# 演示操作手册

## 演示前检查

1. 在 WSL 中确认 `/opt/project2` 是最新项目副本，`.env` 存在且 `PROJECT_DATA_DIR` 指向已存在的数据目录，再启动容器：

   ```bash
   cd /opt/project2
   docker compose up --build -d
   docker compose ps
   curl -i http://localhost:8000/health
   ```

   容器应为 `healthy`，健康检查返回 HTTP 200。Swagger 在 <http://localhost:8000/docs>。

   Compose 不会为错误的 bind mount 路径自动创建空目录；若启动时报挂载源路径不存在，先核对 `PROJECT_DATA_DIR`，不要改动现有持久数据目录。

2. 查看日志：

   ```bash
   docker compose logs --tail=100 support-agent
   ```

   日志为 JSON；演示时确认没有 `ERROR`。不要在屏幕录制中展示 `.env` 或 Key。

3. 用户报告 Windows 登录触发任务负责启动 WSL Docker daemon，并在 WSL 重启后修复过 Docker NAT 网段冲突。该任务为 Logon 触发，不承诺用户登录前可用；演示前请确认容器 healthy。不要为演示改网络适配器或 systemd。更多信息见 [`wsl_docker_lifecycle.md`](wsl_docker_lifecycle.md)。

## 演示流程

除 `/health` 外的业务 API 使用本地演示 Bearer 身份。`demo-a-local-token` 是租户 `demo-a` 的请求人；`demo-a-approver-local-token` 是同租户另一位虚构审批人；`legacy-demo-local-token` 映射到 V1 导入租户。公开令牌只是演示身份选择器，不是真实认证。

### 1. 中文紧邻订单号识别与只读查询

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer demo-a-local-token' \
  -d '{"question":"查询订单1001"}'
```

预期 `intent` 为 `order_lookup`，订单号为 `1001`，订单状态为“已完成”。响应包含 `trace_id`，HTTP Header 中也有 `X-Trace-ID`。

### 2. 租户隔离

```bash
curl -i http://localhost:8000/orders/1001 -H 'Authorization: Bearer demo-a-local-token'
curl -i http://localhost:8000/orders/1001 -H 'Authorization: Bearer legacy-demo-local-token'
```

预期 `demo-a` 能读取演示订单；`legacy-demo` 收到 404，响应不泄露其他租户订单内容。

### 3. 政策 RAG 与引用

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer demo-a-local-token' \
  -d '{"question":"退款中表示钱已经到账了吗？"}'
```

预期 `intent` 为 `policy_qa`，证据包含 `POL-06`，`citations_valid` 为 `true`。这只表示回答引用了本次检索到的政策编号，仍需阅读 `evidence` 核对语义。

### 4. 非退款写操作拒绝

在 `/docs` 的 `POST /chat` 中输入：`帮我把订单 1001 地址改一下`。预期 `intent=write_request`，回答明确表示不能改地址；不应返回“修改成功”。

### 5. 本地模拟物流 API

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer demo-a-local-token' \
  -d '{"question":"查询订单1001物流到哪了"}'
```

预期 `intent=logistics_lookup`，`shipment.demo_only=true`。LangGraph 先从租户范围内的 SQLite 核对订单，再通过内部 HTTP 网络调用 `mock-logistics`；数据为静态虚构轨迹。跨租户找不到订单时不会访问物流服务。该服务不调用商业快递 API。

### 6. 退款人工审批暂停与恢复

在 `/docs` 的 `POST /chat` 中输入：`帮我给订单 1001 直接退款`。预期 `approval_status=pending`，响应返回 `thread_id`。保留这个 ID，之后：

1. 调用 `GET /approvals/{thread_id}`，Header 使用 `Authorization: Bearer demo-a-local-token`，应看到 `pending`。
2. 请求人令牌尝试决定时应返回 403。前端演示可切换到审批人：对话历史会切换到审批人自己的会话，待审批任务则保留为独立任务卡；随后改用 `Authorization: Bearer demo-a-approver-local-token` 调用 `POST /approvals/{thread_id}/decision`，请求体 `{"approved":true}`。
3. 预期返回 `approval_status=approved_demo`，并明确说明没有执行真实退款。
4. 再查 `GET /orders/1001`，订单状态仍是“已完成”。这证明审批演示未写订单数据。

也可将 `approved` 设为 `false` 演示拒绝分支。同一审批人发起后自批会返回 403；跨租户审批访问应返回 404；重复提交决定应返回 409。批准不执行退款，订单保持不变。

## 验收清单

- [ ] 容器状态 `healthy`，`/health` 返回 200。
- [ ] `查询订单1001` 路由为 `order_lookup`。
- [ ] 当前租户查到订单，其他租户无法读取。
- [ ] 政策问题返回 `POL-06` 证据和有效引用标记。
- [ ] 改址等写操作被拒绝。
- [ ] 物流查询显示标记为虚构数据的模拟轨迹。
- [ ] 请求人自批返回 403，独立审批人可记录演示决定。
- [ ] 退款请求进入 `pending`，批准后为 `approved_demo`，订单保持原状态。
- [ ] 日志没有错误；演示录屏未包含 Key。

本项目使用虚构订单和政策，仅用于工程演示；公开 Bearer 演示令牌不能保护真实用户或生产数据。
