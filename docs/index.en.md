# ChatCRS

ChatCRS is ChatArch's remote CRS operations CLI. The registered command surface now focuses on remote admin inspection, API-key-only self checks, guarded official `crs` lifecycle wrapping, health, and read-only inspect.

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

-   **Safety boundaries**

    ---

    Web-edge work, formal switching, image capability acceptance, and isolated debug runtime operations are not registered package commands; the model handles them from the active task runbook when needed.

    [Open safety boundaries](cli.md#safety-boundaries)

</div>

## Capability map

| Scenario | Implemented entry point | Default behavior |
|---|---|---|
| CRS health | `chatcrs health` | Read-only |
| Topology summary | `chatcrs inspect` | Read-only |
| Admin account usage | `chatcrs admin accounts usage` | HTTPS Admin API, redacted summary |
| Admin account status refresh | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls CRS reset-status |
| Admin API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted by default, optional stats |
| API-key-only info | `chatcrs key info` | No administrator login |
| Official `crs` lifecycle | `chatcrs service ...` | Plan by default; `--execute` runs over SSH |

## Safety defaults

- Inspection commands do not mutate remote state.
- Mutations require explicit `--execute`.
- `chatcrs service` targets are bound by `--ssh-alias`, `--app-dir`, and `--crs-command`; captured stdout/stderr are redacted before rendering.
- API keys, tokens, passwords, and OAuth credentials must not appear in command arguments or documentation output.

## Next steps

<div class="grid cards" markdown>

-   **Complete CLI tree**

    ---

    Generated from actual Click command registration and annotated with command boundaries.

    [Open the CLI tree](cli.md)

-   **Configuration and targets**

    ---

    Review ChatEnv/environment fields, remote targets, and service lifecycle parameters.

    [Open configuration](configuration.md)

-   **Production maintenance**

    ---

    Understand why production update, Nginx/edge work, and guarded release/cutover flows stay at the task-runbook layer.

    [Open production maintenance](production-maintenance.md)

</div>
