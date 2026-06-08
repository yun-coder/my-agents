# 40 — 多模态 Agent

## 概念概述

### 什么是多模态 Agent

多模态 Agent（Multimodal Agent）是指能够同时处理文本、图像、音频、视频等多种数据模态的 AI Agent。与传统纯文本 Agent 不同，多模态 Agent 可以"看见"图片、"听见"声音、"观看"视频，从而实现更丰富的交互方式。

随着 GPT-4V（2023 年 9 月）、Gemini（2023 年 12 月）、Claude 3（2024 年 3 月）等原生多模态模型的发布，多模态 Agent 从实验室走向了生产环境。2024 年 GPT-4o 的发布进一步将视觉、听觉与语言能力整合到单一模型中。

### 能力矩阵

多模态 Agent 支持以下输入-输出组合：

- 文本 + 图像输入：视觉问答、图表分析、文档阅读
- 文本 + 音频输入：语音助手、会议转录分析
- 文本 + 视频输入：视频摘要、监控分析
- 混合多模态输入：同时分析图片和语音

### 核心应用场景

- 视觉问答（VQA）：分析图表、识别物体、阅读文档截图
- 语音助手：语音输入 + LLM 推理 + 语音输出的完整闭环
- 视频理解：从监控视频或教学视频中提取关键事件摘要
- 多模态 RAG：同时搜索文本和图片，综合生成答案
- 文档理解：从扫描 PDF 或截图中提取结构化表格信息

---

## 核心原理

### 1. 图像理解管道

多模态 Agent 处理图像的典型流程基于多模态大模型：

```python
import base64
from openai import OpenAI

class VisionAgent:
    """基于 GPT-4o 的图像理解 Agent"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """分析单张图片"""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{b64}",
                        "detail": "high"
                    }}
                ]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content

    def compare_images(self, images: list[str], question: str) -> str:
        """比较多张图片"""
        content = [{"type": "text", "text": question}]
        for img_path in images:
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}
            })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_tokens=1024
        )
        return response.choices[0].message.content

    def extract_table_from_screenshot(self, image_path: str) -> list[dict]:
        """从截图提取表格数据"""
        result = self.analyze_image(
            image_path,
            "提取这张图片中的所有表格数据，以 Markdown 表格格式返回。只返回数据本身。"
        )
        return self._parse_markdown_table(result)

    def _parse_markdown_table(self, md: str) -> list[dict]:
        lines = md.strip().split("\n")
        if len(lines) < 3:
            return []
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]
        rows = []
        for line in lines[2:]:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
        return rows
```

### 2. Gemini 多模态处理

Google Gemini 支持图像、视频和音频的混合输入，且原生支持视频文件上传：

```python
import google.generativeai as genai

class GeminiMultimodalAgent:
    """基于 Gemini 2.0 的多模态 Agent"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def analyze_video(self, video_path: str, prompt: str) -> str:
        """分析视频内容"""
        video_file = genai.upload_file(video_path)
        import time
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        response = self.model.generate_content([prompt, video_file])
        return response.text

    def image_and_audio(self, image_path: str, audio_path: str, prompt: str) -> str:
        """同时处理图片和音频"""
        image = genai.upload_file(image_path)
        audio = genai.upload_file(audio_path)
        response = self.model.generate_content([prompt, image, audio])
        return response.text

    def stream_vision(self, image_path: str, prompt: str):
        """流式输出图像分析结果"""
        image = genai.upload_file(image_path)
        response = self.model.generate_content([prompt, image], stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
```

### 3. 语音处理管道

完整的语音交互需要"语音转文字（STT）— LLM 推理 — 文字转语音（TTS）"三条流水线：

