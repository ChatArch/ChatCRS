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
chatcrs
├── health
├── admin login
├── admin accounts usage / refresh-status
├── admin keys list / show
├── key info
└── service install / update / start / stop / restart / status / switch-branch / update-pricing
```

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

ChatCRS 使用一套 CRS ChatEnv profile，默认读取 `~/.chatarch/envs/CRS/admin.env`，也可以用 `--profile` 指定其它 profile。

Canonical 字段：

```text
CRS_API_BASE
CRS_API_KEY
CRS_USERNAME
CRS_PASSWORD
CRS_ACCESS_TOKEN
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
