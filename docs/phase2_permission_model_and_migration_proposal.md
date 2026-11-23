# Phase 2 权限模型审计与迁移提案

日期：2026-11-22
状态：实施与本机测试完成；schema 仅在 pytest 隔离临时库验证，未迁移现有 D 盘/WSL 业务数据库。

## 1. 当前数据结构

| 概念 | 当前实现 | 与目标模型的差异 |
|---|---|---|
| Tenant | `tenants(tenant_id, display_name, is_demo)` | 有租户边界，未包含 tenant 内角色/授权关系。 |
| User | `demo_users(user_id, tenant_id, display_name, is_demo)`；`auth.py` 将固定 Bearer token 映射为 `DemoIdentity(user_id, tenant_id, role)` | 数据库用户没有 role；角色来自代码中的 token 字典。没有 Customer 实体或服务人员客户授权表。当前角色值是 `requester`/`approver`，不是目标的 Customer/Service/Approver/Admin。 |
| SQLite Order | `orders(order_id PK, tenant_id, customer_id nullable, ...)` | `customer_id` 可空且语义不统一。种子订单将 `customer_id` 清空；固定订单 1001 将它设为 `demo-a`（租户样式 ID），不等同 MockShop 的 `customer-demo-a`。不能据此安全回填真实所有权。 |
| MockShop Order | 独立 MockShop fixture 含 `order_id, shop_id, customer_id, ...` | fixture 的 customer 归属较明确；但访问控制映射 `_CUSTOMER_BY_USER` 和 store/tenant 对照写在 `integrations/permissions.py`，不是可管理授权数据。 |
| After-sale request | `aftersale_requests` 有 `user_id, tenant_id, order_id, status`；`user_id` 记录当前提交身份 | 没有分开的 `actor_id`（代办客服）和 `customer_id`（业务客户），客服代客户无法准确审计。读取规则仅让同租户原始 `user_id` 或任意 approver 读取。 |
| Approval | LangGraph interrupt + SQLite checkpoint；State 存 `tenant_id/user_id/user_role/pending_action` | 无持久 `task_id/approver_id/assignee/status/decision_at` 表；同租户 approver 可查看已知 thread；审批范围不是按任务分配。Checkpoint State 中历史身份不足以证明恢复调用人的权限。 |
| Agent Run | `agent_runs(run_id, user_id, tenant_id, ...)` | 查询、更新按 `run_id + tenant_id`，同租户其他用户可读取/更新记录。 |
| Webhook | `webhook_events` 与 `platform_order_states` 存 tenant/store/customer | HMAC 身份由服务配置验证，tenant 由 store 映射派生；当前 webhook 是可信平台同步入口，不是用户授权来源。订单状态 overlay 按 tenant/order 读取。 |

## 2. 当前身份与权限关系

```text
固定 Demo Bearer token
        │ auth.py 映射
        ▼
DemoIdentity(user_id, tenant_id, role)
        ├── SQLite orders / agent_runs：主要只检查 tenant_id
        ├── MockShop：请求 adapter.get_order 后才比对 tenant/store/customer
        ├── 售后：仅 requester 可提交；本人 user_id 可读取，任一同租户 approver 可读取
        └── Refund interrupt：approver 角色 + 非本人 + checkpoint pending
```

这适用于固定虚构演示身份，不是可配置的四角色权限系统。当前没有 Service 或 Admin 身份/授权实现。

## 3. 需要修正的越权面

1. `db.fetch_order()`、`fetch_agent_run()`、`update_agent_run()` 只按租户约束，没有 customer/user/assignee 范围。
2. `main.get_order()` 和 Agent `lookup_order/lookup_logistics/prepare_refund_approval` 只把 tenant 传给 Repository；Graph State 中的身份字段由 API 构造，但底层函数本身无法验证身份。
3. `main._load_authorized_platform_order()` 和 `integrations.tools.authorized_order()` 先读取 MockShop 订单对象，再检查用户是否有权；未授权对象已经进入服务内存。MockShop service API 本身以服务 key 认证，不识别业务调用者，这是内部平台边界；调用方必须先做资源定位/授权再取详情。
4. `permissions.can_access_order()` 将 approver 视作整个 tenant store 的订单可访问者，与“只读分配给自己的任务所需订单字段”冲突。
5. `/approvals/{thread_id}` 没有验证当前用户是否是被分配的 approver；审批决策也没有 assignee 检查或数据库条件更新。重复操作由 checkpoint pending 状态做有限保护，不能作为并发互斥或持久任务审计保证。
6. 恢复 LangGraph interrupt 时，API 检查当前 token 的 tenant/role/self-approval，但审批任务分配和 checkpoint 状态之间没有持久绑定；需用 DB 任务记录做当前权限的权威判断，再恢复 graph。
7. 售后提交目前将 `user_id` 当提交者，也只接受 requester；无法表示 Service 代客户申请，也无法在 Repository 层校验 customer 对订单的所有权。
8. `/agent-runs/{run_id}` 同租户范围过宽；运行记录虽不写 question 明文，也应限制到所有者或经授权管理范围。
9. 认证与授权目前概念上分开（Bearer 映射身份，业务函数再检查部分规则），但身份来源是公开固定 Demo token。客户端伪造 `X-Tenant-ID` 无效并不能代替资源所有权授权。

