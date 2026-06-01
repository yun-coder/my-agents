# 40. 多模态 Agent

## 学习目标

- 理解文本、图片、音频和视频如何进入 Agent 工作流。
- 会构造文本 + 图片输入结构。
- 知道多模态输入同样需要权限、大小和隐私控制。

## 核心概念

多模态 Agent 不只是“让模型看图”。完整链路还包括输入采集、格式转换、模型能力检查、成本控制和结果验证。

| 输入 | 常见任务 | 额外注意 |
| --- | --- | --- |
| 图片 | OCR、截图理解、图表分析 | 分辨率、隐私、视觉误判 |
| 音频 | 转写、客服质检 | 采样率、语言、个人信息 |
| 视频 | 关键帧分析、流程理解 | 文件大小、帧采样、延迟 |

对于 OpenAI Responses API，文本和图片可以作为同一条用户消息中的不同内容项提交。模型是否支持视觉输入，应以当前模型文档为准。

## 示例说明

`demo.py` 只生成请求结构，不发送网络请求。这样可以先理解字段，再将 payload 接入自己的 OpenAI 兼容配置。

## 运行

```powershell
python .\learning\phase04_frontier\40_multimodal_agent\demo.py
```

## 延伸阅读

- [OpenAI Images and Vision 官方指南](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI Responses API 参考](https://developers.openai.com/api/reference/responses/overview)
