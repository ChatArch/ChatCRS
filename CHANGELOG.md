# Changelog

## 2026-06-29 - 0.1.0

### Added

- Initial ChatCRS package scaffold with `chatcrs` CLI.
- ChatEnv provider entry point for `chatcrs` configuration discovery.
- CI and tag-driven PyPI Trusted Publisher workflow scaffold.
## Unreleased

- Add local CRS verification commands: `chatcrs health` and `chatcrs local verify`.
- Add ChatEnv fields for CRS base URL, local secrets file, and CRS API key.
- Add read-only CRS management helpers for inspect, sidecar verification, Nginx cutover planning, and formal cutover precheck.
- Add thin CLI wrappers around importable Python APIs.
