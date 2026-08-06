# 配置与目标

## 单一 CRS ChatEnv profile

ChatCRS 使用一套 canonical CRS ChatEnv namespace：

```text
~/.chatarch/envs/CRS/<profile>.env
```

默认 profile 是 `admin`，也可以用 `--profile` 指定其它 profile。当前包内 CLI 不维护第二套 ChatEnv target namespace。

## 环境变量

| 变量 | 说明 | 敏感 |
|---|---|---|
| `CRS_API_BASE` | 远程 CRS URL | 否 |
| `CRS_API_KEY` | CRS API key，用于普通 key 自查 | 是 |
| `CRS_USERNAME` | CRS 管理员用户名 | 是 |
| `CRS_PASSWORD` | CRS 管理员密码 | 是 |
| `CRS_ACCESS_TOKEN` | CRS 管理员 bearer/session token | 是 |

## 本地/服务端能力边界

当前配置只描述 CRS HTTP/API 连接与凭据。服务进程生命周期、部署目录、Nginx/edge、Redis、release/cutover 等 host-local 信息不属于这套 profile。

如果某个管理动作没有 CRS HTTP/Admin endpoint，ChatCRS 应报告缺口；后续若要实现，只能作为明确的 server-local/host-agent 能力重新设计，而不是混入普通 HTTP 管理配置。

## 登录排查

`chatcrs key info` 使用 CRS API key；`chatcrs admin ...` 使用管理员用户名/密码或管理员 token。前者 HTTP 200 只能证明 API key 自查链路可用，不能证明 admin profile 可用。

如果 `chatcrs admin accounts usage` 返回 `CRS admin login failed status=401 reason=Invalid username or password`，说明当前 profile 的管理员凭据没有被生产 `/web/auth/login` 接受。此时应刷新 ChatEnv profile 中的 `CRS_USERNAME` / `CRS_PASSWORD` 或提供有效 `CRS_ACCESS_TOKEN`，而不是排查 account usage API 解析。

敏感字段只应存在于 ChatEnv 或进程环境中，不进入命令行参数、文档、PR body 或日志输出。Profile 文件应使用 `0600` 权限。
