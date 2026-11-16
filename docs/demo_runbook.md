# 演示操作手册

## 演示前检查

1. 在 WSL 中确认 `/opt/project2` 是最新项目副本，并启动容器：

   ```bash
   cd /opt/project2
   docker compose up --build -d
   docker compose ps
   curl -i http://localhost:8000/health
   ```

   容器应为 `healthy`，健康检查返回 HTTP 200。Swagger 在 <http://localhost:8000/docs>。

2. 查看日志：

   ```bash
   docker compose logs --tail=100 support-agent
   ```

   日志为 JSON；演示时确认没有 `ERROR`。不要在屏幕录制中展示 `.env` 或 Key。

3. 当前 `dockerd` 由 WSL 会话启动。演示期间不要关闭承载 daemon 的会话/发行版；如需在系统重启后自动恢复，先检查 systemd 服务状态，步骤见 [`wsl_docker_lifecycle.md`](wsl_docker_lifecycle.md)。

## 演示流程

除 `/health` 外的业务 API 使用本地演示 Bearer 身份。`demo-a-local-token` 映射到 `user-demo-a`/`demo-a`；`legacy-demo-local-token` 映射到 V1 导入租户。令牌公开，仅用于本地演示。

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

### 5. 退款人工审批暂停与恢复

在 `/docs` 的 `POST /chat` 中输入：`帮我给订单 1001 直接退款`。预期 `approval_status=pending`，响应返回 `thread_id`。保留这个 ID，之后：

1. 调用 `GET /approvals/{thread_id}`，Header 使用 `Authorization: Bearer demo-a-local-token`，应看到 `pending`。
2. 调用 `POST /approvals/{thread_id}/decision`，同样带租户 Header，请求体 `{"approved":true}`。
3. 预期返回 `approval_status=approved_demo`，并明确说明没有执行真实退款。
4. 再查 `GET /orders/1001`，订单状态仍是“已完成”。这证明审批演示未写订单数据。

也可将 `approved` 设为 `false` 演示拒绝分支。跨租户审批访问应返回 404；重复提交决定应返回 409。

## 验收清单

- [ ] 容器状态 `healthy`，`/health` 返回 200。
- [ ] `查询订单1001` 路由为 `order_lookup`。
- [ ] 当前租户查到订单，其他租户无法读取。
- [ ] 政策问题返回 `POL-06` 证据和有效引用标记。
- [ ] 改址等写操作被拒绝。
- [ ] 退款请求进入 `pending`，批准后为 `approved_demo`，订单保持原状态。
- [ ] 日志没有错误；演示录屏未包含 Key。

本项目使用虚构订单和政策，仅用于工程演示；公开 Bearer 演示令牌不能保护真实用户或生产数据。
