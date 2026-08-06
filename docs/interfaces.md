# 命令与 HTTP 接口映射

此页是 ChatCRS 当前剩余 CLI 与 CRS HTTP/Admin API 的对齐表。它只描述已经注册、已经测试的命令；没有 HTTP/Admin endpoint 的服务端本机能力不在当前 CLI 中伪装实现。

## 当前 CLI 树

```text
chatcrs
├── health                         # GET /health
├── admin                          # CRS Admin HTTP API 命令组
│   ├── login                      # POST /web/auth/login
│   ├── accounts                   # OpenAI/Codex 账号状态
│   │   ├── usage                  # GET /admin/openai-accounts
│   │   └── refresh-status         # POST /admin/openai-accounts/{account_id}/reset-status
│   └── keys                       # CRS API key 元数据与统计
│       ├── list                   # GET /admin/api-keys + batch stats/last usage
│       └── show                   # GET /admin/api-keys + batch stats/last usage 后按 id/name 过滤
└── key                            # API-key-only 自查
    └── info                       # GET /openai/key-info
```

## CLI 到 HTTP endpoint

| CLI | HTTP endpoint | 认证来源 | 是否写入 | Python API |
|---|---|---|---|---|
| `chatcrs health` | `GET /health` | 无；只需要 `CRS_API_BASE` 或 `--base-url` | 否 | `chatcrs.local.health_check` |
| `chatcrs admin login` | `POST /web/auth/login` | `CRS_USERNAME` + `CRS_PASSWORD`，或显式参数 | 否；只验证登录并报告 token 是否存在 | `CrsHttpClient.login` |
| `chatcrs admin accounts usage` | `GET /admin/openai-accounts` | Admin bearer token；可由 login/profile 解析 | 否 | `CrsHttpClient.accounts_usage` |
| `chatcrs admin accounts refresh-status` | `POST /admin/openai-accounts/{account_id}/reset-status` | Admin bearer token | 默认否；只有 `--execute` 才调用 endpoint | `CrsHttpClient.reset_openai_account_status` |
| `chatcrs admin keys list` | `GET /admin/api-keys`、可选 `POST /admin/api-keys/batch-stats`、`POST /admin/api-keys/batch-last-usage` | Admin bearer token | 否 | `CrsHttpClient.api_keys` |
| `chatcrs admin keys show` | `GET /admin/api-keys`、可选 `POST /admin/api-keys/batch-stats`、`POST /admin/api-keys/batch-last-usage` | Admin bearer token | 否 | `CrsHttpClient.api_key_detail` |
| `chatcrs key info` | `GET /openai/key-info` | CRS caller API key：`CRS_API_KEY` 或 `--api-key` | 否 | `CrsHttpClient.key_info` |

## 配置解析边界

| 配置字段 | 作用 | 使用命令 |
|---|---|---|
| `CRS_API_BASE` | CRS HTTP base URL | 全部命令 |
| `CRS_API_KEY` | caller API key | `chatcrs key info` |
| `CRS_USERNAME` | admin username | `chatcrs admin login` 及需要登录换 token 的 admin 命令 |
| `CRS_PASSWORD` | admin password | `chatcrs admin login` 及需要登录换 token 的 admin 命令 |
| `CRS_ACCESS_TOKEN` | admin bearer token | `chatcrs admin ...` |

ChatEnv namespace 固定为 `CRS`：`~/.chatarch/envs/CRS/<profile>.env`。当前包内不维护第二套服务目标 profile。

## 当前 HTTP 接口覆盖

<div class="grid cards" markdown>

-   **Health**

    ---

    `GET /health` 用于确认目标 CRS 服务是否响应，输出只读 health 摘要。

-   **Admin login**

    ---

    `POST /web/auth/login` 用于验证管理员凭据并获得 admin bearer token；ChatCRS 输出只报告 token presence，不打印 token。

-   **Accounts**

    ---

    `GET /admin/openai-accounts` 读取账号 usage、状态和调度信息；`POST /admin/openai-accounts/{account_id}/reset-status` 仅在 `--execute` 时重置 CRS 本地状态。

-   **API keys**

    ---

    `GET /admin/api-keys` 读取 key metadata；`POST /admin/api-keys/batch-stats` 和 `POST /admin/api-keys/batch-last-usage` 补统计和最近使用归因。

-   **Caller key info**

    ---

    `GET /openai/key-info` 用 caller CRS API key 自查，不需要管理员账号。

</div>

## 明确缺口

以下能力当前没有已确认的 CRS HTTP/Admin endpoint，因此 ChatCRS 当前不注册对应普通命令：

| 缺口 | 当前处理方式 |
|---|---|
| service lifecycle：status/update/restart/start/stop | 报告缺口；需要新增受限 HTTP 管理 endpoint 或单独 host-agent 设计 |
| API key create/update/delete/restore/tag/index | 需要先确认或新增 Admin HTTP endpoint，再按 dry-run/execute 和脱敏审计规则实现 |
| account add/delete/toggle/schedulable/test | 需要先确认或新增 Admin HTTP endpoint；不能用本机脚本或数据库直写代替 |
| topology/edge/Redis/Nginx/release/cutover | 这是部署/运维层能力，不属于当前普通 CRS HTTP client surface |

## 更新规则

- 新增 CLI 命令前，先确认真实 HTTP/Admin endpoint，并把 endpoint 写入本页。
- 没有 endpoint 的能力，文档必须写成缺口或外部 host-agent 设计，不得写成已实现 CLI。
- 新增或删除命令后，同步更新 `docs/cli.md`、本页、README、CHANGELOG 和 CLI/docs alignment tests。
- 所有输出必须保持脱敏：API key、token、password、OAuth 凭据只报告 presence、计数、状态或 `[REDACTED]`。
