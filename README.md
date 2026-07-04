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

ChatCRS package scaffold.

## 快速开始

```bash
pip install -e ".[dev]"
chatcrs --help
chatcrs --version
chatcrs health --base-url http://127.0.0.1:12392 --json-output
chatcrs local verify --base-url http://127.0.0.1:12392 --secrets-file ~/.chatarch/crs/local/.local-secrets.env --json-output
python -m pytest -q
python -m build
```

## CLI 规范

这个模板默认依赖 `chatstyle>=0.1.0,<0.2.0` 和 `chatenv>=0.2.0,<0.3.0`，新的命令应优先使用：

- `CommandSchema` / `CommandField` 描述输入。
- `add_interactive_option()` 提供统一 `-i/-I`。
- `resolve_command_inputs()` 统一缺参补问、默认值、TTY 与校验。
- 默认生成 `config.py` 和 `chatenv.configs` entry point，使包可被 ChatEnv 发现；只有明确不需要 ChatEnv 接入时才使用 `--without-chatenv-provider`。

## 目录结构

- `src/`：包源码
- `tests/code-tests/`：代码测试和历史测试迁移
- `tests/cli-tests/`：真实 CLI 测试，doc-first
- `tests/mock-cli-tests/`：mock/fake CLI 测试，doc-first

## 开发说明

扩展脚手架前，先阅读 `DEVELOP.md` 和 `AGENTS.md`。

## Local CRS verification

ChatCRS can verify a local CRS instance installed by ChatUp:

```bash
chatcrs health --base-url http://127.0.0.1:12392 --json-output
chatcrs local verify --base-url http://127.0.0.1:12392 --secrets-file ~/.chatarch/crs/local/.local-secrets.env --json-output
```

`health` verifies `/health`. `local verify` additionally checks the admin SPA route, root redirect, auth-protected API route, and optional admin login using a local secrets file. Secret values are redacted from command output.

## Read-only CRS management helpers

ChatCRS includes read-only / plan-only commands for inspecting a CRS migration without mutating services or Nginx:

```bash
chatcrs inspect --json-output
chatcrs verify sidecar --json-output
chatcrs nginx plan-cutover --json-output
chatcrs cutover precheck --json-output
```

These commands are intentionally safe by default:

- they do not edit Nginx;
- they do not reload Nginx;
- they do not stop CRS services;
- they return structured output suitable for ChatUp or Python callers.

The core logic is also available as importable Python functions:

```python
from chatcrs.inspect import inspect_crs_layout
from chatcrs.verify import verify_sidecar
from chatcrs.nginx import plan_nginx_cutover
from chatcrs.cutover import formal_single_active_precheck
```
