# 任务 Runbook 边界

这类能力已经从 ChatCRS 包内注册 CLI 移出。

原因：Web edge、正式流量切换、图片能力验收和隔离调试 runtime 管理都依赖当前主机拓扑、Nginx 配置、凭据来源、回滚窗口和实时风险判断，不适合固定成一个通用包命令。

需要执行时，模型应在当前 workspace project 中：

1. 读取项目 `PRD.md` / `progress.md` 和对应 skill；
2. 明确目标主机、目录、端口、edge config、Redis 与回滚边界；
3. 先生成或读取 task-local runbook/script；
4. dry-run 和只读验证通过后，再在用户授权下执行真实变更；
5. 全程脱敏输出，并把证据写回当前 project。
