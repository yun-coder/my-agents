# LangSmith integration

This project uses Python to test the OpenAI Responses API with LangSmith tracing.

```powershell
python -m pip install -r requirements.txt
```

Set these environment variables before running the script:

```powershell
$env:LANGSMITH_TRACING = "true"
$env:LANGSMITH_API_KEY = "lsv2_..."
$env:LANGSMITH_PROJECT = "prompt"
$env:OPENAI_API_KEY = "sk-..."
```

Then run:

```powershell
python ResponsesAPI.py
```

`ResponsesAPI.py` uses:

- `wrap_openai(OpenAI())` to trace OpenAI SDK calls, including `responses.create`.
- `@traceable(...)` to group the whole business function as `Generate bedtime story`.

After the script finishes, open https://smith.langchain.com/ and check the `prompt` project, or the project name in `LANGSMITH_PROJECT`.
