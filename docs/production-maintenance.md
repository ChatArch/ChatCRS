# 生产维护

## 当前只读能力

```bash
chatcrs-production health --json-output
chatcrs inspect --json-output
chatcrs verify sidecar --json-output
chatcrs nginx plan-cutover --json-output
chatcrs cutover precheck --json-output
```

这些命令不修改 Nginx、不 reload、不停服务。

## 不要直接使用上游 `crs update`

当前主机有 12390、12391、12392 三个 Node CRS。上游单实例管理脚本包含全局进程匹配，可能影响多个实例，也只更新官方 `main`，不理解 ChatArch `dev` 和 Nginx slot。

## Production switch

生产更新目前使用独立任务中的 guarded script。默认只 dry-run，实际执行要求：

- exact reviewed ChatArch `dev` SHA；
- public-domain confirmation；
- Redis snapshot；
- candidate health/model smoke；
- Nginx backup/test/reload；
- automatic rollback；
- 12390 保持运行。

在 execute 流程完成一次受控验证和代码评审前，不将生产写操作暴露为 `chatcrs` 子命令。

## 带宽事件

高流量排查应优先使用 Nginx `body_bytes_sent`、route/client 聚合和 Redis per-key usage。不要根据日志大小误判公网带宽；stdout 日志膨胀是磁盘风险，不等于网络出流量。
