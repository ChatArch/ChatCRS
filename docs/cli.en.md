# CLI Tree

This page lists **commands currently implemented and registered in `chatcrs.cli`**. Tests read the Click registry and keep this page aligned with command changes.

## Top-level commands

```text
chatcrs                                           # CRS HTTP/API-first management CLI
├── health                                        # Check the selected CRS /health endpoint
├── admin                                         # Remote CRS Admin HTTP API operations
│   ├── login                                     # Verify admin login without printing the session token
│   ├── accounts                                  # Inspect or refresh OpenAI/Codex account state
│   │   ├── usage                                 # Account usage, scheduling, and availability summary
│   │   └── refresh-status                        # Dry-run by default; --execute calls reset-status
│   └── keys                                      # Inspect CRS API key metadata and statistics
│       ├── list                                  # List keys; optionally include batch stats/last-usage
│       └── show                                  # Safe summary for one key by id/name
└── key                                           # API-key-only self-inspection commands
    └── info                                      # Current API key information, availability, and usage
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

## Remote admin and API key { #remote-admin-and-api-key }

<div class="grid cards" markdown>

-   **Admin login**

    ---

    `chatcrs admin login` verifies CRS admin credentials and reports only safe token presence metadata.

-   **Account usage**

    ---

    `chatcrs admin accounts usage` reports OpenAI/Codex account usage, status, scheduling, and recent-use summaries.

-   **Account status refresh**

    ---

    `chatcrs admin accounts refresh-status <account_id>` is dry-run by default; `--execute` calls CRS reset-status.

-   **API key statistics**

    ---

    `chatcrs admin keys list --include-stats` combines key metadata, batch stats, and last-usage; `show` inspects one key.

</div>

```text
chatcrs admin                                     # Remote CRS administrator entry point
├── login                                         # Verify login without leaking token
├── accounts                                      # Account status and usage
│   ├── usage                                     # List account usage and scheduling state
│   └── refresh-status                            # Dry-run by default; --execute resets CRS state
└── keys                                          # Admin API key inspection
    ├── list                                      # List keys, redacted by default; can include stats
    └── show                                      # Safe summary for one key
```

Common commands:

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

```text
chatcrs key                                       # API-key-only self-inspection entry point
└── info                                          # Current API key information, availability, and usage
```

```bash
chatcrs key info --profile admin --json-output
chatcrs key info --profile admin --path /openai/key-info --json-output
```

## Server-local candidate capabilities { #server-local-candidates }

The following capabilities may be useful, but they are not current HTTP Admin/API capabilities. They usually require server-local authority over a process manager, filesystem, Nginx, Redis, or deployment artifacts. The packaged CLI does **not** register these commands today; if reintroduced later, they must be redesigned and tested as explicit server-local/host-agent capabilities.

| Candidate capability | Why it is not supported by the current RESTful API |
|---|---|
| install/update/start/stop/restart/status | Controls service processes and deployment scripts; depends on local supervisor state, working directories, Node/npm, and runtime files rather than CRS application resources |
| switch branch / update pricing data | Depends on local git/package scripts and runtime files; the current Admin API has no restricted endpoint for it |
| topology/doctor/edge inspection | Requires reading processes, ports, Nginx config, Redis keyspace, or deployment directories; those are not CRS HTTP resources |
| release/cutover/rollback | Coordinates build artifacts, snapshots, edge reloads, and rollback; this belongs in deployment runbooks or a host agent, not an ordinary CRS HTTP client |

## Safety boundaries { #safety-boundaries }

- The packaged CLI keeps only HTTP health, Admin API inspection/status operations, and API-key-only self checks.
- If a management action has no CRS HTTP/Admin endpoint, ChatCRS should report the capability gap instead of substituting remote execution or local scripts.
- Any production mutation still requires explicit `--execute` plus a confirmed HTTP endpoint, rollback boundary, and redacted output.
- API keys, tokens, passwords, and OAuth credentials must not appear in chat, docs, PR bodies, or command output.
