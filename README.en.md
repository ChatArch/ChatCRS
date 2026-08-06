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

ChatCRS is ChatArch's remote CRS operations CLI. It provides remote CRS admin/API-key inspection, guarded CRS service lifecycle management, health, and read-only topology summaries. Web-edge work, formal switching, image capability acceptance, and isolated debug-runtime operations are not registered package commands; the model handles them from the active task runbook when needed.

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
├── inspect
├── admin login
├── admin accounts usage / refresh-status
├── admin keys list / show
├── key info
├── service install / update / start / stop / restart
└── service status / switch-branch / update-pricing
```

## Remote admin and API key

```bash
chatcrs admin login --json-output
chatcrs admin accounts usage --json-output
chatcrs admin accounts refresh-status <account_id> --json-output
chatcrs admin accounts refresh-status <account_id> --execute --json-output
chatcrs admin keys list --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --json-output
chatcrs key info --json-output
```

## Service lifecycle

```bash
chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --json-output

chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --execute   --json-output
```

`chatcrs service install/update/start/stop/restart/switch-branch/update-pricing` absorbs official `crs` management semantics. It prints a remote execution plan by default; only `--execute` runs the official `crs ...` command through SSH in the target app directory. Captured stdout/stderr are redacted before rendering.

Service target defaults can live in the ChatEnv `Chatcrs` active profile (`~/.chatarch/envs/Chatcrs/.env`): `CHATCRS_SSH_ALIAS`, `CHATCRS_APP_DIR`, and `CHATCRS_CRS_COMMAND`. Resolution order is explicit CLI options > process environment variables > ChatEnv profile > package defaults.

## Production safety

ChatCRS does not directly execute production traffic switching or edge-configuration changes. Production updates remain in the reviewed, dry-run-by-default release/cutover workflow.

See:

- `docs/cli.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`
