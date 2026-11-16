# 快速执行模式：当前交接步骤

更新时间：2026-11-16

## 当前状态

本地 Windows 执行通道在只读检查时返回 `setup refresh had errors`。本次无法重新读取 Git 状态、执行完整测试或确认当前未提交改动清单。因此不要把这些改动同步到 WSL，也不要据此重建容器。

最近一次可确认的定向测试记录为 `tests/test_api.py` 与 `tests/test_db.py` 共 26 项通过；这不等同于完整测试通过，也不代表 WSL 部署已验收。

## 你现在只需做

1. 重新打开 Codex 项目 `D:\project_2`，确保终端/执行功能可用。
2. 回到当前对话回复“继续”。不需要改 Docker、WSL、网络适配器、计划任务或项目配置。

## 执行通道恢复后的自动步骤

1. 检查 `git status`、完整差异和 `.env`/运行数据忽略规则；不输出任何密钥值。
2. 检查 API 身份映射、租户隔离、运行记录和异常处理；补齐必要的故障用例。
3. 运行全量 pytest 和差异格式检查；失败则修复并重跑。
4. 更新 `AGENTS.md`、`task_plan.md`、`progress.md`、`findings.md`、`docs/project_status.md` 及中文学习文档，记录真实测试结果。
5. 提供精确的 WSL 同步文件清单与重建/验收命令。只同步核实过的项目文件，保留 D 盘数据和本机 `.env`。
6. 由用户在 WSL 完成同步、Docker 重建与验收；在得到结果前不标记部署完成。

## 后续 WSL 验收命令（届时按核对后的文件清单执行）

```bash
cd /opt/project2
docker compose up --build -d
docker compose ps
curl -fsS http://localhost:8000/health
bash scripts/verify_phase6.sh
```

若 API 使用可配置的演示令牌，按项目 `.env` 中的本机配置调用验收脚本；不要把令牌发到聊天或提交到 Git。
