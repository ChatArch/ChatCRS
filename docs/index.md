# ChatCRS

ChatCRS 是 ChatArch 的 CRS 运维与验收 CLI。它把远程 CRS 管理员查询、普通 API key 自查、官方 `crs` 生命周期管理语义、Nginx/切流规划和隔离 debug runtime 管理收敛到一个默认安全的命令面。

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

-   **生产安全与调试服务**

    ---

    生产侧默认只读或 plan-only；debug 写操作固定在 12392 隔离 runtime。

    [查看安全边界](cli.md#safety-boundaries)

</div>

## 当前能力地图

| 场景 | 已实现入口 | 默认行为 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 |
| 本机验证 | `chatcrs local verify` | 只读 |
| sidecar / Images 验收 | `chatcrs verify sidecar`, `chatcrs verify images` | 默认只读；图片生成需显式 opt-in |
| 管理员账号 usage | `chatcrs admin accounts usage` | HTTPS Admin API，只输出脱敏摘要 |
| 管理员账号状态刷新 | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status |
| 管理员 API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | 默认脱敏，可带统计 |
| 普通 API key 查询 | `chatcrs key info` | 不需要管理员登录 |
| 官方 `crs` lifecycle | `chatcrs service ...` | 默认 plan；`--execute` 才 SSH 执行 |
| Nginx / cutover | `chatcrs nginx plan-cutover`, `chatcrs cutover precheck` | 只读/只生成计划 |
| Debug runtime | `chatcrs debug ...` | 固定 12392；写操作默认 plan |

## 安全默认值

- 查看类命令返回 `mutated=false` 或只输出状态。
- 写操作必须显式 `--execute`。
- `chatcrs service` 通过 `--ssh-alias`、`--app-dir` 和 `--crs-command` 锁定目标；stdout/stderr 在渲染前脱敏。
- `chatcrs debug` 固定绑定 `127.0.0.1:12392`、Redis `127.0.0.1:6382/0` 和 tmux `crs-debug-12392`，不能改去操作生产。
- `HOST`、`PORT`、`REDIS_*`、JWT 和加密字段不能通过 settings 命令修改。
- API key、token、密码和 OAuth 凭据不得进入命令行参数或文档输出。

## 下一步

<div class="grid cards" markdown>

-   **完整 CLI 命令树**

    ---

    从实际 Click 注册命令对齐，包含每个已实现命令的右侧注释和状态边界。

    [打开 CLI 命令树](cli.md)

-   **调试服务管理**

    ---

    查看固定 12392 debug runtime 的 status、logs、restart、settings 和 upgrade。

    [打开调试服务管理](debug-service.md)

-   **生产维护**

    ---

    理解生产只读检查、切流规划和 service lifecycle 的边界。

    [打开生产维护](production-maintenance.md)

</div>
