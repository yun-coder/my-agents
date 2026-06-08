FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir openai langgraph langfuse fastapi uvicorn[standard] \
    pydantic instructor chromadb sentence-transformers FlagEmbedding PyMuPDF python-docx httpx

COPY src/ ./src/
RUN mkdir -p /app/data/chroma
EXPOSE 8000
CMD ["python", "-m", "src.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
