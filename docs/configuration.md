# 配置与目标

## 单一 CRS ChatEnv profile

ChatCRS 使用一套 canonical CRS ChatEnv namespace。默认 profile 是 `admin`，也可以用 `--profile` 指定其它 profile。当前包内 CLI 不维护第二套 ChatEnv target namespace。公开文档不写具体 secret 文件路径。

## 配置字段类别

| 字段类别 | 说明 | 敏感 |
|---|---|---|
| HTTP base URL | 远程 CRS URL | 否 |
| caller API key | CRS API key，用于普通 key 自查 | 是 |
| admin username | CRS 管理员用户名 | 是 |
| admin password | CRS 管理员密码 | 是 |

## Runtime token store

短期 CRS Admin session token 不再作为主要配置写入 Env。ChatCRS 会使用与 Env profile 平行的 token store；安装 ChatCRS 后也会注册 ChatEnv refresh provider，因此既可以运行 `chatcrs admin token refresh --profile <profile>`，也可以运行 `chatenv token refresh CRS <profile>`：

```text
~/.chatarch/envs/CRS/<profile>.env     # 稳定配置
~/.chatarch/tokens/CRS/<profile>.json  # 动态 Admin session token
```

读取顺序是：显式 `--admin-token` > runtime token file > 使用 username/password 登录。Admin API 返回 401 时，如果 profile 里有 username/password，ChatCRS 会重新登录、更新 token file，并重试一次。

`chatcrs admin token status` 只输出 token 文件路径、存在性、是否过期、base URL 是否匹配等元数据；不会打印 token。`chatcrs admin token clear` 默认 dry-run，必须加 `--execute` 才删除本地 token file。

## Codex/OpenAI relay 字段

`chatcrs codex ...` 复用 ChatEnv 中由 ChatCRS 拥有的 `Codex` namespace。稳定 refresh seed 与非 secret relay 字段在 `envs/Codex/<profile>.env`，runtime access/refresh token 与 account metadata 在 `tokens/Codex/<profile>.json`。

| 字段 | 用途 | 敏感 |
|---|---|---|
| `OPENAI_OAUTH_BASE_URL` | OAuth refresh 与 accounts API base URL；默认 `https://auth.openai.com` | 否 |
| `CHATGPT_BACKEND_BASE_URL` | ChatGPT backend base URL；默认 `https://chatgpt.com/backend-api` | 否 |

中转只改变目标 base URL。Access token、refresh token、`ChatGPT-Account-ID` 等凭据仍由客户端按请求头或 token-store 管理，不能写入 Nginx/proxy 配置或日志。`account` 输出优先使用 access-token claims 与 token-store metadata 生成安全 `account_summary`，accounts API 只作为 redacted probe；`usage` 输出只保留 `account_id_hash` 与脱敏 body，不打印 raw account id、email 或 user id。

## 本地/服务端能力边界

当前配置只描述 CRS HTTP/API 连接与凭据。服务进程生命周期、部署目录、Nginx/edge、Redis、release/cutover 等 host-local 信息不属于这套 profile。

如果某个管理动作没有 CRS HTTP/Admin endpoint，ChatCRS 应报告缺口；后续若要实现，只能作为明确的 server-local/host-agent 能力重新设计，而不是混入普通 HTTP 管理配置。

## 登录排查

`chatcrs key info` 使用 CRS API key；`chatcrs admin ...` 使用管理员用户名/密码或管理员 token。前者 HTTP 200 只能证明 API key 自查链路可用，不能证明 admin profile 可用。

如果 `chatcrs admin accounts usage` 返回 `CRS admin login failed status=401 reason=Invalid username or password`，说明当前 profile 的管理员凭据没有被生产 `/web/auth/login` 接受。此时应刷新 ChatEnv profile 中的管理员 identity/password 字段，或一次性提供有效的 `--admin-token`，而不是排查 account usage API 解析。

敏感字段只应存在于 ChatEnv、runtime token store 或进程环境中，不进入文档、PR body 或日志输出。
