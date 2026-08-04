# ChatCRS

ChatCRS is ChatArch's CRS operations and acceptance CLI. It brings remote CRS admin inspection, API-key-only self checks, guarded official `crs` lifecycle semantics, Nginx/cutover planning, and isolated debug runtime management into one safety-first command surface.

## Choose an entry point

<div class="grid cards" markdown>

-   **Remote admin inspection**

    ---

    Inspect OpenAI/Codex account usage, CRS API key statistics, and guarded account status refresh plans.

    [Open the CLI tree](cli.md#remote-admin-and-api-key)

-   **API-key-only self check**

    ---

    Query the current CRS API key without administrator login.

    [Open key-only commands](cli.md#api-key-only)

-   **Service lifecycle management**

    ---

    Absorb official `/usr/bin/crs` semantics for `install/update/start/stop/restart/switch-branch/update-pricing`; default output is a plan.

    [Open service commands](cli.md#service-lifecycle)

-   **Production safety and debug runtime**

    ---

    Production commands are read-only or plan-only by default; debug mutations are pinned to the isolated 12392 runtime.

    [Open safety boundaries](cli.md#safety-boundaries)

</div>

## Capability map

| Scenario | Implemented entry point | Default behavior |
|---|---|---|
| CRS health | `chatcrs health` | Read-only |
| Local verification | `chatcrs local verify` | Read-only |
| Sidecar / Images acceptance | `chatcrs verify sidecar`, `chatcrs verify images` | Read-only by default; image generation requires opt-in |
| Admin account usage | `chatcrs admin accounts usage` | HTTPS Admin API, redacted summary |
| Admin account status refresh | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS reset-status |
| Admin API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted by default, optional stats |
| API-key-only info | `chatcrs key info` | No administrator login |
| Official `crs` lifecycle | `chatcrs service ...` | Plan by default; `--execute` runs over SSH |
| Nginx / cutover | `chatcrs nginx plan-cutover`, `chatcrs cutover precheck` | Read-only / plan-only |
| Debug runtime | `chatcrs debug ...` | Pinned to 12392; mutations are plan-only by default |

## Safety defaults

- Inspection commands do not mutate remote state.
- Mutations require explicit `--execute`.
- `chatcrs service` targets are bound by `--ssh-alias`, `--app-dir`, and `--crs-command`; captured stdout/stderr are redacted before rendering.
- `chatcrs debug` is pinned to `127.0.0.1:12392`, Redis `127.0.0.1:6382/0`, and tmux `crs-debug-12392`.
- `HOST`, `PORT`, `REDIS_*`, JWT, and encryption settings cannot be changed through settings commands.
- API keys, tokens, passwords, and OAuth credentials must not appear in command arguments or documentation output.

## Next steps

<div class="grid cards" markdown>

-   **Complete CLI tree**

    ---

    Generated from actual Click command registration and annotated with command boundaries.

    [Open the CLI tree](cli.md)

-   **Debug runtime**

    ---

    Manage the fixed 12392 debug runtime: status, logs, restart, settings, and upgrade.

    [Open debug runtime docs](debug-service.md)

-   **Production maintenance**

    ---

    Understand read-only checks, cutover planning, and service lifecycle boundaries.

    [Open production maintenance](production-maintenance.md)

</div>
