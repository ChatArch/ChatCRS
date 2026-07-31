# Changelog

## Unreleased - 0.2.0

### Added

- Add fixed-target `chatcrs debug` management tree for status, redacted logs,
  guarded restart, safe settings, and exact-SHA upgrade.
- Add explicit `--execute` gates, isolation validation, backups, health checks,
  audit records, and failure recovery for debug mutations.
- Add Redis-authenticated debug status without exposing the password in argv or
  output.
- Add ChatEnv fields for OpenAI env-file and audit-directory configuration.
- Add complete MkDocs operations site and CI strict documentation build.
- Add target wrappers and deployment guidance for debug/candidate/production.

### Changed

- Replace scaffold README copy with bilingual operations documentation.
- Bump package version to 0.2.0.

### Security

- Protect host/port/Redis/JWT/encryption settings from debug settings mutation.
- Prevent debug mutation commands from accepting arbitrary app paths or ports.

## 2026-06-29 - 0.1.0

### Added

- Initial ChatCRS package scaffold with `chatcrs` CLI.
- ChatEnv provider entry point for `chatcrs` configuration discovery.
- CI and tag-driven PyPI Trusted Publisher workflow scaffold.
- Local CRS health and verification commands.
- Read-only CRS inspection, sidecar verification, Nginx cutover planning, and
  formal cutover precheck.
- Staged CRS API-key and Images acceptance flow.
