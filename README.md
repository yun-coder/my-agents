# OpenAI Responses API Python 示例

这个示例使用 Python 调用 OpenAI Responses API，并通过 LangSmith 记录调用链路。

## 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 配置本地 dev 文件

项目会在运行时读取当前目录下的 `dev.json`，不用在系统环境变量里配置 OpenAI key。

如果还没有 `dev.json`，可以复制示例文件：

```powershell
Copy-Item dev.example.json dev.json
```

然后修改 `dev.json`：

```json
{
  "openai": {
    "api_key": "your-api-key",
    "base_url": "https://your-api-provider.example.com/v1",
    "model": "gpt-4.1-mini"
  },
  "langsmith": {
    "tracing": false,
    "api_key": "",
    "project": "prompt"
  }
}
```

其中 `openai.base_url` 改成第三方 API 服务提供的 OpenAI 兼容接口地址，`openai.api_key` 改成对应 key。

如果需要启用 LangSmith Trace，把 `langsmith.tracing` 改成 `true`，并填写 `langsmith.api_key`。

## 运行示例

```powershell
python ResponsesAPI.py
```

运行完成后，可以打开 https://smith.langchain.com/ 查看 `LANGSMITH_PROJECT` 对应项目中的 Trace。

## 最基础 Prompt 调用

如果只需要读取 `dev.json` 并发送一条 prompt，可以运行：

```powershell
python basic_prompt.py "请用中文介绍一下你自己"
```

不传参数时，会使用脚本里的默认 prompt：

```powershell
python basic_prompt.py
```

## 常见错误

如果看到下面这类错误：

```text
openai.RateLimitError: Error code: 429
code: insufficient_quota
```

说明当前 `dev.json` 里的 `openai.api_key` 对应账号额度不足，或者账号计划、账单、用量限制不允许继续调用。这不是脚本语法问题。

处理方式：

1. 登录 OpenAI 控制台检查 billing、plan 和 usage limits。
2. 确认 `dev.json` 里的 `openai.api_key` 是有可用额度的 key。
3. 如果刚充值或刚调整限制，等待一段时间后重新运行。

## 文件说明

- `ResponsesAPI.py`：Python 调用 OpenAI Responses API 的示例脚本。
- `basic_prompt.py`：最基础的 prompt API 调用示例，不包含 LangSmith。
- `dev.example.json`：本地配置示例。
- `dev.json`：本地开发配置文件，存放 `api_key` 和 `base_url`，已加入 `.gitignore`。
- `requirements.txt`：Python 依赖列表。
