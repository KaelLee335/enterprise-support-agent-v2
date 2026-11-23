# Phase 4 提案：SQLite 外部事件键与迁移版本

## 状态

Phase 3 已由用户于 2026-11-23 验收通过。Phase 4 实现提交 `d15d6f3` 已推送；本机 pytest **142 passed / 17.52s**，GitHub Actions run `45169866834` 成功。用户随后明确授权持久库迁移与部署：已在部署前创建并验证在线备份 `data/support_agent.db.bak-20261123-200521-pre-phase4`（完整性 `ok`、schema version 0），并将新版本部署至 WSL `/opt/project2`。三容器 healthy，`verify_phase6.sh` 与 `verify_v21.sh` 最终全 PASS。运行库完整性 `ok`、`user_version=1`，两张目标表主键均包含 platform/tenant/store。首次验收只发现脚本漏传 `store_id`；修复并同步后重跑通过。备份留在本地且不得提交/删除。

## 迁移前证据（历史快照）

- `src/support_agent/db.py` 中 `webhook_events` 的主键是 `(platform, event_id)`；`platform_order_states` 的主键是 `(platform, order_id)`。
- Webhook 状态 upsert、读取以平台和订单号定位；事件去重以平台和 event_id 定位。订单状态读取再附加 tenant 条件，但 store 未参与唯一键。
- `/webhooks/mock-shop/events/{event_id}` 目前只用当前 tenant 与 event_id 查询。若同一平台的 event ID 或 order ID 只在店铺范围唯一，多个店铺可能共享编号，旧键表达不了其身份边界。
- 当前数据库 `PRAGMA user_version=0`，代码以 `CREATE TABLE IF NOT EXISTS` 初始化，没有统一 schema 版本机制。
- 只读核验：当前库和 `support_agent.db.bak-20261122` 均 `PRAGMA integrity_check=ok`。备份为旧 schema，缺少权限相关表和售后 audit 列。没有读取具体业务行。
- 当前数据在旧主键约束下未发现可报告的跨租户/店铺重复；旧唯一键会阻止此类重复写入，所以该结果不能证明新键已经受过真实碰撞验证。

## 本地实现与临时库验收

- `SCHEMA_VERSION=1` 使用 SQLite `PRAGMA user_version`；新库直接创建目标键，旧版 version 0 库在事务内 rebuild 两张表、复制所有列/行、重建事件索引后更新版本。
- 老版本缺少的售后 `actor_id`、`customer_id` 列在同一版本事务中补齐；未知的未来 schema version 在执行建表脚本前拒绝初始化。
- 写入/去重/状态更新以 `(platform, tenant_id, store_id, event_id/order_id)` 精确限定；订单状态读取和事件回查也要求 tenant + store。
- 事件查询 API 增加必需 `store_id` 参数，并以当前认证 tenant 的后端 store 映射校验；缺少参数 422，错误租户/店铺隐藏为 404。
- 测试覆盖 v0 schema 行复制和结构升级、重复初始化幂等、迁移失败事务回滚、拒绝未来版本、同 tenant 不同 store 复用相同 event/order ID、重复 payload 幂等及冲突 payload 拒绝。

## 建议的数据身份键

- Webhook 去重：`(platform, tenant_id, store_id, event_id)`。
- 订单状态：`(platform, tenant_id, store_id, order_id)`。
- 事件回查接口也必须以可信当前身份和 store scope 查询；不能只按 event_id 返回记录。
- 状态更新、重复投递和 stale-event 检查应在新复合键的单一事务中完成。

## 实施前必须补的验证

1. 临时 SQLite 库迁移测试：旧 schema 迁移到新 schema，数据与索引保留，`user_version` 更新。
2. 同平台、不同店铺重复使用同一 `event_id` 和 `order_id`：彼此独立且状态不覆盖。
3. 同一店铺重复事件保持幂等；同一事件编号配不同签名 payload 仍返回冲突。
4. 事件查询只返回当前身份被授权的 store/tenant 记录。
5. 迁移失败时事务回滚；迁移重跑不会重复损坏数据。
6. 对旧数据库从只读备份副本执行升级演练，比较表行数、关键约束和完整性；不接触原备份或当前库。

## 已执行的持久库迁移

- 获得用户明确授权后，在 Compose 部署之前使用 SQLite 在线备份 API 生成时间戳备份，避免复制活动 WAL 数据库文件。
- 备份通过 `PRAGMA integrity_check=ok`，版本为 0；保留原文件，没有覆盖旧备份。
- 使用已建立的 WSL 部署脚本同步源码并重建服务。第一次脚本在 `verify_phase_v21` 发现验收脚本未传新的必需 `store_id` 参数；这是检查脚本兼容问题，不是服务迁移错误。已修复 `scripts/verify_v21.sh` 的跨店铺和所属店铺查询，再次同步并重跑完整流程。
- 最终验收：support-agent、mock-logistics、mock-shop 三容器均 healthy；Phase 6 与 V2.1 verifier 全 PASS；运行库 `integrity_check=ok`、`user_version=1`；webhook 与平台订单状态主键均包含平台、租户和店铺范围。
- 回滚时不能只把数据库文件直接替换回旧版本：须先停止写入并按 SQLite/WAL 备份流程恢复。若新版本已产生旧主键无法表达的重复身份，降级会丢失区分能力；需先审计并按新方案处理。当前没有执行回滚。

## 持久库迁移方案草案（历史方案，已执行）

SQLite 不能直接替换现存表的主键。获批后建议使用事务化 rebuild：建立临时新表、复制字段与记录、校验行数、替换旧表、重建索引，最后设置 schema version。迁移前在用户指定目录创建带时间戳备份；失败时事务回滚。回滚到旧主键前需检查新复合键下是否已产生旧键无法表达的重复项；若有重复，不能直接降级覆盖，应保留新 schema 并采取经用户确认的数据处置方案。

## 阶段边界

- Phase 4 持久迁移和 WSL 验收已完成；备份保留在本地，未纳入提交。
- 真实物流平台 API、真实客户数据和生产化不在本阶段范围内。
