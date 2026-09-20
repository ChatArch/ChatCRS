<div align="center">
    <a href="https://pypi.python.org/pypi/ChatCRS">
        <img src="https://img.shields.io/pypi/v/ChatCRS.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/ChatArch/ChatCRS/actions/workflows/ci.yml">
        <img src="https://github.com/ChatArch/ChatCRS/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
</div>

<div align="center">

[English](README.en.md) | [简体中文](README.md)
</div>

# ChatCRS

ChatCRS 是 ChatArch 的 CRS 管理 CLI。外部管理面优先使用 CRS HTTP/Admin API；`service` 域是 server-local surface，只在 CRS 服务器本机 shell 里操作本机 CRS checkout / Node runtime / `crs` executable。

Images 验收、debug runtime、Nginx/edge、release/cutover 等花哨/任务型能力不作为当前包内命令暴露；这些属于代理站维护、专项验收或运维 runbook，后续需要时单独设计。

## 安装与开发

```bash
python -m pip install -e '.[dev,docs]'
chatcrs --help
chatcrs --version
python -m pytest -q
python -m mkdocs build --strict
python -m build
```

完整文档使用 MkDocs，本地预览：

```bash
python -m mkdocs serve
```

线上文档：https://arch.gh.wzhecnu.cn/ChatCRS/

## 配置测试

安装后用 `chatenv paste --stdin --profile smoke -I --yes` 导入 `CRS_API_BASE`（服务根 URL）与 `CRS_API_KEY`，再 `chatenv use smoke -t crs -I`、`chatenv test -t crs -I`。
默认只验证 Key 鉴权，明确不证明上游可用；显式配置可选 `CRS_API_MODEL` 后才发起同 Key 的 Codex Responses 流式文本请求（会产生用量）。失败非零，不打印凭据或原始错误。详见[配置文档](docs/configuration.md)。

## CLI 树

