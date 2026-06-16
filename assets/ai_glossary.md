# Comprehensive AI Glossary / AI 术语大全

---

## 1. 基础概念 / Foundational Concepts

### Artificial Intelligence (人工智能, AI)
A broad field of computer science focused on building systems capable of performing tasks that typically require human intelligence, such as reasoning, learning, perception, and decision-making. Encompasses many subfields including machine learning, natural language processing, and robotics.

### Machine Learning (机器学习, ML)
A subset of AI where systems learn patterns from data and improve their performance on a task without being explicitly programmed for every rule. Instead of hard-coded logic, algorithms adjust their internal parameters based on examples.

### Deep Learning (深度学习, DL)
A subfield of machine learning that uses multi-layered artificial neural networks to learn hierarchical representations of data. Enables breakthroughs in image recognition, speech, and language by automatically discovering features at multiple levels of abstraction.

### Narrow AI / Weak AI (狭义人工智能 / 弱人工智能)
AI systems designed and trained for a specific task or narrow domain (e.g., chess playing, image classification, language translation). These systems excel at their designated task but cannot generalize beyond it. All current AI systems are narrow AI.

### General AI / Strong AI / AGI (通用人工智能 / 强人工智能)
A theoretical form of AI that possesses the ability to understand, learn, and apply intelligence across any domain, matching or exceeding human cognitive abilities. Would be capable of transferring knowledge from one context to an entirely different one. Does not yet exist.

### Superintelligence (超级人工智能)
A hypothetical AI that surpasses human intelligence in every aspect, including creativity, wisdom, and social skills. Often discussed in the context of long-term AI safety and existential risk.

---

## 2. 机器学习类型 / Types of Machine Learning

### Supervised Learning (监督学习)
A paradigm where the model is trained on labeled data — each training example includes both input and the correct output. The algorithm learns a mapping from inputs to outputs and is evaluated on its ability to predict labels for unseen data. Common tasks: classification, regression.

### Unsupervised Learning (无监督学习)
Learning from unlabeled data where the algorithm discovers hidden structures, patterns, or groupings on its own. Common techniques include clustering (e.g., K-Means) and dimensionality reduction (e.g., PCA, t-SNE).

### Semi-supervised Learning (半监督学习)
Combines a small amount of labeled data with a large amount of unlabeled data during training. Leverages the structure in unlabeled data to improve learning accuracy when labeling is expensive or scarce.

### Self-supervised Learning (自监督学习)
A form of unsupervised learning where the data itself generates the supervisory signal through pretext tasks (e.g., predicting masked words in a sentence). The foundation of modern large language models.

### Transfer Learning (迁移学习)
Taking a model trained on one task and adapting it to a related but different task. Typically involves taking pre-trained weights and fine-tuning them on new data, saving significant training time and data requirements.

### Few-shot Learning (少样本学习)
The ability of a model to learn a new task from only a small number (typically a handful) of labeled examples. Large pre-trained models exhibit few-shot capabilities through in-context learning.

### Zero-shot Learning (零样本学习)
A model performs a task it was never explicitly trained on, without seeing any task-specific examples. Made possible by large-scale pre-training that produces generalized representations.

### Multi-task Learning (多任务学习)
Training a single model to perform multiple tasks simultaneously, allowing shared representations to benefit all tasks. Can improve generalization and efficiency compared to training separate models per task.

### Online Learning (在线学习)
A learning paradigm where the model is updated continuously as new data arrives, rather than in offline batches. Useful for streaming data and non-stationary environments where data distributions shift over time.

### Incremental Learning / Continual Learning (增量学习 / 持续学习)
The ability to learn new tasks sequentially while retaining knowledge from previously learned tasks. Addresses the "catastrophic forgetting" problem where learning new information erases old knowledge.

### Active Learning (主动学习)
A strategy where the learning algorithm actively queries an oracle (usually a human) to label the most informative data points. Reduces labeling costs by focusing annotation effort on samples that will most improve the model.

### Meta-learning (元学习)
"Learning to learn" — training models to quickly adapt to new tasks with minimal data. The model learns general learning strategies across many tasks rather than task-specific solutions.

---

## 3. 深度学习 / Deep Learning

### Neural Network (神经网络)
A computational model inspired by biological neurons, composed of layers of interconnected nodes (neurons) that transform input data through weighted connections and activation functions. Can learn complex non-linear mappings.

