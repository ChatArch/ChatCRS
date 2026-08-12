# ChatCRS

ChatCRS is ChatArch's CRS management CLI. Outside-server management focuses on CRS HTTP/Admin API, API-key-only self checks, and health. The `service` namespace runs local `crs` commands only inside the CRS server shell.

## Documentation sections

<div class="grid cards" markdown>

-   **Management**

    ---

    Start from the real CLI tree and inspect HTTP/Admin API, API-key-only checks, and local service commands.

    [Open the CLI tree](cli.md)
    [Open the interface map](interfaces.md)

-   **Configuration**

    ---

    Review the single CRS ChatEnv profile, `CRS_*` fields, redaction rules, and local service targets.

    [Open configuration](configuration.md)

-   **Operations**

    ---

    Separate package commands, server-local maintenance entry points, and production work that still needs a runbook or new API.

    [Open production maintenance](production-maintenance.md)

-   **Development**

    ---

    Review local setup, tests, documentation builds, release flow, and version constraints.

    [Open development and release](development.md)

</div>

## Common entry points

<div class="grid cards" markdown>

-   **Remote admin inspection**

    ---

    Inspect OpenAI/Codex account usage, CRS API key statistics, and dry-run-by-default account status reset.

    [Open admin commands](cli.md#remote-admin-and-api-key)

-   **API-key-only self check**

    ---

    Query the current CRS API key without administrator login.

    [Open key-only commands](cli.md#api-key-only)

-   **CLI and interface map**

    ---

    Review the HTTP endpoint or local_command, authentication source, mutation boundary, and Python API behind each registered CLI leaf.

    [Open the interface map](interfaces.md)

-   **Server-local service**

    ---

    The `service` namespace runs install/update/status/restart-style local `crs` commands only on the CRS server itself.

    [Review the service boundary](cli.md#server-local-service)

-   **Safety boundaries**

    ---

    Actions without HTTP/Admin endpoints should be reported as capability gaps, not replaced with remote execution or local scripts.

    [Open safety boundaries](cli.md#safety-boundaries)

</div>

## Capability map

| Scenario | Implemented entry point | Default behavior |
|---|---|---|
| CRS health | `chatcrs health` | Read-only HTTP |
| Admin account usage | `chatcrs admin accounts usage` | HTTP Admin API, redacted summary |
| Admin account status refresh | `chatcrs admin accounts refresh-status` | Dry-run by default; `--execute` calls the CRS reset-status endpoint |
| Admin API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | Redacted by default, optional stats |
| API-key-only info | `chatcrs key info` | No administrator login |
| Codex direct usage | `chatcrs codex account`, `chatcrs codex usage` | Direct OpenAI/Codex account and usage/quota inspection with redacted output |
| Server-local service | `chatcrs service ...` | Runs local commands only on the CRS server itself |

For the endpoint-level map, see [CLI and HTTP interface map](interfaces.md).

## Safety defaults

- Inspection commands do not mutate remote state.
- Mutations require explicit `--execute`.
- Outside-server management must use CRS HTTP/Admin API; lifecycle capabilities without endpoints require a new API/agent or running `chatcrs service ...` on the server itself.
- API keys, tokens, passwords, and OAuth credentials must not appear in command arguments or documentation output.
