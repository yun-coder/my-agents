# 16 Python 工程化基础

## 学习目标

- 建立可维护的 Agent 项目结构。
- 掌握配置隔离、依赖管理、日志、类型提示和测试。
- 避免 Demo 代码直接长成不可维护的生产系统。

## 推荐结构

```text
project/
  app/
    config.py
    services/
    api/
  tests/
  dev.example.json
  requirements.txt
  README.md
```

## 基本原则

- 真实密钥只放本地未跟踪文件或 secret manager。
- 提交 `dev.example.json`，不提交 `dev.json`。
- 公共客户端创建逻辑只写一次。
- 为纯函数优先写单元测试。
- 外部模型调用要有超时、日志和可观测性。
- 依赖版本要可复现，升级时跑回归测试。

## 当前仓库建议

- 新课程统一复用 `shared/config.py`。
- 后续逐步把旧 Demo 迁移到共享配置。
- `local-langSmith/langsmith_config.yaml` 中的明文敏感值需要脱敏并轮换。

## 参考资料

- [Python Packaging User Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python logging](https://docs.python.org/3/library/logging.html)
- [Ruff](https://docs.astral.sh/ruff/)

## 验收清单

- 能解释配置文件为何不能提交真实密钥。
- 能运行测试。
- 能为新章节复用共享配置模块。
