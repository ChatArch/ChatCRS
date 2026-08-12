# ChatCRS

ChatCRS 是 ChatArch 的 CRS 管理 CLI。外部管理面聚焦 CRS HTTP/Admin API、普通 API key 自查和 health；`service` 域只在 CRS 服务器本机运行本机 `crs` 命令。

## 文档栏目

<div class="grid cards" markdown>

-   **管理面**

    ---

    从真实 CLI 树进入，查看 HTTP/Admin API、API-key-only 自查和本机 service 命令。

    [查看命令树](cli.md)
    [查看接口映射](interfaces.md)

-   **配置**

    ---

    只保留一套 CRS ChatEnv profile，说明 `CRS_*` 字段、脱敏规则和本机 service 目标。

    [查看配置](configuration.md)

-   **运维**

    ---

    区分包内可执行能力、服务器本机维护入口，以及仍需 runbook 或新 API 的生产动作。

    [查看生产维护](production-maintenance.md)

-   **开发**

    ---

    查看本地安装、测试、文档构建、发布和版本约束。

    [查看开发与发布](development.md)

</div>

## 常用入口

<div class="grid cards" markdown>

-   **远程管理员查询**

    ---

    查询 OpenAI/Codex 账号 usage、CRS API key 统计，以及默认 dry-run 的账号状态 reset。

    [打开管理员命令](cli.md#remote-admin-and-api-key)

-   **API-key-only 自查**

    ---

    不需要管理员登录，直接查询当前 CRS API key 的安全摘要。

    [打开 key-only 命令](cli.md#api-key-only)

-   **命令与接口映射**

    ---

    查看当前 CLI leaf 对应的 HTTP endpoint 或 local_command、认证来源、写入边界和 Python API。

    [打开接口映射](interfaces.md)

-   **本机 service**

    ---

    `service` 域只用于在 CRS 服务器本机运行 install/update/status/restart 等本机 `crs` 命令。

    [查看 service 边界](cli.md#server-local-service)

-   **安全边界**

    ---

    没有 HTTP/Admin endpoint 的动作应报告能力缺口，不用远端执行或本地脚本补洞。

    [打开安全边界](cli.md#safety-boundaries)

</div>

## 能力地图

| 场景 | 已实现入口 | 默认行为 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 HTTP |
| Admin account usage | `chatcrs admin accounts usage` | HTTP Admin API，脱敏摘要 |
| Admin account status refresh | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 调 CRS reset-status endpoint |
| Admin API key statistics | `chatcrs admin keys list`, `chatcrs admin keys show` | 默认脱敏，可选 stats |
| API-key-only info | `chatcrs key info` | 不需要管理员登录 |
| Codex direct usage | `chatcrs codex account`, `chatcrs codex quota`, `chatcrs codex usage` | 直接查 OpenAI/Codex account 与 usage/quota，输出脱敏 |
| Server-local service | `chatcrs service ...` | 只在 CRS 服务器本机执行本机命令 |

接口级映射见：[命令与 HTTP 接口映射](interfaces.md)。

## 安全默认值

- Inspection commands 不修改远端状态。
- 变更动作必须显式 `--execute`。
- 外部管理必须走 CRS HTTP/Admin API；没有 endpoint 的 lifecycle 能力只能新增 API/agent，或在服务器本机跑 `chatcrs service ...`。
- API key、token、password、OAuth 凭据不得进入命令参数或文档输出。