```python
import whisper
from openai import OpenAI

class VoicePipeline:
    """语音处理管道：STT + LLM + TTS"""

    def __init__(self, openai_key: str, deepgram_key: str = None, stt_engine: str = "whisper", tts_engine: str = "openai"):
        self.openai = OpenAI(api_key=openai_key)
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        if stt_engine == "whisper":
            self.whisper_model = whisper.load_model("medium")

    def speech_to_text(self, audio_path: str) -> str:
        """语音转文字"""
        if self.stt_engine == "whisper":
            result = self.whisper_model.transcribe(audio_path, language="zh")
            return result["text"]
        return ""

    def text_to_speech(self, text: str, output_path: str = "output.mp3", voice: str = "alloy") -> str:
        """文字转语音"""
        response = self.openai.audio.speech.create(
            model="tts-1", voice=voice, input=text
        )
        response.stream_to_file(output_path)
        return output_path

    def voice_conversation(self, audio_input: str) -> str:
        """语音对话：输入音频文件路径，返回回答音频文件路径"""
        user_text = self.speech_to_text(audio_input)
        print(f"[转录] {user_text}")

        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一个语音助手，请简洁回答问题。"},
                {"role": "user", "content": user_text}
            ]
        )
        ai_text = response.choices[0].message.content
        print(f"[回答] {ai_text}")

        output_path = self.text_to_speech(ai_text)
        return output_path
```

### 4. 多模态 RAG

多模态 RAG 在传统文本 RAG 基础上增加了图像检索和图像理解能力：

```python
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import base64

class MultimodalRAG:
    """多模态 RAG 系统：同时索引文本和图片"""

    def __init__(self, openai_key: str, collection_name: str = "multimodal_rag"):
        self.openai = OpenAI(api_key=openai_key)
        self.chroma = chromadb.Client()
        self.collection = self.chroma.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.text_encoder = SentenceTransformer("BAAI/bge-m3")

    def add_text_document(self, text: str, metadata: dict, doc_id: str):
        """添加文本文档"""
        embedding = self.text_encoder.encode(text).tolist()
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[{**metadata, "type": "text"}],
            ids=[doc_id]
        )

    def add_image(self, image_path: str, caption: str, metadata: dict, doc_id: str):
        """添加图片到知识库"""
        embedding = self.text_encoder.encode(caption).tolist()
        self.collection.add(
            embeddings=[embedding],
            documents=[caption],
            metadatas=[{**metadata, "type": "image", "image_path": image_path}],
            ids=[doc_id]
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """图文混合检索"""
        query_embedding = self.text_encoder.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i]
            })
        return documents

    def generate_with_images(self, query: str, top_k: int = 3) -> str:
        """基于图文检索的答案生成"""
        results = self.search(query, top_k)
        content = [{"type": "text", "text": f"问题: {query}\n\n参考信息:\n"}]

        for doc in results:
            if doc["metadata"]["type"] == "text":
                content.append({"type": "text", "text": f"[文本] {doc['content']}\n"})
            elif doc["metadata"]["type"] == "image":
                with open(doc["metadata"]["image_path"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                content.append({"type": "text", "text": f"[图片] {doc['content']}\n"})
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "low"}
                })

        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=1024
        )
        return response.choices[0].message.content
```

---

## 实战指南

### 环境配置

```bash
pip install openai google-generativeai anthropic
pip install openai-whisper        # 本地 STT（需 GPU）
pip install Pillow opencv-python  # 图像处理
pip install chromadb sentence-transformers  # 多模态 RAG
pip install ffmpeg-python         # 视频处理
```

### 图像预处理最佳实践

多模态模型对输入图像有大小限制和格式要求，预处理可以提升性能和准确性：

```python
from PIL import Image
import io

class ImagePreprocessor:
    """图像预处理工具"""

    MAX_SIZE = 2048

    @classmethod
    def optimize_for_model(cls, image_path: str, max_size: int = None) -> bytes:
        """优化图片供模型使用：缩放 + 格式转换"""
        max_size = max_size or cls.MAX_SIZE
        img = Image.open(image_path)

        ratio = min(max_size / img.width, max_size / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        if img.mode == "RGBA":
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()

    @classmethod
    def split_large_image(cls, image_path: str, tile_size: int = 1024) -> list[Image.Image]:
        """将大图分割为瓦片，适合处理扫描文档"""
        img = Image.open(image_path)
        tiles = []
        for y in range(0, img.height, tile_size):
            for x in range(0, img.width, tile_size):
                tile = img.crop((
                    x, y,
                    min(x + tile_size, img.width),
                    min(y + tile_size, img.height)
                ))
                tiles.append(tile)
        return tiles
```

### 视频处理管道

