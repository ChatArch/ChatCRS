# CLI Tree

This page lists **commands currently implemented and registered in `chatcrs.cli`**. Tests read the Click registry and keep this page aligned with command changes.

## Top-level commands

```text
chatcrs                                           # CRS HTTP/API-first + server-local management CLI
├── health                                        # Check the selected CRS /health endpoint
├── admin                                         # Remote CRS Admin HTTP API operations
│   ├── login                                     # Verify admin login without printing the session token
│   ├── accounts                                  # Inspect or refresh OpenAI/Codex account state
│   │   ├── usage                                 # Account usage, scheduling, and availability summary
│   │   └── refresh-status                        # Dry-run by default; --execute calls reset-status
│   └── keys                                      # Inspect CRS API key metadata and statistics
│       ├── list                                  # List keys; optionally include batch stats/last-usage
│       └── show                                  # Safe summary for one key by id/name
├── key                                           # API-key-only self-inspection commands
│   └── info                                      # Current API key information, availability, and usage
└── service                                       # Service commands that run only on the CRS server itself
    ├── install                                   # Dry-run by default; --execute runs local crs install
    ├── update                                    # Dry-run by default; --execute runs local crs update
    ├── start                                     # Dry-run by default; --execute runs local crs start
    ├── stop                                      # Dry-run by default; --execute runs local crs stop
    ├── restart                                   # Dry-run by default; --execute runs local crs restart
    ├── status                                    # Runs local crs status; read-only
    ├── switch-branch                             # Dry-run by default; --execute runs local crs switch-branch
    └── update-pricing                            # Dry-run by default; --execute runs local crs update-pricing
```

## Coverage matrix

| Capability | Implemented commands | Boundary |
|---|---|---|
| CRS health | `chatcrs health` | Read-only HTTP health summary |
| Admin login | `chatcrs admin login` | Verifies credentials; reports token presence only |
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
- API keys, tokens, passwords, and OAuth credentials must not appear in chat, docs, PR bodies, or command output.
