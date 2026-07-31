# 开发与发布

## 本地 gates

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
python -m mkdocs build --strict
python -m build
```

## CLI 变更检查

新增命令时必须同步：

1. Click command registration test
2. `docs/cli.md` 命令树
3. 对应运维页面
4. README / README.en
5. CHANGELOG

## Debug 写操作设计

- 默认 dry-run
- 显式 `--execute`
- 固定 target guard
- 写前备份
- 写后 health
- 失败恢复
- safe audit JSON
- 不输出 credential

## 发布

版本来自 `chatcrs.__version__`。CI 运行测试、MkDocs strict 和 package build；tag workflow 负责发布。