### Perceptron (感知器)
The simplest form of artificial neuron, introduced by Frank Rosenblatt in 1958. Takes multiple binary inputs, computes a weighted sum, applies a step activation function, and produces a binary output. Single-layer perceptrons cannot solve non-linearly separable problems (e.g., XOR).

### Multi-Layer Perceptron (MLP) (多层感知机)
A feedforward neural network with at least one hidden layer between input and output. The addition of hidden layers and non-linear activation functions enables the network to approximate any continuous function (universal approximation theorem).

### Convolutional Neural Network (CNN) (卷积神经网络)
A neural network architecture designed for processing grid-like data (images). Uses convolutional filters that slide across the input to detect spatial patterns (edges, textures, objects). Includes pooling layers for downsampling and weight sharing for efficiency.

### Recurrent Neural Network (RNN) (循环神经网络)
A neural network designed for sequential data, where information from previous time steps is fed back into the network as input. Maintains a hidden state that acts as memory. Suffers from vanishing gradients in long sequences.

### Long Short-Term Memory (LSTM) (长短期记忆网络)
A type of RNN architecture that addresses the vanishing gradient problem through gating mechanisms (input gate, forget gate, output gate). Can learn long-range dependencies in sequences, widely used before Transformers.

### Gated Recurrent Unit (GRU) (门控循环单元)
A simplified variant of LSTM with fewer gates (update gate and reset gate) but comparable performance. More computationally efficient than LSTM while maintaining the ability to capture long-range dependencies.

### Autoencoder (自编码器)
An unsupervised neural network that learns to compress input data into a lower-dimensional representation (encoder) and then reconstruct the original input from that representation (decoder). Used for dimensionality reduction, denoising, and generative modeling.

### Generative Adversarial Network (GAN) (生成对抗网络)
Two neural networks (generator and discriminator) trained in competition. The generator creates fake data, and the discriminator tries to distinguish real from fake. Through adversarial training, the generator produces increasingly realistic outputs.

### Variational Autoencoder (VAE) (变分自编码器)
A probabilistic autoencoder that learns a latent probability distribution over the data rather than a deterministic encoding. Enables generative modeling by sampling from the learned latent space. Enforces a smooth, continuous latent space via a KL-divergence regularization term.

### Attention Mechanism (注意力机制)
A technique that allows a model to dynamically focus on different parts of the input when producing each output element. Assigns weights to input elements based on relevance, enabling the model to handle long-range dependencies. Core innovation behind the Transformer.

### Transformer (Transformer 架构)
A neural architecture introduced in "Attention Is All You Need" (2017) that relies entirely on self-attention mechanisms, eliminating recurrence and convolution. Enables parallel processing of sequences and has become the dominant architecture for NLP and beyond.

### Encoder (编码器)
The part of a model that transforms input data into a compact internal representation (latent vectors). In Transformers, the encoder processes the entire input sequence to produce contextualized representations.

### Decoder (解码器)
The part of a model that transforms internal representations back into output form. In sequence-to-sequence models, the decoder generates output tokens autoregressively conditioned on the encoder's representation.

---

## 4. 自然语言处理 / Natural Language Processing (NLP)

### Token (词元)
The basic unit of text that a model processes. Tokens can represent whole words, subwords, or characters. Tokenization is the process of splitting text into tokens. BPE (Byte-Pair Encoding) is a common tokenization scheme.

### Tokenization (分词)
The process of breaking text into smaller units (tokens) that a model can process. Methods include whitespace tokenization, word-level tokenization, subword tokenization (BPE, WordPiece, SentencePiece), and character-level tokenization.

### Subword Tokenization (子词分词)
A tokenization strategy that splits rare words into common subword units, balancing vocabulary size and coverage. Allows models to handle out-of-vocabulary words by composing them from known subwords. Examples: BPE, WordPiece, Unigram.

### Word Embedding (词嵌入)
A dense vector representation of words where semantically similar words are positioned close together in vector space. Captures linguistic properties like analogy (e.g., king - man + woman = queen). Examples: Word2Vec, GloVe, FastText.

### Language Model (语言模型, LM)
A probability distribution over sequences of words (or tokens). Estimates the likelihood of a word given its preceding context. Modern LMs are neural networks trained to predict the next token. Foundation of text generation, translation, and understanding.

