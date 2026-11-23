# Phase 5：SQLite 迁移后置核验

## 目标

Phase 4 已完成真实 SQLite 迁移和 WSL 部署。本阶段把“容器健康”与“数据库迁移正确”分开核验，避免服务能启动但数据库结构未满足当前代码预期时仍被误判为通过。

## 流程

```text
更新 WSL 源码并重建容器
          │
          ├─ health 200 + support-agent healthy
          │
          ├─ SQLite 只读检查
          │    ├─ integrity_check = ok
          │    ├─ user_version = 当前代码 SCHEMA_VERSION
          │    └─ webhook / order-state 主键含 platform + tenant + store
          │
          └─ RAG smoke + Phase 6 + V2.1 业务验收
```

## 实现

- `scripts/update_wsl_and_verify.sh` 在服务健康后通过容器内项目虚拟环境读取配置中的真实数据库路径。
- SQLite 以只读 URI 打开，不创建或修改文件；检查完整性、版本号和两张表的主键列及顺序。
- 任一项不符合即因断言失败终止后续验收，不会继续报告部署成功。
- GitHub Actions 增加 `bash -n scripts/*.sh`，在合并前检查 shell 脚本语法。

## 验证结果（2026-11-23）

- 本机 WSL 更新流程再次运行成功。检查输出：`integrity_check=ok`、schema version 1、两张主键均符合预期。
- 三个 Compose 容器 healthy；health 200；RAG 冲突/例外/复合检索 smoke 通过；Phase 6 与 V2.1 verifier 全通过。
- `bash -n scripts/update_wsl_and_verify.sh` 通过。
- 这是只读数据库核验，没有重新迁移、回滚或修改业务记录。迁移前在线备份继续保留且不得提交。

## 需要掌握的概念

- 容器 `healthy` 只说明健康检查定义的服务条件成立，不自动证明数据库 schema 正确。
- SQLite `PRAGMA user_version` 是应用管理的版本标记；所以还要核对真实主键，避免版本号与结构意外不一致。
- 只读连接与 `integrity_check` 用于上线后验收；迁移仍由应用启动时的事务化迁移逻辑负责。

## 状态

本阶段实现、WSL 验收与仓库 CI 均完成。提交 `20e954e` 的 GitHub Actions run `45180300306` 成功。
