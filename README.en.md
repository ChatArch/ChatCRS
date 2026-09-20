<div align="center">
    <a href="https://pypi.python.org/pypi/ChatCRS">
        <img src="https://img.shields.io/pypi/v/ChatCRS.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatCRS/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatCRS/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatCRS

ChatCRS is ChatArch's CRS management CLI. Outside-server management is HTTP/Admin API-first. The `service` namespace is a server-local surface: it runs only inside the CRS server shell and operates on that server's CRS checkout / Node runtime / `crs` executable.

Image acceptance, debug runtimes, Nginx/edge work, release/cutover workflows, and similar task-specific surfaces are not package commands today. They belong to proxy-site maintenance, special acceptance, or operations runbooks and should be designed separately when scoped.

## Install and develop

```bash
python -m pip install -e '.[dev,docs]'
chatcrs --help
chatcrs --version
python -m pytest -q
python -m mkdocs build --strict
python -m build
```

Serve the complete MkDocs site with:

```bash
python -m mkdocs serve
```

Documentation: https://arch.gh.wzhecnu.cn/ChatCRS/

## Configuration test

After installation, import `CRS_API_BASE` (service root URL) and `CRS_API_KEY` with `chatenv paste --stdin --profile smoke -I --yes`, then run `chatenv use smoke -t crs -I` and `chatenv test -t crs -I`.
The default checks key authentication only and explicitly does not verify upstream availability. Set optional `CRS_API_MODEL` to opt into one billable Codex Responses text request using the same key, typed input, `stream=true`, and `store=false`. A completed response with nonempty text is required. Failures exit nonzero without printing credentials or raw errors. See [configuration details](docs/configuration.en.md).

## CLI tree

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

Run `chatcrs --tree` to read back the command tree with parameter signatures. `chatcrs --tree-brief` keeps command nodes and descriptions while omitting signatures. Both modes use the canonical `chatcrs` root.


## HTTP/Admin and API key

```bash
chatcrs health --base-url https://crs.example.com --json-output
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
chatcrs key info --profile admin --json-output
chatcrs codex token status --profile default --json-output
chatenv token refresh Codex default
chatcrs codex account --profile default --json-output
chatcrs codex quota --profile default --json-output
chatcrs codex usage --profile default --json-output
```

## Server-local service

These commands should be installed on and executed from the target CRS server itself:

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --execute --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

`status` runs local read-only `crs status` by default. Other service mutations are dry-run by default and require `--execute`.

## Configuration

ChatCRS uses one CRS ChatEnv profile namespace for CRS Admin/API configuration and registers an `Codex` OAuth token refresher for Codex direct. Codex direct stable OAuth profiles live in `envs/Codex/<profile>.env`; runtime tokens live in `tokens/Codex/<profile>.json`; use `chatenv token refresh Codex <profile>` for durable refresh. Codex profiles may set non-secret relay fields: `OPENAI_OAUTH_BASE_URL` overrides the OAuth token/accounts upstream, and `CHATGPT_BACKEND_BASE_URL` overrides the ChatGPT backend upstream. Public docs describe field categories only and intentionally omit concrete secret-file paths or secret-bearing env key names.

Canonical field categories:

```text
HTTP base URL
caller API key
admin username
admin password
admin bearer/session token
```

Service-local targets do not create a second ChatEnv namespace; use the current working directory or `--app-dir` / `--crs-command` for the local checkout and executable.

Sensitive fields should live only in ChatEnv or the process environment, never in command arguments, documentation, PR bodies, or logs. Profile files should use `0600` permissions.

## Production safety

Outside-server management must use HTTP/Admin API. If no HTTP lifecycle endpoint exists, do not fill the gap with remote execution. Add a CRS API/host-agent, or run `chatcrs service ...` on the target server itself.

See:

- `docs/cli.md`
- `docs/interfaces.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`


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


## CRS-managed Codex (Unreleased)

This managed client is **Unreleased** source functionality, **not included in 0.3.4**. Network operations require a CRS server with the native, Admin-authenticated routes below. Older servers without them fail closed: no fallback to local OAuth, cached statistics, or `reset-status`. This does not claim a server release or deployment.

Every command requires `--account-id`. `--profile` defaults to `default` and selects the existing `CRS` ChatEnv namespace, never a `Codex` OAuth profile. It pins the server origin/account identity (`token_service="CRS"`) without copying upstream OAuth credentials. Dashboards should use a dedicated management Key (`CRS_API_KEY`, `crsm_` prefix) in the selected CRS profile: Key mode never reads an Admin session or falls back to username/password login, including after rejection. Without a Key, operator calls use an already-established CRS Admin session only; missing or rejected sessions fail without login, renewal or replay. Establish a session separately with `chatcrs admin login --profile <profile> --save-token`. Legacy Admin commands keep their normal login lifecycle; ordinary model Keys are not accepted. The thin CLI lazily calls `chatcrs.managed_codex.CrsManagedCodexClient.from_profile(crs_profile="default", account_id="account-placeholder", home=None, timeout=20)`. Python consumers use its `identity`, `token_service`, and methods directly, without shelling out to the CLI.

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
