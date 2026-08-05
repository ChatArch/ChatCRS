# CLI 命令树

此页只列出 **当前已经在 `chatcrs.cli` 中注册的命令**。命令树由测试从 Click 注册表回读；新增或删除命令必须同步本页。

## 顶层命令

```text
chatcrs                                           # ChatArch CRS remote operations CLI
├── health                                        # 检查选定 CRS /health endpoint
├── inspect                                       # 只读汇总已知 CRS 拓扑与入口状态
├── admin                                         # 远程 CRS Admin API 操作
│   ├── login                                     # 验证管理员登录，不打印 session token
│   ├── accounts                                  # 查询或刷新 OpenAI/Codex 账号状态
│   │   ├── usage                                 # usage、调度、可用性摘要
│   │   └── refresh-status                        # 默认 dry-run；--execute 才调用 reset-status
│   └── keys                                      # 查询 CRS API key 元数据与统计
│       ├── list                                  # 列表；可选 batch stats / last-usage
│       └── show                                  # 按 id/name 返回单个 key 的安全摘要
├── key                                           # 普通 CRS API key 自查
│   └── info                                      # 当前 key 的信息、可用性和 usage
└── service                                       # 受控包装官方 crs lifecycle 语义
    ├── install                                   # 默认计划；--execute 才远程运行 crs install
    ├── update                                    # 默认计划；--execute 才远程运行 crs update
    ├── start                                     # 默认计划；--execute 才远程运行 crs start
    ├── stop                                      # 默认计划；--execute 才远程运行 crs stop
    ├── restart                                   # 默认计划；--execute 才远程运行 crs restart
    ├── status                                    # 默认计划；--execute 才远程运行 crs status
    ├── switch-branch                             # 默认计划；--execute 才远程运行 crs switch-branch
    └── update-pricing                            # 默认计划；--execute 才远程运行 crs update-pricing
```

## 覆盖矩阵

| 能力 | 已实现命令 | 边界 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 HTTP health 摘要 |
| 拓扑摘要 | `chatcrs inspect` | 只读聚合已知实例、入口和运行状态；不写配置 |
| 管理员登录 | `chatcrs admin login` | 验证凭据，只报告 token 是否存在，不打印 token |
| 账号 usage | `chatcrs admin accounts usage` | Admin HTTPS API；脱敏 usage/status/scheduling 摘要 |
| 账号状态 reset | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status；不是 OAuth refresh-token 强刷 |
| API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | key 值脱敏，返回状态、限制、统计和 last-usage 摘要 |
| 普通 API key 自查 | `chatcrs key info` | 不需要管理员登录 |
| 官方 lifecycle | `chatcrs service install`, `chatcrs service update`, `chatcrs service start`, `chatcrs service stop`, `chatcrs service restart`, `chatcrs service status`, `chatcrs service switch-branch`, `chatcrs service update-pricing` | 默认只输出计划；`--execute` 才通过 SSH 到目标 app 目录运行官方 `crs ...` |

