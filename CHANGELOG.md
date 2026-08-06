# Changelog

## Unreleased

### Changed

- Let `chatcrs service ...` resolve `CHATCRS_SSH_ALIAS`, `CHATCRS_APP_DIR`, and
  `CHATCRS_CRS_COMMAND` from the ChatEnv `Chatcrs` active profile before falling
  back to package defaults, so local service management can be configured once
  without repeating target arguments.

## 2026-08-04 - 0.2.1

### Added

- Add remote CRS Admin/API-key inspection commands: `chatcrs admin login`,
  `chatcrs admin accounts usage`, `chatcrs admin accounts refresh-status`,
  `chatcrs admin keys list`, `chatcrs admin keys show`, and `chatcrs key info`.
- Add guarded `chatcrs service` lifecycle commands that absorb official `crs`
  management semantics for `install`, `update`, `start`, `stop`, `restart`,
  `status`, `switch-branch`, and `update-pricing`.
- Document the current implemented CLI tree with right-side command comments.
- Align the MkDocs site with the ChatArch documentation pattern: card-based home
  pages, i18n suffix pages, canonical ChatArch docs URL, and a segmented CLI
  reference.
- Add Preview Docs and Deploy Docs workflows for the ChatArch project-pages
  documentation path.

### Changed

- Keep service lifecycle actions dry-run/plan-only by default; only `--execute`
  runs the official `crs ...` command over SSH in the target app directory.
- Redact captured service stdout/stderr, including Authorization headers and
  CRS API-key-shaped `cr_...` values.
- Add a CLI-doc alignment test so the registered leaf commands exactly match
  the user-approved final command tree and stale operational commands stay out
  of the Chinese and English CLI reference pages.
- Remove legacy local verification, special acceptance, edge cutover, and debug
  runtime operations from the registered package CLI surface; those workflows
  move to task-specific runbooks and model-operated tooling.
- Improve remote Admin API login failures so the CLI reports safe status/reason
  details such as `status=401 reason=Invalid username or password` without
  leaking credentials.
- Bump package version to 0.2.1.

## 2026-08-04 - 0.2.0

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
