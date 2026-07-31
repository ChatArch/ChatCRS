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

### `nginx plan-cutover`

生成 Nginx 端口替换 diff，不写文件、不 reload。

### `cutover precheck`

只读评估 12390 -> 12391 单活切换条件。

## Debug 命令

参见 [调试服务管理](debug-service.md)。所有 Debug 写操作都固定在 12392，不接受 app/port 参数。
