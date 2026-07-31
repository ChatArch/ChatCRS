# ChatCRS

ChatCRS 是 ChatArch 的 CRS 运维与验收 CLI。它把“查看状态、验证路由、管理隔离调试服务、规划切流”做成结构化命令，并把危险操作设计为显式 opt-in。

## 安全原则

- 查看类命令返回 `mutated=false`。
- 调试服务写操作默认只输出计划，必须加 `--execute`。
- 新增写操作固定绑定 `127.0.0.1:12392`、Redis `127.0.0.1:6382/0` 和 tmux `crs-debug-12392`。
- `HOST`、`PORT`、`REDIS_*`、JWT 和加密字段不能通过 settings 命令修改。
- API key 只从 env 文件读取，不进入命令行和 JSON 输出。
- 生产切换仍采用独立、经过审核的 dry-run 流程；ChatCRS 当前不直接执行生产切流。

## 三类目标

| 入口 | 默认 URL | 用途 |
|---|---|---|
| `chatcrs` / `chatcrs-debug` | `http://127.0.0.1:12392` | 调试服务日常管理 |
| `chatcrs-candidate` | `http://127.0.0.1:12391` | 候选服务只读验证 |
| `chatcrs-production` | `http://127.0.0.1:12390` | 生产只读健康/验收 |

## 快速检查

```bash
chatcrs debug status --json-output
chatcrs debug restart --json-output
chatcrs debug settings show --json-output
chatcrs debug upgrade plan --json-output
```

第二条是 restart **计划**，没有 `--execute` 时不会重启。

下一步：阅读 [CLI 命令树](cli.md) 和 [调试服务管理](debug-service.md)。
