# V2.1 MockShop API 参考

本文描述本地演示新增的 MockShop 集成接口。所有身份、店铺、订单和售后记录均为虚构数据；接口不连接淘宝、京东、Shopify 等真实平台，也不执行真实退货或退款。

## 调用身份

除 `/health` 和供模拟平台调用的 webhook 外，接口使用 `Authorization: Bearer <demo-token>`。服务端 token 映射身份，不接受客户端传入的 tenant/store 作为授权依据。

| Token | 身份 | 范围 |
|---|---|---|
| `demo-a-local-token` | 请求人 A | `demo-a` / 店铺 A / customer-demo-a |
| `demo-a-approver-local-token` | 审批人 A | `demo-a`，仅能处理演示审批 |
| `demo-b-local-token` | 请求人 B | `demo-b` / 店铺 B / customer-demo-c |

演示令牌是公开的本地选择器，不是生产凭据。

## 业务接口

### 读取 MockShop 订单

`GET /ecommerce/orders/{order_id}`

返回 Adapter 归一后的订单 DTO。只有当前身份有权访问的店铺和客户订单可读；其他订单统一返回 404，避免泄露其存在性。

### 查询平台物流

`GET /ecommerce/orders/{order_id}/logistics`

先验证订单访问范围，再返回虚构运单和轨迹。

### 检查售后资格

`GET /ecommerce/orders/{order_id}/aftersale-eligibility?reason=商品质量问题`

这是只读资格判断，不会创建申请。规则由 MockShop fixture 明确给出。

### 创建演示售后申请

`POST /ecommerce/orders/{order_id}/aftersales`

请求示例：

```json
{
  "reason": "商品存在质量问题（虚构演示）",
  "idempotency_key": "demo-request-unique-001",
  "confirmed": true
}
```

只有请求人可以调用，必须明确 `confirmed: true`，并通过订单权限和资格检查。重复幂等键返回同一申请记录。成功状态为 `pending_demo`，表示 MockShop 演示申请已记录；不代表人工审批通过、平台已经退货或款项已经退款。

### 查询演示申请

`GET /ecommerce/aftersales/{request_id}`

按 tenant 读取本地 SQLite 中的演示申请状态。

## Webhook

`POST /webhooks/mock-shop`

平台模拟器按原始请求体计算 HMAC-SHA256，放入 `X-MockShop-Signature: sha256=<hex>`。验证签名后才进行 Pydantic schema 校验及事件入库。`event_id` 唯一：同一 ID 和相同 body 返回重复事件结果；相同 ID 携带不同 body 返回 409。过期事件会留存但不会覆盖较新的订单状态。租户由可信的 `shop_id` 映射派生，忽略 payload 中伪造的 tenant 字段。

事件状态可以经 `GET /webhooks/mock-shop/events/{event_id}` 查询，且受 tenant scope 限制。请求大小限制、错误响应和日志均避免暴露签名或密钥。

## Mock 平台 API

独立服务 `support_agent.mock_shop_api:app` 提供：

- `GET /mock-shop/orders/{order_id}`
- `GET /mock-shop/orders/{order_id}/logistics`
- `GET /mock-shop/orders/{order_id}/aftersale-eligibility`
- `POST /mock-shop/orders/{order_id}/aftersales`
- `GET /mock-shop/aftersales/{aftersale_id}`

这些接口由 Adapter 的 typed client 使用服务密钥调用，仅在 Compose 内部网络暴露，不发布宿主机端口。

完整 schema 可在 FastAPI `/docs` 查看。错误采用通用 HTTP 状态与安全消息；平台原始异常细节不会返回给访客。
