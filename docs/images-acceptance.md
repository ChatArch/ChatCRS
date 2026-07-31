# Images 验收

## 默认预检

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --json-output
```

默认阶段：

1. `/openai/key-info`
2. 普通 `gpt-5.5` Responses marker
3. Image 阶段标记为未执行

JSON 中 `mutated=false`。普通模型请求可能产生上游使用量，但不会写服务配置或生成图片。

## 真实图片

```bash
chatcrs verify images \
  --base-url http://127.0.0.1:12392 \
  --openai-env-file ~/.chatarch/envs/OpenAI/image2-73-debug.env \
  --execute-image \
  --output ./chatcrs-image-acceptance.png \
  --json-output
```

只有 `--execute-image` 才调用 `gpt-image-2`、消耗额度并写 PNG。API key 不进入 argv 和输出。

生产环境不应把真实图片验收当作常规 health check。
