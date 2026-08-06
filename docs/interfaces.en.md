# CLI and HTTP Interface Map

This page aligns the current ChatCRS CLI surface with its execution boundary. Outside-server management commands map to the CRS HTTP/Admin API; `service` is a server-local surface that runs local `crs` commands only on the CRS server itself.

## Current CLI tree

```text
chatcrs
├── health                         # GET /health
├── admin                          # CRS Admin HTTP API command group
│   ├── login                      # POST /web/auth/login
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

## CLI to HTTP / local interface

| CLI | Interface | Authentication source | Mutation | Python API |
|---|---|---|---|---|
| `chatcrs health` | `GET /health` | None; only `CRS_API_BASE` or `--base-url` | No | `chatcrs.local.health_check` |
| `chatcrs admin login` | `POST /web/auth/login` | `CRS_USERNAME` + `CRS_PASSWORD`, or explicit options | No durable mutation; verifies login and reports token presence | `CrsHttpClient.login` |
| `chatcrs admin accounts usage` | `GET /admin/openai-accounts` | Admin bearer token, resolved from profile/login | No | `CrsHttpClient.accounts_usage` |
| `chatcrs admin accounts refresh-status` | `POST /admin/openai-accounts/{account_id}/reset-status` | Admin bearer token | No by default; calls endpoint only with `--execute` | `CrsHttpClient.reset_openai_account_status` |
| `chatcrs admin keys list` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_keys` |
| `chatcrs admin keys show` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_key_detail` |
| `chatcrs key info` | `GET /openai/key-info` | Caller CRS API key: `CRS_API_KEY` or `--api-key` | No | `CrsHttpClient.key_info` |
| `chatcrs service install` | local `crs install` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update` | local `crs update` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service start` | local `crs start` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service stop` | local `crs stop` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service restart` | local `crs restart` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service status` | local `crs status` via `local_command` | Current server shell | Read-only local execution by default | `chatcrs.service.run_service_action` |
| `chatcrs service switch-branch` | local `crs switch-branch <branch>` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |
| `chatcrs service update-pricing` | local `crs update-pricing` via `local_command` | Current server shell | Plan by default; `--execute` runs locally | `chatcrs.service.run_service_action` |

## Configuration boundary

| Field / option | Purpose | Used by |
|---|---|---|
| `CRS_API_BASE` | CRS HTTP base URL | HTTP/Admin/API-key commands |
| `CRS_API_KEY` | Caller API key | `chatcrs key info` |
| `CRS_USERNAME` | Admin username | `chatcrs admin login` and admin commands that need a login-derived token |
| `CRS_PASSWORD` | Admin password | `chatcrs admin login` and admin commands that need a login-derived token |
| `CRS_ACCESS_TOKEN` | Admin bearer token | `chatcrs admin ...` |
| `--app-dir` | Local CRS app directory on the current server | `chatcrs service ...` |
| `--crs-command` | Local CRS executable or command name | `chatcrs service ...` |

The canonical ChatEnv namespace is `CRS`: `~/.chatarch/envs/CRS/<profile>.env`. Service-local options are CLI/Python parameters, not a second ChatEnv target namespace.

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
