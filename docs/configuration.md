# 配置与目标

## 环境变量

| 变量 | 说明 | 敏感 |
|---|---|---|
| `CHATCRS_BASE_URL` | 远程 CRS URL | 否 |
| `CHATCRS_API_KEY` | CRS API key，用于普通 key 自查 | 是 |
| `CHATCRS_ADMIN_USERNAME` | CRS 管理员用户名 | 是 |
| `CHATCRS_ADMIN_PASSWORD` | CRS 管理员密码 | 是 |
| `CHATCRS_ADMIN_TOKEN` | CRS 管理员 bearer token | 是 |
| `CHATCRS_SSH_ALIAS` | service lifecycle 的 SSH 目标别名 | 否 |
| `CHATCRS_APP_DIR` | service lifecycle 的远端 CRS app 目录 | 否 |
| `CHATCRS_CRS_COMMAND` | 远端官方 `crs` 命令路径；默认 `crs` | 否 |

远程 Admin API 也兼容既有 `CRS_API_BASE`、`CRS_API_KEY`、`CRS_USERNAME`、`CRS_PASSWORD`、`CRS_ACCESS_TOKEN` 字段，便于复用现有 ChatEnv profile。

## tencent.am wrapper

机器上的 wrapper 只保存 URL、SSH alias 和 app 目录这类定位信息，不保存 key 值：

```text
/usr/local/bin/chatcrs
/usr/local/bin/chatcrs-production
```

显式 target wrapper 主要影响 `health`、`admin`、`key` 和 `service` 的默认目标。生产写操作仍必须显式 `--execute`，并在执行前确认目标与回滚边界。

## ChatEnv profile

推荐把生产 CRS 管理 profile 放在 ChatEnv / `~/.chatarch/envs/CRS/<profile>.env`，命令默认读取 `admin` profile，也可以用 `--profile` 指定。

Service lifecycle target profile 使用 ChatEnv `Chatcrs` active profile：`~/.chatarch/envs/Chatcrs/.env`。`chatcrs service ...` 会按“显式 CLI 参数 > 进程环境变量 > ChatEnv `Chatcrs` active profile > 包内默认值”解析 `CHATCRS_SSH_ALIAS`、`CHATCRS_APP_DIR` 和 `CHATCRS_CRS_COMMAND`。

敏感字段只应存在于 ChatEnv 或进程环境中，不进入命令行参数、文档、PR body 或日志输出。Profile 文件应使用 `0600` 权限。

## 登录排查

`chatcrs key info` 使用 CRS API key；`chatcrs admin ...` 使用管理员用户名/密码或管理员 token。前者 HTTP 200 只能证明 API key 自查链路可用，不能证明 admin profile 可用。

如果 `chatcrs admin accounts usage` 返回 `CRS admin login failed status=401 reason=Invalid username or password`，说明当前 profile 的管理员凭据没有被生产 `/web/auth/login` 接受。此时应刷新 ChatEnv profile 中的 `CRS_USERNAME` / `CRS_PASSWORD` 或提供有效 `CRS_ACCESS_TOKEN`，而不是排查 account usage API 解析。
