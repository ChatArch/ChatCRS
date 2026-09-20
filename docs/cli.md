# CLI 命令树

此页只列出 **当前已经在 `chatcrs.cli` 中注册的命令**。`chatcrs --tree` 回读带参数签名的树，`chatcrs --tree-brief` 回读省略签名但保留节点和描述的树；两者都使用 canonical 根名 `chatcrs`。新增或删除命令必须同步本页。

## 顶层命令

```text
chatcrs
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── admin  # Remote CRS administrator operations via HTTPS Admin API.
│   ├── accounts  # Inspect or refresh remote CRS account state via HTTP Admin API.
│   │   ├── codex  # CRS 托管 Codex 账号；需原生 Admin 接口。
│   │   │   ├── consume [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output] [--request-id REQUEST-ID] [--credit-id CREDIT-ID] [--execute]  # 默认本地计划；显式执行消费，不自动重放。
│   │   │   ├── credits [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output]  # 只读查询重置卡，不消费。
│   │   │   ├── operation [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output] [--request-id REQUEST-ID]  # 读取历史回执；待定或未知状态退出非零。
│   │   │   └── usage [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output]  # 读取固定账号的实时上游额度；不是缓存统计。
│   │   ├── refresh-status [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] <ACCOUNT-ID> [--execute] [--json-output]  # Reset a CRS OpenAI account status after transient failures.
│   │   └── usage [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # List OpenAI/Codex account usage and scheduling metadata.
│   ├── keys  # Inspect remote CRS API keys with admin privileges.
│   │   ├── list [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--include-stats] [--time-range TIME-RANGE] [--json-output]  # List CRS API key metadata, optionally including usage stats.
│   │   └── show [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] <KEY-ID> [--include-stats] [--time-range TIME-RANGE] [--json-output]  # Show one CRS API key by id or name.
│   ├── login [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--save-token] [--json-output]  # Verify CRS admin login without printing the session token.
│   └── token  # Manage cached CRS admin session tokens in the ChatArch token store.
│       ├── clear [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--execute] [--json-output]  # Clear the cached CRS admin session token.
│       ├── refresh [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # Login and save a fresh CRS admin session token.
│       └── status [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # Show cached CRS admin token metadata without printing the token.
├── codex  # Direct OpenAI Codex account token and usage helpers.
│   ├── account [--profile PROFILE] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Read a safe OpenAI Codex account summary from token claims and API probe.
│   ├── quota [--profile PROFILE] [--account-id ACCOUNT-ID] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--model MODEL] [--timeout TIMEOUT] [--json-output]  # Run a profile-only Codex responses smoke and show quota headers.
│   ├── reset  # Inspect or explicitly redeem banked Codex resets without model requests.
│   │   ├── consume [--json-output] [--timeout TIMEOUT] [--base-url BASE-URL] [--profile PROFILE] [--request-id REQUEST-ID] [--execute]  # Plan or redeem one reset with a persisted receipt and GET readback.
│   │   └── list [--json-output] [--timeout TIMEOUT] [--base-url BASE-URL] [--profile PROFILE]  # Read reset count and expirations; renew profile credentials when required.
│   ├── token  # Manage OpenAI OAuth tokens through the ChatEnv Codex token store.
│   │   ├── refresh [--profile PROFILE] [--refresh-token REFRESH-TOKEN] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Refresh an OpenAI OAuth access token without printing token values.
│   │   └── status [--profile PROFILE] [--json-output]  # Show cached OpenAI OAuth token metadata without printing tokens.
│   └── usage [--profile PROFILE] [--account-id ACCOUNT-ID] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Read Codex usage and quota metadata directly from OpenAI.
├── health [--base-url BASE-URL] [--json-output]  # Verify the CRS /health endpoint.
├── key  # CRS API-key-only operations that do not require admin login.
│   └── info [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--timeout TIMEOUT] [--path INFO-PATH] [--json-output]  # Query CRS key-info using only a CRS API key.
└── service  # Local CRS service lifecycle commands for the current server.
    ├── install [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs install` on this server.
    ├── restart [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs restart` on this server.
    ├── start [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs start` on this server.
    ├── status [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--json-output]  # Execute local `crs status` on this server.
    ├── stop [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs stop` on this server.
    ├── switch-branch <BRANCH> [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs switch-branch <branch>` on this server.
    ├── update [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs update` on this server.
    └── update-pricing [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs update-pricing` on this server.
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
| OpenAI/Codex direct token/account/usage | `chatcrs codex token ...`, `chatcrs codex account`, `chatcrs codex quota`, `chatcrs codex usage` | 直接调用 OpenAI/Codex OAuth 与 backend API；输出只包含脱敏 token 状态、account 摘要、usage/quota header 摘要 |
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
| `chatcrs codex token refresh` | Refresh an OpenAI access token; prefer `chatenv token refresh Codex <profile>` |
| `chatcrs codex account` | Safe OpenAI Codex account summary from token claims/API probe |
| `chatcrs codex quota` | Profile-only Codex responses quota smoke; returns quota headers and account-id hash |
| `chatcrs codex usage` | Direct Codex usage inspection via usage endpoint |
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
chatenv token refresh Codex default
chatcrs codex account --profile default --json-output
chatcrs codex quota --profile default --json-output
chatcrs codex usage --profile default --json-output
```

`codex` 分支通过所选 Base URL 调用 OAuth 与 backend API，不把 CRS 调用 Key 当作账号 OAuth。ChatCRS 向 ChatEnv 注册 `Codex` namespace：稳定配置位于 `envs/Codex/<profile>.env`，动态 access/refresh token 与到期信息位于 `tokens/Codex/<profile>.json`。额度查询使用 `GET /wham/usage`，优先读取已保存的账号映射；`quota` 是真正的模型 smoke，应显式选择该账号支持的模型。需要标准持久续期时使用 `chatenv token refresh Codex <profile>`；reset profile 客户端已自动复用该流程。

Codex profile 必须显式配置请求所需的非敏感 Base URL：`OPENAI_OAUTH_BASE_URL` 用于认证端点，`CHATGPT_BACKEND_BASE_URL` 用于业务端点（通常含 `/backend-api`）。缺失配置在发起网络请求前失败，不自动回退到官方地址。Authorization 与 `ChatGPT-Account-ID` 仍由客户端按请求头发送，不能写进 Nginx 配置或日志。

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


## Codex 重置卡

Profile 客户端使用标准 ChatEnv `Codex` 续期流程：稳定配置位于 `envs/Codex`，轮换后的 access/refresh token 与到期元数据只写入 `tokens/Codex`，不会回填 ENV。过期时先续期；只读 GET 遇到 401 最多续期并重试一次；消费 POST 不自动重放。刷新凭据被上游拒绝时应重新授权，而不是切换代理或复制其他服务的 token。

账号请求必须配置对应的 HTTPS Base URL。所有 ChatCRS HTTP 请求都忽略环境和系统 Proxy，并拒绝重定向；反代示例位于仓库 `infra/nginx/codex-relay.conf.example`。Nginx 只透传请求，不保存账号密钥。

```env
OPENAI_OAUTH_BASE_URL=https://auth-relay.example.com
CHATGPT_BACKEND_BASE_URL=https://gpt-relay.example.com/backend-api
```

Python 消费者使用 `CodexResetClient.from_profile("work", refresh=True)`；需要完全不续期的诊断时显式传 `refresh=False`。不要在仪表盘或机器私有脚本中重写 OAuth。


`chatcrs codex reset list` 通过 `GET /wham/rate-limit-reset-credits` 查询可用次数与到期时间；不请求模型；必要时通过 ChatEnv 标准流程续期 OAuth，并只更新运行态 token store。`chatcrs codex reset consume` 默认只生成计划，必须同时提供持久化的 `--request-id` 和 `--execute` 才消费一张卡。请求前保存审计，之后 GET 读回；相同请求 ID 不重复发送，结果不明应人工核对，不要生成新 ID 盲重试。完整重置会改变自然重置时间，且不是购买 Credits。

```bash
chatcrs codex reset list --profile work --json-output
chatcrs codex reset consume --profile work --request-id one-reviewed-operation --json-output
```

如既有反代未提供重置路由，可用 `--base-url` 显式指定重置后端；它不改变该 profile 的 usage/auth base，也不会修改配置。服务使用 ChatGPT 后端接口，可能随上游变化，不等同于稳定的 OpenAI Platform 公共 API。Python 消费者使用 `chatcrs.reset_credits.CodexResetClient`、`inspect_reset_credits` 与 `consume_reset_credit`；客户端 `consume(..., execute=True)` 由调用者自己的策略和持久化去重保护。ChatGlance 的阈值策略不属于 ChatCRS。


## CRS 托管 Codex（Unreleased）

此管理型客户端是 **Unreleased** 源码功能，**不包含在 0.3.4**。网络操作的前置条件是 CRS 服务端部署原生、受 Admin 鉴权保护的以下接口；旧服务器没有这些路由时会失败，不回退为本地 OAuth、缓存统计或 `reset-status`。这不是服务端已发布/已部署的承诺。

所有命令必须指定 `--account-id`；`--profile` 默认 `default`，只选择既有 `CRS` ChatEnv namespace，绝不是 `Codex` OAuth profile。固定服务 origin 与账号 identity（`token_service="CRS"`），不复制上游 OAuth。仪表板优先在所选 CRS profile 中配置专用管理 Key（`CRS_API_KEY`，`crsm_` 前缀）：客户端只发送该 Key，不读取 Admin 会话或以用户名/密码回退；Key 被拒绝时明确失败。未配置 Key 的操作员路径只复用已存在的 CRS Admin 会话；缺失或被拒绝时失败，不自动登录、续期或重放。请先独立运行 `chatcrs admin login --profile <profile> --save-token` 建立会话。旧 Admin 命令的默认登录生命周期不变。普通模型 Key 不适用于此接口。CLI 仅延迟导入并调用 `chatcrs.managed_codex.CrsManagedCodexClient.from_profile(crs_profile="default", account_id="account-placeholder", home=None, timeout=20)`；Python 消费者直接使用该类的 `identity`、`token_service` 和下表方法，不要 shell out 到 CLI。

| CLI | 原生 CRS 接口（服务端前置） | Python 方法 / 写入边界 |
|---|---|---|
| `chatcrs admin accounts codex usage` | `GET /admin/openai-accounts/{account_id}/codex/usage` | `usage()`；实时上游额度，只读 |
| `chatcrs admin accounts codex credits` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits` | `reset_credits()`；只读，不消费 |
| `chatcrs admin accounts codex consume` | `POST /admin/openai-accounts/{account_id}/codex/reset-credits/consume` | `consume(request_id, credit_id=None, execute=False)`；默认本地无网络 dry-run |
| `chatcrs admin accounts codex operation` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits/operations/{request_id}` | `operation(request_id)`；只读历史回执 |

```bash
chatcrs admin accounts codex usage --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex credits --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex consume --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
chatcrs admin accounts codex operation --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
```

`consume` 与 `operation` 的 `--request-id` 必需；消费可选 `--credit-id credit-placeholder`。确认目标后才给消费命令加 `--execute`，并持久保存同一个 request ID。CLI 每次只调用一次客户端方法，不自动重试、不换 ID；不确定结果使用原 ID 查回执，不盲目再消费。

`--json-output` 输出客户端安全结构化 JSON；异常输出固定安全错误，退出非零，不输出原始异常或凭据。默认消费计划的 `dry_run` 退出 0；实际消费或历史回执仅 `reset_verified`、`nothing_to_reset`、`no_credit` 为已知完成结果、退出 0（后两者不代表已消费）。`uncertain`、`pending`、未知状态、HTTP 202 或异常均非成功、退出非零；历史 receipt 的未知状态可以显示，但不是新鲜额度验证。旧 `chatcrs admin accounts usage` 仍读取 CRS 缓存统计，不改变语义。
