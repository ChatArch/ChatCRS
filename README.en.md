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

## Quick Start

```bash
pip install -e ".[dev]"
chatcrs --help
chatcrs --version
python -m pytest -q
python -m build
```

## CLI Contract

This template depends on `chatstyle>=0.1.0,<0.2.0` and `chatenv>=0.2.0,<0.3.0`. New commands should prefer:

- `CommandSchema` / `CommandField` for inputs.
- `add_interactive_option()` for the shared `-i/-I` switch.
- `resolve_command_inputs()` for missing args, defaults, TTY behavior, and validation.
- Generate `config.py` and a `chatenv.configs` entry point by default so the package is ChatEnv-discoverable; use `--without-chatenv-provider` only when ChatEnv integration is intentionally not needed.

## Layout

- `src/`: package source code
- `tests/code-tests/`: code tests and migrated historical tests
- `tests/cli-tests/`: real CLI tests, doc-first
- `tests/mock-cli-tests/`: mock/fake CLI tests, doc-first

## Development Notes

See `DEVELOP.md` and `AGENTS.md` before expanding the scaffold.

## CRS API-key Images acceptance

`verify images` runs staged CRS API-key verification. By default it only calls `key-info` and a regular `gpt-5.5` Responses request; it does not generate an image:

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --json-output
```

After the first two gates pass, add `--execute-image` explicitly to call `gpt-image-2`, consume image quota, and write a PNG:

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --execute-image \
  --output ./chatcrs-image-acceptance.png \
  --json-output
```

The API key is read only from the env file and is never included in CLI arguments or output. Without `--openai-env-file`, ChatCRS checks `CHATCRS_OPENAI_ENV_FILE` and then `~/.chatarch/envs/OpenAI/.env`. JSON reports `mutated=false` for key/regular-model preflight and `mutated=true` after a real Images request.
