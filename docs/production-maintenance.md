# 生产维护

## 当前包内能力

```bash
chatcrs health --base-url https://crs.example.com --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
```

前 3 类入口只通过 CRS HTTP/Admin API 工作。`chatcrs service ...` 是 server-local：它要求命令已经安装在 CRS 服务器本机，并且只操作本机 checkout / Node runtime / `crs` executable。

## 外部管理与本机 service 的边界

- 如果人在服务器外部，普通管理只能走 CRS HTTP/Admin API。
- 如果 CRS 没有 restart/update/status 等 HTTP lifecycle endpoint，不用远端执行补洞。
- 需要远程 lifecycle 时，应新增 CRS HTTP/Admin endpoint 或受限 host-agent。
- 已经进入目标 CRS 服务器 shell 时，可以运行 `chatcrs service ...` 管理本机服务。

## Service mutation 默认 dry-run

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service restart --app-dir /path/to/crs --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

`status` 是只读，默认执行本机 `crs status`。`install/update/start/stop/restart/switch-branch/update-pricing` 默认只输出 plan；必须显式 `--execute` 才执行。

## 继续不属于当前包内 surface 的任务

以下能力继续不作为 ChatCRS 核心 CLI 暴露：

- Images / image capability acceptance；
- debug runtime；
- topology/doctor/edge inspection；
- Redis snapshot/keyspace inventory；
- Nginx plan-cutover；
- release/cutover/rollback orchestration。

这些能力属于代理站维护、专项验收、运维 runbook 或未来明确 scoped 的 host-agent/API 设计。

## 不要直接使用上游 `crs update` 做生产切流

多实例 CRS 主机上可能同时存在生产、候选和调试进程。上游单实例管理脚本可能包含宽泛进程匹配，只理解官方分支，不理解 ChatArch 维护线、slot 或 edge 路由。生产更新应优先走受控 release/cutover runbook。

## Production switch

生产更新目前使用独立任务中的 guarded script。默认只 dry-run，实际执行要求：

- exact reviewed ChatArch `dev` SHA；
- public-domain confirmation；
- Redis snapshot；
- candidate health/model smoke；
- edge config backup/test/reload；
- automatic rollback；
- 当前生产 slot 保持可回滚。

在 execute 流程完成一次受控验证和代码评审前，不将生产切流写操作暴露为 `chatcrs` 子命令。

## 带宽事件

高流量排查应优先使用 Nginx `body_bytes_sent`、route/client 聚合和 Redis per-key usage。不要根据日志大小误判公网带宽；stdout 日志膨胀是磁盘风险，不等于网络出流量。