## 4. 建议的数据模型（不执行）

采用明确的 tenant 复合键和授权关系，不把 `role`/`customer_id` 从请求体读取：

- `customers(tenant_id, customer_id, display_name, ...)`：租户内客户主体。
- `tenant_users(tenant_id, user_id, role, customer_id, active, ...)`：用户在租户中的身份；role 限定 `customer/service/approver/admin`。Customer 行必须关联同租户 customer；其他角色不得借该字段获得客户身份。
- `service_customer_grants(tenant_id, service_user_id, customer_id, active, ...)`：客服可服务的客户范围；每次查订单/售后都以当前认证身份连接授权记录。
- `order_customer_ownership(tenant_id, source, store_id, order_id, customer_id, active, ...)`：统一给 SQLite 和 MockShop 订单建立 tenant/customer 所有权映射。Provider 返回的 customer_id 必须与授权表一致；不能只依赖客户端给出的 order_id。
- `approval_tasks(task_id, tenant_id, order_id, customer_id, requester_id, actor_id, approver_id, status, decision, decision_by, decision_at, created_at, updated_at, thread_id)`：审批分配及状态权威记录。状态使用受限值；任务查询必须同时匹配 tenant、当前 approver 和 pending 状态。`thread_id` 唯一关联 LangGraph checkpoint。
- `approval_task_events`（可选但建议）：分配、批准、拒绝事件的追加记录，包含操作者与时间；租户管理员的分配操作必须在同一租户内。
- After-sale 记录迁移：保留旧 `user_id` 原值为历史 actor；增加明确 `actor_id/customer_id`，写入新记录时当前身份从认证上下文得出。客服代办时 `actor_id=service user`、`customer_id=customer`；Customer 自助时 actor 与 customer 仍分开存，避免混淆。

建议授权查询一律形如 `WHERE resource.tenant_id = identity.tenant_id AND ...`，并在 Repository 接口传入不可由请求体构造的 `DemoIdentity`/授权上下文。Customer 需 customer_id 匹配；Service 需存在有效 grant；Approver 仅能通过分配任务读取必要订单字段；Admin 可管理同租户用户和任务分配，但订单查询仍须显式业务授权。

## 5. SQLite 权限 schema（实现参考；用户报告已在 WSL 迁移）

以下为实现采用的目标约束核心。`initialize_database()` 以幂等 DDL 创建新权限表，并用 `PRAGMA table_info` 检查后为旧 `aftersale_requests` 增加 `actor_id/customer_id` 两列；新增列没有批量回填。本会话只在临时测试库验证；用户报告已先备份并在 WSL 业务库执行迁移。

```sql
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS customers (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    customer_id TEXT NOT NULL,
    display_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    PRIMARY KEY (tenant_id, customer_id)
);

-- tenant_users 是 tenant/user 关系的权限事实来源；demo_users 暂保留兼容旧代码。
CREATE TABLE IF NOT EXISTS tenant_users (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('customer','service','approver','admin')),
    customer_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, user_id),
    FOREIGN KEY (tenant_id, user_id) REFERENCES demo_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, customer_id)
        REFERENCES customers(tenant_id, customer_id),
    CHECK ((role = 'customer' AND customer_id IS NOT NULL)
        OR (role <> 'customer' AND customer_id IS NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_demo_users_tenant_user
    ON demo_users(tenant_id, user_id);

CREATE TABLE IF NOT EXISTS service_customer_grants (
    tenant_id TEXT NOT NULL,
    service_user_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    granted_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, service_user_id, customer_id),
    FOREIGN KEY (tenant_id, service_user_id)
        REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, customer_id)
        REFERENCES customers(tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS order_customer_ownership (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    source TEXT NOT NULL CHECK (source IN ('sqlite','mock-shop')),
    store_id TEXT NOT NULL DEFAULT '',
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    PRIMARY KEY (tenant_id, source, store_id, order_id),
    FOREIGN KEY (tenant_id, customer_id)
        REFERENCES customers(tenant_id, customer_id)
);

CREATE TABLE IF NOT EXISTS approval_tasks (
    task_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    source TEXT NOT NULL CHECK (source IN ('sqlite','mock-shop')),
    store_id TEXT NOT NULL DEFAULT '',
    order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    approver_id TEXT NOT NULL,
    thread_id TEXT UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending','approved_demo','rejected','cancelled')),
    decision TEXT CHECK (decision IN ('approve','reject') OR decision IS NULL),
    decision_by TEXT,
    decision_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (tenant_id, customer_id)
        REFERENCES customers(tenant_id, customer_id),
    FOREIGN KEY (tenant_id, requester_id)
        REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, actor_id)
        REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, approver_id)
        REFERENCES tenant_users(tenant_id, user_id),
    FOREIGN KEY (tenant_id, decision_by)
        REFERENCES tenant_users(tenant_id, user_id),
    CHECK (requester_id <> approver_id AND actor_id <> approver_id)
);
CREATE INDEX IF NOT EXISTS idx_approval_tasks_assignee_status
    ON approval_tasks(tenant_id, approver_id, status, created_at);

CREATE TABLE IF NOT EXISTS approval_task_events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES approval_tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    actor_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('assigned','approved','rejected','cancelled')),
    created_at TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}'
);

-- 旧版 aftersale_requests 上由应用检查列是否存在后再分别执行：
-- ALTER TABLE aftersale_requests ADD COLUMN actor_id TEXT;
-- ALTER TABLE aftersale_requests ADD COLUMN customer_id TEXT;

COMMIT;
```

