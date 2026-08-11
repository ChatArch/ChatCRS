# CLI Tree

This page lists **commands currently implemented and registered in `chatcrs.cli`**. Run `chatcrs --tree` to read back the same tree from the live Click registry; command changes must keep this page aligned.

## Top-level commands

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

## Coverage matrix

| Capability | Implemented commands | Boundary |
|---|---|---|
| CRS health | `chatcrs health` | Read-only HTTP health summary |
| Admin login | `chatcrs admin login` | Verifies credentials; reports token presence only; `--save-token` writes the runtime token store |
| Admin token cache | `chatcrs admin token status`, `chatcrs admin token refresh`, `chatcrs admin token clear` | Manages short-lived Admin session tokens under `~/.chatarch/tokens/CRS/<profile>.json`; status output never prints tokens |
| Account usage | `chatcrs admin accounts usage` | Admin HTTP API; redacted usage/status/scheduling summary |
| Account status reset | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS reset-status; not an OAuth refresh-token force-refresh |
| API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted key values, status, limits, stats, and last-usage summaries |
| API-key-only self info | `chatcrs key info` | No administrator login required |
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