### Context Window (上下文窗口)
The maximum number of tokens a model can process in a single input. Determines how much prior text the model can "remember" and attend to. Larger windows enable better comprehension of long documents but increase computation quadratically (due to self-attention).

### Prompt (提示)
The input text given to a large language model to elicit a desired response. The design of prompts significantly affects model output quality. Can include instructions, examples, and formatting cues.

### Prompt Engineering (提示工程)
The practice of designing and optimizing prompts to elicit the best possible responses from LLMs. Techniques include few-shot examples, chain-of-thought prompting, role-playing, and structured output formatting.

### In-context Learning (上下文学习)
The ability of large language models to learn and adapt to new tasks from examples provided within the prompt, without updating model weights. The model conditions its response on the examples given in the context window.

### Fine-tuning (微调)
The process of continuing to train a pre-trained model on a task-specific dataset to adapt it to a particular domain or task. Adjusts all or part of the model's weights, unlike inference-time techniques. More effective than prompt engineering for specialized tasks.

### Pre-training (预训练)
The initial phase of training a model on a large, general corpus of data to learn broad language patterns and world knowledge. Produces a foundation model that can be adapted to many downstream tasks via fine-tuning or prompting.

### Alignment (对齐)
Techniques used to ensure that AI systems behave in ways that are consistent with human intentions, values, and preferences. Goes beyond task performance to address safety, helpfulness, and honesty.

### RLHF (Reinforcement Learning from Human Feedback) (基于人类反馈的强化学习)
A technique for aligning LLMs by training a reward model on human preference rankings of model outputs, then using reinforcement learning (typically PPO) to optimize the policy model to maximize that reward. Used in ChatGPT, Claude, and other conversational models.

### DPO (Direct Preference Optimization) (直接偏好优化)
A simpler alternative to RLHF that directly optimizes the policy model using preference pairs (chosen vs. rejected responses) without requiring a separate reward model or reinforcement learning loop. More stable and computationally efficient.

### Instruction Tuning (指令微调)
Fine-tuning a pre-trained language model on a dataset of (instruction, response) pairs so it can follow natural language instructions. Bridges the gap between raw language modeling and interactive assistant behavior.

### RAG (Retrieval-Augmented Generation) (检索增强生成)
A technique that combines a retriever (searching a knowledge base) with a generator (LLM) to produce responses grounded in external information. Mitigates hallucinations and enables models to use up-to-date or proprietary knowledge without retraining.

### Hallucination (幻觉)
When an LLM generates confident-sounding but factually incorrect or fabricated information. Occurs because models generate text based on statistical patterns rather than verified facts. Mitigated by RAG, grounding, and better training.

### Temperature (温度)
A hyperparameter that controls the randomness of token sampling. Lower temperatures (near 0) make outputs more deterministic and focused; higher temperatures produce more diverse and creative (but potentially less coherent) outputs.

### Top-k Sampling (Top-k 采样)
A sampling method that restricts token selection to the k most likely candidates at each step, then samples randomly from that reduced set. Controls diversity by limiting the candidate pool size.

### Top-p / Nucleus Sampling (Top-p / 核采样)
A sampling method that selects tokens from the smallest set whose cumulative probability exceeds p (e.g., 0.9). Dynamically adjusts the candidate pool size based on probability distribution, offering a balance between diversity and coherence.

### Beam Search (束搜索)
A decoding algorithm that maintains the top-k most likely partial sequences at each step, rather than greedily choosing the single best token. Produces higher-quality outputs than greedy decoding but is slower and can be overly conservative.

### Chain-of-Thought (思维链)
A prompting technique where the model is encouraged to generate intermediate reasoning steps before producing a final answer. Significantly improves performance on complex reasoning tasks like math and logic puzzles.

### Function Calling (函数调用)
The ability of an LLM to recognize when a task requires external tools and output structured calls to specific functions with properly formatted arguments. Enables LLMs to interact with APIs, databases, and software tools.

---

## 5. 生成式 AI / Generative AI

### Diffusion Model (扩散模型)
A generative model that learns to reverse a gradual noising process. During training, it learns to denoise data step by step; during inference, it generates data by starting from pure noise and iteratively denoising. State-of-the-art for image generation.

