# WSL Docker daemon 生命周期

## 当前已知状态

WSL Docker 容器功能验收已通过；最新只读检查结果为 `pgrep -a dockerd` 显示 PID 11、`systemctl is-active docker` 为空、`systemctl is-enabled docker` 为 `enabled`。这表示 daemon 当前存活，但当前 WSL 会话没有通过 systemd 报告其为 active；仅有 `enabled` 标记不能证明 systemd 正在管理服务或重启后会自动恢复。现有证据仍指向 daemon 由 `inbox` WSL 会话持有。

用户随后提供的实测截图补充了恢复证据：`wsl -l -v` 显示 Ubuntu 为 `Stopped`；触发 `Start-ScheduledTask` 后日志显示 `dockerd ready`，`pgrep dockerd` 有进程，`docker ps` 显示 `project2-support-agent-1` 为 `Up (healthy)`，`/health` 返回 200。这证明该计划任务可在 Ubuntu 已停止时启动 Docker 并恢复项目服务。

## 2026-11-16 计划任务只读检查

本机任务 `\\WSL-Dockerd-Autostart` 的动作是 `wsl.exe -d Ubuntu -u root -- /usr/local/bin/start-dockerd.sh`。任务当前由 `LAPTOP-08OK88SN\\17488` 交互式账户运行，触发器为已启用的 Logon（用户登录），运行级别 Limited；任务状态为 Running。最近一次运行时间为 2026-11-16 09:58:58，结果代码 267009。

这确认了用户登录触发，不代表 Windows 启动时或用户登录前会触发。此次只读取任务属性，没有运行任务、停止 daemon、修改计划任务、改 WSL/systemd 或调整虚拟网卡。若需要登录前开机自启，应先明确运行账户和后台运行需求，再单独批准并实施任务变更。

尚未验证 Windows 完整重启后的触发行为（例如计划任务是否配置为开机触发、用户未登录时能否运行）。若 Windows 重启后服务不可用，再检查任务触发条件和任务历史。不要为验证而关闭当前 daemon。

项目 Compose 的 `restart: unless-stopped` 只定义 Docker daemon 仍运行时容器的重启策略；它不能启动已停止的 `dockerd`。

## 只读检查

在运行 `/opt/project2` 的 WSL 发行版中执行：

```bash
docker info --format 'Docker server: {{.ServerVersion}}'
pgrep -a dockerd || true
systemctl is-active docker 2>/dev/null || true
systemctl is-enabled docker 2>/dev/null || true
```

解释结果：

- `docker info` 成功表示当前 CLI 能连上 daemon。
- `pgrep` 有进程但 `systemctl` 不是 `active`，通常说明 daemon 是手动启动的；需确认它由哪个 shell/脚本持有。
- `systemctl is-active` 为 `active` 且 `is-enabled` 为 `enabled`，说明 Docker systemd 服务正在运行并配置为发行版启动时启动。
- `is-active` 为空而 `is-enabled` 为 `enabled` 时，不能据此认定 Docker systemd 服务当前运行；`enabled` 只表示单元的启用标记。还需确认发行版是否以 systemd 为 PID 1 及当前 daemon 的启动者。
- 如果发行版没有启用 systemd，不要直接执行 `systemctl enable`；先确认 WSL 的 systemd 设置和启动方式。

如果 `dockerd` 在名为 `inbox` 的发行版中启动，应在该发行版里运行 `pgrep`/`systemctl` 检查，而不只是从运行项目的发行版检查。用户本次报告的 `Start-ScheduledTask` 结果已验证 Ubuntu 停止状态到服务 healthy 的恢复链路；这不是 Windows 重启测试。不要为验证而关闭当前 daemon 会话；只读取进程和服务状态即可。

## 自动启动前的安全边界

当前由会话启动的 daemon 可能与 systemd Docker 服务使用同一个 socket/数据目录。不要在旧 daemon 未停止时再启动第二个 `dockerd` 或直接启用另一套服务，以免 socket/数据目录冲突。先确定当前启动命令和 systemd 状态，再决定是否迁移为 systemd 管理。

目前没有为本机自动启用 systemd 或改写 WSL 启动配置。WSL 的 systemd 需要在 `/etc/wsl.conf` 中配置并重启发行版；即使使用 systemd，服务也不会让 WSL 发行版在 Windows 退出后持续运行。参见 [Microsoft WSL systemd 指南](https://learn.microsoft.com/en-us/windows/wsl/systemd) 和 [WSL 高级设置](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)。项目 Docker 功能验收及“Ubuntu 停止 → 触发计划任务 → Docker/容器恢复”已通过；Windows 完整重启后的自动触发尚未验收。
