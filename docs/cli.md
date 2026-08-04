# CLI 命令树

以下命令树与 `chatcrs --help` 及自动化 CLI 注册测试保持一致。

```text
chatcrs
├── health
├── inspect
├── local
│   └── verify
├── verify
│   ├── sidecar
│   └── images
├── admin
│   ├── login
│   ├── accounts
│   │   ├── usage
│   │   └── refresh-status
│   └── keys
│       ├── list
│       └── show
├── key
│   └── info
├── nginx
│   └── plan-cutover
├── cutover
│   └── precheck
└── debug
    ├── status
    ├── logs
    ├── restart
    ├── settings
    │   ├── show
    │   └── set
    └── upgrade
        ├── plan
        └── apply
```

## 全局入口

### `health`

检查指定或默认 CRS 的 `/health`。

```bash
chatcrs health --json-output
chatcrs-production health --json-output
```

### `inspect`

只读检查生产/sidecar 路径、端口、Redis DB、systemd、Nginx 和监听端口。

### `local verify`

检查 health、Web、受保护 API，以及可选的 admin login。

### `verify sidecar`

验证 12390/12391 的只读 sidecar 状态。

### `verify images`

先验证 API key 和普通 Responses；只有 `--execute-image` 才生成图片。

## 远程 CRS 管理员命令

`chatcrs admin` 通过 CRS HTTP Admin API 操作远程 CRS，不直接写 Redis，也不要求 SSH 进服务器。

默认凭据来源为 ChatEnv 风格文件：

```text
~/.chatarch/envs/CRS/admin.env
```

支持字段：

```text
CRS_API_BASE       # 例如 https://crs.example.com
CRS_API_KEY        # 普通 CRS API key，用于 key-only 查询
CRS_USERNAME       # 管理员用户名
CRS_PASSWORD       # 管理员密码
CRS_ACCESS_TOKEN   # 可选：已有 admin bearer token
```

命令输出会脱敏常见 token / password / api key 字段。真实使用时优先让命令从 ChatEnv profile 读取，不要把 secret 放到 shell argv。

### `admin login`

验证管理员登录，只报告状态和 token 是否存在，不输出 token。

```bash
chatcrs admin login --json-output
```

### `admin accounts usage`

查看 OpenAI/Codex 账号的状态、调度和 usage 元数据。

```bash
chatcrs admin accounts usage --json-output
```

### `admin accounts refresh-status`

刷新/重置单个 OpenAI/Codex 账号的 CRS 状态。默认 dry-run；只有显式 `--execute` 才调用：

```http
POST /admin/openai-accounts/<account_id>/reset-status
```

```bash
chatcrs admin accounts refresh-status <account_id> --json-output
chatcrs admin accounts refresh-status <account_id> --execute --json-output
```

注意：这个命令是 CRS 账号状态重置，不等同于强制刷新 Codex/OpenAI OAuth refresh token。OAuth token 刷新仍由 CRS 后端策略和账号使用路径决定。

### `admin keys list`

统计/列出 CRS API key 元数据。`--include-stats` 会额外调用 batch stats 和 batch last-usage，返回每个 key 的用量统计与最近使用账号归因。

```bash
chatcrs admin keys list --json-output
chatcrs admin keys list --include-stats --json-output
```

### `admin keys show`

按 key id 或名称查单个 API key。

```bash
chatcrs admin keys show <key_id_or_name> --json-output
```

## API-key-only 命令

### `key info`

只使用普通 CRS API key 查询 `/openai/key-info`，不需要管理员登录。

```bash
chatcrs key info --json-output
```

如果需要兼容其他 CRS key-info 路径，可以指定：

```bash
chatcrs key info --path /api/v1/key-info --json-output
```

## 生产/调试安全边界

### `nginx plan-cutover`

生成 Nginx 端口替换 diff，不写文件、不 reload。

### `cutover precheck`

只读评估 12390 -> 12391 单活切换条件。

## Debug 命令

参见 [调试服务管理](debug-service.md)。所有 Debug 写操作都固定在 12392，不接受 app/port 参数。