### Stable Diffusion (Stable Diffusion)
A popular open-source diffusion model for text-to-image generation. Uses a latent space (compressed representation via VAE) to make diffusion computationally tractable. Conditioned on text prompts via cross-attention.

### Text-to-Image (文生图)
Generating images from textual descriptions. Models learn the joint distribution of text and image modalities, enabling creative image synthesis from natural language prompts.

### Text-to-Video (文生视频)
Extending text-to-image models to generate temporal sequences of frames. Requires modeling motion and temporal consistency across frames. Emerging area with models like Sora, Runway Gen-2.

### Text-to-Speech (TTS) (语音合成 / 文字转语音)
Converting written text into natural-sounding spoken audio. Modern neural TTS models (e.g., Tacotron, VITS) produce high-quality speech that is often indistinguishable from human voices.

### Speech-to-Text (STT) / Automatic Speech Recognition (ASR) (语音识别 / 文字转语音)
Transcribing spoken audio into written text. Modern systems use deep neural networks (e.g., Whisper) trained on massive speech-text datasets, supporting multiple languages and accents.

### Voice Cloning (声音克隆)
Creating a synthetic voice that closely matches a specific person's vocal characteristics using a relatively small amount of audio data. Raises significant ethical and security concerns regarding impersonation and fraud.

---

## 6. 强化学习 / Reinforcement Learning

### Reward Function (奖励函数)
A function that defines the goal of a reinforcement learning agent by assigning scalar feedback (reward) to states or state-action pairs. The agent's objective is to maximize cumulative reward over time.

### Policy (策略)
A strategy that an agent uses to determine actions given a state. Can be deterministic (same action always) or stochastic (probability distribution over actions). The policy is what gets optimized during training.

### Value Function (价值函数)
Estimates the expected cumulative future reward from a given state (state-value) or state-action pair (action-value). Provides a measure of how "good" a state is, guiding the agent toward beneficial decisions.

### Q-Learning (Q学习)
A model-free reinforcement learning algorithm that learns the value of state-action pairs (Q-values) independently of the agent's policy. Uses a temporal difference update rule and converges to optimal Q-values under certain conditions.

### Proximal Policy Optimization (PPO) (近端策略优化)
A popular policy gradient method that constrains policy updates to prevent destructive large changes. Uses a clipped objective function to maintain training stability. Widely used for RLHF alignment of LLMs.

### Deep Q-Network (DQN) (深度Q网络)
Combines Q-learning with deep neural networks to approximate Q-values. Introduces experience replay and a target network for stable training. First deep RL system to achieve superhuman performance on Atari games.

### Actor-Critic (演员-评论家)
A reinforcement learning architecture that combines policy-based (actor) and value-based (critic) methods. The actor proposes actions while the critic evaluates them, reducing variance compared to pure policy gradient methods.

### Exploration vs Exploitation (探索与利用)
The fundamental trade-off in reinforcement learning between trying new actions to discover better strategies (exploration) and using known good actions to maximize immediate reward (exploitation). Addressed via epsilon-greedy, entropy regularization, and UCB methods.

### Markov Decision Process (MDP) (马尔可夫决策过程)
A mathematical framework for modeling decision-making where outcomes are partly random and partly under the agent's control. Defined by states, actions, transition probabilities, rewards, and a discount factor. The formal foundation of RL.

---

## 7. 模型训练与优化 / Model Training & Optimization

### Backpropagation (反向传播)
The algorithm for efficiently computing gradients of the loss function with respect to each model parameter by applying the chain rule of calculus from the output layer backward through the network. Enables gradient-based optimization of deep networks.

### Gradient Descent (梯度下降)
An optimization algorithm that iteratively updates model parameters in the direction that reduces the loss function. The step size is controlled by the learning rate. The workhorse of neural network training.

### Stochastic Gradient Descent (SGD) (随机梯度下降)
A variant of gradient descent that approximates the gradient using a single randomly selected training example (or mini-batch) per step. Introduces noise that helps escape local minima and speeds up convergence.

### Adam Optimizer (Adam 优化器)
An adaptive learning rate optimizer that combines momentum (exponentially weighted moving average of gradients) with RMSProp (adaptive per-parameter learning rates). The default optimizer for most deep learning applications due to its robustness and fast convergence.

### Learning Rate (学习率)
A hyperparameter controlling the step size of parameter updates during training. Too high causes divergence; too low leads to slow convergence. Often scheduled to decrease over time (learning rate decay) for finer tuning near convergence.

