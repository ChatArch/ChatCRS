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

ChatCRS 是 ChatArch 的 CRS 远程运维 CLI，提供远程 CRS 管理员/API-key 查询、受控 CRS service 生命周期管理、health 和只读拓扑摘要。Web edge、正式切换、图片能力验收和隔离调试 runtime 不作为包内注册命令；需要时按当前任务 runbook 由模型操作。

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
├── inspect
├── admin login
├── admin accounts usage / refresh-status
├── admin keys list / show
├── key info
├── service install / update / start / stop / restart
└── service status / switch-branch / update-pricing
```

## 远程管理员与 API key

```bash
chatcrs admin login --json-output
chatcrs admin accounts usage --json-output
chatcrs admin accounts refresh-status <account_id> --json-output
chatcrs admin accounts refresh-status <account_id> --execute --json-output
chatcrs admin keys list --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --json-output
chatcrs key info --json-output
```

## Service 生命周期

```bash
chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --json-output

chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --execute   --json-output
```

`chatcrs service install/update/start/stop/restart/switch-branch/update-pricing` 吸收官方 `crs` 管理语义；默认只输出远程执行计划，只有显式 `--execute` 才通过 SSH 在目标 app 目录执行官方 `crs ...`。stdout/stderr 会做敏感信息脱敏。

Service target 默认值可放在 ChatEnv `Chatcrs` active profile（`~/.chatarch/envs/Chatcrs/.env`）：`CHATCRS_SSH_ALIAS`、`CHATCRS_APP_DIR`、`CHATCRS_CRS_COMMAND`。解析顺序为显式 CLI 参数 > 进程环境变量 > ChatEnv profile > 包内默认值。

## 生产安全

ChatCRS 当前不直接执行生产切流或 edge 配置变更。生产更新继续使用经过审核、默认 dry-run 的独立 release/cutover 流程。

更多内容见：

- `docs/cli.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`
