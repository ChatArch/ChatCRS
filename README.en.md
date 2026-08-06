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
chatcrs
├── health
├── admin login
├── admin accounts usage / refresh-status
├── admin keys list / show
├── key info
└── service install / update / start / stop / restart / status / switch-branch / update-pricing
```

## HTTP/Admin and API key

```bash
chatcrs health --base-url https://crs.example.com --json-output
chatcrs admin login --profile admin --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --execute --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --profile admin --json-output
chatcrs key info --profile admin --json-output
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

ChatCRS uses one CRS ChatEnv profile namespace. By default it reads `~/.chatarch/envs/CRS/admin.env`; use `--profile` for another profile.

Canonical fields:

```text
CRS_API_BASE
CRS_API_KEY
CRS_USERNAME
CRS_PASSWORD
CRS_ACCESS_TOKEN
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
