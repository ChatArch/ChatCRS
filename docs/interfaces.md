# 命令与接口映射

此页对齐当前 ChatCRS CLI surface 与其执行边界：外部管理命令映射 CRS HTTP/Admin API；`service` 是 server-local surface，只能在 CRS 服务器本机运行本机 `crs` 命令。

## 当前 CLI 树

```text
chatcrs
├── health                         # GET /health
├── admin                          # CRS Admin HTTP API command group
│   ├── login                      # POST /web/auth/login
│   ├── token                      # local runtime Admin session token cache
│   │   ├── status                 # token file metadata, no token output
│   │   ├── refresh                # POST /web/auth/login, then save token file
│   │   └── clear                  # dry-run/delete local token file
│   ├── accounts                   # OpenAI/Codex account state
│   │   ├── usage                  # GET /admin/openai-accounts
│   │   └── refresh-status         # POST /admin/openai-accounts/{account_id}/reset-status
│   └── keys                       # CRS API key metadata and statistics
│       ├── list                   # GET /admin/api-keys + batch stats/last usage
│       └── show                   # GET /admin/api-keys + batch stats/last usage, filtered by id/name
├── key                            # API-key-only self inspection
│   └── info                       # GET /openai/key-info
└── service                        # server-local service lifecycle
    ├── install                    # local crs install; dry-run by default
    ├── update                     # local crs update; dry-run by default
    ├── start                      # local crs start; dry-run by default
    ├── stop                       # local crs stop; dry-run by default
    ├── restart                    # local crs restart; dry-run by default
    ├── status                     # local crs status; read-only execution by default
    ├── switch-branch              # local crs switch-branch; dry-run by default
    └── update-pricing             # local crs update-pricing; dry-run by default
```

## CLI 到 HTTP / local 接口

| CLI | Interface | Authentication source | Mutation | Python API |
|---|---|---|---|---|
| `chatcrs health` | `GET /health` | None; configured base URL field or `--base-url` | No | health-check helper |
| `chatcrs admin login` | `POST /web/auth/login` | configured admin identity/password fields, or explicit options | No durable mutation by default; `--save-token` writes the runtime token file | `CrsHttpClient.login` |
| `chatcrs admin token status` | local token file read | CRS profile + runtime token store | No | `CrsTokenStore.status` |
| `chatcrs admin token refresh` | `POST /web/auth/login`, then local token file write | Admin username/password | Writes `~/.chatarch/tokens/CRS/<profile>.json` | `CrsHttpClient.login(save_token=True)` |
| `chatcrs admin token clear` | local token file delete | CRS profile + runtime token store | Dry-run by default; deletes only with `--execute` | `CrsTokenStore.clear` |
| `chatcrs admin accounts usage` | `GET /admin/openai-accounts` | Admin bearer token, resolved from profile/login | No | `CrsHttpClient.accounts_usage` |
| `chatcrs admin accounts refresh-status` | `POST /admin/openai-accounts/{account_id}/reset-status` | Admin bearer token | No by default; calls endpoint only with `--execute` | `CrsHttpClient.reset_openai_account_status` |
| `chatcrs admin keys list` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_keys` |
| `chatcrs admin keys show` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_key_detail` |
| `chatcrs key info` | `GET /openai/key-info` | caller CRS API key from profile or `--api-key` | No | `CrsHttpClient.key_info` |
| `chatcrs service install` | local `crs install` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update` | local `crs update` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service start` | local `crs start` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service stop` | local `crs stop` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service restart` | local `crs restart` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service status` | local `crs status` via `local_command` | Current server shell | Read-only local execution by default | `chatcrs.service.run_service_action` |
| `chatcrs service switch-branch` | local `crs switch-branch <branch>` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update-pricing` | local `crs update-pricing` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |

## 配置边界

| Field / option | Purpose | Used by |
|---|---|---|
| HTTP base URL profile field | CRS HTTP base URL | HTTP/Admin/API-key commands |
| caller API-key profile field | Caller API key | `chatcrs key info` |
| admin identity profile field | Admin username | `chatcrs admin login` and admin commands that need a login-derived token |
| admin password profile field | Admin password | `chatcrs admin login` and admin commands that need a login-derived token |
| admin bearer/session token profile field | Legacy Admin bearer token fallback | `chatcrs admin ...` |
| runtime token file | Cached login-derived Admin session token | `chatcrs admin token ...` and Admin auto-refresh |
| `--app-dir` | Local CRS app directory on the current server | `chatcrs service ...` |
| `--crs-command` | Local CRS executable or command name | `chatcrs service ...` |

The canonical ChatEnv namespace is `CRS`; stable configuration lives in Env, while dynamic Admin session tokens live in the parallel token store. Public docs intentionally omit concrete secret values. Service-local options are CLI/Python parameters, not a second ChatEnv target namespace.

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
