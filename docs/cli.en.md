# CLI Tree

This page lists **commands currently implemented and registered in `chatcrs.cli`**. Tests read the Click registry and keep this page aligned with command changes.

## Top-level commands

```text
chatcrs                                           # ChatArch CRS remote operations CLI
├── health                                        # Check the selected CRS /health endpoint
├── inspect                                       # Read-only summary of known CRS topology and entry state
├── admin                                         # Remote CRS Admin API operations
│   ├── login                                     # Verify admin login without printing the session token
│   ├── accounts                                  # Inspect or refresh OpenAI/Codex account state
│   │   ├── usage                                 # Account usage, scheduling, and availability summary
│   │   └── refresh-status                        # Dry-run by default; --execute calls CRS reset-status
│   └── keys                                      # Inspect CRS API key metadata and statistics
│       ├── list                                  # List keys; optionally include batch stats/last-usage
│       └── show                                  # Safe summary for one key by id/name
├── key                                           # API-key-only self-inspection commands
│   └── info                                      # Current API key information, availability, and usage
└── service                                       # Guarded wrapper for official crs lifecycle semantics
    ├── install                                   # Plan by default; --execute runs crs install remotely
    ├── update                                    # Plan by default; --execute runs crs update remotely
    ├── start                                     # Plan by default; --execute runs crs start remotely
    ├── stop                                      # Plan by default; --execute runs crs stop remotely
    ├── restart                                   # Plan by default; --execute runs crs restart remotely
    ├── status                                    # Plan by default; --execute runs crs status remotely
    ├── switch-branch                             # Plan by default; --execute runs crs switch-branch remotely
    └── update-pricing                            # Plan by default; --execute runs crs update-pricing remotely
```

## Coverage matrix

| Capability | Implemented commands | Boundary |
|---|---|---|
| CRS health | `chatcrs health` | Read-only HTTP health summary |
| Topology summary | `chatcrs inspect` | Read-only aggregation of known instances, edge state, and runtime status; no config writes |
| Admin login | `chatcrs admin login` | Verifies credentials; reports token presence only |
| Account usage | `chatcrs admin accounts usage` | Admin HTTPS API; redacted usage/status/scheduling summary |
| Account status reset | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS reset-status; not an OAuth refresh-token force-refresh |
| API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted key values, status, limits, stats, and last-usage summaries |
| API-key-only self info | `chatcrs key info` | No administrator login required |
| Official lifecycle | `chatcrs service install`, `chatcrs service update`, `chatcrs service start`, `chatcrs service stop`, `chatcrs service restart`, `chatcrs service status`, `chatcrs service switch-branch`, `chatcrs service update-pricing` | Plan by default; `--execute` SSHes into the target app directory and runs official `crs ...` |

## Registered command list

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs inspect` | Read-only known CRS topology inspection |
| `chatcrs admin login` | Admin login verification |
| `chatcrs admin accounts usage` | Account usage inspection |
| `chatcrs admin accounts refresh-status` | CRS account reset-status |
| `chatcrs admin keys list` | API key list and statistics |
| `chatcrs admin keys show` | Single API key summary |
| `chatcrs key info` | API-key-only self check |
| `chatcrs service install` | Official crs install semantics |
| `chatcrs service update` | Official crs update semantics |
| `chatcrs service start` | Official crs start semantics |
| `chatcrs service stop` | Official crs stop semantics |
| `chatcrs service restart` | Official crs restart semantics |
| `chatcrs service status` | Official crs status semantics |
| `chatcrs service switch-branch` | Official crs switch-branch semantics |
| `chatcrs service update-pricing` | Official crs update-pricing semantics |

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
chatcrs admin login --json-output
chatcrs admin accounts usage --json-output
chatcrs admin accounts refresh-status <account_id> --json-output
chatcrs admin accounts refresh-status <account_id> --execute --json-output
chatcrs admin keys list --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --json-output
```

!!! warning "Meaning of refresh-status"
    `refresh-status` resets CRS account state. It does not force-refresh Codex/OpenAI OAuth refresh tokens.

## API-key-only { #api-key-only }

```text
chatcrs key                                       # API-key-only self-inspection entry point
└── info                                          # Current API key information, availability, and usage
```

```bash
chatcrs key info --json-output
chatcrs key info --path /api/v1/key-info --json-output
```

## Service lifecycle { #service-lifecycle }

`chatcrs service` absorbs official `/usr/bin/crs` lifecycle management semantics without directly running unsafe actions. It SSHes into the target CRS app directory and runs official `crs ...`; default output is a plan, and only `--execute` mutates the remote target.

```text
chatcrs service                                   # Remote wrapper for official crs lifecycle
├── install                                       # Plan by default; --execute runs crs install
├── update                                        # Plan by default; --execute runs crs update
├── start                                         # Plan by default; --execute runs crs start
├── stop                                          # Plan by default; --execute runs crs stop
├── restart                                       # Plan by default; --execute runs crs restart
├── status                                        # Plan by default; --execute runs crs status
├── switch-branch                                 # Plan by default; --execute runs crs switch-branch <branch>
└── update-pricing                                # Plan by default; --execute runs crs update-pricing
```

Common target options:

```bash
chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --json-output

chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --execute   --json-output
```

Environment defaults:

```text
CHATCRS_SSH_ALIAS   # example: tencent.am
CHATCRS_APP_DIR     # example: /home/zhihong/claude-relay-service/app
CHATCRS_CRS_COMMAND # example: /usr/bin/crs; default: crs
```

!!! note "Output redaction"
    Service commands redact Authorization headers, tokens, passwords, API keys, and CRS `cr_...` shaped values from captured stdout/stderr before rendering.

## Safety boundaries { #safety-boundaries }

- The packaged CLI now keeps only remote admin/key inspection, service lifecycle wrapping, health, and read-only inspect.
- Web-edge work, formal traffic switching, image capability acceptance, and isolated debug-runtime operations are intentionally outside the registered command surface; when needed, the model should execute them from the active task runbook, scripts, and SSH/Nginx tools.
- Any production mutation still requires explicit `--execute` plus a confirmed target, working directory, rollback boundary, and redacted output.
- API keys, tokens, passwords, and OAuth credentials must not appear in chat, docs, PR bodies, or command output.
