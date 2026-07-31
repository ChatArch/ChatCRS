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

ChatCRS is ChatArch's CRS operations and acceptance CLI. It provides read-only
topology inspection, API-key/Images verification, Nginx cutover planning, and
guarded management of the isolated debug runtime.

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

## CLI tree

```text
chatcrs
├── health
├── inspect
├── local verify
├── verify sidecar
├── verify images
├── nginx plan-cutover
├── cutover precheck
└── debug
    ├── status
    ├── logs
    ├── restart
    ├── settings show / set
    └── upgrade plan / apply
```

## Debug runtime management

`chatcrs debug` is hard-bound to:

- `/home/zhihong/claude-relay-service-independent/app`
- `127.0.0.1:12392`
- Redis `127.0.0.1:6382 DB0`
- tmux session `crs-debug-12392`

Read-only commands:

```bash
chatcrs debug status --json-output
chatcrs debug logs --lines 100
chatcrs debug settings show --json-output
chatcrs debug upgrade plan --json-output
```

Restart, setting changes, and upgrades are dry-run by default. Mutation requires
`--execute`; settings/upgrades create backups and recover on failure.

```bash
chatcrs debug restart --execute --json-output
chatcrs debug settings set LOG_LEVEL info --execute --json-output
chatcrs debug upgrade apply --expected-sha <40-char-sha> --execute --json-output
```

Isolation settings (`HOST`, `PORT`, `REDIS_*`, JWT, and encryption keys) cannot
be changed through the settings command. Debug mutation commands accept no
custom app or port, so they cannot be redirected to production.

## Images acceptance

The default flow verifies key-info and a regular `gpt-5.5` request without
creating an image:

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --json-output
```

Only `--execute-image` invokes the image endpoint and writes a PNG.

## Production safety

These commands are read-only or plan-only:

```bash
chatcrs inspect --json-output
chatcrs verify sidecar --json-output
chatcrs nginx plan-cutover --json-output
chatcrs cutover precheck --json-output
```

ChatCRS does not currently execute production cutovers. Production updates remain
in the reviewed, dry-run-by-default release/cutover workflow.

See `docs/cli.md`, `docs/debug-service.md`, and
`docs/production-maintenance.md` for details.
