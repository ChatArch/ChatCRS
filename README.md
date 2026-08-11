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

ChatCRS 是 ChatArch 的 CRS 管理 CLI。外部管理面优先使用 CRS HTTP/Admin API；`service` 域是 server-local surface，只在 CRS 服务器本机 shell 里操作本机 CRS checkout / Node runtime / `crs` executable。

Images 验收、debug runtime、Nginx/edge、release/cutover 等花哨/任务型能力不作为当前包内命令暴露；这些属于代理站维护、专项验收或运维 runbook，后续需要时单独设计。

## 安装与开发

```bash
python -m pip install -e '.[dev,docs]'
chatcrs --help
chatcrs --version
python -m pytest -q
python -m mkdocs build --strict
python -m build
```

完整文档使用 MkDocs，本地预览：

```bash
python -m mkdocs serve
```

线上文档：https://arch.gh.wzhecnu.cn/ChatCRS/

## CLI 树

```text
chatcrs  # CRS HTTP/API helpers plus server-local service commands for ChatArch.
├── --help  # Show this help message.
├── --version  # Show the installed package version.
├── --tree  # Print the registered command tree.
├── health [--base-url <BASE-URL>] [--json-output]  # Verify the CRS /health endpoint.
├── admin  # Remote CRS administrator operations via HTTPS Admin API.
│   ├── login [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--json-output]  # Verify CRS admin login without printing the session token.
│   ├── accounts  # Inspect or refresh remote CRS account state via HTTP Admin API.
│   │   ├── usage [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--json-output]  # List OpenAI/Codex account usage and scheduling metadata.
│   │   └── refresh-status <ACCOUNT-ID> [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--execute] [--json-output]  # Reset a CRS OpenAI account status after transient failures.
│   └── keys  # Inspect remote CRS API keys with admin privileges.
│       ├── list [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--include-stats] [--time-range <TIME-RANGE>] [--json-output]  # List CRS API key metadata, optionally including usage stats.
│       └── show <KEY-ID> [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--username <USERNAME>] [--password <PASSWORD>] [--admin-token <ADMIN-TOKEN>] [--timeout <TIMEOUT>] [--include-stats/--no-include-stats] [--time-range <TIME-RANGE>] [--json-output]  # Show one CRS API key by id or name.
├── key  # CRS API-key-only operations that do not require admin login.
│   └── info [--profile <PROFILE>] [--base-url <BASE-URL>] [--api-key <API-KEY>] [--timeout <TIMEOUT>] [--path <INFO-PATH>] [--json-output]  # Query CRS key-info using only a CRS API key.
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

运行 `chatcrs --tree` 可从实际 Click 注册表回读同一棵命令树。


## HTTP/Admin 与 API key

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

这些命令应安装在目标 CRS 服务器上，并在该服务器本机执行：

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --execute --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

`status` 默认执行本机只读 `crs status`。其它 service mutation 默认 dry-run，需要 `--execute` 才执行。

## 配置

ChatCRS 使用一套 CRS ChatEnv profile；默认 profile 是 `admin`，也可以用 `--profile` 指定其它 profile。公开文档只描述字段类别，不写具体 secret 文件路径或 secret-bearing env key 名。

Canonical 字段类别：

```text
HTTP base URL
caller API key
admin username
admin password
admin bearer/session token
```

Service-local 目标不进入第二套 ChatEnv namespace；用当前工作目录或 `--app-dir` / `--crs-command` 指定本机 checkout 和 executable。

敏感字段只应存在于 ChatEnv 或进程环境中，不进入命令行参数、文档、PR body 或日志输出。Profile 文件应使用 `0600` 权限。

## 生产安全

外部管理只能使用 HTTP/Admin API；没有 HTTP lifecycle 接口时，不用远端执行补洞。要么新增 CRS API/host-agent，要么在目标服务器本机运行 `chatcrs service ...`。

更多内容见：

- `docs/cli.md`
- `docs/interfaces.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`