### Batch Size (批次大小)
The number of training samples processed before the model's parameters are updated. Larger batches give more accurate gradient estimates and enable GPU parallelism but use more memory and may generalize worse. Smaller batches add useful noise.

### Epoch (轮次)
One complete pass through the entire training dataset. Multiple epochs are typically needed for the model to learn effectively. Early stopping monitors validation performance to determine the optimal number of epochs.

### Overfitting (过拟合)
When a model learns the training data too well, including noise and idiosyncrasies, resulting in poor generalization to unseen data. The training loss decreases while validation loss increases.

### Regularization (正则化)
Techniques that constrain model complexity to improve generalization. Includes L1/L2 weight penalties, dropout, data augmentation, and early stopping. Adds a penalty for large weights or randomness to prevent memorization.

### Early Stopping (早停)
A regularization technique that halts training when validation performance stops improving, preventing the model from overfitting to the training data. The best validation checkpoint is saved and restored.

### Loss Function (损失函数)
A mathematical function that quantifies the difference between predicted and actual outputs. The training process minimizes this function. Choices include Mean Squared Error (regression), Cross-Entropy (classification), and Huber loss (robust regression).

### Cross-Entropy (交叉熵)
A loss function commonly used for classification that measures the difference between two probability distributions (predicted and true). Lower cross-entropy indicates better-calibrated probability predictions. Binary and categorical variants exist.

---

## 8. 推理与部署 / Inference & Deployment

### Inference (推理)
The process of using a trained model to make predictions on new, unseen data. Contrasted with training (learning from data). Inference latency and throughput are critical for production systems.

### Quantization (量化)
Reducing the precision of model weights and activations (e.g., from FP32 to INT8) to shrink model size and accelerate inference. May cause minor accuracy degradation but offers significant speed and memory benefits.

### Pruning (剪枝)
Removing redundant or unimportant weights/neurons from a neural network to reduce model size and computation. Structured pruning removes entire channels/layers; unstructured pruning removes individual connections, often requiring sparse matrix support.

### Distillation / Knowledge Distillation (知识蒸馏)
Training a smaller "student" model to mimic the behavior of a larger "teacher" model. The student learns from the teacher's soft probability outputs (not just hard labels), capturing richer information. Enables deploying powerful models on resource-constrained devices.

### Edge Computing (边缘计算)
Running AI models on local devices (phones, IoT devices, edge servers) rather than in centralized cloud data centers. Reduces latency, bandwidth usage, and privacy concerns, but requires model compression (quantization, pruning, distillation) to fit hardware constraints.

### Model Serving (模型服务)
Deploying trained models as APIs or services that can accept requests and return predictions at scale. Involves infrastructure for load balancing, versioning, monitoring, and autoscaling. Frameworks: TensorFlow Serving, Triton, vLLM, TGI.

---

## 9. 向量与检索 / Vectors & Retrieval

### Embedding (嵌入)
A dense, fixed-length vector representation of data (text, images, audio) where semantic similarity corresponds to geometric proximity. Enables machines to process and compare unstructured data numerically. Core to modern AI systems.

### Vector Database (向量数据库)
A specialized database optimized for storing, indexing, and querying high-dimensional vector embeddings. Supports fast similarity search operations. Examples: Pinecone, Weaviate, Milvus, Qdrant, pgvector.

### Similarity Search (相似度搜索)
Finding the most similar items to a query item in a high-dimensional space based on distance or similarity metrics. The backbone of recommendation systems, image retrieval, and semantic search.

### Cosine Similarity (余弦相似度)
A measure of similarity between two vectors computed as the cosine of the angle between them. Ranges from -1 (opposite) to 1 (identical direction). Commonly used for text embeddings because it is invariant to vector magnitude.

### FAISS (Facebook AI Similarity Search) (FAISS)
A library by Meta for efficient similarity search and clustering of dense vectors. Supports multiple indexing strategies (IVF, HNSW, PQ) and scales to billions of vectors. Widely used in production retrieval systems.

### HNSW (Hierarchical Navigable Small World) (分层导航小世界图)
An approximate nearest neighbor algorithm that builds a multi-layer graph for fast navigation. Offers excellent recall-speed tradeoff and is the indexing method of choice for many vector databases.

