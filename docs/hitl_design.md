# 人工审批与 Checkpoint 演示

## 演示范围

- 用户提出退款请求后，系统校验该租户下订单是否存在，并创建一个 `refund_review` 待审批状态。
- LangGraph `interrupt()` 暂停执行，checkpoint 保存 thread State 到 `data/checkpoints.sqlite`。
- 人工通过 `POST /approvals/{thread_id}/decision` 提交批准/拒绝；API 校验请求租户和 checkpoint 中的 `tenant_id` 一致后，通过 `Command(resume=...)` 恢复同一 Graph thread。
- 批准后只把状态标记为 `approved_demo`；不更新订单、不调用真实退款服务。拒绝后状态为 `rejected`。
- 没有订单号或租户下不存在该订单时，不创建可审批 thread。跨租户用户看不到 thread。重复审批返回 HTTP 409。

## State 增量

- `approval_ready`：订单范围校验成功，可以暂停审批。
- `approval_status`：`pending`、`missing_order_id`、`order_not_found`、`approved_demo`、`rejected`。
- `pending_action`：最小摘要（动作名、订单号、订单状态、demo 标记），不存 API Key。
- `thread_id`：由 API 生成并用于恢复同一个 checkpoint thread。

## 本地演示步骤

1. 调用 `POST /chat` 请求退款，拿到 `thread_id` 和 `approval_status=pending`。
2. 通过 `GET /approvals/{thread_id}` 查看待审批状态。
3. 调用 `POST /approvals/{thread_id}/decision`，请求体 `{ "approved": true }` 或 `false`。
4. 重启 FastAPI 后再次查询同一 thread，确认 SQLite checkpoint 可恢复状态。

所有接口都需 `X-Tenant-ID`。它在此项目中仅是演示租户选择，不是登录或真实审批人身份验证；不要把该流程描述成生产权限系统。
