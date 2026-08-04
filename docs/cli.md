# CLI 命令树

本页只列 **当前代码已经实现并注册的命令**。命令树由 `chatcrs.cli` 的 Click 注册表回读校验；新增或删除命令时，测试会要求同步更新本页。

## 顶层命令

```text
chatcrs                                           # ChatArch CRS 运维与验收 CLI
├── health                                        # 检查指定 CRS 的 /health
├── local                                         # 本机 CRS 验证入口
│   └── verify                                    # 验证本机 health/web/API/admin login
├── verify                                        # sidecar 与专项产物验收
│   ├── sidecar                                   # 只读验证 12390/12391 sidecar 状态
│   └── images                                    # 默认只验 key-info/Responses；图片生成需 opt-in
├── admin                                         # 通过 HTTPS Admin API 管理远程 CRS
│   ├── login                                     # 验证管理员登录，不输出 session token
│   ├── accounts                                  # 查看/刷新 OpenAI/Codex 账号状态
│   │   ├── usage                                 # 查看账号 usage、调度与可用状态
│   │   └── refresh-status                        # 默认 dry-run；--execute 调 CRS reset-status
│   └── keys                                      # 查看 CRS API key 元数据和统计
│       ├── list                                  # 列出 API key；可附带 batch stats/last-usage
│       └── show                                  # 按 id/name 查看单个 API key 安全摘要
├── key                                           # 普通 CRS API key 自查命令
│   └── info                                      # 查询当前 API key 信息/可用性/usage
├── service                                       # 吸收官方 crs lifecycle 管理语义
│   ├── install                                   # 默认 plan；--execute 远程执行 crs install
│   ├── update                                    # 默认 plan；--execute 远程执行 crs update
│   ├── start                                     # 默认 plan；--execute 远程执行 crs start
│   ├── stop                                      # 默认 plan；--execute 远程执行 crs stop
│   ├── restart                                   # 默认 plan；--execute 远程执行 crs restart
│   ├── status                                    # 默认 plan；--execute 远程执行 crs status
│   ├── switch-branch                             # 默认 plan；--execute 远程执行 crs switch-branch
│   └── update-pricing                            # 默认 plan；--execute 远程执行 crs update-pricing
├── nginx                                         # Nginx CRS 路由规划
│   └── plan-cutover                              # 生成切流 diff，不写文件、不 reload
├── cutover                                       # 正式单活切换检查
│   └── precheck                                  # 只读评估切换条件
├── debug                                         # 只管理隔离 debug runtime，不碰生产
│   ├── status                                    # 查看 debug health/tmux/Redis/Git/安全配置
│   ├── logs                                      # 读取 debug 日志尾部并脱敏
│   ├── restart                                   # 默认 plan；--execute 重启 debug tmux
│   ├── settings                                  # 查看/修改白名单 debug 设置
│   │   ├── show                                  # 展示可公开的非敏感设置
│   │   └── set                                   # 默认 plan；--execute 修改白名单字段
│   └── upgrade                                   # debug checkout 升级流程
│       ├── plan                                  # 比较当前 debug 与远端 ChatArch dev
│       └── apply                                 # 默认 plan；--execute 按审核 SHA 升级 debug
└── inspect                                       # 只读检查已知生产/sidecar 拓扑
```

## 覆盖矩阵

