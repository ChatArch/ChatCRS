# CLI and HTTP Interface Map

This page aligns the current ChatCRS CLI surface with its execution boundary. Outside-server management commands map to the CRS HTTP/Admin API; `service` is a server-local surface that runs local `crs` commands only on the CRS server itself.

## Current CLI tree

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

## CLI to HTTP / local interface

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
| `chatcrs codex token refresh` | `POST <OPENAI_OAUTH_BASE_URL>/oauth/token` (explicit Base URL required) | OpenAI refresh token from explicit option or `envs/Codex/<profile>.env` / `tokens/Codex/<profile>.json` | No durable mutation by default; durable refresh should use `chatenv token refresh Codex <profile>` so ChatEnv writes `tokens/Codex/<profile>.json` | `chatcrs.codex_direct.refresh_access_token` / `chatcrs.codex_direct.refresh_chatenv_token` |
| `chatcrs codex account` | access-token claims/token-store summary; best-effort `GET <OPENAI_OAUTH_BASE_URL>/api/accounts` probe (explicit Base URL required) | OpenAI access token from option or Codex ChatEnv token store; optional refresh | No | `chatcrs.codex_direct.inspect_account` |
| `chatcrs codex quota` | `POST <CHATGPT_BACKEND_BASE_URL>/codex/responses` (explicit Base URL required) | OpenAI access token + stored/explicit account mapping | Sends minimal quota smoke; no local write | `chatcrs.codex_direct.inspect_quota` |
| `chatcrs codex usage` | `GET <CHATGPT_BACKEND_BASE_URL>/wham/usage` (explicit Base URL required); `GET <OPENAI_OAUTH_BASE_URL>/api/accounts` only when no token-store account mapping exists and `--account-id` is omitted | OpenAI access token from option or Codex ChatEnv token store; optional refresh; profile-only use prefers `tokens/Codex/<profile>.json` `values.account_id` and otherwise auto-resolves a unique account id | No | `chatcrs.codex_direct.inspect_usage` |

| `chatcrs service install` | local `crs install` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update` | local `crs update` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service start` | local `crs start` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service stop` | local `crs stop` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service restart` | local `crs restart` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service status` | local `crs status` via `local_command` | Current server shell | Read-only local execution by default | `chatcrs.service.run_service_action` |
| `chatcrs service switch-branch` | local `crs switch-branch <branch>` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update-pricing` | local `crs update-pricing` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |

Note: Quota smoke uses `store:false`, `stream:true`, canonical `ChatGPT-Account-ID`, `originator: codex_cli_rs`, and the default live-validated smoke model `gpt-5.5`. Output keeps quota headers and account-id hash only.

## Configuration boundary

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


## Banked Codex resets

Profile clients use the registered ChatEnv `Codex` renewal flow: stable configuration stays in `envs/Codex`, while rotated access/refresh tokens and expiry metadata are written only to `tokens/Codex`, without changing ENV. Expired credentials are renewed before use. A read-only GET 401 permits one renewal/retry; a consume POST is never replayed. Rejected refresh credentials require renewed authorization, not another proxy or a copied token from a different service.

Configure the HTTPS Base URLs needed by the account operation. All ChatCRS HTTP transports ignore environment/system proxies and reject redirects. The repository provides `infra/nginx/codex-relay.conf.example`; the reverse proxy forwards requests without storing account secrets.

```env
OPENAI_OAUTH_BASE_URL=https://auth-relay.example.com
CHATGPT_BACKEND_BASE_URL=https://gpt-relay.example.com/backend-api
```

Python consumers use `CodexResetClient.from_profile("work", refresh=True)`. Set `refresh=False` explicitly for diagnostics that must not renew credentials. OAuth belongs in ChatCRS, not dashboard code or machine-private scripts.


`chatcrs codex reset list` reads available count and expirations with `GET /wham/rate-limit-reset-credits`, without model generation; credentials are renewed through ChatEnv when required, updating only the runtime token store. `chatcrs codex reset consume` is a dry-run unless both a persistent `--request-id` and `--execute` are provided. It persists an audit before sending and performs GET readback afterward. The same request ID is never sent twice; resolve uncertain outcomes through read-only inspection instead of creating another ID. A full reset changes the natural reset schedule and is not a Credits purchase.

