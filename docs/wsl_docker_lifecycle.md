# WSL Docker 生命周期

## 当前运行方式

项目使用 WSL 中的 Docker daemon 运行。用户确认，当前由 Windows 用户登录触发的启动方式符合预期，应保留现状。此前用户报告：WSL 发行版停止后，手动触发启动任务可以使 daemon 就绪、项目容器恢复为 healthy，健康接口返回 HTTP 200。该结果验证的是任务触发恢复链路，不代表完整 Windows 重启后的自动恢复已经验证。

用户后续报告 WSL 重启后容器网络曾因私有网段冲突而异常；用户自行调整 Docker daemon 网桥配置并增加网络就绪等待后，重建容器，health 返回 200，阶段 6 验收脚本 11/11 通过。以上为用户提供的主机验收结果，本会话未独立检查或修改主机配置。公开项目文档不保存本机账户、目录、脚本路径或具体网段。

## 只读检查建议

在用户平时运行项目的 WSL 环境中，可使用以下命令查看 daemon 与容器状态：

```bash
docker info --format 'Docker server: {{.ServerVersion}}'
pgrep -a dockerd || true
systemctl is-active docker 2>/dev/null || true
systemctl is-enabled docker 2>/dev/null || true
docker compose ps
```

- `docker info` 成功表示 Docker CLI 当前能连接 daemon。
- `pgrep` 有进程但 systemd 未报告 active，表示 daemon 可能由其他启动方式管理；应先确认其来源。
- Compose 的重启策略只在 daemon 已运行时影响容器，不能启动已停止的 daemon。
- 不要为常规验收而关闭当前 daemon、启动第二个 daemon、启用另一套服务或重启 WSL。

## 自动启动边界

当前用户登录触发方式是用户确认保留的设置。它不承诺用户登录前即可用；完整 Windows 重启后的行为仍未验收。若未来确需改变启动时机，应先确认目标和运行账户，再单独处理主机设置。