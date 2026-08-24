# Changelog

## 2026-08-24 - 0.3.0

### Changed

- Move direct Codex OAuth profile and token storage to the ChatCRS-owned `Codex` ChatEnv namespace (`envs/Codex/<profile>.env` and `tokens/Codex/<profile>.json`) instead of ChatEnv's general `OpenAI` namespace.
- Register the durable Codex OAuth refresher as `chatenv token refresh Codex <profile>` and keep `chatcrs.codex_direct` as the importable Python API behind `chatcrs codex ...`.

## 2026-08-21 - 0.2.15

### Changed

- Replace the package-local Click tree renderer with `chatstyle.add_tree_option` from `chatstyle>=0.2.0,<0.3.0`, using `chatcrs` as the canonical root for console and module readback.
- Add `chatcrs --tree-brief`; the default `--tree` keeps parameter signatures while brief output retains registered command nodes and descriptions without signatures.
- Require `chatenv>=0.2.10,<0.3.0` and smoke both shared tree modes in package tests and CI.

## 2026-08-13 - 0.2.14

### Added

- Add non-secret OpenAI profile relay base URL support: `OPENAI_OAUTH_BASE_URL` overrides OAuth token/accounts upstreams and `CHATGPT_BACKEND_BASE_URL` overrides ChatGPT backend upstreams for `chatcrs codex ...`.
- Route `chatcrs codex usage` through the ChatGPT `wham/usage` endpoint while preserving the profile-only `account_id` token-store resolution path.

### Fixed

- Redact raw Codex usage identity fields (`account_id`, `email`, `user_id`) from JSON output and expose only `account_id_hash` plus usage/quota data.
- Make `chatcrs codex account` claims-first: it returns a safe account summary from access-token claims/token-store metadata and keeps the accounts API as a redacted probe so Cloudflare-protected accounts responses do not prevent account inspection.

## 2026-08-12 - 0.2.13

### Fixed

- Send Codex CLI-compatible headers for `chatcrs codex usage --profile <profile>` (`originator: codex_cli_rs`, canonical `ChatGPT-Account-ID`, JSON accept, and Codex CLI user-agent) so profile-only usage reads return the full upstream usage JSON instead of `403` HTML.

## 2026-08-12 - 0.2.12

### Fixed

- Change the Codex quota-smoke default model to live-validated `gpt-5.5`; `gpt-5` and `gpt-5.6` returned `400` for ChatGPT-account Codex on the production CRS host.
- Send Codex CLI-compatible headers for quota smoke (`originator: codex_cli_rs`, canonical `ChatGPT-Account-ID`, SSE accept/content-type) and use the Responses message input shape.

## 2026-08-12 - 0.2.11

### Added

- Add `chatcrs codex quota --profile <profile>` as the profile-only Codex quota smoke command. It uses the same OpenAI ChatEnv profile/token lifecycle, resolves account id from the OpenAI token store, calls `POST https://chatgpt.com/backend-api/codex/responses` with `store:false` / `stream:true`, and prints only status, account-id hash, and `x-codex-*` quota headers.

## 2026-08-12 - 0.2.10

### Fixed

- Let `chatcrs codex usage --profile <profile>` use a stored `account_id` in the `OpenAI` token-store profile before falling back to the OpenAI accounts API, so profile-only quota checks work for Codex OAuth tokens whose account-metadata endpoint returns 403.
- Preserve non-secret account mapping metadata (`account_id`, `account_label`, `account_name`) across `chatenv token refresh OpenAI <profile>` writes while keeping safe summaries limited to presence and account-id hash.

## 2026-08-12 - 0.2.9

### Fixed

- Register the ChatCRS Codex direct OAuth refresher as ChatEnv's `OpenAI` token provider so durable refresh uses `chatenv token refresh OpenAI <profile>` and writes `~/.chatarch/tokens/OpenAI/<profile>.json` through ChatEnv, not a hand-written Codex namespace.
- Make `chatcrs codex ...` consume ChatEnv's built-in `OpenAI` profiles (`envs/OpenAI/<profile>.env`) and OpenAI token store (`tokens/OpenAI/<profile>.json`) for access/refresh token state while preserving redacted CLI output.
- Allow `chatcrs codex usage --profile <profile>` to resolve the profile's unique OpenAI account id automatically before reading Codex quota/usage; ambiguous multi-account profiles still require `--account-id`.
- Hide the deprecated `chatcrs codex token refresh --save-token` compatibility flag from `chatcrs --tree` and docs so operators do not confuse one-off smoke refreshes with the ChatEnv token lifecycle.

