# 命令与接口映射

此页对齐当前 ChatCRS CLI surface 与其执行边界：外部管理命令映射 CRS HTTP/Admin API；`service` 是 server-local surface，只能在 CRS 服务器本机运行本机 `crs` 命令。

## 当前 CLI 树

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

## CLI 到 HTTP / local 接口

| CLI | Interface | Authentication source | Mutation | Python API |
|---|---|---|---|---|
| `chatcrs health` | `GET /health` | None; configured base URL field or `--base-url` | No | health-check helper |
| `chatcrs admin login` | `POST /web/auth/login` | configured admin identity/password fields, or explicit options | No durable mutation by default; `--save-token` writes the runtime token file | `CrsHttpClient.login` |
| `chatcrs admin token status` | local token file read | CRS profile + runtime token store | No | `CrsTokenStore.status` |
| `chatcrs admin token refresh` | `POST /web/auth/login`; `chatenv token refresh CRS <profile>` uses the same provider and lets ChatEnv write the token file | Admin username/password from matching stable `envs/CRS/<profile>.env` profile | Writes `~/.chatarch/tokens/CRS/<profile>.json` only through ChatEnv token-store persistence | `chatcrs.tokens.refresh_chatenv_token` / `CrsHttpClient.login(save_token=True)` |
| `chatcrs admin token clear` | local token file delete | CRS profile + runtime token store | Dry-run by default; deletes only with `--execute` | `CrsTokenStore.clear` |
| `chatcrs admin accounts usage` | `GET /admin/openai-accounts` | Admin bearer token, resolved from profile/login | No | `CrsHttpClient.accounts_usage` |
| `chatcrs admin accounts refresh-status` | `POST /admin/openai-accounts/{account_id}/reset-status` | Admin bearer token | No by default; calls endpoint only with `--execute` | `CrsHttpClient.reset_openai_account_status` |
| `chatcrs admin keys list` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_keys` |
| `chatcrs admin keys show` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_key_detail` |
| `chatcrs key info` | `GET /openai/key-info` | caller CRS API key from profile or `--api-key` | No | `CrsHttpClient.key_info` |
| `chatcrs codex token status` | local `tokens/Codex/<profile>.json` metadata | Codex ChatEnv profile/token store | No | `chatcrs.codex_direct.token_status` |
| `chatcrs codex token refresh` | `POST <OPENAI_OAUTH_BASE_URL>/oauth/token`（需显式配置 Base URL） | OpenAI refresh token from explicit option or `envs/Codex/<profile>.env` / `tokens/Codex/<profile>.json` | No durable mutation by default; durable refresh should use `chatenv token refresh Codex <profile>` so ChatEnv writes `tokens/Codex/<profile>.json` | `chatcrs.codex_direct.refresh_access_token` / `chatcrs.codex_direct.refresh_chatenv_token` |
| `chatcrs codex account` | access-token claims/token-store summary; best-effort `GET <OPENAI_OAUTH_BASE_URL>/api/accounts` probe（需显式配置 Base URL） | OpenAI access token from option or Codex ChatEnv token store; optional refresh | No | `chatcrs.codex_direct.inspect_account` |
| `chatcrs codex quota` | `POST <CHATGPT_BACKEND_BASE_URL>/codex/responses`（需显式配置 Base URL） | OpenAI access token + stored/explicit account mapping | Sends minimal quota smoke; no local write | `chatcrs.codex_direct.inspect_quota` |
| `chatcrs codex usage` | `GET <CHATGPT_BACKEND_BASE_URL>/wham/usage`（需显式配置 Base URL）；`GET <OPENAI_OAUTH_BASE_URL>/api/accounts` only when no token-store account mapping exists and `--account-id` is omitted | OpenAI access token from option or Codex ChatEnv token store; optional refresh; profile-only use prefers `tokens/Codex/<profile>.json` `values.account_id` and otherwise auto-resolves a unique account id | No | `chatcrs.codex_direct.inspect_usage` |

| `chatcrs service install` | local `crs install` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update` | local `crs update` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service start` | local `crs start` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service stop` | local `crs stop` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service restart` | local `crs restart` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service status` | local `crs status` via `local_command` | Current server shell | Read-only local execution by default | `chatcrs.service.run_service_action` |
| `chatcrs service switch-branch` | local `crs switch-branch <branch>` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update-pricing` | local `crs update-pricing` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |

Note: Quota smoke uses `store:false`, `stream:true`, canonical `ChatGPT-Account-ID`, `originator: codex_cli_rs`, and the default live-validated smoke model `gpt-5.5`. Output keeps quota headers and account-id hash only.

## 配置边界

