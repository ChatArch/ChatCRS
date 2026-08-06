# CLI 命令树

此页只列出 **当前已经在 `chatcrs.cli` 中注册的命令**。命令树由测试从 Click 注册表回读；新增或删除命令必须同步本页。

## 顶层命令

```text
chatcrs                                           # CRS HTTP/API-first management CLI
├── health                                        # 检查选定 CRS /health endpoint
├── admin                                         # 远程 CRS Admin HTTP API 操作
│   ├── login                                     # 验证管理员登录，不打印 session token
│   ├── accounts                                  # 查询或刷新 OpenAI/Codex 账号状态
│   │   ├── usage                                 # usage、调度、可用性摘要
│   │   └── refresh-status                        # 默认 dry-run；--execute 才调用 reset-status
│   └── keys                                      # 查询 CRS API key 元数据与统计
│       ├── list                                  # 列表；可选 batch stats / last-usage
│       └── show                                  # 按 id/name 返回单个 key 的安全摘要
└── key                                           # 普通 CRS API key 自查
    └── info                                      # 当前 key 的信息、可用性和 usage
```

## 覆盖矩阵

| 能力 | 已实现命令 | 边界 |
|---|---|---|
| CRS health | `chatcrs health` | 只读 HTTP health 摘要 |
| 管理员登录 | `chatcrs admin login` | HTTP 登录验证，只报告 token 是否存在，不打印 token |
| 账号 usage | `chatcrs admin accounts usage` | Admin HTTP API；脱敏 usage/status/scheduling 摘要 |
| 账号状态 reset | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 才调用 CRS reset-status；不是 OAuth refresh-token 强刷 |
| API key 统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | key 值脱敏，返回状态、限制、统计和 last-usage 摘要 |
| 普通 API key 自查 | `chatcrs key info` | 不需要管理员登录 |

## 注册命令清单

| Command | Responsibility |
|---|---|
| `chatcrs health` | CRS health check |
| `chatcrs admin login` | Admin login verification |
| `chatcrs admin accounts usage` | Account usage inspection |
| `chatcrs admin accounts refresh-status` | CRS account reset-status |
| `chatcrs admin keys list` | API key list and statistics |
| `chatcrs admin keys show` | Single API key summary |
| `chatcrs key info` | API-key-only self check |

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
chatcrs admin login --profile admin --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --execute --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --profile admin --json-output
```

!!! warning "refresh-status 的含义"
    `refresh-status` 重置 CRS 账号状态。它不会强制刷新 Codex/OpenAI OAuth refresh token。

## API-key-only { #api-key-only }

```text
chatcrs key                                       # API-key-only self-inspection entry point
└── info                                          # Current API key information, availability, and usage
```

```bash
chatcrs key info --profile admin --json-output
chatcrs key info --profile admin --path /openai/key-info --json-output
```

## 当前不注册的服务端本机候选能力 { #server-local-candidates }

以下能力可能有用，但它们不是当前 HTTP Admin/API 能力，通常需要服务端本机权限、进程管理器、文件系统、Nginx 或 Redis 访问。当前包内 CLI **不注册**这些命令；后续若要加回，必须作为明确的 server-local/host-agent 能力重新设计和测试。

| 候选能力 | 为什么不是当前 RESTful API |
|---|---|
| install/update/start/stop/restart/status | 控制服务进程和部署脚本，依赖本机 supervisor、工作目录、Node/npm/runtime，不是 CRS 应用层资源 |
| switch branch / update pricing data | 依赖本机 git/package 脚本和运行时文件；当前 Admin API 没有受限 endpoint |
| topology/doctor/edge inspection | 需要读取进程、端口、Nginx config、Redis keyspace 或部署目录；这些不是 CRS HTTP 资源 |
| release/cutover/rollback | 涉及构建产物、快照、edge reload 和回滚编排；应该属于部署 runbook 或 host-agent，不属于普通 CRS HTTP client |

## Safety boundaries { #safety-boundaries }

- 当前包内 CLI 只保留 HTTP health、Admin API 查询/状态操作和 API-key-only 自查。
- 如果某个管理动作没有 CRS HTTP/Admin endpoint，ChatCRS 应明确报告能力缺口，而不是用远端执行或本地脚本补洞。
- 任何生产写操作仍必须显式 `--execute`，并且要先确认目标、HTTP endpoint、回滚边界和脱敏输出。
- API key、token、password、OAuth 凭据不得进入聊天、文档、PR body 或命令输出。
