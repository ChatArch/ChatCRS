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

ChatCRS is ChatArch's HTTP/API-first CRS management CLI. The current registered commands cover CRS HTTP health, administrator HTTP API inspection/status operations, and CRS API-key self checks.

Host lifecycle, process management, Nginx/edge work, Redis snapshots, release/cutover workflows, debug runtimes, and image capability acceptance are not exposed as package commands today. They are server-local operations or task-runbook workflows; if they are reintroduced later, they must be designed as explicit server-local/host-agent capabilities rather than ordinary HTTP management commands.

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
└── key info
```

## Remote admin and API key

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

Sensitive fields should live only in ChatEnv or the process environment, never in command arguments, documentation, PR bodies, or logs. Profile files should use `0600` permissions.

## Production safety

ChatCRS does not directly execute production traffic switching, service process control, or edge-configuration changes. Production updates remain in the reviewed, dry-run-by-default release/cutover workflow.

See:

- `docs/cli.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`