### Approximate Nearest Neighbor (ANN) (近似最近邻)
Algorithms that find vectors similar to a query with near-perfect recall but much faster than exhaustive (brute-force) search. Essential for scaling similarity search to large datasets. Trade precision for speed.

### Semantic Search (语义搜索)
Searching for information based on meaning rather than exact keyword matching. Uses embeddings to represent both queries and documents, enabling retrieval of conceptually relevant results even without lexical overlap.

### Hybrid Search (混合搜索)
Combining keyword-based search (BM25, lexical) with semantic (vector) search and fusing the results. Captures both exact-match precision and semantic recall, generally outperforming either method alone.

---

## 10. Agent 与多智能体 / Agents & Multi-Agent Systems

### Agent (智能体)
An autonomous system that perceives its environment, makes decisions, and takes actions to achieve specific goals. Modern AI agents combine LLMs with planning, memory, and tool-use capabilities to perform complex, multi-step tasks.

### Multi-Agent System (多智能体系统)
A system composed of multiple interacting AI agents that cooperate, compete, or coordinate to solve problems that are beyond the capability of a single agent. Applications include simulations, game playing, and distributed problem solving.

### ReAct (Reasoning + Acting) (推理-行动框架)
A prompting framework that interleaves reasoning (thought traces) with action (tool execution) in an alternating loop. Enables agents to dynamically reason about situations and take actions based on observations.

### Planning (规划)
The process of generating a sequence of steps or actions to achieve a goal. In AI agents, planning involves decomposing complex tasks into subtasks, sequencing tool calls, and handling contingencies.

### Memory (记忆)
In AI agents, the capacity to retain and retrieve information across interactions. Types include short-term (working) memory, long-term memory (vector stores), episodic memory (specific experiences), and semantic memory (facts). Critical for coherent multi-turn interactions.

### Tool Use (工具使用)
An agent's ability to invoke external functions, APIs, or software tools (calculators, search engines, code interpreters) to augment its capabilities. Transforms passive LLMs into active problem solvers.

### Autonomous Agent (自主智能体)
An AI agent capable of independently planning and executing multi-step tasks with minimal human intervention. Can set sub-goals, manage resources, recover from errors, and decide when to stop.

---

## 11. 评估与指标 / Evaluation & Metrics

### Accuracy (准确率)
The proportion of correct predictions among all predictions. Simple and intuitive but misleading for imbalanced datasets where one class dominates.

### Precision (精确率 / 查准率)
The proportion of positive predictions that are actually correct (TP / (TP + FP)). Measures how many selected items are relevant. Important when false positives are costly.

### Recall (召回率 / 查全率)
The proportion of actual positives that are correctly identified (TP / (TP + FN)). Measures how many relevant items are retrieved. Important when false negatives are costly.

### F1 Score (F1 分数)
The harmonic mean of precision and recall: 2 × (Precision × Recall) / (Precision + Recall). Provides a single metric that balances both concerns, especially useful for imbalanced classification.

### ROC-AUC (ROC 曲线下面积)
The Area Under the Receiver Operating Characteristic Curve, which plots true positive rate against false positive rate at various thresholds. AUC of 1.0 is perfect classification; 0.5 is random guessing. Threshold-independent metric.

### BLEU (Bilingual Evaluation Understudy)
A metric for evaluating machine translation quality by measuring n-gram overlap between generated and reference translations. Ranges from 0 to 1 (higher is better). Computed at multiple n-gram levels with a brevity penalty.

### ROUGE (Recall-Oriented Understudy for Gisting Evaluation)
A family of metrics (ROUGE-N, ROUGE-L) that measure overlap of n-grams or longest common subsequences between generated and reference summaries. Widely used for evaluating text summarization.

### Perplexity (困惑度)
A measure of how well a language model predicts a sample. Computed as the exponentiated average negative log-likelihood. Lower perplexity indicates better predictive performance. Intuitively: how many choices the model has at each step.

### Benchmark (基准测试)
A standardized dataset and evaluation protocol used to compare models objectively. Examples: GLUE/SuperGLUE (NLU), MMLU (general knowledge), HumanEval (code), ImageNet (vision).

### Confusion Matrix (混淆矩阵)
A table showing true positives, true negatives, false positives, and false negatives for a classification model. Provides a detailed breakdown of prediction errors by class, enabling calculation of precision, recall, and other metrics.

