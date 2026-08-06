# ChatCRS

ChatCRS 是 ChatArch 的 CRS 管理 CLI。外部管理面聚焦 CRS HTTP/Admin API、普通 API key 自查和 health；`service` 域只在 CRS 服务器本机运行本机 `crs` 命令。

## 选择入口

<div class="grid cards" markdown>

-   **远程管理员查询**

    ---

    查询 OpenAI/Codex 账号 usage、CRS API key 统计，以及默认 dry-run 的账号状态 reset。

    [打开 CLI 树](cli.md#remote-admin-and-api-key)

-   **API-key-only 自查**

    ---

    不需要管理员登录，直接查询当前 CRS API key 的安全摘要。

    [打开 key-only 命令](cli.md#api-key-only)

-   **命令与接口映射**

    ---

    查看当前 CLI leaf 对应的 HTTP endpoint 或 local_command、认证来源、写入边界和 Python API。

    [打开接口映射](interfaces.md)

-   **Server-local service**

    ---

    `service` 域已经恢复，但只用于在 CRS 服务器本机运行 install/update/status/restart 等本机 `crs` 命令。

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
| Server-local service | `chatcrs service ...` | 只在 CRS 服务器本机执行本机命令 |

接口级映射见：[命令与 HTTP 接口映射](interfaces.md)。

## 安全默认值

- Inspection commands 不修改远端状态。
- 变更动作必须显式 `--execute`。
- 外部管理必须走 CRS HTTP/Admin API；没有 endpoint 的 lifecycle 能力只能新增 API/agent，或在服务器本机跑 `chatcrs service ...`。
- API key、token、password、OAuth 凭据不得进入命令参数或文档输出。

## 下一步

<div class="grid cards" markdown>

-   **完整 CLI 树**

    ---

    从实际 Click command registration 回读，并标注命令边界。

    [打开 CLI 树](cli.md)

-   **配置与目标**

    ---

    查看单一 CRS ChatEnv profile、环境变量字段和敏感信息规则。

    [打开配置](configuration.md)

-   **生产维护**

    ---

    了解为什么生产更新、edge work 和 release/cutover 仍停留在 task-runbook 层。

    [打开生产维护](production-maintenance.md)

</div>
