# 阶段四：前沿能力验证

阶段四不追求堆叠功能，而是学习如何为高风险或高成本能力建立小型验证集。

| 编号 | 知识点 | 默认 Demo |
| --- | --- | --- |
| 39 | Computer Use / GUI Agent | GUI 动作审批策略 |
| 40 | 多模态 Agent | 文本 + 图片请求结构 |
| 41 | Agent 微调 / Fine-tuning / RLHF | 训练样本校验 |

## 运行单个 Demo

```powershell
python .\learning\phase04_frontier\39_computer_use\demo.py
```

## 运行阶段测试

```powershell
python -m unittest discover -s .\learning\phase04_frontier\tests -v
```

综合项目见 `projects/frontier_validation`。