---

## 12. 数据工程 / Data Engineering

### Dataset (数据集)
A curated collection of data used for training, validating, or testing machine learning models. Quality and representativeness of the dataset fundamentally limit model performance.

### Training Set (训练集)
The portion of data used to teach the model by adjusting its parameters through optimization. Typically 60-80% of the total dataset.

### Validation Set (验证集)
A held-out portion of data used during training to tune hyperparameters and monitor for overfitting. Provides an unbiased estimate of generalization performance but is used repeatedly, so it can partially leak information.

### Test Set (测试集)
A completely held-out portion of data used only once (or rarely) to evaluate final model performance. Provides an unbiased estimate of how the model will perform on truly unseen data.

### Data Pipeline (数据管道)
The automated workflow for collecting, cleaning, transforming, and feeding data into a machine learning system. Includes ingestion, preprocessing, feature extraction, and delivery to training/inference pipelines.

### Feature Engineering (特征工程)
The process of selecting, transforming, and creating input features that make machine learning algorithms work better. Includes handling missing values, encoding categoricals, scaling, and creating interaction terms. Less critical with deep learning but still important.

### Synthetic Data (合成数据)
Artificially generated data that mimics the statistical properties of real data. Used when real data is scarce, expensive, or private (e.g., healthcare). Generated by GANs, diffusion models, or LLMs.

### Data Leakage (数据泄露)
When information from the test or validation set inadvertently influences training, leading to overly optimistic performance estimates. Causes include improper train-test splitting, feature normalization before splitting, and target leakage.

---

## 13. 伦理与安全 / Ethics & Safety

### Bias (偏见)
Systematic unfairness in AI outputs that disadvantages certain groups, often reflecting biases present in training data or design choices. Can be demographic, historical, or measurement bias. Requires active mitigation.

### Fairness (公平性)
The principle that AI systems should treat all individuals and groups equitably. Multiple mathematical definitions exist (demographic parity, equalized odds, calibration) that often conflict, requiring stakeholder input to choose appropriately.

### Explainability / XAI (可解释性 / 可解释人工智能)
The degree to which a human can understand and trust the reasons behind a model's predictions. Black-box models (deep networks) lack inherent interpretability; XAI techniques (SHAP, LIME, attention visualization) provide post-hoc explanations.

### Privacy (隐私)
Protecting sensitive personal information from unauthorized access or inference. ML models can memorize and leak training data (membership inference attacks). Techniques include differential privacy, federated learning, and anonymization.

### Adversarial Attack (对抗攻击)
Deliberately crafted inputs designed to cause a model to make incorrect predictions with high confidence. Small, often imperceptible perturbations to inputs can fool even sophisticated models. Reveals fragility of learned representations.

### Jailbreak (越狱)
Prompting techniques designed to bypass an LLM's safety filters and alignment constraints, eliciting harmful, illegal, or restricted outputs. Examples include role-playing, encoding, and multi-step logical traps.

### Red Teaming (红队演练)
A structured process of probing AI systems with adversarial inputs to discover safety vulnerabilities before deployment. Conducted by diverse teams to uncover biases, jailbreaks, and misuse scenarios. Essential for responsible AI development.

### Safety Alignment (安全对齐)
Processes (RLHF, DPO, constitutional AI) that shape model behavior to be helpful, honest, and harmless. Ensures the model refuses harmful requests, avoids generating dangerous content, and acknowledges uncertainty.

### Watermarking (水印)
Techniques for embedding identifiable signals in AI-generated content (text, images, audio) to distinguish machine-generated from human-generated material. Approaches include statistical watermarking in token selection and invisible perturbations in media.

---

## 14. MLOps / Machine Learning Operations

### Experiment Tracking (实验追踪)
Recording and comparing the details of each training run (hyperparameters, code version, metrics, artifacts) to identify what works. Tools: MLflow, Weights & Biases, TensorBoard, Comet.

### Model Registry (模型注册表)
A centralized repository that manages the lifecycle of trained models across stages (staging, production, archived). Tracks versions, metadata, performance metrics, and approval status.

### Feature Store (特征存储)
A centralized system for managing, sharing, and serving features consistently across training and inference. Solves the training-serving skew problem by ensuring the same feature computations are used in both phases. Examples: Feast, Tecton.

