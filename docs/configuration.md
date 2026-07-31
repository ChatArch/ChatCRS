# 配置与目标

## 环境变量

| 变量 | 说明 | 敏感 |
|---|---|---|
| `CHATCRS_BASE_URL` | 默认 CRS URL | 否 |
| `CHATCRS_SECRETS_FILE` | 本地 admin secrets 文件路径 | 是 |
| `CHATCRS_API_KEY` | CRS API key（schema 兼容） | 是 |
| `CHATCRS_OPENAI_ENV_FILE` | 含 `OPENAI_API_KEY` 的 env 文件路径 | 是 |
| `CHATCRS_AUDIT_DIR` | 调试写操作的 safe audit/backup 目录 | 否 |

## tencent.am wrappers

机器上的 wrapper 只保存 URL 和 env-file 路径，不保存 key 值：

```text
/usr/local/bin/chatcrs
/usr/local/bin/chatcrs-debug
/usr/local/bin/chatcrs-candidate
/usr/local/bin/chatcrs-production
```

普通 `chatcrs` 默认 debug，降低误操作生产的风险。显式 target wrapper 主要影响 `health`、`local verify` 和 `verify images` 的 base URL。

`chatcrs debug ...` 始终固定管理 12392；即使从 production wrapper 调用，也不会改为操作 12390。

## Audit 目录

每次真正执行 debug restart/settings/upgrade 后，ChatCRS 写入 0600 safe JSON。settings/upgrade 的敏感备份位于 0700 子目录，不能提交 Git。
