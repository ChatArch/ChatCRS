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

ChatCRS 是 ChatArch 的 CRS HTTP/API 管理 CLI。当前注册命令只覆盖 CRS HTTP health、管理员 HTTP API 查询/状态操作，以及普通 CRS API key 自查。

Host lifecycle、进程管理、Nginx/edge、Redis 快照、release/cutover、debug runtime 和图片能力验收不作为当前包内命令暴露；这些属于服务端本机运维或任务 runbook，后续若要加回，必须设计为明确的 server-local/host-agent 能力，而不是普通 HTTP 管理命令。

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
└── key info
```

## 远程管理员与 API key

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

敏感字段只应存在于 ChatEnv 或进程环境中，不进入命令行参数、文档、PR body 或日志输出。Profile 文件应使用 `0600` 权限。

## 生产安全

ChatCRS 当前不直接执行生产切流、服务进程控制或 edge 配置变更。生产更新继续使用经过审核、默认 dry-run 的独立 release/cutover 流程。

更多内容见：

- `docs/cli.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`