| 前面讨论的能力 | 当前已实现命令 | 状态边界 |
|---|---|---|
| 每个账号使用情况 | `chatcrs admin accounts usage` | 管理员 HTTPS API，只输出脱敏 usage / status / scheduling 摘要 |
| 刷新/重置账号使用状态 | `chatcrs admin accounts refresh-status` | 默认 dry-run；`--execute` 调 CRS `reset-status`；不是 OAuth refresh-token 强刷 |
| API key 信息统计 | `chatcrs admin keys list`, `chatcrs admin keys show` | 支持 masked key、状态、限制、统计和 last-usage 摘要 |
| 普通 CRS API key 查询自身信息 | `chatcrs key info` | 不需要管理员凭据，只查当前 key 可见的信息 |
| 吸收官方 `/usr/bin/crs` 生命周期命令 | `chatcrs service install`, `chatcrs service update`, `chatcrs service start`, `chatcrs service stop`, `chatcrs service restart`, `chatcrs service status`, `chatcrs service switch-branch`, `chatcrs service update-pricing` | 默认只输出远程执行计划；`--execute` 才 SSH 到目标 app 目录执行官方 `crs ...` |
| 生产/sidecar 拓扑检查 | `chatcrs inspect`, `chatcrs verify sidecar`, `chatcrs health` | 只读 |
| Nginx / cutover 规划 | `chatcrs nginx plan-cutover`, `chatcrs cutover precheck` | 只生成 diff 或 precheck，不写 Nginx、不 reload |
| Images 专项验收 | `chatcrs verify images` | 默认不生成图片；`--execute-image` 才调用图片接口 |
| 隔离 debug runtime 管理 | `chatcrs debug status/logs/restart/settings/upgrade` | 固定 12392；写操作默认 plan；不能改去操作生产 |

## 注册命令清单

| 命令 | 责任 |
|---|---|
| `chatcrs health` | CRS health 检查 |
| `chatcrs local verify` | 本机 CRS 验证 |
| `chatcrs verify sidecar` | sidecar 只读验收 |
| `chatcrs verify images` | Images/Responses 验收 |
| `chatcrs admin login` | 管理员登录验证 |
| `chatcrs admin accounts usage` | 账号 usage 查询 |
| `chatcrs admin accounts refresh-status` | 账号 CRS 状态 reset-status |
| `chatcrs admin keys list` | API key 列表与统计 |
| `chatcrs admin keys show` | 单个 API key 摘要 |
| `chatcrs key info` | 普通 API key 自查 |
| `chatcrs service install` | 官方 crs install 语义 |
| `chatcrs service update` | 官方 crs update 语义 |
| `chatcrs service start` | 官方 crs start 语义 |
| `chatcrs service stop` | 官方 crs stop 语义 |
| `chatcrs service restart` | 官方 crs restart 语义 |
| `chatcrs service status` | 官方 crs status 语义 |
| `chatcrs service switch-branch` | 官方 crs switch-branch 语义 |
| `chatcrs service update-pricing` | 官方 crs update-pricing 语义 |
| `chatcrs nginx plan-cutover` | Nginx 切流 diff 规划 |
| `chatcrs cutover precheck` | 正式切换 precheck |
| `chatcrs debug status` | debug runtime 状态 |
| `chatcrs debug logs` | debug 日志脱敏读取 |
| `chatcrs debug restart` | debug 重启计划/执行 |
| `chatcrs debug settings show` | debug 设置查看 |
| `chatcrs debug settings set` | debug 白名单设置修改 |
| `chatcrs debug upgrade plan` | debug 升级计划 |
| `chatcrs debug upgrade apply` | debug 升级执行 |
| `chatcrs inspect` | 已知 CRS 拓扑只读检查 |

## 远程管理员与 API key { #remote-admin-and-api-key }

<div class="grid cards" markdown>

-   **管理员登录**

    ---

    `chatcrs admin login` 验证 CRS 管理员凭据，只报告状态和 token 是否存在，不输出 token。

-   **账号 usage**

    ---

    `chatcrs admin accounts usage` 查看 OpenAI/Codex 账号 usage、状态、调度可用性和最近使用摘要。

-   **账号状态刷新**

    ---

    `chatcrs admin accounts refresh-status <account_id>` 默认 dry-run；`--execute` 才调用 CRS reset-status。

-   **API key 统计**

    ---

    `chatcrs admin keys list --include-stats` 聚合 API key 元数据、batch stats 与 last-usage；`show` 查单个 key。

</div>