### Changed

- Sync README, bilingual CLI docs, interface maps, and tests with the OpenAI ChatEnv token lifecycle contract.

## 2026-08-12 - 0.2.8

### Added

- Add `chatcrs codex ...` direct OpenAI Codex helpers for redacted OAuth token status/refresh, account metadata inspection, and usage/quota inspection without going through CRS Admin API.
- Add `chatcrs.codex_direct` as the importable Python API behind the new CLI leaves: `token_status`, `refresh_access_token`, `save_token_values`, `inspect_account`, and `inspect_usage`.

### Changed

- Sync README, bilingual CLI docs, interface maps, and CLI-doc alignment tests with the live `chatcrs --tree` Codex command surface.

## 2026-08-12 - 0.2.7

### Changed

- Add the MkDocs Material emoji renderer baseline so Material icon shorthand cannot leak into generated/live docs.
- Harden package publishing with a default-branch ancestry guard before OIDC PyPI publish.
- Expand CI to Python 3.10/3.11/3.12 and smoke the installed `chatcrs --version` / `chatcrs --tree` entry point.
- Sync the README CLI tree with the live runtime tree, including the Admin token-store commands.

## 2026-08-11 - 0.2.6

### Changed

- Require `chatenv>=0.2.7,<0.3.0` and register a `chatenv.token_refreshers` provider so `chatenv token refresh CRS <profile>` refreshes CRS Admin session tokens through ChatCRS-owned `/web/auth/login` semantics.
- Keep ChatEnv as the owner of token-store writes for provider refreshes; ChatCRS returns opaque `admin_session` values plus redacted base URL/user metadata and does not write the token file inside the provider hook.
- Make provider refresh use the matching stable `envs/CRS/<profile>.env` profile only, without falling back to ambient process env values for named profiles.

## 2026-08-11 - 0.2.5

### Changed

- Refactor ChatCRS Admin session caching to use ChatEnv 0.2.5's generic `TokenStore` substrate while keeping CRS-specific base URL matching and redacted status output.
- Remove `CRS_ACCESS_TOKEN` from the stable CRS ChatEnv profile schema; dynamic Admin session state now lives only in the parallel token profile.

### Fixed

- Translate legacy `chatcrs admin keys --time-range 30days` requests into a CRS Admin API `custom` 30-day date window so key usage stats no longer silently fall through to empty results.

## 2026-08-11 - 0.2.4

### Added

- Add a runtime CRS Admin session token store under `~/.chatarch/tokens/CRS/<profile>.json`, parallel to `envs/CRS/<profile>.env`.
- Add `chatcrs admin token status`, `chatcrs admin token refresh`, and `chatcrs admin token clear` commands with redacted JSON output and dry-run deletion by default.
- Add `chatcrs admin login --save-token` for explicitly saving a fresh login-derived Admin session token.

### Changed

- Admin HTTP requests now prefer the runtime token file over legacy `CRS_ACCESS_TOKEN`, fall back to username/password login when needed, and retry once after a 401 by refreshing the token file.
- Document Env-vs-token state separation so stable CRS configuration stays in ChatEnv while short-lived Admin session tokens live in the token store.

## 2026-08-10 - 0.2.3

### Added

- Add runtime-generated `chatcrs --tree` support backed by the registered Click command tree.
- Cover `--help`, `--tree`, representative command groups, and template `hello` absence in CLI tests.

### Changed

- Rework the MkDocs navigation into top-level documentation sections and make the homepage a card-based hub for management, configuration, operations, and development entry points.
- Sync README and bilingual CLI docs with the runtime `chatcrs --tree` output.
- Tighten ChatArch internal dependency windows for the 0.2.3 patch release.

## 2026-08-06 - 0.2.2

### Changed

- Replace the host-bound remote service lifecycle wrapper with local-only
  `chatcrs service ...` commands that run on the CRS server itself and never use
  remote execution transport.
- Keep one canonical CRS ChatEnv namespace for the HTTP base URL, caller API key,
  admin identity, admin password, and admin bearer/session token categories.
- Document `service` as a server-local lifecycle/install/update/status surface,
  while keeping verify/image/debug/Nginx/cutover task surfaces removed.
- Add a CLI-to-HTTP/local interface map that ties every registered CLI leaf to its
  CRS endpoint, auth source, mutation boundary, and importable Python API.
- Keep API-key-only `chatcrs key info --help` focused on key/base-url/profile
  options and wrap health connection failures as clean Click errors.
- Bump package version to 0.2.2 for the local-only service patch release.

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
