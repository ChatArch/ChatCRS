# Configuration and targets

## CRS profiles

ChatCRS uses the `CRS` ChatEnv namespace for HTTP/API management. Most `chatcrs` commands default to the named `admin` profile; select another with `--profile`. Host lifecycle settings do not belong in this profile.

| Category | Purpose | Sensitive |
|---|---|---|
| HTTP base URL | CRS service root | No |
| Caller API key | Key self-inspection and model requests | Yes |
| Administrator username/password | Admin API login | Yes |
| Optional model | Opt-in Codex Responses verification | No |

## Key authentication and optional model verification

Use the registered ChatEnv test rather than a separate HTTP script:

```bash
chatenv paste --stdin --profile smoke -I --yes
# Supply CRS_API_BASE=<service root> and CRS_API_KEY=<your key> via stdin.
chatenv use smoke -t crs -I
chatenv test -t crs -I

# Opt in to one model request, which consumes upstream usage.
chatenv set 'CRS_API_MODEL=<supported model ID>' -I
chatenv test -t crs -I
# Return to key-only verification:
chatenv set CRS_API_MODEL= -I
```

`CRS_API_BASE` is the service root, such as `https://crs.example.com`, without `/openai` or `/v1`. The test reads the active CRS profile, honoring `CHATARCH_HOME` and `chatenv --home`. Profile values take precedence over process environment values and schema defaults; an explicit empty value does not fall back to the environment. This active-profile selection is distinct from the named `admin` default of ordinary ChatCRS commands.

| Configuration | Request | Success criterion |
|---|---|---|
| Required base and key | GET `/openai/key-info` | Authenticated, nonempty, non-error JSON |
| Model unset | No model request | Explicitly reports `key-only verification; upstream not tested` |
| Model explicitly set | POST `/openai/responses` with the same key | Nonempty text delta and a successful `response.completed` event |

The model request uses typed message/input-text input, `stream=true`, and `store=false`. HTTP 200 or the start of an SSE stream alone is not success. Requests use a 20-second socket timeout with no automatic retry; model SSE reads are capped at 64 KiB. Empty text, malformed/truncated/oversized streams, error events, and HTTP/network errors fail with a nonzero command exit. Credentials, response bodies, generated text, and raw errors are not printed.

This test does not load or refresh administrator tokens, perform administrator login, or modify the Codex OAuth lifecycle. `CodexConfig.test()` remains an offline schema check. Python callers may use `ChatcrsConfig.test()` for the active configuration or `CrsHttpClient.responses_smoke(model=...)` for a safe structured result.

## Administrator session tokens

Stable connection and login configuration stays in the CRS Env profile. Login-derived session tokens are generated runtime state in the parallel ChatEnv token store:

```text
~/.chatarch/envs/CRS/<profile>.env
~/.chatarch/tokens/CRS/<profile>.json
```

Refresh through `chatcrs admin token refresh --profile <profile>` or `chatenv token refresh CRS <profile>`. Resolution order is an explicit one-shot administrator token, the runtime token file, then username/password login. On an Admin API 401, configured login credentials allow one session refresh and one retry.

Token status exposes metadata only. `chatcrs admin token clear` is a dry run unless `--execute` is supplied.

## Direct Codex OAuth profiles

Direct `chatcrs codex ...` operations use the separate ChatCRS-owned `Codex` namespace. Stable refresh seed and relay configuration live in the matching Env profile; generated access/refresh tokens and account metadata live in its runtime token store.

| Field | Purpose | Default |
|---|---|---|
| `OPENAI_OAUTH_BASE_URL` | OAuth token and accounts operations | `https://auth.openai.com` |
| `CHATGPT_BACKEND_BASE_URL` | ChatGPT backend requests | `https://chatgpt.com/backend-api` |

A relay changes the destination base URL, not credential ownership. Keep tokens and account headers out of reverse-proxy configuration and logs. Account summaries prefer token claims and stored metadata; usage output redacts account, email, and user identities.

## Troubleshooting and boundaries

A successful caller-key test does not prove that administrator credentials work. `chatcrs admin ...` uses a different authentication surface. If login returns 401, correct the selected administrator profile rather than changing account-usage parsing or resetting the service.

Process supervision, deployment paths, Redis, reverse-proxy configuration, and release cutover are host-level concerns, not ordinary CRS HTTP profile fields. Unsupported Admin API operations remain explicit capability gaps. Credentials belong only in approved profiles, runtime token stores, or process environment—not public documentation or logs.
