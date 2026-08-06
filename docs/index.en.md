# ChatCRS

ChatCRS is ChatArch's HTTP/API-first CRS management CLI. The registered command surface focuses on remote administrator HTTP API inspection, API-key-only self checks, and health.

## Choose an entry point

<div class="grid cards" markdown>

-   **Remote admin inspection**

    ---

    Inspect OpenAI/Codex account usage, CRS API key statistics, and dry-run-by-default account status reset.

    [Open the CLI tree](cli.md#remote-admin-and-api-key)

-   **API-key-only self check**

    ---

    Query the current CRS API key without administrator login.

    [Open key-only commands](cli.md#api-key-only)

-   **CLI and HTTP interface map**

    ---

    Review the HTTP endpoint, authentication source, mutation boundary, and Python API behind each of the seven registered CLI leaves.

    [Open the interface map](interfaces.md)

-   **Server-local candidate capabilities**

    ---

    Lifecycle, topology, edge, release/cutover, and similar capabilities are not registered today because they require server-local authority or a host-agent design.

    [Review candidate boundaries](cli.md#server-local-candidates)

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

For the endpoint-level map, see [CLI and HTTP interface map](interfaces.md).

## Safety defaults

- Inspection commands do not mutate remote state.
- Mutations require explicit `--execute`.
- Management actions without CRS HTTP/Admin endpoints are not registered in the current CLI.
- API keys, tokens, passwords, and OAuth credentials must not appear in command arguments or documentation output.

## Next steps

<div class="grid cards" markdown>

-   **Complete CLI tree**

    ---

    Generated from actual Click command registration and annotated with command boundaries.

    [Open the CLI tree](cli.md)

-   **Configuration and targets**

    ---

    Review the single CRS ChatEnv profile, environment fields, and sensitive-value rules.

    [Open configuration](configuration.md)

-   **Production maintenance**

    ---

    Understand why production update, edge work, and release/cutover flows stay at the task-runbook layer.

    [Open production maintenance](production-maintenance.md)

</div>
