# CLI and HTTP Interface Map

This page aligns the remaining ChatCRS CLI surface with the CRS HTTP/Admin API. It documents only commands that are registered and tested today. Server-local capabilities without an HTTP/Admin endpoint are not represented as ordinary ChatCRS CLI commands.

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
└── key                            # API-key-only self inspection
    └── info                       # GET /openai/key-info
```

## CLI to HTTP endpoint

| CLI | HTTP endpoint | Authentication source | Mutation | Python API |
|---|---|---|---|---|
| `chatcrs health` | `GET /health` | None; only `CRS_API_BASE` or `--base-url` | No | `chatcrs.local.health_check` |
| `chatcrs admin login` | `POST /web/auth/login` | `CRS_USERNAME` + `CRS_PASSWORD`, or explicit options | No durable mutation; verifies login and reports token presence | `CrsHttpClient.login` |
| `chatcrs admin accounts usage` | `GET /admin/openai-accounts` | Admin bearer token, resolved from profile/login | No | `CrsHttpClient.accounts_usage` |
| `chatcrs admin accounts refresh-status` | `POST /admin/openai-accounts/{account_id}/reset-status` | Admin bearer token | No by default; calls endpoint only with `--execute` | `CrsHttpClient.reset_openai_account_status` |
| `chatcrs admin keys list` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_keys` |
| `chatcrs admin keys show` | `GET /admin/api-keys`, optional `POST /admin/api-keys/batch-stats`, `POST /admin/api-keys/batch-last-usage` | Admin bearer token | No | `CrsHttpClient.api_key_detail` |
| `chatcrs key info` | `GET /openai/key-info` | Caller CRS API key: `CRS_API_KEY` or `--api-key` | No | `CrsHttpClient.key_info` |

## Configuration boundary

| Field | Purpose | Used by |
|---|---|---|
| `CRS_API_BASE` | CRS HTTP base URL | All commands |
| `CRS_API_KEY` | Caller API key | `chatcrs key info` |
| `CRS_USERNAME` | Admin username | `chatcrs admin login` and admin commands that need a login-derived token |
| `CRS_PASSWORD` | Admin password | `chatcrs admin login` and admin commands that need a login-derived token |
| `CRS_ACCESS_TOKEN` | Admin bearer token | `chatcrs admin ...` |

The canonical ChatEnv namespace is `CRS`: `~/.chatarch/envs/CRS/<profile>.env`. The packaged CLI does not maintain a second service-target profile namespace.

## Current HTTP coverage

<div class="grid cards" markdown>

-   **Health**

    ---

    `GET /health` checks whether the selected CRS service responds and returns a read-only health summary.

-   **Admin login**

    ---

    `POST /web/auth/login` verifies admin credentials and obtains an admin bearer token; ChatCRS reports only token presence and never prints the token.

-   **Accounts**

    ---

    `GET /admin/openai-accounts` reads account usage, status, and scheduling metadata. `POST /admin/openai-accounts/{account_id}/reset-status` resets CRS-local state only when `--execute` is supplied.

-   **API keys**

    ---

    `GET /admin/api-keys` reads key metadata. `POST /admin/api-keys/batch-stats` and `POST /admin/api-keys/batch-last-usage` add usage statistics and last-account attribution.

-   **Caller key info**

    ---

    `GET /openai/key-info` checks a caller CRS API key and does not require admin credentials.

</div>

## Explicit gaps

These capabilities do not have a confirmed CRS HTTP/Admin endpoint today, so ChatCRS does not register ordinary commands for them:

| Gap | Current handling |
|---|---|
| service lifecycle: status/update/restart/start/stop | Report the gap; add a restricted HTTP management endpoint or a separate host-agent design first |
| API key create/update/delete/restore/tag/index | Confirm or add Admin HTTP endpoints first, then implement with dry-run/execute and redacted audit rules |
| account add/delete/toggle/schedulable/test | Confirm or add Admin HTTP endpoints first; do not substitute local scripts or direct database writes |
| topology/edge/Redis/Nginx/release/cutover | Deployment/operations-layer work, outside the ordinary CRS HTTP client surface |

## Update rules

- Before adding a CLI command, confirm the live HTTP/Admin endpoint and add it to this page.
- If no endpoint exists, document the capability as a gap or an external host-agent design, not as an implemented CLI command.
- When command registrations change, update `docs/cli.md`, this page, README, CHANGELOG, and the CLI/docs alignment tests together.
- Keep all outputs redacted: API keys, tokens, passwords, and OAuth credentials are reported only as presence, counts, status, or `[REDACTED]`.
