# CLI 命令树

以下命令树与 `chatcrs --help` 及自动化 CLI 注册测试保持一致。

```text
chatcrs                                           # ChatArch CRS 运维与验收 CLI
├── health                                        # 检查指定 CRS 的 /health
├── inspect                                       # 只读检查已知生产/sidecar 拓扑
├── local verify                                  # 验证本机 CRS health/web/API/admin login
├── verify sidecar                                # 只读验证 12390/12391 sidecar 状态
├── verify images                                 # 验证 CRS API-key/Responses，可选真实 Images 请求
├── admin                                         # 通过 HTTPS Admin API 管理远程 CRS
│   ├── login                                     # 验证管理员登录，不输出 session token
│   ├── accounts                                  # 查看/刷新 CRS 账号状态
│   │   ├── usage                                 # 查看 OpenAI/Codex 账号 usage 与调度状态
│   │   └── refresh-status                        # 默认 dry-run；--execute 调 reset-status
│   └── keys                                      # 查看 CRS API key 元数据和统计
│       ├── list                                  # 列出 API key，默认脱敏；可 --include-stats
│       └── show                                  # 按 id/name 查看单个 API key 安全摘要
├── key                                           # 只凭普通 CRS API key 的非管理员命令
│   └── info                                      # 查询当前 API key 信息/绑定/usage
├── service                                       # 吸收官方 crs 生命周期管理命令
│   ├── install                                   # 默认 plan；--execute 远程执行 crs install
│   ├── update                                    # 默认 plan；--execute 远程执行 crs update
│   ├── start                                     # 默认 plan；--execute 远程执行 crs start
│   ├── stop                                      # 默认 plan；--execute 远程执行 crs stop
│   ├── restart                                   # 默认 plan；--execute 远程执行 crs restart
│   ├── status                                    # 默认 plan；--execute 远程执行 crs status
│   ├── switch-branch                             # 默认 plan；--execute 远程执行 crs switch-branch
│   └── update-pricing                            # 默认 plan；--execute 远程执行 crs update-pricing
├── nginx plan-cutover                            # 生成 Nginx 切流 diff，不写文件、不 reload
├── cutover precheck                              # 只读评估正式单活切换条件
└── debug                                         # 只管理隔离 debug runtime，不碰生产
    ├── status                                    # 查看 debug health/tmux/Redis/Git/安全配置
    ├── logs                                      # 读取 debug 日志尾部并脱敏
    ├── restart                                   # 默认 plan；--execute 重启 debug tmux
    ├── settings show                             # 查看允许展示的非敏感 debug 设置
    ├── settings set                              # 默认 plan；--execute 修改白名单设置并重启 debug
    ├── upgrade plan                              # 比较 debug checkout 与远端 ChatArch dev
    └── upgrade apply                             # 默认 plan；--execute 按审核 SHA 升级 debug
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

## Service 生命周期命令

`chatcrs service` 吸收官方 `/usr/bin/crs` 的机械生命周期入口，用作模型和人类共同调用的远程管理工具。实现上通过 SSH 在目标 CRS app 目录执行官方 `crs ...`，但默认只输出计划；`install/update/start/stop/restart/switch-branch/update-pricing` 只有显式 `--execute` 才会实际变更远端服务或代码。

通用参数：

```bash
chatcrs service <command> --ssh-alias tencent.am --app-dir /home/zhihong/claude-relay-service/app --json-output
chatcrs service <command> --ssh-alias tencent.am --app-dir /home/zhihong/claude-relay-service/app --execute --json-output
```

支持环境变量默认值：

```text
CHATCRS_SSH_ALIAS   # 例如 tencent.am
CHATCRS_APP_DIR     # 例如 /home/zhihong/claude-relay-service/app
CHATCRS_CRS_COMMAND # 例如 /usr/bin/crs，默认 crs
```

### `service install`

计划或执行官方 `crs install`。

### `service update`

计划或执行官方 `crs update`。

### `service start`

计划或执行官方 `crs start`。

### `service stop`

计划或执行官方 `crs stop`。这是生产影响动作，默认 dry-run。

### `service restart`

计划或执行官方 `crs restart`。

### `service status`

计划或执行官方 `crs status`。

### `service switch-branch`

计划或执行官方 `crs switch-branch <branch>`。

```bash
chatcrs service switch-branch dev --ssh-alias tencent.am --json-output
chatcrs service switch-branch dev --ssh-alias tencent.am --execute --json-output
```

### `service update-pricing`

计划或执行官方 `crs update-pricing`。

命令输出会脱敏 stdout/stderr 中的 Authorization、token、API key 等敏感片段。

## 生产/调试安全边界

### `nginx plan-cutover`

生成 Nginx 端口替换 diff，不写文件、不 reload。

### `cutover precheck`

只读评估 12390 -> 12391 单活切换条件。

## Debug 命令

参见 [调试服务管理](debug-service.md)。所有 Debug 写操作都固定在 12392，不接受 app/port 参数。