```text
chatcrs
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── admin  # Remote CRS administrator operations via HTTPS Admin API.
│   ├── accounts  # Inspect or refresh remote CRS account state via HTTP Admin API.
│   │   ├── codex  # CRS 托管 Codex 账号；需原生 Admin 接口。
│   │   │   ├── consume [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output] [--request-id REQUEST-ID] [--credit-id CREDIT-ID] [--execute]  # 默认本地计划；显式执行消费，不自动重放。
│   │   │   ├── credits [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output]  # 只读查询重置卡，不消费。
│   │   │   ├── operation [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output] [--request-id REQUEST-ID]  # 读取历史回执；待定或未知状态退出非零。
│   │   │   └── usage [--profile PROFILE] [--account-id ACCOUNT-ID] [--timeout TIMEOUT] [--json-output]  # 读取固定账号的实时上游额度；不是缓存统计。
│   │   ├── refresh-status [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] <ACCOUNT-ID> [--execute] [--json-output]  # Reset a CRS OpenAI account status after transient failures.
│   │   └── usage [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # List OpenAI/Codex account usage and scheduling metadata.
│   ├── keys  # Inspect remote CRS API keys with admin privileges.
│   │   ├── list [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--include-stats] [--time-range TIME-RANGE] [--json-output]  # List CRS API key metadata, optionally including usage stats.
│   │   └── show [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] <KEY-ID> [--include-stats] [--time-range TIME-RANGE] [--json-output]  # Show one CRS API key by id or name.
│   ├── login [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--save-token] [--json-output]  # Verify CRS admin login without printing the session token.
│   └── token  # Manage cached CRS admin session tokens in the ChatArch token store.
│       ├── clear [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--execute] [--json-output]  # Clear the cached CRS admin session token.
│       ├── refresh [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # Login and save a fresh CRS admin session token.
│       └── status [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--username USERNAME] [--password PASSWORD] [--admin-token ADMIN-TOKEN] [--timeout TIMEOUT] [--json-output]  # Show cached CRS admin token metadata without printing the token.
├── codex  # Direct OpenAI Codex account token and usage helpers.
│   ├── account [--profile PROFILE] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Read a safe OpenAI Codex account summary from token claims and API probe.
│   ├── quota [--profile PROFILE] [--account-id ACCOUNT-ID] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--model MODEL] [--timeout TIMEOUT] [--json-output]  # Run a profile-only Codex responses smoke and show quota headers.
│   ├── reset  # Inspect or explicitly redeem banked Codex resets without model requests.
│   │   ├── consume [--json-output] [--timeout TIMEOUT] [--base-url BASE-URL] [--profile PROFILE] [--request-id REQUEST-ID] [--execute]  # Plan or redeem one reset with a persisted receipt and GET readback.
│   │   └── list [--json-output] [--timeout TIMEOUT] [--base-url BASE-URL] [--profile PROFILE]  # Read reset count and expirations; renew profile credentials when required.
│   ├── token  # Manage OpenAI OAuth tokens through the ChatEnv Codex token store.
│   │   ├── refresh [--profile PROFILE] [--refresh-token REFRESH-TOKEN] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Refresh an OpenAI OAuth access token without printing token values.
│   │   └── status [--profile PROFILE] [--json-output]  # Show cached OpenAI OAuth token metadata without printing tokens.
│   └── usage [--profile PROFILE] [--account-id ACCOUNT-ID] [--access-token ACCESS-TOKEN] [--refresh] [--client-id CLIENT-ID] [--timeout TIMEOUT] [--json-output]  # Read Codex usage and quota metadata directly from OpenAI.
├── health [--base-url BASE-URL] [--json-output]  # Verify the CRS /health endpoint.
├── key  # CRS API-key-only operations that do not require admin login.
│   └── info [--profile PROFILE] [--base-url BASE-URL] [--api-key API-KEY] [--timeout TIMEOUT] [--path INFO-PATH] [--json-output]  # Query CRS key-info using only a CRS API key.
└── service  # Local CRS service lifecycle commands for the current server.
    ├── install [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs install` on this server.
    ├── restart [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs restart` on this server.
    ├── start [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs start` on this server.
    ├── status [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--json-output]  # Execute local `crs status` on this server.
    ├── stop [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs stop` on this server.
    ├── switch-branch <BRANCH> [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs switch-branch <branch>` on this server.
    ├── update [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs update` on this server.
    └── update-pricing [--app-dir APP-DIR] [--crs-command CRS-COMMAND] [--timeout TIMEOUT] [--execute] [--json-output]  # Plan or execute local `crs update-pricing` on this server.
```

运行 `chatcrs --tree` 可从实际 Click 注册表回读带参数签名的命令树；`chatcrs --tree-brief` 保留命令节点和描述，但省略参数签名。两种模式都固定使用 canonical 根名 `chatcrs`。


## HTTP/Admin 与 API key

```bash
chatcrs health --base-url https://crs.example.com --json-output
chatcrs admin login --profile admin --json-output
chatcrs admin login --profile admin --save-token --json-output
chatcrs admin token status --profile admin --json-output
chatcrs admin token refresh --profile admin --json-output
chatcrs admin token clear --profile admin --json-output
chatcrs admin token clear --profile admin --execute --json-output
chatcrs admin accounts usage --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --json-output
chatcrs admin accounts refresh-status <account_id> --profile admin --execute --json-output
chatcrs admin keys list --profile admin --include-stats --json-output
chatcrs admin keys show <key_id_or_name> --profile admin --json-output
chatcrs key info --profile admin --json-output
chatcrs codex token status --profile default --json-output
chatenv token refresh Codex default
chatcrs codex account --profile default --json-output
chatcrs codex quota --profile default --json-output
chatcrs codex usage --profile default --json-output
```

## Server-local service

这些命令应安装在目标 CRS 服务器上，并在该服务器本机执行：

```bash
chatcrs service status --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --json-output
chatcrs service update --app-dir /path/to/crs --execute --json-output
chatcrs service restart --app-dir /path/to/crs --execute --json-output
```

`status` 默认执行本机只读 `crs status`。其它 service mutation 默认 dry-run，需要 `--execute` 才执行。

## 配置

ChatCRS 使用 `CRS` ChatEnv profile 管理 CRS Admin/API 配置，并为 `OpenAI` 注册 OAuth token refresher 供 Codex direct 使用。Codex direct 的稳定 OAuth profile 来自 `envs/Codex/<profile>.env`，runtime token 来自 `tokens/Codex/<profile>.json`，持久刷新用 `chatenv token refresh Codex <profile>`。Codex profile 可设置非敏感 relay 字段：`OPENAI_OAUTH_BASE_URL` 覆盖 OAuth token/accounts upstream，`CHATGPT_BACKEND_BASE_URL` 覆盖 ChatGPT backend upstream。公开文档只描述字段类别，不写具体 secret 文件路径或 secret-bearing env key 名。

Canonical 字段类别：

```text
HTTP base URL
caller API key
admin username
admin password
admin bearer/session token
```

Service-local 目标不进入第二套 ChatEnv namespace；用当前工作目录或 `--app-dir` / `--crs-command` 指定本机 checkout 和 executable。

敏感字段只应存在于 ChatEnv 或进程环境中，不进入命令行参数、文档、PR body 或日志输出。Profile 文件应使用 `0600` 权限。

## 生产安全

外部管理只能使用 HTTP/Admin API；没有 HTTP lifecycle 接口时，不用远端执行补洞。要么新增 CRS API/host-agent，要么在目标服务器本机运行 `chatcrs service ...`。

更多内容见：

- `docs/cli.md`
- `docs/interfaces.md`
- `docs/configuration.md`
- `docs/production-maintenance.md`


## Codex 重置卡

Profile 客户端使用标准 ChatEnv `Codex` 续期流程：稳定配置位于 `envs/Codex`，轮换后的 access/refresh token 与到期元数据只写入 `tokens/Codex`，不会回填 ENV。过期时先续期；只读 GET 遇到 401 最多续期并重试一次；消费 POST 不自动重放。刷新凭据被上游拒绝时应重新授权，而不是切换代理或复制其他服务的 token。

账号请求必须配置对应的 HTTPS Base URL。所有 ChatCRS HTTP 请求都忽略环境和系统 Proxy，并拒绝重定向；反代示例位于仓库 `infra/nginx/codex-relay.conf.example`。Nginx 只透传请求，不保存账号密钥。

```env
OPENAI_OAUTH_BASE_URL=https://auth-relay.example.com
CHATGPT_BACKEND_BASE_URL=https://gpt-relay.example.com/backend-api
```

Python 消费者使用 `CodexResetClient.from_profile("work", refresh=True)`；需要完全不续期的诊断时显式传 `refresh=False`。不要在仪表盘或机器私有脚本中重写 OAuth。


`chatcrs codex reset list` 通过 `GET /wham/rate-limit-reset-credits` 查询可用次数与到期时间；不请求模型；必要时通过 ChatEnv 标准流程续期 OAuth，并只更新运行态 token store。`chatcrs codex reset consume` 默认只生成计划，必须同时提供持久化的 `--request-id` 和 `--execute` 才消费一张卡。请求前保存审计，之后 GET 读回；相同请求 ID 不重复发送，结果不明应人工核对，不要生成新 ID 盲重试。完整重置会改变自然重置时间，且不是购买 Credits。

```bash
chatcrs codex reset list --profile work --json-output
chatcrs codex reset consume --profile work --request-id one-reviewed-operation --json-output
```

如既有反代未提供重置路由，可用 `--base-url` 显式指定重置后端；它不改变该 profile 的 usage/auth base，也不会修改配置。服务使用 ChatGPT 后端接口，可能随上游变化，不等同于稳定的 OpenAI Platform 公共 API。Python 消费者使用 `chatcrs.reset_credits.CodexResetClient`、`inspect_reset_credits` 与 `consume_reset_credit`；客户端 `consume(..., execute=True)` 由调用者自己的策略和持久化去重保护。ChatGlance 的阈值策略不属于 ChatCRS。


## CRS 托管 Codex（Unreleased）

此管理型客户端是 **Unreleased** 源码功能，**不包含在 0.3.4**。网络操作的前置条件是 CRS 服务端部署原生、受 Admin 鉴权保护的以下接口；旧服务器没有这些路由时会失败，不回退为本地 OAuth、缓存统计或 `reset-status`。这不是服务端已发布/已部署的承诺。

所有命令必须指定 `--account-id`；`--profile` 默认 `default`，只选择既有 `CRS` ChatEnv namespace，绝不是 `Codex` OAuth profile。固定服务 origin 与账号 identity（`token_service="CRS"`），不复制上游 OAuth。仪表板优先在所选 CRS profile 中配置专用管理 Key（`CRS_API_KEY`，`crsm_` 前缀）：客户端只发送该 Key，不读取 Admin 会话或以用户名/密码回退；Key 被拒绝时明确失败。未配置 Key 的操作员路径只复用已存在的 CRS Admin 会话；缺失或被拒绝时失败，不自动登录、续期或重放。请先独立运行 `chatcrs admin login --profile <profile> --save-token` 建立会话。旧 Admin 命令的默认登录生命周期不变。普通模型 Key 不适用于此接口。CLI 仅延迟导入并调用 `chatcrs.managed_codex.CrsManagedCodexClient.from_profile(crs_profile="default", account_id="account-placeholder", home=None, timeout=20)`；Python 消费者直接使用该类的 `identity`、`token_service` 和下表方法，不要 shell out 到 CLI。

| CLI | 原生 CRS 接口（服务端前置） | Python 方法 / 写入边界 |
|---|---|---|
| `chatcrs admin accounts codex usage` | `GET /admin/openai-accounts/{account_id}/codex/usage` | `usage()`；实时上游额度，只读 |
| `chatcrs admin accounts codex credits` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits` | `reset_credits()`；只读，不消费 |
| `chatcrs admin accounts codex consume` | `POST /admin/openai-accounts/{account_id}/codex/reset-credits/consume` | `consume(request_id, credit_id=None, execute=False)`；默认本地无网络 dry-run |
| `chatcrs admin accounts codex operation` | `GET /admin/openai-accounts/{account_id}/codex/reset-credits/operations/{request_id}` | `operation(request_id)`；只读历史回执 |

```bash
chatcrs admin accounts codex usage --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex credits --profile crs-profile --account-id account-placeholder --json-output
chatcrs admin accounts codex consume --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
chatcrs admin accounts codex operation --profile crs-profile --account-id account-placeholder --request-id request-placeholder --json-output
```

`consume` 与 `operation` 的 `--request-id` 必需；消费可选 `--credit-id credit-placeholder`。确认目标后才给消费命令加 `--execute`，并持久保存同一个 request ID。CLI 每次只调用一次客户端方法，不自动重试、不换 ID；不确定结果使用原 ID 查回执，不盲目再消费。

`--json-output` 输出客户端安全结构化 JSON；异常输出固定安全错误，退出非零，不输出原始异常或凭据。默认消费计划的 `dry_run` 退出 0；实际消费或历史回执仅 `reset_verified`、`nothing_to_reset`、`no_credit` 为已知完成结果、退出 0（后两者不代表已消费）。`uncertain`、`pending`、未知状态、HTTP 202 或异常均非成功、退出非零；历史 receipt 的未知状态可以显示，但不是新鲜额度验证。旧 `chatcrs admin accounts usage` 仍读取 CRS 缓存统计，不改变语义。
