# CLI Tree

This page lists **commands that are implemented and registered in code**. The command tree is verified against `chatcrs.cli` Click registration; command changes must keep this page in sync.

## Top-level commands

```text
chatcrs                                           # ChatArch CRS operations and acceptance CLI
├── health                                        # Check the selected CRS /health endpoint
├── local                                         # Local CRS verification entry point
│   └── verify                                    # Verify local health/web/API/admin login
├── verify                                        # Sidecar and special-output acceptance
│   ├── sidecar                                   # Read-only 12390/12391 sidecar verification
│   └── images                                    # Key-info/Responses by default; image generation requires opt-in
├── admin                                         # Remote CRS Admin API operations over HTTPS
│   ├── login                                     # Verify admin login without printing the session token
│   ├── accounts                                  # Inspect or refresh OpenAI/Codex account state
│   │   ├── usage                                 # Account usage, scheduling, and availability state
│   │   └── refresh-status                        # Dry-run by default; --execute calls CRS reset-status
│   └── keys                                      # Inspect CRS API key metadata and statistics
│       ├── list                                  # List keys; optionally include batch stats/last-usage
│       └── show                                  # Safe summary for one key by id/name
├── key                                           # API-key-only self-inspection commands
│   └── info                                      # Current API key information, availability, and usage
├── service                                       # Guarded wrapper for official crs lifecycle semantics
│   ├── install                                   # Plan by default; --execute runs crs install remotely
│   ├── update                                    # Plan by default; --execute runs crs update remotely
│   ├── start                                     # Plan by default; --execute runs crs start remotely
│   ├── stop                                      # Plan by default; --execute runs crs stop remotely
│   ├── restart                                   # Plan by default; --execute runs crs restart remotely
│   ├── status                                    # Plan by default; --execute runs crs status remotely
│   ├── switch-branch                             # Plan by default; --execute runs crs switch-branch remotely
│   └── update-pricing                            # Plan by default; --execute runs crs update-pricing remotely
├── nginx                                         # Nginx CRS routing planning
│   └── plan-cutover                              # Render a cutover diff; do not write or reload
├── cutover                                       # Formal single-active cutover checks
│   └── precheck                                  # Read-only cutover precheck
├── debug                                         # Manage only the isolated debug runtime, never production
│   ├── status                                    # Debug health/tmux/Redis/Git/safe settings
│   ├── logs                                      # Redacted debug log tail
│   ├── restart                                   # Plan by default; --execute restarts debug tmux
│   ├── settings                                  # Show or update whitelisted debug settings
│   │   ├── show                                  # Show non-sensitive settings
│   │   └── set                                   # Plan by default; --execute mutates whitelisted fields
│   └── upgrade                                   # Debug checkout upgrade flow
│       ├── plan                                  # Compare current debug checkout with ChatArch dev
│       └── apply                                 # Plan by default; --execute upgrades by reviewed SHA
└── inspect                                       # Read-only inspection for known production/sidecar topology
```

## Coverage matrix

| Discussed capability | Implemented commands | Boundary |
|---|---|---|
| Per-account usage | `chatcrs admin accounts usage` | Admin HTTPS API; redacted usage/status/scheduling summary |
| Refresh/reset account status | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS `reset-status`; not an OAuth refresh-token force refresh |
| API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Masked key, status, limits, stats, and last-usage summaries |
| API-key-only self info | `chatcrs key info` | No admin credentials required |
| Official `/usr/bin/crs` lifecycle | `chatcrs service install`, `chatcrs service update`, `chatcrs service start`, `chatcrs service stop`, `chatcrs service restart`, `chatcrs service status`, `chatcrs service switch-branch`, `chatcrs service update-pricing` | Plan by default; `--execute` SSHes into the target app directory and runs official `crs ...` |
| Production/sidecar topology | `chatcrs inspect`, `chatcrs verify sidecar`, `chatcrs health` | Read-only |
| Nginx / cutover planning | `chatcrs nginx plan-cutover`, `chatcrs cutover precheck` | Diff/precheck only; no write and no reload |
| Images acceptance | `chatcrs verify images` | No image generation unless `--execute-image` is passed |
| Isolated debug runtime | `chatcrs debug status/logs/restart/settings/upgrade` | Pinned to 12392; mutations are plan-only by default |

## Registered command list

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs local verify` | Local CRS verification |
| `chatcrs verify sidecar` | Read-only sidecar acceptance |
| `chatcrs verify images` | Images/Responses acceptance |
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
| `chatcrs nginx plan-cutover` | Nginx cutover diff planning |
| `chatcrs cutover precheck` | Formal cutover precheck |
| `chatcrs debug status` | Debug runtime status |
| `chatcrs debug logs` | Redacted debug log reading |
| `chatcrs debug restart` | Debug restart plan/execute |
| `chatcrs debug settings show` | Show debug settings |
| `chatcrs debug settings set` | Mutate whitelisted debug settings |
| `chatcrs debug upgrade plan` | Debug upgrade plan |
| `chatcrs debug upgrade apply` | Debug upgrade execute |
| `chatcrs inspect` | Read-only known CRS topology inspection |

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
    `refresh-status` resets CRS account status. It does not force-refresh Codex/OpenAI OAuth refresh tokens.

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
chatcrs service update \
  --ssh-alias tencent.am \
  --app-dir /home/zhihong/claude-relay-service/app \
  --json-output

chatcrs service update \
  --ssh-alias tencent.am \
  --app-dir /home/zhihong/claude-relay-service/app \
  --execute \
  --json-output
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

### Read-only acceptance and production planning

```text
chatcrs health                                    # Check /health
chatcrs local verify                              # Verify local CRS
chatcrs verify sidecar                            # Verify sidecar topology
chatcrs verify images                             # Does not generate images by default
chatcrs inspect                                   # Read-only topology inspection
chatcrs nginx plan-cutover                        # Render Nginx diff
chatcrs cutover precheck                          # Evaluate single-active cutover conditions
```

These commands do not write Nginx, reload, or stop services.

## Debug runtime

```text
chatcrs debug                                     # Fixed isolated debug runtime
├── status                                        # health/tmux/Redis/Git/settings
├── logs                                          # Redacted log tail
├── restart                                       # Plan by default; --execute restarts tmux
├── settings                                      # Debug settings whitelist
│   ├── show                                      # Show public settings
│   └── set                                       # Plan by default; --execute mutates whitelisted fields
└── upgrade                                       # Debug checkout upgrade
    ├── plan                                      # Read-only SHA comparison
    └── apply                                     # Plan by default; --execute upgrades by reviewed SHA
```

Debug mutations are pinned to:

```text
app:   /home/zhihong/claude-relay-service-independent/app
HTTP:  127.0.0.1:12392
Redis: 127.0.0.1:6382 DB0
tmux:  crs-debug-12392
```

## Update rules

- New Click commands must update the top-level tree, the relevant group tree, and the coverage matrix.
- Removed or renamed commands must update tests, README files, MkDocs pages, and CHANGELOG.
- Planned but unimplemented capabilities must not appear in this command tree.
