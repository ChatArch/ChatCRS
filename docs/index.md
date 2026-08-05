# ChatCRS

ChatCRS 是 ChatArch 的 CRS 远程运维 CLI。当前注册命令面聚焦远程管理员查询、普通 API key 自查、官方 `crs` lifecycle 的受控包装、health 和只读 inspect。

## 入口选择

<div class="grid cards" markdown>

-   **远程管理员查询**

    ---

    查看 OpenAI/Codex 账号 usage、CRS API key 统计和账号状态刷新计划。

    [查看 CLI 树](cli.md#remote-admin-and-api-key)

-   **普通 API key 自查**

    ---

    不使用管理员登录，只凭 CRS API key 查询自己的可用性、绑定和 usage 摘要。

    [查看 key-only 命令](cli.md#api-key-only)

-   **Service 生命周期管理**

    ---

    吸收官方 `/usr/bin/crs` 的 `install/update/start/stop/restart/switch-branch/update-pricing` 语义，默认只输出计划。

    [查看 service 命令](cli.md#service-lifecycle)

-   **安全边界**

    ---

    Web edge、正式切换、图片能力验收和隔离调试 runtime 不再作为包内注册命令；需要时按当前任务 runbook 由模型操作。

    [查看安全边界](cli.md#safety-boundaries)

</div>

## 当前能力地图

| 场景 | 已实现入口 | 默认行为 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 |
| 拓扑摘要 | `chatcrs inspect` | 只读 |
| 管理员账号 usage | `chatcrs admin accounts usage` | HTTPS Admin API，只输出脱敏摘要 |
| 管理员账号状态刷新 | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status |
| 管理员 API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | 默认脱敏，可带统计 |
| 普通 API key 查询 | `chatcrs key info` | 不需要管理员登录 |
| 官方 `crs` lifecycle | `chatcrs service ...` | 默认 plan；`--execute` 才 SSH 执行 |

## 安全默认值

- 查看类命令返回 `mutated=false` 或只输出状态。
- 写操作必须显式 `--execute`。
- `chatcrs service` 通过 `--ssh-alias`、`--app-dir` 和 `--crs-command` 锁定目标；stdout/stderr 在渲染前脱敏。
- API key、token、密码和 OAuth 凭据不得进入命令行参数或文档输出。

## 下一步

<div class="grid cards" markdown>

-   **完整 CLI 命令树**

    ---

    从实际 Click 注册命令对齐，包含每个已实现命令的右侧注释和状态边界。

    [打开 CLI 命令树](cli.md)

-   **配置与目标**

    ---

    查看 ChatEnv/环境变量字段、remote target 和 service lifecycle 参数。

    [打开配置与目标](configuration.md)

-   **生产维护**

    ---

    理解生产更新、Nginx/edge 操作和受控 release/cutover 流程为什么保留在任务 runbook 层。

    [打开生产维护](production-maintenance.md)

</div>