### ML Pipeline (ML 流水线)
An orchestrated workflow that automates the end-to-end ML process: data ingestion, preprocessing, training, evaluation, and deployment. Ensures reproducibility and enables continuous delivery of ML systems. Tools: Kubeflow, Airflow, Dagster.

### Model Monitoring (模型监控)
Continuously tracking deployed model performance, input data quality, and system health in production. Detects degradation, latency issues, and anomalous behavior. Includes logging, alerting, and dashboarding.

### Drift Detection (漂移检测)
Identifying when the statistical properties of input data (data drift) or model predictions (concept drift) change significantly from the training distribution. Triggers model retraining or alerts. Measured via PSI, KS test, population stability indicators.

### CI/CD for ML (机器学习持续集成/持续交付)
Adapting DevOps CI/CD practices to ML workflows: automated testing of data and models, automated retraining on new data, and safe deployment of model updates. Includes data validation tests, model quality gates, and canary deployments.

---

## 15. 其他重要概念 / Additional Important Concepts

### Scaling Laws (缩放定律)
Empirical relationships showing that model performance improves predictably as model size, dataset size, and compute increase. Power-law relationships mean doubling compute yields consistent percentage improvements. Guides resource allocation for training large models.

### Emergent Abilities (涌现能力)
Capabilities that appear suddenly at large scale but are absent in smaller models (e.g., in-context learning, instruction following, chain-of-thought reasoning). Their exact nature and predictability remain debated.

### Parameter-Efficient Fine-Tuning (PEFT) (参数高效微调)
Techniques that adapt large pre-trained models by training only a small fraction of parameters, keeping the bulk frozen. Examples: LoRA (Low-Rank Adaptation), adapters, prefix tuning. Enables fine-tuning on consumer GPUs.

### LoRA (Low-Rank Adaptation) (低秩自适应)
A PEFT method that approximates weight updates as low-rank matrix decompositions, dramatically reducing trainable parameters. Achieves performance comparable to full fine-tuning for many tasks while using ~1000x fewer trainable parameters.

### MoE (Mixture of Experts) (混合专家模型)
An architecture where each input is routed to a subset of specialized "expert" sub-networks. Only active experts compute for each token, enabling very large models with manageable compute cost. Used in Mixtral, Grok-1.

### Chain-of-Thought Prompting (思维链提示)
Encouraging the model to generate step-by-step reasoning before answering by including examples with intermediate reasoning steps in the prompt. Dramatically improves performance on arithmetic, commonsense, and symbolic reasoning tasks.

### System Prompt (系统提示)
The hidden instruction given to an LLM at the start of a conversation that defines its role, behavior guidelines, and constraints. Shapes the model's overall personality and safety boundaries. Not visible to end users in product deployments.

### Latent Space (潜在空间)
The high-dimensional continuous space in which embeddings live. Semantic relationships between concepts are encoded as geometric relationships (directions and distances) in this space. Enables operations like analogy reasoning and interpolation.

### Zero-Shot vs Few-Shot vs Fine-tuned (零样本 vs 少样本 vs 微调)
Three paradigms for adapting a pre-trained model to a new task: zero-shot (no examples), few-shot (a few examples in the prompt), and fine-tuned (weight updates on task-specific data). Generally: fine-tuned > few-shot > zero-shot in performance, but opposite in cost and flexibility.

### Open Source vs Closed Source (开源 vs 闭源)
Open source models release weights and code for public inspection and modification (e.g., Llama, Mistral). Closed source models are proprietary APIs with restricted access (e.g., GPT-4, Claude). Open source enables transparency and customization; closed source often leads in capability.

### Foundation Model (基础模型)
A large-scale pre-trained model (typically on vast, diverse data) that serves as a starting point for many downstream applications. Characterized by scale, general-purpose architecture, and adaptability via fine-tuning or prompting. Examples: GPT series, PaLM, Llama.

### Multimodal (多模态)
Models that process and generate across multiple data modalities (text, images, audio, video, structured data). Learn joint representations that connect different senses of data. Examples: GPT-4V, CLIP, Flamingo.

### Cold Start Problem (冷启动问题)
The challenge of providing recommendations or making predictions when little or no data exists for a new user, item, or scenario. Addressed via content-based methods, popularity heuristics, or transfer learning from related domains.

---

*Compiled as a comprehensive reference glossary covering foundational, practical, and emerging AI terminology.*
