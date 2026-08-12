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

## CLI tree

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
├── codex  # Direct OpenAI Codex account token and usage helpers.
│   ├── token  # Manage OpenAI OAuth tokens through the ChatEnv OpenAI token store.
│   │   ├── status [--profile <PROFILE>] [--json-output]  # Show cached OpenAI OAuth token metadata without printing tokens.
│   │   └── refresh [--profile <PROFILE>] [--refresh-token <REFRESH-TOKEN>] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Refresh an OpenAI OAuth access token without printing token values.
│   ├── account [--profile <PROFILE>] [--access-token <ACCESS-TOKEN>] [--refresh/--no-refresh] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Read OpenAI Codex account metadata directly from OpenAI.
│   └── usage [--profile <PROFILE>] [--account-id <ACCOUNT-ID>] [--access-token <ACCESS-TOKEN>] [--refresh/--no-refresh] [--client-id <CLIENT-ID>] [--timeout <TIMEOUT>] [--json-output]  # Read Codex usage and quota metadata directly from OpenAI.
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

Run `chatcrs --tree` to read back the same command tree from the live Click registry.


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
chatenv token refresh OpenAI default
chatcrs codex account --profile default --json-output
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

ChatCRS uses one CRS ChatEnv profile namespace. The default profile is `admin`; use `--profile` for another profile. Public docs describe field categories only and intentionally omit concrete secret-file paths or secret-bearing env key names.

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