| Field / option | Purpose | Used by |
|---|---|---|
| HTTP base URL profile field | CRS HTTP base URL | HTTP/Admin/API-key commands |
| caller API-key profile field | Caller API key | `chatcrs key info` |
| admin identity profile field | Admin username | `chatcrs admin login` and admin commands that need a login-derived token |
| admin password profile field | Admin password | `chatcrs admin login` and admin commands that need a login-derived token |
| admin bearer/session token profile field | Legacy Admin bearer token fallback | `chatcrs admin ...` |
| runtime token file | Cached login-derived Admin session token | `chatcrs admin token ...` and Admin auto-refresh |
| Codex token profile | Stable OAuth metadata in `envs/Codex/<profile>.env` plus runtime OAuth token values in `tokens/Codex/<profile>.json` | `chatenv token refresh Codex <profile>` and `chatcrs codex ...`; output is redacted and raw token values are not printed |
| `--app-dir` | Local CRS app directory on the current server | `chatcrs service ...` |
| `--crs-command` | Local CRS executable or command name | `chatcrs service ...` |

The canonical CRS ChatEnv namespace is `CRS`; stable CRS configuration lives in Env, while dynamic Admin session tokens live in the parallel token store. Codex direct deliberately reuses ChatEnv's ChatCRS-owned `Codex` namespace for OAuth profile/token lifecycle instead of creating a `Codex` namespace. Public docs intentionally omit concrete secret values. Service-local options are CLI/Python parameters, not a second ChatEnv target namespace.

## Service-local contract

`chatcrs service ...` exists because some lifecycle/install/update/status capabilities are not HTTP resources. The command must be installed on and executed inside the CRS server environment that owns the process and checkout.

- It does not use SSH transport or host aliases.
- It does not maintain another server from outside.
- It does not read legacy service-target environment fields or profile directories.
- For outside-server operations, use HTTP/Admin API commands. If the CRS app needs remote lifecycle control, add a CRS HTTP/Admin endpoint or a restricted host-side agent instead of hiding remote execution in ChatCRS.

## Current HTTP coverage

- `GET /health`
- `POST /web/auth/login`
- `GET /admin/openai-accounts`
- `POST /admin/openai-accounts/{account_id}/reset-status`
- `GET /admin/api-keys`
- `POST /admin/api-keys/batch-stats`
- `POST /admin/api-keys/batch-last-usage`
- `GET /openai/key-info`
- OpenAI/Codex direct APIs used by `chatcrs codex ...`: `POST https://auth.openai.com/oauth/token`, `GET https://auth.openai.com/api/accounts`, `GET https://chatgpt.com/backend-api/wham/usage`, and `POST https://chatgpt.com/backend-api/codex/responses`.

## Explicit gaps / out-of-scope task surfaces

| Gap or removed surface | Current handling |
|---|---|
| API key create/update/delete/restore/tag/index | Confirm or add Admin HTTP endpoints first, then implement with dry-run/execute and redacted audit rules |
| account add/delete/toggle/schedulable/test | Confirm or add Admin HTTP endpoints first; do not substitute local scripts or direct database writes for external management |
| topology/edge/Redis/Nginx/release/cutover | Deployment/operations-layer work, outside the ordinary CRS HTTP client and outside this service restore |
| verify/image/debug surfaces | Kept out of ChatCRS package CLI; handle as separate acceptance/proxy-site/runbook tasks when scoped |

## Update rules

- Every registered leaf must appear on this page with its interface, auth source, mutation boundary, and Python API.
- HTTP/Admin commands must name the endpoint.
- Service commands must remain server-local and explicit about `local_command` execution.
- Keep all outputs redacted: API keys, tokens, passwords, and OAuth credentials are reported only as presence, counts, status, or `[REDACTED]`.


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

| CLI | HTTP | Python API |
|---|---|---|
| `chatcrs codex reset list` | `GET /wham/rate-limit-reset-credits` | `inspect_reset_credits` |
| `chatcrs codex reset consume` | `POST /wham/rate-limit-reset-credits/consume`; GET readback | `consume_reset_credit` |


## CRS 托管 Codex（Unreleased）

此管理型客户端是 **Unreleased** 源码功能，**不包含在 0.3.4**。网络操作的前置条件是 CRS 服务端部署原生、受 Admin 鉴权保护的以下接口；旧服务器没有这些路由时会失败，不回退为本地 OAuth、缓存统计或 `reset-status`。这不是服务端已发布/已部署的承诺。

所有命令必须指定 `--account-id`；`--profile` 默认 `default`，只选择既有 `CRS` ChatEnv namespace，绝不是 `Codex` OAuth profile。使用所选 CRS profile 的专用管理 Key（`CRS_API_KEY`，`crsm_` 前缀）；Key 模式不读 Admin 会话、不自动登录、不回退。未配置 Key 的操作员路径只使用已存在的 Admin 会话，缺失或被拒绝即失败；须另行运行 `chatcrs admin login --profile <profile> --save-token` 建立会话，旧 Admin 命令的默认行为不变。`token_service="CRS"`，固定服务 origin 与账号 identity，不复制上游 OAuth。CLI 仅延迟导入并调用 `chatcrs.managed_codex.CrsManagedCodexClient.from_profile(crs_profile="default", account_id="account-placeholder", home=None, timeout=20)`；Python 消费者直接使用该类的 `identity`、`token_service` 和下表方法，不要 shell out 到 CLI。

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