```bash
chatcrs codex reset list --profile work --json-output
chatcrs codex reset consume --profile work --request-id one-reviewed-operation --json-output
```

An explicit `--base-url` can select a reset backend when a configured relay does not expose reset routes; it does not change the profile usage/auth base or stored config. These are evolving ChatGPT backend endpoints, not a stable public OpenAI Platform API. Python consumers use `chatcrs.reset_credits.CodexResetClient`, `inspect_reset_credits`, and `consume_reset_credit`. Client `consume(..., execute=True)` requires caller-owned policy and durable de-duplication; ChatGlance threshold policy stays outside ChatCRS.

| CLI | HTTP | Python API |
|---|---|---|
| `chatcrs codex reset list` | `GET /wham/rate-limit-reset-credits` | `inspect_reset_credits` |
| `chatcrs codex reset consume` | `POST /wham/rate-limit-reset-credits/consume`; GET readback | `consume_reset_credit` |


## CRS-managed Codex (Unreleased)

This managed client is **Unreleased** source functionality, **not included in 0.3.4**. Network operations require a CRS server with the native, Admin-authenticated routes below. Older servers without them fail closed: no fallback to local OAuth, cached statistics, or `reset-status`. This does not claim a server release or deployment.

Every command requires `--account-id`. `--profile` defaults to `default` and selects the existing `CRS` ChatEnv namespace, never a `Codex` OAuth profile. It uses a scoped management Key (`CRS_API_KEY`, `crsm_` prefix) from the selected CRS profile, without reading Admin sessions, logging in or falling back. Operators without a Key must establish an Admin session separately with `chatcrs admin login --profile <profile> --save-token`; missing or rejected sessions fail without login, renewal or replay. Legacy Admin commands retain their defaults. It pins the server origin/account identity (`token_service="CRS"`) without copying upstream OAuth credentials. The thin CLI lazily calls `chatcrs.managed_codex.CrsManagedCodexClient.from_profile(crs_profile="default", account_id="account-placeholder", home=None, timeout=20)`. Python consumers use its `identity`, `token_service`, and methods directly, without shelling out to the CLI.

| CLI | Native CRS route (server prerequisite) | Python method / mutation boundary |
|---|---|---|
| `chatcrs admin accounts codex usage` | `GET /admin/openai-accounts/{account_id}/codex/usage` | `usage()`; fresh upstream windows, read-only |
| `chatcrs admin accounts codex credits` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits` | `reset_credits()`; read-only, never consumes |
| `chatcrs admin accounts codex consume` | `POST /admin/openai-accounts/{account_id}/codex/reset-credits/consume` | `consume(request_id, credit_id=None, execute=False)`; local network-free dry-run by default |
| `chatcrs admin accounts codex operation` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits/operations/{request_id}` | `operation(request_id)`; read-only historical receipt |

```bash
chatcrs admin accounts codex usage --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex credits --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex consume --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
chatcrs admin accounts codex operation --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
```

`consume` and `operation` require `--request-id`; consumption optionally accepts `--credit-id credit-placeholder`. Add `--execute` only after reviewing the target and persist the same request ID. Each CLI invocation calls the adapter method once: no automatic replay or new ID. Inspect an uncertain receipt with the original ID instead of blindly consuming again.

`--json-output` emits the adapter's safe structured JSON. Exceptions produce fixed safe errors and nonzero exits, never raw exceptions or credentials. A local `dry_run` exits 0. Executed consumption and historical receipts exit 0 only for `reset_verified`, `nothing_to_reset`, or `no_credit` (the latter two do not mean a credit was consumed). `uncertain`, `pending`, unknown states, HTTP 202, and exceptions are not success and exit nonzero. Historical unknown receipt states may be displayed but are not fresh quota verification. Existing `chatcrs admin accounts usage` keeps its cached CRS statistics semantics.