关键更新建议使用事务内比较并交换：

```sql
UPDATE approval_tasks
SET status = ?, decision = ?, decision_by = ?, decision_at = ?, updated_at = ?
WHERE task_id = ? AND tenant_id = ? AND approver_id = ?
  AND status = 'pending' AND requester_id <> ?;
```

必须检查 `changes() = 1`；0 行统一映射为不可见/非待处理/未分配，不应泄露其他租户任务是否存在。LangGraph 恢复前重新从认证上下文校验 `tenant_id + approver_id + pending`；checkpoint 中的 user/role 只作为业务历史，不作为授权凭据。SQLite 任务更新与 checkpoint 不是同一事务，落地时还需设计可重试的恢复标记/幂等决策，避免两库状态分叉。

### 迁移影响与回滚

- 新增 6 张权限表，并给 `aftersale_requests` 增加 2 个可空审计列；不删除或改写现有业务表，不批量回填历史订单/审批分配。
- 固定演示订单 1001 是应用代码创建的明确演示 fixture；应用在独立 ownership 表登记 `demo-a/customer-demo-a` 归属，不改 `orders.customer_id` 原字段。V1 导入订单保持未映射，对 Customer/Service 默认不可见。
- MockShop 固定 fixture 的店铺/客户/订单归属由演示 seed 明确登记；Service-A 的两个客户 grant 也仅为演示 seed。Admin 撤销 grant 后保留 `is_active=0`，不会因幂等 seed 重启而恢复。
- 新旧表并存期须保持旧接口兼容但拒绝旧宽权限入口；切换完成后再考虑移除旧实现，这不在本次提案中。
- 回滚（仅限迁移前备份数据库的恢复方案）：停止写入后恢复迁移前数据库备份。若只回滚新增空表，可按依赖逆序 `DROP TABLE approval_task_events; DROP TABLE approval_tasks; DROP TABLE order_customer_ownership; DROP TABLE service_customer_grants; DROP TABLE tenant_users; DROP TABLE customers;`。一旦写入授权/任务数据，DROP 会丢失新记录，不能作为无损回滚；需先导出新表数据并经审核。
- 现有本机/WSL 数据文件首次启动新版本时，应用会自动进行上述增量 schema 创建/列追加；部署前应备份数据库，并由用户通过已建立的 WSL 同步/验收流程执行。当前会话未启动 Compose、未同步 WSL，也未改业务数据库。

## 6. 已修改的代码入口

- `auth.py/config.py`：token 只映射可信主体，角色和客户归属从 SQLite membership 读取；支持 Customer/Service/Approver/Admin 固定虚构身份。
- `db.py`：增量权限 schema；SQL 订单读取按 tenant/customer/grant，AgentRun 按 tenant/user；售后记录拆分 requester/actor/customer；审批任务事务内校验租户、分配人、状态及自批边界。
- `main.py/schemas.py`：订单/售后/审批 API 接入身份授权；增加 Admin 用户角色读取/更新、服务客户授权管理、待审批任务重新分配和 Approver assigned-task list。
- `permissions.py/mock_shop.py/mock_shop_api.py/tools.py`：MockShop 增加最小 scope 元数据查询；应用和 Agent Tool 先检查 tenant/customer/grant，再读取详情、物流、资格、售后状态或写申请。
- `agent/state.py/nodes.py`：State 保留 user/tenant/role/customer；非 Customer/Service 不得启动审批申请，历史 checkpoint 恢复前由 API 使用当前 DB task assignee 重新鉴权。
- `.env.example`、README、`docs/demo_runbook.md`：补充固定演示角色和权限边界说明。
- `tests/test_api.py/test_db.py/test_ecommerce_api.py/test_mock_shop_integration.py/test_webhooks.py`：增加边界和回归；对旧假设作了窄修订，原因见第 8 节。