```python
import cv2
import numpy as np
from typing import Generator

class VideoProcessor:
    """视频处理工具：提取关键帧并生成摘要"""

    def __init__(self, video_path: str, fps_sample: int = 1):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.original_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.original_fps
        self.sample_interval = max(1, int(self.original_fps / fps_sample))

    def extract_frames(self) -> Generator[np.ndarray, None, None]:
        """提取关键帧"""
        frame_count = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            if frame_count % self.sample_interval == 0:
                yield frame
            frame_count += 1
        self.cap.release()

    def summarize_video(self, vision_agent, prompt: str = "描述关键内容") -> str:
        """生成视频摘要"""
        frames = list(self.extract_frames())
        step = max(1, len(frames) // 10)
        key_frames = frames[::step][:10]

        descriptions = []
        for i, frame in enumerate(key_frames):
            frame_path = f"/tmp/frame_{i}.jpg"
            cv2.imwrite(frame_path, frame)
            desc = vision_agent.analyze_image(frame_path, f"视频第{i * step}秒画面")
            descriptions.append(f"[第{i * step}秒] {desc}")

        summary_prompt = "基于以下逐帧描述生成视频摘要:\n\n" + "\n".join(descriptions)
        response = vision_agent.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return response.choices[0].message.content
```

### 流式多模态对话

```python
class MultimodalChatAgent:
    """支持图文混合输入的多模态对话 Agent"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.messages = [{"role": "system", "content": "你是多模态 AI 助手，可以分析图片和回答视觉问题。"}]

    def add_image_message(self, image_path: str, text: str = "请分析这张图片"):
        """添加包含图片的用户消息"""
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        self.messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{b64}",
                    "detail": "auto"
                }}
            ]
        })

    def chat(self, text: str, stream: bool = False):
        """发送消息并获取回复"""
        self.messages.append({"role": "user", "content": text})
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        else:
            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            return reply

    def _stream_response(self, response):
        collected = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                collected += content
                yield content
        self.messages.append({"role": "assistant", "content": collected})
```

---

## 最佳实践

### 图片细节级别控制

GPT-4o 支持三种图片细节级别：
- low：低分辨率（512x512），速度最快，适合简单图表
- high：高分辨率（2048x2048），细节最丰富，适合文字密集图片
- auto：模型自动选择，平衡速度和质量

### 语音处理并发优化

生产环境中 STT 和 LLM 可以优化为并行处理：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OptimizedVoicePipeline:
    async def process(self, audio_chunks: list[str]):
        with ThreadPoolExecutor(max_workers=3) as pool:
            texts = await asyncio.gather(*[
                asyncio.get_event_loop().run_in_executor(pool, self.stt, chunk)
                for chunk in audio_chunks
            ])
        return texts
```

### Token 预算估算

处理视频时需要注意 token 消耗：

```python
def estimate_video_cost(duration_sec: int, fps_sample: int = 1) -> dict:
    frames = min(duration_sec * fps_sample, 300)
    tokens_low = frames * 258
    tokens_high = frames * 1700
    return {
        "frames": frames,
        "low_detail_tokens": tokens_low,
        "high_detail_tokens": tokens_high,
    }
```

---

## 常见陷阱

### 陷阱 1：Base64 编码过大

大图编码为 base64 会导致请求体过大。使用 JPEG 压缩（quality=85）并合理缩放（最大 2048px）。

### 陷阱 2：音频采样率不匹配

Whisper 期望 16kHz，Deepgram 期望 8-16kHz。上传前检查采样率并进行重采样。

### 陷阱 3：多模态 Token 消耗失控

图片占据大量 token。默认使用 low detail 模式节省成本，仅在对细节要求高时使用 high detail。

### 陷阱 4：视频处理时序问题

视频上传到 Gemini 需要处理时间。使用异步方式避免阻塞主线程。

---

## API Key 依赖

| 服务                 | 所需 API Key         | 获取方式              |
|----------------------|----------------------|-----------------------|
| OpenAI Vision        | OPENAI_API_KEY       | platform.openai.com   |
| Google Gemini        | GOOGLE_API_KEY       | makersuite.google.com |
| Anthropic Vision     | ANTHROPIC_API_KEY    | console.anthropic.com |
| Deepgram STT/TTS     | DEEPGRAM_API_KEY     | deepgram.com          |
| Whisper（本地）      | 无需 API Key         | 本地 GPU 运行          |

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxx
GOOGLE_API_KEY=AIzaxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx
DEEPGRAM_API_KEY=xxxxxxxxxxxxxx
```
ENDOFFILE