```text
chatcrs admin                                     # 远程 CRS 管理员入口
├── login                                         # 验证登录，不泄露 token
├── accounts                                      # 账号状态和 usage
│   ├── usage                                     # 列出账号 usage 与调度状态
│   └── refresh-status                            # 默认 dry-run；--execute 重置 CRS 状态
└── keys                                          # API key 管理员查询
    ├── list                                      # 列出 key，默认脱敏；可 include stats
    └── show                                      # 单 key 安全摘要
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
    `refresh-status` 是 CRS 账号状态重置，不等同于强制刷新 Codex/OpenAI OAuth refresh token。OAuth token 刷新仍由 CRS 后端策略和账号使用路径决定。

## 普通 API key { #api-key-only }

```text
chatcrs key                                       # 普通 CRS API key 自查入口
└── info                                          # 查询当前 API key 信息/可用性/usage
```

```bash
chatcrs key info --json-output
chatcrs key info --path /api/v1/key-info --json-output
```

## Service 生命周期 { #service-lifecycle }

`chatcrs service` 吸收官方 `/usr/bin/crs` 的生命周期管理语义，但不裸执行危险动作。它通过 SSH 在目标 CRS app 目录运行官方 `crs ...`；默认输出计划，只有 `--execute` 才变更远端。

```text
chatcrs service                                   # 远程封装官方 crs lifecycle
├── install                                       # 默认 plan；--execute 执行 crs install
├── update                                        # 默认 plan；--execute 执行 crs update
├── start                                         # 默认 plan；--execute 执行 crs start
├── stop                                          # 默认 plan；--execute 执行 crs stop
├── restart                                       # 默认 plan；--execute 执行 crs restart
├── status                                        # 默认 plan；--execute 执行 crs status
├── switch-branch                                 # 默认 plan；--execute 执行 crs switch-branch <branch>
└── update-pricing                                # 默认 plan；--execute 执行 crs update-pricing
```

通用参数：

```bash
chatcrs service update \
  --ssh-alias tencent.am \
  --app-dir /home/zhihong/claude-relay-service/app \
  --json-output

chatcrs service update \
  --ssh-alias tencent.am \
  --app-dir /home/zhihong/claude-relay-service/app \
  --execute \
  --json-output
```

环境默认值：

```text
CHATCRS_SSH_ALIAS   # 例如 tencent.am
CHATCRS_APP_DIR     # 例如 /home/zhihong/claude-relay-service/app
CHATCRS_CRS_COMMAND # 例如 /usr/bin/crs，默认 crs
```

!!! note "输出脱敏"
    service 命令会在渲染前过滤 stdout/stderr 中的 Authorization、token、password、API key 和 `cr_...` 形态值。

## 安全边界 { #safety-boundaries }

### 只读验收与生产规划

```text
chatcrs health                                    # 检查 /health
chatcrs local verify                              # 验证本机 CRS
chatcrs verify sidecar                            # 验证 sidecar 拓扑
chatcrs verify images                             # 默认不生成图片
chatcrs inspect                                   # 只读拓扑检查
chatcrs nginx plan-cutover                        # 生成 Nginx diff
chatcrs cutover precheck                          # 评估单活切换条件
```

这些命令不会写 Nginx、不会 reload、不会停服务。

## Debug runtime

```text
chatcrs debug                                     # 固定隔离 debug runtime
├── status                                        # health/tmux/Redis/Git/settings
├── logs                                          # 脱敏日志尾部
├── restart                                       # 默认 plan；--execute 重启 tmux
├── settings                                      # debug settings 白名单
│   ├── show                                      # 查看可公开设置
│   └── set                                       # 默认 plan；--execute 修改白名单字段
└── upgrade                                       # debug checkout 升级
    ├── plan                                      # 只读比较 SHA
    └── apply                                     # 默认 plan；--execute 按审核 SHA 升级
```

Debug 写操作固定在：

```text
app:   /home/zhihong/claude-relay-service-independent/app
HTTP:  127.0.0.1:12392
Redis: 127.0.0.1:6382 DB0
tmux:  crs-debug-12392
```

## 更新规则

- 新增 Click 命令时，必须同步本页的顶层树、对应分组树和覆盖矩阵。
- 删除或重命名命令时，必须同步测试、README、MkDocs 页和 CHANGELOG。
- 规划中但尚未实现的能力不得出现在本页命令树中；只能写在能力地图或 roadmap，并明确标注未实现。