## 7. 测试计划

| 层 | 覆盖项 |
|---|---|
| Authentication/API | 缺 token、无效 token、伪造 user/tenant/role header/body、四角色的身份映射；伪造 `approver_id` 不生效。 |
| SQLite Repository | Customer 自有/他人/跨租户订单；Service 有 grant/无 grant/跨租户客户；AgentRun 所有者和授权管理范围；Repository 直接调用也无法绕过 tenant/customer 条件。 |
| After-sale | Customer 自助申请；Service 代办时 actor/customer 分离；Service 未授权客户被拒；客服不能审批；申请状态读取范围正确。 |
| Approval | assigned approver 可读/审批；其他 approver 和 requester 不可读/审批；自批拒绝；伪造 task/order/approver ID；pending 之外拒绝；重复请求和并发更新；非 Admin 重新分配拒绝。 |
| Admin | 同租户用户管理/任务分配成功；不可跨租户；Admin 不能因此查询所有订单；角色变更立即影响权限。 |
| LangGraph/AgentRun | API chat、Agent Node 和 Repository 入口使用同一身份语义；恢复旧 checkpoint 时按当前 token/任务 assignee 重验；不匹配不调用 `Command(resume=...)`。 |
| MockShop | 先做授权资源定位，再取订单详情；Customer 自己/他人订单；Service grant；Approver 只有任务所需字段；eligibility/logistics/create/status 每个入口重复授权；与 SQLite 对照同一权限矩阵。 |
| Webhook | 保持原 HMAC/store→tenant 派生，不采信 payload 中 tenant/user/role；不同 tenant/store 的冲突/状态 overlay 不能泄漏。 |
| 回归 | 保留并运行原有 105 项测试；若角色语义导致某断言需要更新，先标明旧假设和替代断言，不删测试。 |

## 8. 当前验证状态

- 审计依据：上一轮全量 pytest 105 passed / 17.99s；这是阶段 1 已记录结果，本轮未重跑测试。
- 本机完整 pytest：**115 passed / 20.29s**。MockShop/SQLite/API/Agent 与审批权限回归均在 pytest 临时测试数据库运行。
- 新增测试覆盖 Customer ownership、Service grant/revoke、租户管理员限制、伪造身份参数、MockShop 详情预检、审批任务分配、自批/非分配审批拒绝、重复及并发决定、旧 schema 增量加列且不回填、代客服 actor/customer 拆分。
- 原有测试没有删除；其中过时的权限期望已改为新规则：同租户 Approver 无任务时不能读店铺订单；Approver 不能自己发起待审批请求；无归属的历史导入订单不可被 Customer 读取。既有用例均包含在 115 passed 中。
- 用户报告已备份并迁移 WSL 持久数据库；`verify_phase6` 通过。`verify_v21` 曾发现旧记录新增的 `actor_id/customer_id` 为 NULL 时幂等校验报冲突，现已修复并补回归；用户随后报告修复已同步并重建；`verify_phase6` 与 `verify_v21` 全 PASS（EXIT=0），且 2026-11-18 的存量 NULL 审计字段重试返回同一申请。Phase 2 实机验收完成。
- 代码将本地固定演示 1001 映射到演示客户 A；V1 导入订单因 `customer_id` 缺失仍不可访问。新增用户凭据发放/真实认证不在 Demo 范围。
- 历史验收脚本最初仍期待审批人先创建任务后再收到 403；已改为断言 chat 返回 `approval_status=forbidden_role`。用户报告后续 phase6 与 V2.1 两套验收均全通过。

## 9. 实施注意项与剩余风险

- SQLite task 更新与 LangGraph checkpoint 恢复位于不同数据库，不能组成单一原子事务。审批先以 SQL 条件更新消费 pending 任务，再恢复 Graph；若 Graph 恢复进程级失败，任务可能已决定而 checkpoint 尚未完成，需要运维级检查/恢复策略。当前不执行真实资金操作。
- MockShop scope endpoint 仍由内部演示服务 key 保护，仅返回 order/store/customer 标识；读取详情、物流、资格和写入前会再次检查 caller scope。
- Demo Bearer token 是公开固定演示值，不具生产认证强度；权限代码演示 RBAC/tenant boundary，不代表生产级 IAM。
