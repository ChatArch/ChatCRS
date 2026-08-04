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

ChatCRS 是 ChatArch 的 CRS 运维与验收 CLI，提供只读拓扑检查、远程 CRS 管理员/API-key 查询、受控 CRS service 生命周期管理、API-key/Images 验收、Nginx 切流规划，以及固定隔离边界的 debug runtime 管理。

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
├── local verify
├── verify sidecar
├── verify images
├── admin login
├── admin accounts usage / refresh-status
├── admin keys list / show
├── key info
├── service install / update / start / stop / restart
├── service status / switch-branch / update-pricing
├── nginx plan-cutover
├── cutover precheck
└── debug
    ├── status
    ├── logs
    ├── restart
    ├── settings show / set
    └── upgrade plan / apply
```

## 调试服务管理

`chatcrs debug` 固定管理：

- `/home/zhihong/claude-relay-service-independent/app`
- `127.0.0.1:12392`
- Redis `127.0.0.1:6382 DB0`
- tmux `crs-debug-12392`

查看状态：

```bash
chatcrs debug status --json-output
chatcrs debug logs --lines 100
chatcrs debug settings show --json-output
chatcrs debug upgrade plan --json-output
```

Restart/settings/upgrade 默认只返回计划。真正执行必须显式加 `--execute`；settings/upgrade 会备份并在失败时恢复。

```bash
chatcrs debug restart --execute --json-output
chatcrs debug settings set LOG_LEVEL info --execute --json-output
chatcrs debug upgrade apply --expected-sha <40-char-sha> --execute --json-output
```

隔离字段 `HOST`、`PORT`、`REDIS_*`、JWT 和加密密钥不能由 settings 修改。Debug 写操作不接受自定义 app/port，因此不能改去操作生产。

## Images 验收

默认只验证 key-info 和普通 `gpt-5.5`，不生成图片：

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --json-output
```

只有显式添加 `--execute-image` 才调用图片接口并写 PNG。

## 生产安全

以下命令默认是只读/plan-only：

```bash
chatcrs inspect --json-output
chatcrs verify sidecar --json-output
chatcrs nginx plan-cutover --json-output
chatcrs cutover precheck --json-output
chatcrs service update --ssh-alias tencent.am --app-dir /home/zhihong/claude-relay-service/app --json-output
```

`chatcrs service install/update/start/stop/restart/switch-branch/update-pricing` 吸收官方 `crs` 管理语义；默认只输出远程执行计划，只有显式 `--execute` 才通过 SSH 在目标 app 目录执行官方 `crs ...`。stdout/stderr 会做敏感信息脱敏。

ChatCRS 当前不直接执行生产切流。生产更新继续使用经过审核、默认 dry-run 的独立 release/cutover 流程。

更多内容见 `docs/`，尤其是：

- `docs/cli.md`
- `docs/debug-service.md`
- `docs/production-maintenance.md`
