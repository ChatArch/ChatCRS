# 调试服务管理

## 固定安全边界

`chatcrs debug` 只管理：

- app：`/home/zhihong/claude-relay-service-independent/app`
- HTTP：`127.0.0.1:12392`
- Redis：`127.0.0.1:6382 DB0`
- tmux：`crs-debug-12392`

CLI 不提供覆盖这些路径和端口的选项。执行写操作前还会再次读取 `.env`，任何 isolation mismatch 都会拒绝。

## Status

```bash
chatcrs debug status --json-output
```

返回 health、tmux、Redis PING、Git、版本和非敏感 settings。Redis 密码只通过子进程环境 `REDISCLI_AUTH` 传递。

## Logs

```bash
chatcrs debug logs --lines 100
chatcrs debug logs --lines 100 --json-output
```

输出经过凭据过滤。日志仍可能包含请求元数据，应当视为运维敏感信息。

## Restart

Dry-run：

```bash
chatcrs debug restart --json-output
```

执行：

```bash
chatcrs debug restart --execute --json-output
```

执行路径只 kill/create 固定 tmux session，然后等待 `/health` HTTP 200。不会操作 debug Redis session，更不会使用全局 `pkill`。

## Settings

查看可修改和 protected 字段：

```bash
chatcrs debug settings show --json-output
```

计划修改：

```bash
chatcrs debug settings set LOG_LEVEL info --json-output
```

执行修改：

```bash
chatcrs debug settings set LOG_LEVEL info --execute --json-output
```

允许字段：

- `LOG_LEVEL`
- `ENABLE_CORS`
- `TRUST_PROXY`
- `OPENAI_IMAGES_HOST_MODEL`
- `REQUEST_MAX_SIZE_MB`
- `WEB_TITLE`
- `WEB_DESCRIPTION`

执行时先备份 `.env`，原子写入，然后重启 debug 并验证 health。失败时恢复 `.env` 并尝试恢复启动。

## Upgrade

只读计划：

```bash
chatcrs debug upgrade plan --json-output
```

计划会比较当前 SHA/tree、local `origin/dev` 和 remote `dev`。如果当前 tree 已一致，不需要升级。

显式执行：

```bash
chatcrs debug upgrade apply \
  --expected-sha <40-character-reviewed-sha> \
  --execute \
  --json-output
```

执行要求：

- 固定 debug isolation guard 通过；
- worktree clean；
- remote `dev` 与 expected SHA 完全一致；
- 旧 SHA 和 `.env` 已记录/备份。

升级失败时切回旧 SHA、恢复 `.env` 并重启 debug。生产和 sidecar 不在该代码路径中。
