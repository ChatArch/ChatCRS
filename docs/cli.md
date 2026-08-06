# CLI 命令树

此页只列出 **当前已经在 `chatcrs.cli` 中注册的命令**。命令树由测试从 Click 注册表回读；新增或删除命令必须同步本页。

## 顶层命令

```text
chatcrs                                           # CRS HTTP/API-first + server-local management CLI
├── health                                        # 检查选定 CRS /health endpoint
├── admin                                         # 远程 CRS Admin HTTP API 操作
│   ├── login                                     # 验证管理员登录，不打印 session token
│   ├── accounts                                  # 查询或刷新 OpenAI/Codex 账号状态
│   │   ├── usage                                 # usage、调度、可用性摘要
│   │   └── refresh-status                        # 默认 dry-run；--execute 才调用 reset-status
│   └── keys                                      # 查询 CRS API key 元数据与统计
│       ├── list                                  # 列表；可选 batch stats / last-usage
│       └── show                                  # 按 id/name 返回单个 key 的安全摘要
├── key                                           # 普通 CRS API key 自查
│   └── info                                      # 当前 key 的信息、可用性和 usage
└── service                                       # 只在 CRS 服务器本机运行的 service 命令
    ├── install                                   # 默认 dry-run；--execute 才运行本机 crs install
    ├── update                                    # 默认 dry-run；--execute 才运行本机 crs update
    ├── start                                     # 默认 dry-run；--execute 才运行本机 crs start
    ├── stop                                      # 默认 dry-run；--execute 才运行本机 crs stop
    ├── restart                                   # 默认 dry-run；--execute 才运行本机 crs restart
    ├── status                                    # 直接运行本机 crs status，只读
    ├── switch-branch                             # 默认 dry-run；--execute 才运行本机 crs switch-branch
    └── update-pricing                            # 默认 dry-run；--execute 才运行本机 crs update-pricing
```

## 覆盖矩阵

| 能力 | 已实现命令 | 边界 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 HTTP health 摘要 |
| 管理员登录 | `chatcrs admin login` | HTTP 登录验证，只报告 token 是否存在，不打印 token |
| 账号 usage | `chatcrs admin accounts usage` | Admin HTTP API；脱敏 usage/status/scheduling 摘要 |
| 账号状态 reset | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status；不是 OAuth refresh-token 强刷 |
| API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | key 值脱敏，返回状态、限制、统计和 last-usage 摘要 |
| 普通 API key 自查 | `chatcrs key info` | 不需要管理员登录 |
| 本机 service lifecycle | `chatcrs service ...` | 只在 CRS 服务器本机执行本机 `crs` 命令；外部管理必须走 HTTP/Admin API 或新增服务端 API/agent |

## 注册命令清单

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs admin login` | Admin login verification |
| `chatcrs admin accounts usage` | Account usage inspection |
| `chatcrs admin accounts refresh-status` | CRS account reset-status |
| `chatcrs admin keys list` | API key list and statistics |
| `chatcrs admin keys show` | Single API key summary |
| `chatcrs key info` | API-key-only self check |
| `chatcrs service install` | Local CRS install command plan/execute |
| `chatcrs service update` | Local CRS update command plan/execute |
| `chatcrs service start` | Local CRS start command plan/execute |
| `chatcrs service stop` | Local CRS stop command plan/execute |
| `chatcrs service restart` | Local CRS restart command plan/execute |
| `chatcrs service status` | Local CRS status command |
| `chatcrs service switch-branch` | Local CRS branch switch command plan/execute |
| `chatcrs service update-pricing` | Local CRS pricing update command plan/execute |

## 远程管理员与 API key { #remote-admin-and-api-key }

```bash
chatcrs admin login --profile admin --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --execute --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --profile admin --json-output
```

!!! warning "refresh-status 的含义"
    `refresh-status` 重置 CRS 账号状态。它不会强制刷新 Codex/OpenAI OAuth refresh token。

## API-key-only { #api-key-only }

```bash
chatcrs key info --profile admin --json-output
chatcrs key info --profile admin --path /openai/key-info --json-output
```

## Server-local service { #server-local-service }

`chatcrs service ...` 是 server-local surface：它假设命令已经安装并运行在 CRS 服务器本机 shell 里，操作当前机器上的 CRS checkout / Node runtime / `crs` executable。

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --execute --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

规则：

- `status` 是只读命令，默认直接执行本机 `crs status`。
- `install`、`update`、`start`、`stop`、`restart`、`switch-branch`、`update-pricing` 默认只输出 plan；必须加 `--execute` 才执行。
- 目标只来自当前工作目录或显式 `--app-dir`；`--crs-command` 只指定本机 executable。
- 如果操作者在服务器外部，普通管理只能用 `chatcrs admin ...` / `chatcrs key ...` 的 HTTP/Admin API。没有 HTTP 接口的 lifecycle 能力不能用远端执行补洞，应新增 CRS API/agent 或到服务器本机运行本命令。

## 当前不注册的花哨/任务型能力 { #removed-task-surfaces }

以下类别继续不注册：

- local verify / sidecar verify；
- Images acceptance；
- debug runtime；
- Nginx plan-cutover；
- formal cutover precheck；
- fixed-topology inspect。

这些属于专项验收、debug runtime、edge/cutover runbook 或代理站任务，不属于当前 ChatCRS 核心管理 CLI。

## Safety boundaries { #safety-boundaries }

- 外部 CRS 管理面是 HTTP/Admin API。
- 本机 service 面只能在 CRS 服务器本机执行，不维护远程服务器。
- 任何生产写操作仍必须显式 `--execute`，并且要先确认目标、回滚边界和脱敏输出。
- API key、token、password、OAuth 凭据不得进入聊天、文档、PR body 或命令输出。
