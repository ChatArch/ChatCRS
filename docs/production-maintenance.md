# 生产维护

## 当前包内能力

```bash
chatcrs health --base-url https://crs.example.com --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
```

这些入口只通过 CRS HTTP/API 工作。它们不会写 Nginx、不 reload、不停服务、不读取部署目录。

## 当前不注册的服务端本机能力

以下能力可能有用，但当前 RESTful/Admin API 没有对应 endpoint，且通常需要服务端本机权限：

- service install/update/start/stop/restart/status；
- branch switching 或 pricing data update；
- process/port/topology/edge doctor；
- Redis snapshot/keyspace inventory；
- release/cutover/rollback orchestration。

这些能力后续若要加回，应先设计明确的 server-local/host-agent 边界、权限模型、审计产物和测试，而不是混入当前 HTTP 管理 CLI。

## 不要直接使用上游 `crs update`

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
