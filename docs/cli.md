# CLI 命令树

此页只列出 **当前已经在 `chatcrs.cli` 中注册的命令**。运行 `chatcrs --tree` 可从 Click 注册表回读同一棵树；新增或删除命令必须同步本页。

## 顶层命令

```text
chatcrs  # CRS HTTP/API helpers plus server-local service commands for ChatArch.
├── --help  # Show this help message.
├── --version  # Show the installed package version.
├── --tree  # Print the registered command tree.
├── health [--base-url <BASE-URL>] [--json-output]  # Verify the CRS /health endpoint.
├── admin  # Remote CRS administrator operations via HTTPS Admin API.
│   ├── login [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--save-token] [--json-output]  # Verify CRS admin login without printing the session token.
│   ├── token  # Manage cached CRS admin session tokens in the ChatArch token store.
│   │   ├── status [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--json-output]  # Show cached CRS admin token metadata without printing the token.
│   │   ├── refresh [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--json-output]  # Login and save a fresh CRS admin session token.
│   │   └── clear [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Clear the cached CRS admin session token.
│   ├── accounts  # Inspect or refresh remote CRS account state via HTTP Admin API.
│   │   ├── usage [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--json-output]  # List OpenAI/Codex account usage and scheduling metadata.
│   │   └── refresh-status <ACCOUNT-ID> [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Reset a CRS OpenAI account status after transient failures.
│   └── keys  # Inspect remote CRS API keys with admin privileges.
│       ├── list [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--include-stats] [--time-range <TIME-RANGE>] [--json-output]  # List CRS API key metadata, optionally including usage stats.
│       └── show <KEY-ID> [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--include-stats/--no-include-stats] [--time-range <TIME-RANGE>] [--json-output]  # Show one CRS API key by id or name.
├── key  # CRS API-key-only operations that do not require admin login.
│   └── info [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--timeout <TIMEOUT>] [--path <INFO-PATH>] [--json-output]  # Query CRS key-info using only a CRS API key.
├── codex  # Direct OpenAI Codex account token and usage helpers.
│   ├── token  # Manage OpenAI OAuth tokens through the ChatEnv OpenAI token store.
│   │   ├── status [--profile <PROFILE>] [--json-output]  # Show cached OpenAI OAuth token metadata without printing tokens.
│   │   └── refresh [--profile <PROFILE>] [--refresh-token <REFRESH-TOKEN>] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Refresh an OpenAI OAuth access token without printing token values.
│   ├── account [--profile <PROFILE>] [--access-token <ACCESS-TOKEN>] [--refresh/--no-refresh] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Read OpenAI Codex account metadata directly from OpenAI.
│   └── usage [--profile <PROFILE>] [--account-id <ACCOUNT-ID>] [--access-token <ACCESS-TOKEN>] [--refresh/--no-refresh] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Read Codex usage and quota metadata directly from OpenAI.
└── service  # Local CRS service lifecycle commands for the current server.
    ├── install [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs install` on this server.
    ├── update [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs update` on this server.
    ├── start [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs start` on this server.
    ├── stop [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs stop` on this server.
    ├── restart [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs restart` on this server.
    ├── status [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--json-output]  # Execute local `crs status` on this server.
    ├── switch-branch <BRANCH> [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs switch-branch <branch>` on this server.
    └── update-pricing [--app-dir <APP-DIR>] [--crs-command <CRS-COMMAND>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Plan or execute local `crs update-pricing` on this server.
```

## 覆盖矩阵

| 能力 | 已实现命令 | 边界 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 HTTP health 摘要 |
| 管理员登录 | `chatcrs admin login` | HTTP 登录验证，只报告 token 是否存在，不打印 token；`--save-token` 可写入 runtime token store |
| Admin token cache | `chatcrs admin token status`, `chatcrs admin token refresh`, `chatcrs admin token clear` | 管理 `~/.chatarch/tokens/CRS/<profile>.json` 中的短期 Admin session token；`chatcrs admin token refresh` 是 ChatCRS 本地命令，安装 ChatCRS 后也可用 `chatenv token refresh CRS <profile>` 走同一 provider；状态输出不打印 token |
| 账号 usage | `chatcrs admin accounts usage` | Admin HTTP API；脱敏 usage/status/scheduling 摘要 |
| 账号状态 reset | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status；不是 OAuth refresh-token 强刷 |
| API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | key 值脱敏，返回状态、限制、统计和 last-usage 摘要 |
| 普通 API key 自查 | `chatcrs key info` | 不需要管理员登录 |
| OpenAI/Codex direct token/account/usage | `chatcrs codex token ...`, `chatcrs codex account`, `chatcrs codex usage` | 直接调用 OpenAI/Codex OAuth 与 backend API；输出只包含脱敏 token 状态、account 摘要、usage/quota header 摘要 |
| 本机 service lifecycle | `chatcrs service ...` | 只在 CRS 服务器本机执行本机 `crs` 命令；外部管理必须走 HTTP/Admin API 或新增服务端 API/agent |

## 注册命令清单

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs admin login` | Admin login verification |
| `chatcrs admin token status` | Cached Admin session token metadata |
| `chatcrs admin token refresh` | Login and save a fresh Admin session token |
| `chatcrs admin token clear` | Dry-run or delete cached Admin session token |
| `chatcrs admin accounts usage` | Account usage inspection |
| `chatcrs admin accounts refresh-status` | CRS account reset-status |
| `chatcrs admin keys list` | API key list and statistics |
| `chatcrs admin keys show` | Single API key summary |
| `chatcrs key info` | API-key-only self check |
| `chatcrs codex token status` | Cached OpenAI OAuth token metadata |
| `chatcrs codex token refresh` | Refresh an OpenAI access token; prefer `chatenv token refresh OpenAI <profile>` |
| `chatcrs codex account` | Direct OpenAI Codex account metadata inspection |
| `chatcrs codex usage` | Direct Codex usage and quota inspection |
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
chatcrs admin login --profile admin --save-token --json-output
chatcrs admin token status --profile admin --json-output
chatcrs admin token refresh --profile admin --json-output
chatcrs admin token clear --profile admin --json-output
chatcrs admin token clear --profile admin --execute --json-output
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

## Codex direct { #codex-direct }

```bash
chatcrs codex token status --profile default --json-output
chatcrs codex token refresh --profile default --json-output
chatenv token refresh OpenAI default
chatcrs codex account --profile default --json-output
chatcrs codex usage --profile default --json-output
```

`codex` 分支直接调用 OpenAI/Codex OAuth 与 backend API，不经过 CRS Admin API。稳定 OAuth profile 使用 ChatEnv 内置 `OpenAI` namespace（`envs/OpenAI/<profile>.env`），runtime access/refresh token 使用同一 `OpenAI` token store（`tokens/OpenAI/<profile>.json`）。如果 token-store values 中保存了非 secret `account_id` 映射，`chatcrs codex usage --profile <profile>` 会优先用它查询 quota；没有映射时才退回 OpenAI accounts API 自动解析唯一账号。持久刷新应运行 `chatenv token refresh OpenAI <profile>`；`chatcrs codex ...` 只消费该状态并输出脱敏 token/account/usage 摘要，不打印 access token、refresh token 或 id token。

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
- Env profile 保存稳定配置；短期 Admin session token 默认写入 `~/.chatarch/tokens/CRS/<profile>.json`，不再频繁改 Env 文件。
- API key、token、password、OAuth 凭据不得进入聊天、文档、PR body 或命令输出。
