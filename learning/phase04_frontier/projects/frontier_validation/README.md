# 阶段四综合项目：前沿能力验证集

这个项目为 GUI、多模态和微调建立统一的评估记录格式。

每个能力都需要填写：

| 字段 | 用途 |
| --- | --- |
| `capability` | 被验证的能力 |
| `risk_level` | low、medium 或 high |
| `score` | 当前验证分数 |
| `pass_threshold` | 进入下一阶段所需分数 |
| `evidence` | 可追溯的测试证据 |

## 运行

```powershell
python .\learning\phase04_frontier\projects\frontier_validation\cli.py
```

## 设计边界

- 分数只是决策输入，不是上线许可。
- 高风险能力即使达到分数门槛，也仍需安全评审和人工确认策略。
- 验证集应随着真实失败案例持续扩充。
