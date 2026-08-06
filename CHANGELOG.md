# Changelog

## Unreleased

### Changed

- Remove host-bound remote service lifecycle commands from the registered CLI so
  ChatCRS is HTTP/API-first by default.
- Keep one canonical CRS ChatEnv namespace under `~/.chatarch/envs/CRS/` with
  `CRS_API_BASE`, `CRS_API_KEY`, `CRS_USERNAME`, `CRS_PASSWORD`, and
  `CRS_ACCESS_TOKEN`.
- Document server-local lifecycle, topology, edge, Redis, and release/cutover
  workflows as candidate capabilities that need an explicit server-local or
  host-agent design before they can be reintroduced.
- Add a CLI-to-HTTP interface map that ties every registered CLI leaf to its
  CRS endpoint, auth source, mutation boundary, and importable Python API.
- Keep API-key-only `chatcrs key info --help` focused on key/base-url/profile
  options and wrap health connection failures as clean Click errors.

## 2026-08-04 - 0.2.1

### Added

- Add remote CRS Admin/API-key inspection commands: `chatcrs admin login`,
  `chatcrs admin accounts usage`, `chatcrs admin accounts refresh-status`,
  `chatcrs admin keys list`, `chatcrs admin keys show`, and `chatcrs key info`.
- Document the current implemented CLI tree with right-side command comments.
- Align the MkDocs site with the ChatArch documentation pattern: card-based home
  pages, i18n suffix pages, canonical ChatArch docs URL, and a segmented CLI
  reference.
- Add Preview Docs and Deploy Docs workflows for the ChatArch project-pages
  documentation path.

### Changed

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

- Add fixed-target debug management tree for status, redacted logs,
  guarded restart, safe settings, and exact-SHA upgrade.
- Add explicit execution gates, isolation validation, backups, health checks,
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
