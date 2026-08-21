# CLI Tree

This page lists **commands currently implemented and registered in `chatcrs.cli`**. `chatcrs --tree` reads back signatures, while `chatcrs --tree-brief` keeps nodes and descriptions without signatures; both use the canonical `chatcrs` root. Command changes must keep this page aligned.

## Top-level commands

```text
chatcrs
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── admin  # Remote CRS administrator operations via HTTPS Admin API.
│   ├── accounts  # Inspect or refresh remote CRS account state via HTTP Admin API.
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
│   ├── token  # Manage OpenAI OAuth tokens through the ChatEnv OpenAI token store.
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

## Coverage matrix

| Capability | Implemented commands | Boundary |
|---|---|---|
| CRS health | `chatcrs health` | Read-only HTTP health summary |
| Admin login | `chatcrs admin login` | Verifies credentials; reports token presence only; `--save-token` writes the runtime token store |
| Admin token cache | `chatcrs admin token status`, `chatcrs admin token refresh`, `chatcrs admin token clear` | Manages short-lived Admin session tokens under `~/.chatarch/tokens/CRS/<profile>.json`; `chatcrs admin token refresh` is the ChatCRS-native command, and installed ChatCRS also registers the same provider for `chatenv token refresh CRS <profile>`; status output never prints tokens |
| Account usage | `chatcrs admin accounts usage` | Admin HTTP API; redacted usage/status/scheduling summary |
| Account status reset | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS reset-status; not an OAuth refresh-token force-refresh |
| API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted key values, status, limits, stats, and last-usage summaries |
| API-key-only self info | `chatcrs key info` | No administrator login required |
| OpenAI/Codex direct token/account/usage | `chatcrs codex token ...`, `chatcrs codex account`, `chatcrs codex quota`, `chatcrs codex usage` | Calls OpenAI/Codex OAuth and backend APIs directly; output is limited to redacted token status, account summaries, and usage/quota header summaries |
| Local service lifecycle | `chatcrs service ...` | Runs local `crs` commands only on the CRS server; outside-server management must use HTTP/Admin API or a new service-side API/agent |

## Registered command list

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

## Remote admin and API key { #remote-admin-and-api-key }

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

!!! warning "Meaning of refresh-status"
    `refresh-status` resets CRS account state. It does not force-refresh Codex/OpenAI OAuth refresh tokens.

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
chatcrs codex quota --profile default --json-output
chatcrs codex usage --profile default --json-output
```

The `codex` branch calls OpenAI/Codex OAuth and backend APIs directly instead of using the CRS Admin API. Stable OAuth profile data uses ChatEnv's built-in `OpenAI` namespace (`envs/OpenAI/<profile>.env`), and runtime access/refresh token state uses the same `OpenAI` token store (`tokens/OpenAI/<profile>.json`). If token-store values include a non-secret `account_id` mapping, `chatcrs codex quota --profile <profile>` uses it for a Codex responses quota smoke; the default smoke model is the production-validated `gpt-5.5` (`gpt-5` / `gpt-5.6` returned 400 for ChatGPT-account Codex). `chatcrs codex usage --profile <profile>` keeps the legacy usage endpoint behavior before falling back to the OpenAI accounts API to auto-resolve one unique account. Durable refresh should run `chatenv token refresh OpenAI <profile>`; `chatcrs codex ...` only consumes that state and prints redacted token/account/usage summaries, never raw access tokens, refresh tokens, id tokens, raw account ids, email addresses, or user ids.

OpenAI profiles can set non-secret relay base URLs: `OPENAI_OAUTH_BASE_URL` overrides the OAuth token/accounts upstream, and `CHATGPT_BACKEND_BASE_URL` overrides the ChatGPT backend upstream (usually including the `/backend-api` prefix). These fields only change the request destination; Authorization and `ChatGPT-Account-ID` remain client-supplied request headers and must not be written into proxy config or logs.

## Server-local service { #server-local-service }

`chatcrs service ...` is a server-local surface. It assumes the command is installed and executed inside the CRS server shell, operating on that machine's CRS checkout / Node runtime / `crs` executable.

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --execute --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

Rules:

- `status` is read-only and runs local `crs status` by default.
- `install`, `update`, `start`, `stop`, `restart`, `switch-branch`, and `update-pricing` print a plan by default; `--execute` is required for execution.
- The target comes only from the current working directory or explicit `--app-dir`; `--crs-command` selects only a local executable.
- If the operator is outside the server, ordinary management must use `chatcrs admin ...` / `chatcrs key ...` HTTP/Admin APIs. Lifecycle capabilities without HTTP endpoints should be added to CRS as an API/agent or run from the server itself.

## Removed task-specific surfaces { #removed-task-surfaces }

These categories remain unregistered:

- local verify / sidecar verify;
- Images acceptance;
- debug runtime;
- Nginx plan-cutover;
- formal cutover precheck;
- fixed-topology inspect.

They belong to special acceptance, debug runtime, edge/cutover runbooks, or proxy-site tasks, not the current core ChatCRS management CLI.

## Safety boundaries { #safety-boundaries }

- The outside-server CRS management surface is HTTP/Admin API.
- The service surface runs only on the CRS server itself and does not maintain another server.
- Any production mutation still requires explicit `--execute`, target verification, rollback boundary, and redacted output.
- Env profiles keep stable configuration; short-lived Admin session tokens are cached under `~/.chatarch/tokens/CRS/<profile>.json` instead of frequently rewriting Env files.
- API keys, tokens, passwords, and OAuth credentials must not appear in chat, docs, PR bodies, or command output.
