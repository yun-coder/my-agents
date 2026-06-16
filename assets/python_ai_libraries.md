# Python AI 相关库大全

> 最后更新：2026-06-16

本文档整理了 Python 生态中与人工智能（AI）、机器学习（ML）、深度学习（DL）相关的主要库，按功能分类组织。

---

## 目录

1. [深度学习框架](#1-深度学习框架)
2. [传统/经典机器学习](#2-传统经典机器学习)
3. [自然语言处理 NLP](#3-自然语言处理-nlp)
4. [大语言模型应用框架](#4-大语言模型应用框架)
5. [AI Agent 框架](#5-ai-agent-框架)
6. [计算机视觉](#6-计算机视觉)
7. [生成式 AI](#7-生成式-ai)
8. [音频/语音/音乐 AI](#8-音频语音音乐-ai)
9. [多模态 AI](#9-多模态-ai)
10. [强化学习](#10-强化学习)
11. [图神经网络](#11-图神经网络)
12. [向量数据库](#12-向量数据库)
13. [模型部署与推理](#13-模型部署与推理)
14. [实验追踪与 MLOps](#14-实验追踪与-mlops)
15. [LLM 评估与测试](#15-llm-评估与测试)
16. [分布式训练](#16-分布式训练)
17. [数据处理](#17-数据处理)
18. [ML 应用构建](#18-ml-应用构建)
19. [模型可解释性](#19-模型可解释性)
20. [隐私保护 ML](#20-隐私保护-ml)
21. [编译与优化](#21-编译与优化)
22. [合成数据](#22-合成数据)
23. [知识图谱](#23-知识图谱)
24. [时间序列 AI](#24-时间序列-ai)
25. [量子机器学习](#25-量子机器学习)

---

## 1. 深度学习框架

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **PyTorch** | Meta 开发的张量计算与动态计算图框架；研究和生产领域的主导框架 | 深度学习训练/推理 |
| **TensorFlow** | Google 的全栈 ML 平台，支持静态计算图、Keras API 和广泛的生产工具链 | 深度学习训练/推理 |
| **JAX** | Google 的 Python+NumPy 可组合变换库（自动微分、JIT 编译、向量化）；研究中快速增长 | 高性能数值计算/深度学习 |
| **Keras** | 高级神经网络 API（现已原生集成到 TensorFlow）；用简洁语法快速原型开发 | 深度学习（高层抽象） |
| **Flax** | 原生 JAX 的神经网络库，强调函数式设计和灵活性 | JAX 深度学习 |
| **PaddlePaddle** | 百度的深度学习平台，在中国生态中支持完善，具备生产部署工具 | 深度学习（中国生态） |
| **MindSpore** | 华为开发的 AI 计算框架，面向全场景部署 | 深度学习（中国生态） |
| **PyTorch Lightning** | 标准化 PyTorch 训练循环的结构化库，消除样板代码 | PyTorch 训练管理 |
| **FastAI** | 基于 PyTorch 的高级库，用更少代码训练最先进模型 | 深度学习（快速上手） |
| **MXNet** | Apache 的灵活深度学习框架（活跃度降低但仍在使用） | 深度学习 |

---

## 2. 传统/经典机器学习

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **scikit-learn** | Python 经典 ML 的标杆库：分类、回归、聚类、降维、模型选择 | 传统机器学习 |
| **XGBoost** | 极端梯度提升；表格数据领域的工业标准梯度提升框架 | 梯度提升/表格数据 |
| **LightGBM** | 微软的梯度提升框架，优化速度和内存效率 | 梯度提升/表格数据 |
| **CatBoost** | Yandex 的梯度提升库，对类别特征处理出色 | 梯度提升/表格数据 |
| **MLflow** | 端到端 MLOps 平台：实验追踪、模型打包、注册、部署 | MLOps/实验管理 |
| **Optuna** | 自动超参数优化框架，含高效搜索算法和剪枝策略 | 超参数调优 |
| **Ray Tune** | 基于 Ray 分布式执行引擎的可扩展超参数调优 | 分布式超参数调优 |
| **Hyperopt** | 分布式随机/搜索超参数优化框架 | 超参数调优 |
| **TPOT** | 使用遗传编程自动优化 ML 流水线 | 自动化 ML (AutoML) |
| **AutoGluon** | Amazon 的 AutoML 库，支持表格、图像、文本和时间序列 | 自动化 ML (AutoML) |
| **FLAML** | 微软的快速 AutoML 和调优库 | 自动化 ML (AutoML) |
| **PyCaret** | 低代码 ML 库，自动化模型选择和调优工作流 | 自动化 ML (AutoML) |
| **H2O-3 / H2O Wave** | 开源内存中 ML 平台，含 AutoML、深度学习和可解释性 | AutoML/ML 平台 |
| **Featuretools** | 通过实体关系数据建模实现自动化特征工程 | 特征工程 |
| **tsfresh** | 从时间序列数据中自动提取数百种特征 | 时间序列特征工程 |
| **Category Encoders** | 一系列 scikit-learn 兼容的类别编码转换器 | 数据预处理 |
| **imbalanced-learn** | 处理不平衡数据集的技术：SMOTE、ADASYN、重采样策略 | 数据预处理 |
| **Yellowbrick** | scikit-learn 的可视化诊断和模型选择工具 | 模型可视化 |

---

## 3. 自然语言处理 NLP

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **Transformers** (Hugging Face) | 提供数千个预训练 Transformer 模型，用于文本、音频、视觉任务 | NLP/Transformer |
| **Datasets** (Hugging Face) | 高效加载、预处理和管理大规模 NLP 数据集 | NLP 数据管理 |
| **Tokenizers** (Hugging Face) | 快速 Rust 实现的词元化工具库（Transformers 内部使用） | NLP 词元化 |
| **spaCy** | 工业级 NLP 库，提供预训练管道用于 POS 标注、命名实体识别、依存句法分析 | NLP 管道 |
| **NLTK** | 自然语言工具包；教育型库，用于文本处理、分词、解析 | NLP 教学/研究 |
| **Gensim** | 主题建模和文档相似度分析；含 Word2Vec、Doc2Vec、LSI | 主题建模/相似度 |
| **Stanza** | Stanford 官方 NLP Python 库（取代 CoreNLP 客户端） | NLP |
| **TextBlob** | 简化的 NLP 原型开发 API（情感分析、POS 标注、名词短语提取） | NLP 快速原型 |
| **AllenNLP** | Allen 研究所的深度 NLP 库；面向研究，模块化设计 | NLP 研究 |
| **Flair** | 含最先进嵌入（包括上下文感知词嵌入）的 NLP 库 | NLP 嵌入 |
| **Rasa** | 开源对话 AI 框架，用于构建聊天机器人和助手 | 对话 AI |
| **Pattern** | 网络挖掘和 NLP 工具包，含情感分析、WordNet 集成和机器学习 | NLP/网络挖掘 |
| **jieba** | 中文文本分词库；中文 NLP 必备工具 | 中文 NLP |
| **HanLP** | 生产级中文 NLP 工具包，含解析、NER 和语义分析 | 中文 NLP |
| **paddleNLP** | 百度基于 PaddlePaddle 的 NLP 工具包，含预训练模型 | 中文 NLP |
| **Snorkel** | 程序化标注框架，无需人工标注即可构建训练数据 | 数据标注 |
| **Polyglot** | 支持 160+ 语言的多元 NLP 库，含嵌入、POS 标注、NER | 多元 NLP |

---

## 4. 大语言模型应用框架

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **LangChain** | 构建 LLM 驱动应用的框架，支持链式调用、Agent、记忆和工具集成 | LLM 应用开发 |
| **LlamaIndex** (原 GPT Index) | LLM 应用的数据框架；在 RAG（检索增强生成）方面表现突出 | RAG/数据索引 |
| **LangGraph** | LangChain 的图结构库，用于构建有状态的多参与者应用；精细控制 LLM Agent 工作流 | Agent 编排 |
| **Haystack** (by deepset) | 端到端框架，用于构建生产就绪的 LLM 应用，含检索、问答和文档管道 | RAG/LLM 应用 |
| **Semantic Kernel** | 微软的 SDK，将 LLM 与主流编程语言（Python、C#、Java）集成 | LLM 集成 |
| **Promptflow** | 微软的 LLM 应用构建、测试和评估工具 | LLM 开发/测试 |
| **DSPy** | 斯坦福的"编程而非提示"框架；将提示编译为优化模块 | LLM 编程范式 |
| **LiteLLM** | 统一代理，支持调用 100+ LLM API（OpenAI、Anthropic、Azure 等） | LLM API 统一接口 |
| **Instructor** | 从 LLM 获取可靠结构化输出的库，含验证和重试机制 | LLM 结构化输出 |
| **Guidance** | 微软的约束引导式提示库，控制文本生成过程 | 约束生成 |
| **LMQL** | 带约束和控制流的 LLM 查询语言 | LLM 查询 |
| **SmolAgents** | Hugging Face 的轻量级自主 LLM Agent 构建库 | LLM Agent |
| **Chainlit** | 构建 LLM 应用对话式 UI 的 Python 框架 | LLM 前端 |

---

## 5. AI Agent 框架

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **CrewAI** | 基于角色的多 Agent 框架，AI Agent 以"团队"形式协作，各有明确职责 | 多 Agent 协作 |
| **AutoGen** (Microsoft) | 支持多 Agent 对话的框架，含可定制的对话式 Agent 和代码执行能力 | 多 Agent 对话 |
| **LangGraph** | 基于图的 Agent 编排框架（也在 LLM 框架中列出） | Agent 工作流 |
| **OpenAI Agents SDK** | OpenAI 官方的生产级 Agent 系统构建 SDK | Agent 开发 |
| **Camel** | 可通信 Agent 框架，支持角色扮演和多 Agent 协作 | 多 Agent 角色扮演 |
| **MetaGPT** | 多 Agent 框架，每个 Agent 扮演软件公司不同角色（产品经理、架构师、工程师） | 软件开发 Agent |
| **ChatDev** | 虚拟公司框架，AI 驱动的软件研发协作 | 软件开发 Agent |
| **AgentVerse** | 易于使用的多 LLM Agent 部署和管理框架 | Agent 管理 |

---

## 6. 计算机视觉

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **OpenCV** (opencv-python) | 全面的计算机视觉库，含图像处理、特征检测、目标跟踪 | 计算机视觉 |
| **Pillow** (PIL) | Python 图像处理库；基础图像处理和操作 | 图像处理 |
| **Albumentations** | 为深度学习流水线设计的快速图像增强库 | 图像增强 |
| **imgaug** | 含直观 API 和丰富的图像增强技术的增强库 | 图像增强 |
| **Detectron2** | Facebook 的基于 PyTorch 的目标检测和分割库 | 目标检测 |
| **MMDetection** | OpenMMLab 的检测工具箱，支持数十种检测架构 | 目标检测 |
| **YOLO** (ultralytics) | Ultralytics YOLOv8/v11；最先进的实时目标检测 | 实时目标检测 |
| **SAM** (Segment Anything) | Meta 的图像分割基础模型 | 图像分割 |
| **timm** (PyTorch Image Models) | 含 1000+ 预训练模型的图像模型集合 | 预训练视觉模型 |
| **Kornia** | PyTorch 的可微计算机视觉库（优化、几何、色彩空间） | 可微 CV |
| **Monai** | 基于 PyTorch 的医学影像 AI 框架，含专用变换和网络 | 医学影像 |
| **SimpleITK / ITK** | 医学图像分析工具包，含配准、分割、可视化 | 医学影像 |
| **scikit-image** | 基于 NumPy/scipy 的图像处理和分割算法集合 | 图像处理 |
| **face_recognition** | 基于 dlib 的简单人脸识别库 | 人脸识别 |
| **DeepFace** | 轻量级面部分析框架（验证、属性检测、年龄估计） | 面部分析 |
| **supervision** | CV 模型后处理和标注的工具库 | CV 后处理 |

---

## 7. 生成式 AI

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **diffusers** (Hugging Face) | 最先进的扩散模型库，用于图像、音频和视频生成 | 文生图/扩散模型 |
| **ComfyUI** | 基于节点的 Stable Diffusion GUI，含强大的工作流自定义 | 图像生成 UI |
| **invokeAI** | 专业级 Stable Diffusion 平台，含画布编辑和工作流工具 | 图像生成 |
| **ControlNet** | 为扩散模型添加空间条件控制的网络（姿态、深度、边缘） | 条件生成 |
| **Kandinsky** | Hugging Face 的支持俄语的扩散模型 | 文本到图像 |
| **Kornia-generative** | PyTorch 中可微的生成模型组件（扩散和 VAE） | 生成模型 |
| **MoviePy** | 视频编辑库，用于合成、特效和渲染 | 视频处理 |
| **Manim** | 3Blue1Brown 的数学动画引擎，用于制作解释性视频 | 动画生成 |

---

## 8. 音频/语音/音乐 AI

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **openai-whisper** | OpenAI 的语音识别模型；鲁棒的多元语言语音转文本 | 语音识别 (ASR) |
| **SpeechRecognition** | Google 语音 API 的 Python 封装；简单的语音转文本 | 语音识别 |
| **vosk** | 离线语音识别工具包（轻量级，支持多种语言） | 离线语音识别 |
| **torchaudio** | PyTorch 的音频波形处理、特征提取和数据增强库 | 音频处理 |
| **librosa** | 音乐和音频分析库：特征提取、节拍跟踪、和弦识别 | 音频分析 |
| **pyannote.audio** | 神经说话人日志（识别音频中谁在何时说话） | 说话人识别 |
| **fairseq** | Facebook 的序列建模工具包（文本、音频、视频生成） | 序列建模 |
| **ESPnet** | 端到端语音处理工具包（ASR、TTS、语音翻译） | 语音处理 |
| **Coqui TTS** | 开源文本转语音工具包，含多个预训练模型 | 语音合成 (TTS) |
| **NeMo** (NVIDIA) | NVIDIA 的对话 AI 工具包，覆盖 ASR、TTS、NLP 和 LLM | 对话 AI |
| **pydub** | 简单的音频操作库（格式转换、分割、合并） | 音频操作 |

---

## 9. 多模态 AI

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **CLIP** / **open-clip** | OpenAI 的对比语言-图像预训练；实现零样本图像分类 | 图文理解 |
| **BLIP / BLIP-2** | Salesforce 的启动式语言-图像预训练模型 | 图文生成 |
| **Florence-2** | 微软的统一视觉语言模型，支持多种任务 | 视觉语言模型 |
| **Grounding DINO** | 含自然语言提示的开源目标检测模型 | 开放词汇检测 |
| **Qwen-VL** | 阿里的视觉语言模型，用于图像理解 | 视觉语言 |
| **MiniCPM-V** | 开源多模态模型，用于图文理解 | 视觉语言 |

---

## 10. 强化学习

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **Stable Baselines3** | 可靠的 PyTorch 强化学习实现（PPO、SAC、DQN 等） | RL 算法 |
| **RLlib** (Ray) | 可扩展的 RL 库，支持多 Agent、分布式训练和 20+ 算法 | 分布式 RL |
| **Gymnasium** (OpenAI Gym) | RL 环境的标准 API；OpenAI Gym 的继任者 | RL 环境 |
| **PettingZoo** | 与 Gymnasium 兼容的多 Agent RL 环境 API | 多 Agent RL |
| **CleanRL** | 干净的单文件 RL 算法实现，注重清晰性和可复现性 | RL 研究 |
| **Tianshou** | 现代、干净、快速的 PyTorch 强化学习库 | RL 算法 |
| **FinRL** | 面向量化金融的深度强化学习库 | 金融 RL |
| **Acme** (DeepMind) | DeepMind 的通用 RL 框架，强调灵活性 | RL 研究 |

---

## 11. 图神经网络

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **PyTorch Geometric (PyG)** | 非结构化输入数据（图、流形）的深度学习库 | GNN 训练 |
| **DGL** (Deep Graph Library) | 功能强大的 GNN 库，支持批量、采样和分布式训练 | GNN 训练 |
| **Graph Nets** (DeepMind) | 构建图神经网络的库 | GNN 构建 |
| **Spektral** | 基于 Keras 的图深度学习库 | GNN (Keras) |
| **ogb** (Open Graph Benchmark) | 图机器学习的数据集和基准测试 | GNN 基准 |
| **NetworkX** | 复杂网络的创建、操作和研究 | 图分析 |

---

## 12. 向量数据库

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **FAISS** (Facebook) | 高性能密集向量相似度搜索库；针对 GPU/CPU 优化 | 向量搜索 |
| **Chroma** | 面向 LLM 应用的嵌入优先向量数据库；API 简洁 | RAG 向量存储 |
| **Pinecone** | 托管向量数据库服务，含 Python SDK；适合生产级 RAG | 托管向量库 |
| **Weaviate** | 开源向量数据库，支持混合搜索、GraphQL API 和内置 ML 模块 | 向量数据库 |
| **Milvus** | 开源云原生向量数据库，构建于可扩展相似度搜索 | 大规模向量搜索 |
| **Qdrant** | 用 Rust 编写的向量数据库和语义搜索引擎，含 Python 客户端 | 向量搜索 |
| **pgvector** | PostgreSQL 扩展，用于存储和查询向量嵌入 | SQL 向量存储 |
| **LanceDB** | 无服务器向量数据库，基于 Lance 格式；与 Pandas 集成 | 嵌入式向量搜索 |
| **Annoy** (Netflix) | 近似最近邻库，针对内存效率优化 | 近似最近邻 |
| **HNSWLIB** | HNSW 图的 Python 绑定（快速近似最近邻） | 近似最近邻 |

---

## 13. 模型部署与推理

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **ONNX / ONNX Runtime** | ML 模型的开放表示格式；ONNX Runtime 提供跨平台推理加速 | 模型部署 |
| **TensorRT** | NVIDIA 的高性能深度学习推理优化器和运行时 | GPU 推理 (NVIDIA) |
| **vLLM** | 高吞吐、内存高效的 LLM 推理和服务引擎 | LLM 推理 |
| **Triton Inference Server** (NVIDIA) | 灵活、高性能的 ML 模型规模化推理服务引擎 | 模型推理服务 |
| **TorchServe** | PyTorch 的生产级模型推理部署工具 | PyTorch 部署 |
| **TF Serving** (TensorFlow Serving) | TensorFlow 的生产级模型部署系统 | TensorFlow 部署 |
| **TGI** (Text Generation Inference) | Hugging Face 专为文本生成优化的推理服务方案 | LLM 推理服务 |
| **Ollama** | 本地 LLM 运行时，API 简洁；在设备端推理中日益流行 | 本地 LLM |
| **llama.cpp** | LLaMA 推理的 C++ 实现，含 Python 绑定（量化、CPU/GPU） | 本地 LLM |
| **TensorFlow Lite** | Google 的移动端和嵌入式设备模型部署方案 | 边缘部署 |
| **OpenVINO** | Intel 的模型优化和跨 Intel 硬件部署工具包 | Intel 优化 |
| **BentoML** | 统一模型推理框架，支持多种框架和部署目标 | 模型服务 |
| **KServe** (原 Kubeflow Serving) | 基于 Kubernetes 的推理服务平台 | K8s 部署 |
| **Ray Serve** | 基于 Ray 的可扩展 ML 模型和服务 API 推理库 | 分布式服务 |
| **TensorRT-LLM** | NVIDIA 针对 GPU 优化的 LLM 推理库 | GPU LLM 推理 |
| **bitsandbytes** | 量化库（8-bit/4-bit 优化器），广泛用于 LLM 量化 | 模型量化 |
| **llamafile** | 单个文件中的便携 LLM 推理，支持量化模型 | 便携 LLM |

---

## 14. 实验追踪与 MLOps

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **MLflow** | 开源 ML 生命周期平台：追踪、可复现性、部署 | 实验追踪 |
| **Weights & Biases (wandb)** | 开发者优先的 ML 平台，含实验追踪、数据集版本化和模型管理 | 实验追踪 |
| **Comet** | ML 实验追踪平台，含模型监控和数据集版本化 | 实验追踪 |
| **TensorBoard** | TensorFlow/PyTorch 可视化工具箱（损失曲线、直方图、计算图） | 实验可视化 |
| **ClearML** | 开源 MLOps 平台，含自动化、追踪和可复现 ML | MLOps |
| **Neptune.ai** | ML 实验元数据存储，支持张量、图表、数据集、模型 | 实验追踪 |
| **Aim** | 开源 ML 实验追踪器，含优秀 UI 和 CLI | 实验追踪 |
| **FiftyOne** (Fifty.ai) | 数据集策展和模型分析工具，用于 ML 模型的视觉检查 | 数据集分析 |
| **DVC** (Data Version Control) | 数据版本控制和 ML 实验管理，与 Git 集成 | 数据版本控制 |
| **Kubeflow** | Kubernetes 上的 ML 工具包；端到端 ML 流水线编排 | MLOps 平台 |
| **Airflow** (Apache) | 工作流编排平台，广泛用于 ML 流水线调度 | 流水线编排 |
| **Prefect** | 现代工作流编排库（Airflow 的轻量替代） | 流水线编排 |
| **ZenML** | 模块化 MLOps 框架，构建可复现的 ML 流水线 | MLOps |
| **Feast** | 特征存储，确保训练和服务间特征的一致性 | 特征存储 |

---

## 15. LLM 评估与测试

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **LangSmith** | LangChain 的平台，用于调试、测试和监控 LLM 应用 | LLM 调试/监控 |
| **Promptfoo** | 开源 LLM 提示测试和评估工具，含自动化红队测试 | LLM 测试 |
| **DeepEval** | 单元测试和评估 LLM 输出的框架，支持自定义指标 | LLM 评估 |
| **Ragas** | RAG 评估框架，含忠实度、答案相关性等指标 | RAG 评估 |
| **HELM** (Stanford CRFM) | LLM 的综合评估框架，覆盖准确性、公平性、鲁棒性、毒性 | LLM 综合评估 |
| **lm-evaluation-harness** (EleutherAI) | 大规模自回归语言模型评估框架 | LLM 基准测试 |
| **Giskard** | AI 测试平台，检测 ML 模型中的偏见、毒性和幻觉 | 模型测试 |
| **Arize Phoenix** | LLM 评估、嵌入和模型性能的观测平台 | LLM 可观测性 |
| **TruLens** | 含真实标准和反馈指标的 LLM 评估框架 | LLM 评估 |
| **DeepChecks** | ML 模型和数据验证库（也适用于 LLM） | 模型验证 |
| **Great Expectations** | 数据验证库，维护 ML 流水线中的数据质量 | 数据质量 |

---

## 16. 分布式训练

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **Ray** | Python 分布式执行框架；支撑 Ray Train、Ray Tune、Ray Serve | 分布式计算 |
| **Dask** | 扩展 Python 工作流的并行计算库，从笔记本到集群 | 并行计算 |
| **Horovod** (Uber) | 支持 TensorFlow、PyTorch、Keras 的分布式训练框架 | 分布式训练 |
| **DeepSpeed** (Microsoft) | 含 ZeRO 内存优化的深度学习优化库和分布式训练 | 大规模训练 |
| **Megatron-LM** (NVIDIA) | 万亿参数规模 Transformer 模型的大规模训练库 | 超大模型训练 |
| **Accelerate** (Hugging Face) | 最小代码改动即可在多 GPU/TPU 上分布式训练 | 分布式训练 |
| **FSDP** (Fully Sharded Data Parallel) | PyTorch 原生的大型模型分布式训练策略 | 分布式训练 (PyTorch) |
| **Colossal-AI** | 通用高性能分布式深度学习工具包 | 分布式训练 |
| **FairScale** | 提供高级特性的 PyTorch 库（Pipe、FSDP、TorchScript 并行） | 分布式训练 |

---

## 17. 数据处理

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **NumPy** | 数值计算和数组操作的基础库 | 数值计算 |
| **Pandas** | 数据操作和分析库；Python 数据科学的基石 | 数据分析 |
| **Polars** | 用 Rust 编写的高速 DataFrame 库；作为 Pandas 替代日益流行 | 高性能数据分析 |
| **DuckDB** | 进程内 SQL OLAP 数据库；对 DataFrame 的分析查询表现出色 | 分析型查询 |
| **PyArrow** | Apache Arrow 的 Python 库，用于高效内存数据交换 | 数据交换 |
| **Vaex** | 支持外存操作的 DataFrame，可处理十亿级数据集 | 大数据 DataFrame |
| **Modin** | Pandas 的即插即用替代品，自动并行化操作 | 并行 Pandas |
| **Dask DataFrame** | 针对超内存数据的并行类 Pandas DataFrame | 分布式 DataFrame |
| **PySpark** (Apache Spark) | 大规模数据处理的分布式计算框架，含 Python API | 大数据处理 |

---

## 18. ML 应用构建

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **FastAPI** | 现代快速 Web 框架，构建 API 并自动生成 OpenAPI 文档 | API 开发 |
| **Streamlit** | 纯 Python 构建数据应用和 ML 仪表板的库，无需 HTML/CSS | ML 数据应用 |
| **Gradio** | 快速为 ML 模型创建演示 UI 的库；广泛用于分享模型演示 | ML 演示 |
| **Dash** (Plotly) | 含 React 风格组件的分析性 Web 应用框架 | ML Web 应用 |
| **Panel** (HoloViz) | 交互式仪表板和数据可视化的 Python 应用框架 | ML 仪表板 |
| **NiceGUI** | 基于 Vue.js 的 Python UI 框架；适合 ML 演示和 IoT | ML UI |
| **Marimo** | 含 Web UI 的 Python 响应式笔记本（Jupyter 替代） | 数据科学交互 |
| **Quivr** | 个人 AI 助手框架（基于 RAG 的知识管理） | LLM 应用 |

---

## 19. 模型可解释性

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **SHAP** | 基于博弈论的任意 ML 模型输出解释方法 | 模型解释 |
| **LIME** | 局部可解释的模型无关解释，用于 ML 预测 | 模型解释 |
| **Captum** | PyTorch 的模型可解释性库（梯度、显著图、积分梯度） | PyTorch 可解释性 |
| **ELI5** | ML 分类器的调试库；解释模型预测 | 模型调试 |
| **InterpretML** (Microsoft) | 可解释 ML 模型和洞察生成工具套件 | 可解释 ML |
| **Alibi** | 分类器、回归器和聚类器的黑盒解释库 | 黑盒解释 |

---

## 20. 隐私保护 ML

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **PySyft** (OpenMined) | 安全和隐私深度学习的 Python 库（联邦学习、加密计算） | 联邦学习 |
| **TensorFlow Federated** (TFF) | 在去中心化数据上训练模型的联邦学习框架 | 联邦学习 |
| **Flower (flwr)** | 与框架和算法无关的联邦学习框架 | 联邦学习 |
| **Opacus** | Facebook 的 PyTorch 差分隐私训练库 | 差分隐私 |
| **PyDP** (Intel) | Python 实现的差分隐私 | 差分隐私 |
| **Concrete Numpy** | 全同态加密库，含类 NumPy API 的私有推理 | 同态加密 |

---

## 21. 编译与优化

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **TVM** (Apache TVM) | 可自动移植的 ML 编译器栈，针对各种硬件后端优化模型 | ML 编译 |
| **XLA** | TensorFlow/PyTorch 的 JIT 编译器，融合操作以加速 GPU/TPU | 编译器优化 |
| **torch.compile** | PyTorch 2.0 的原生编译系统，使用 torchdynamo 和 Triton | PyTorch 编译 |
| **Triton** (OpenAI) | 用于编写高效自定义深度学习原语的编程语言和编译器 | 内核编程 |
| **Numba JIT** | 对类 NumPy 代码的即时编译器 | 数值优化 |
| **IREE** | Google 的 ML 编译和推理基础设施 | ML 编译 |

---

## 22. 合成数据

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **SDV** (Synthetic Data Vault) | 生成合成表格、时间序列和图数据的库 | 合成数据 |
| **ctgan** | 条件 GAN，用于表格数据合成（SDV 生态系统的一部分） | 合成数据 |

---

## 23. 知识图谱

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **neo4j** / **py2neo** | Neo4j 图数据库的 Python 驱动；与 AI 结合用于知识图谱 | 知识图谱 |
| **NetworkX** | 图的创建、操作和结构分析 | 图分析 |
| **Graph-tool** | 图的操控和统计建模的 Python 模块 | 图分析 |

---

## 24. 时间序列 AI

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **Prophet** (Meta) | 基于加法模型的时序数据预测过程 | 时间序列预测 |
| **statsmodels** | 含时间序列分析的统计建模和经济计量学库 | 统计建模 |
| **darts** | 多功能时间序列预测和分析的 Python 库 | 时间序列 |
| **NeuralProphet** | 结合深度学习和时间序列的 Prophet 神经网络版 | 深度学习时序 |
| **sktime** | Python 中统一的时间序列机器学习库 | 时间序列 ML |

---

## 25. 量子机器学习

| 库名 | 描述 | 主要用途 |
|------|------|----------|
| **PennyLane** (Xanadu) | 量子机器学习库，用于量子计算机的可微编程 | 量子 ML |
| **Qiskit** (IBM) | 开源 SDK，用于在电路和脉冲级别操作量子计算机 | 量子计算 |
| **MindQuantum** (华为) | 含 ML 能力的量子计算框架 | 量子 ML |

---

## 快速参考：按场景选择

| 你的需求 | 推荐首选 |
|---------|---------|
| 深度学习训练 | PyTorch / TensorFlow / JAX |
| 表格数据 ML | scikit-learn + XGBoost/LightGBM |
| 文本分类/NER | spaCy / Transformers |
| 中文 NLP | jieba / HanLP / paddleNLP |
| 构建 RAG 应用 | LangChain / LlamaIndex / Haystack |
| 构建 Agent | CrewAI / AutoGen / LangGraph |
| 本地运行 LLM | Ollama / llama.cpp / vLLM |
| 图像生成 | diffusers / Stable Diffusion |
| 目标检测 | YOLO (ultralytics) / Detectron2 / MMDetection |
| 语音识别 | whisper / vosk |
| 向量搜索 | FAISS / Chroma / Qdrant |
| 模型量化部署 | ONNX / TensorRT / bitsandbytes |
| 实验追踪 | MLflow / wandb |
| LLM 评估 | LangSmith / Promptfoo / Ragas |
| 分布式训练 | Ray / DeepSpeed / FSDP |
| 快速搭建 ML 演示 | Gradio / Streamlit |

---

## 安装示例

```bash
# 深度学习核心
pip install torch torchvision torchaudio
pip install tensorflow
pip install jax jaxlib

# NLP / LLM
pip install transformers datasets tokenizers
pip install langchain langgraph llama-index

# Agent 框架
pip install crewai autogen-chat

# 计算机视觉
pip install opencv-python albumentations ultralytics

# 向量数据库
pip install chroma faiss-cpu qdrant-client

# 模型部署
pip install onnx onnxruntime vllm

# 实验追踪
pip install mlflow wandb

# 音频
pip install openai-whisper librosa

# 数据处理
pip install pandas polars duckdb

# ML 应用
pip install gradio streamlit fastapi
```

> **说明：** 部分库需要特定硬件（如 GPU）或额外依赖才能发挥全部功能。安装前请查阅各库的官方文档。