## 注册命令清单

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs inspect` | Read-only known CRS topology inspection |
| `chatcrs admin login` | Admin login verification |
| `chatcrs admin accounts usage` | Account usage inspection |
| `chatcrs admin accounts refresh-status` | CRS account reset-status |
| `chatcrs admin keys list` | API key list and statistics |
| `chatcrs admin keys show` | Single API key summary |
| `chatcrs key info` | API-key-only self check |
| `chatcrs service install` | Official crs install semantics |
| `chatcrs service update` | Official crs update semantics |
| `chatcrs service start` | Official crs start semantics |
| `chatcrs service stop` | Official crs stop semantics |
| `chatcrs service restart` | Official crs restart semantics |
| `chatcrs service status` | Official crs status semantics |
| `chatcrs service switch-branch` | Official crs switch-branch semantics |
| `chatcrs service update-pricing` | Official crs update-pricing semantics |

## 远程管理员与 API key { #remote-admin-and-api-key }

<div class="grid cards" markdown>

-   **Admin login**

    ---

    `chatcrs admin login` 验证 CRS 管理员凭据，只返回安全的 token presence 元数据。

-   **Account usage**

    ---

    `chatcrs admin accounts usage` 返回 OpenAI/Codex 账号 usage、状态、调度和最近使用摘要。

-   **Account status refresh**

    ---

    `chatcrs admin accounts refresh-status <account_id>` 默认 dry-run；`--execute` 才调用 CRS reset-status。

-   **API key statistics**

    ---

    `chatcrs admin keys list --include-stats` 合并 key 元数据、batch stats 和 last-usage；`show` 查询单个 key。

</div>

```text
chatcrs admin                                     # Remote CRS administrator entry point
├── login                                         # Verify login without leaking token
├── accounts                                      # Account status and usage
│   ├── usage                                     # List account usage and scheduling state
│   └── refresh-status                            # Dry-run by default; --execute resets CRS state
└── keys                                          # Admin API key inspection
    ├── list                                      # List keys, redacted by default; can include stats
    └── show                                      # Safe summary for one key
```

常用命令：

```bash
chatcrs admin login --json-output
chatcrs admin accounts usage --json-output
chatcrs admin accounts refresh-status <account_id> --json-output
chatcrs admin accounts refresh-status <account_id> --execute --json-output
chatcrs admin keys list --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --json-output
```

!!! warning "refresh-status 的含义"
    `refresh-status` 重置 CRS 账号状态。它不会强制刷新 Codex/OpenAI OAuth refresh token。

## API-key-only { #api-key-only }

```text
chatcrs key                                       # API-key-only self-inspection entry point
└── info                                          # Current API key information, availability, and usage
```

```bash
chatcrs key info --json-output
chatcrs key info --path /api/v1/key-info --json-output
```

## Service lifecycle { #service-lifecycle }

`chatcrs service` 吸收官方 `/usr/bin/crs` lifecycle 管理语义，但不直接裸跑危险动作。它通过 SSH 进入目标 CRS app 目录运行官方 `crs ...`；默认输出计划，只有 `--execute` 才修改远端目标。

```text
chatcrs service                                   # Remote wrapper for official crs lifecycle
├── install                                       # Plan by default; --execute runs crs install
├── update                                        # Plan by default; --execute runs crs update
├── start                                         # Plan by default; --execute runs crs start
├── stop                                          # Plan by default; --execute runs crs stop
├── restart                                       # Plan by default; --execute runs crs restart
├── status                                        # Plan by default; --execute runs crs status
├── switch-branch                                 # Plan by default; --execute runs crs switch-branch <branch>
└── update-pricing                                # Plan by default; --execute runs crs update-pricing
```

常用目标参数：

```bash
chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --json-output

chatcrs service update   --ssh-alias tencent.am   --app-dir /home/zhihong/claude-relay-service/app   --execute   --json-output
```

环境变量默认值：

```text
CHATCRS_SSH_ALIAS   # example: tencent.am
CHATCRS_APP_DIR     # example: /home/zhihong/claude-relay-service/app
CHATCRS_CRS_COMMAND # example: /usr/bin/crs; default: crs
```

!!! note "输出脱敏"
    Service commands 会在渲染前脱敏 Authorization header、token、password、API key 和 CRS `cr_...` 形态值。

## Safety boundaries { #safety-boundaries }

- 当前包内 CLI 只保留远程 admin/key 查询、service lifecycle 包装、health 和只读 inspect。
- Web edge、正式切换、图片能力验收、隔离调试 runtime 这类任务不再作为 ChatCRS 注册命令面；需要时由模型按当前任务的项目 runbook、脚本和 SSH/Nginx 工具链执行。
- 任何生产写操作仍必须显式 `--execute`，并且要先确认目标、工作目录、回滚边界和脱敏输出。
- API key、token、password、OAuth 凭据不得进入聊天、文档、PR body 或命令输出。
