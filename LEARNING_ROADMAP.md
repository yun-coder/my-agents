# LangChain -> LangGraph -> Deep Agents 学习路线

> 基于 first-agent 项目的 MiniMax-M2.7 模型配置，从零到一的系统学习路线

---

## 目录

- [一、环境与模型配置](#一环境与模型配置)
- [二、阶段一：LangChain 基础](#二阶段一langchain-基础)
- [三、阶段二：RAG 检索增强生成](#三阶段二rag-检索增强生成)
- [四、阶段三：语义搜索与向量存储](#四阶段三语义搜索与向量存储)
- [五、阶段四：LangGraph 工作流](#五阶段四langgraph-工作流)
- [六、阶段五：多 Agent 协作](#六阶段五多-agent-协作)
- [七、阶段六：Deep Agents（深度智能体）](#七阶段六deep-agents深度智能体)
- [八、阶段七：Memory 持久化与状态管理](#八阶段七memory-持久化与状态管理)
- [九、完整学习路径图](#九完整学习路径图)
- [十、API 速查表](#十api-速查表)

---

## 一、环境与模型配置

### 1.1 项目初始化

```bash
# 创建项目
mkdir my-agents && cd my-agents
npm init -y

# 安装核心依赖
npm install langchain @langchain/core @langchain/anthropic @langchain/openai @langchain/langgraph dotenv zod

# 安装开发依赖
npm install -D typescript tsx @types/node

# 初始化 TypeScript
npx tsc --init
```

### 1.2 MiniMax-M2.7 模型配置（核心）

MiniMax 提供了 **Anthropic API 兼容模式**，可以直接用 `@langchain/anthropic` 的 `ChatAnthropic` 调用：

```typescript
// .env 文件
// MiniMax Anthropic API 兼容模式配置
// 获取地址: https://platform.minimaxi.com/
// 文档: https://platform.minimaxi.com/docs/guides/quickstart-preparation
ANTHROPIC_API_KEY=sk-cp-your-minimax-api-key
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
```

```typescript
// 核心模型工厂函数 —— 所有 demo 共用
import { ChatAnthropic } from "@langchain/anthropic";
import * as dotenv from "dotenv";
dotenv.config();

function createMiniMaxModel(
  modelName: string = "MiniMax-M2.7",
  temperature: number = 0.7
) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  const baseURL = process.env.ANTHROPIC_BASE_URL;

  if (!apiKey) throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");

  return new ChatAnthropic({
    model: modelName,
    temperature,
    topP: 1.0,
    apiKey: apiKey,
    clientOptions: {
      baseURL: baseURL,  // 关键：指向 MiniMax 的 Anthropic 兼容端点
    },
  });
}
```

**配置要点解析：**

| 配置项 | 值 | 说明 |
|--------|------|------|
| `model` | `"MiniMax-M2.7"` | MiniMax 主力模型，也可用 `"claude-3-5-haiku-20241022"` 等 |
| `clientOptions.baseURL` | `"https://api.minimaxi.com/anthropic"` | MiniMax Anthropic 兼容端点 |
| `temperature` | `0.1~1.0` | 创造性控制：低值=确定性，高值=创造性 |
| `topP` | `1.0` | 核采样参数 |

**为什么用 Anthropic SDK？**
- MiniMax 的 API 完全兼容 Anthropic Messages API 格式
- 无需额外 SDK，直接复用 LangChain 的 `@langchain/anthropic` 包
- 切换模型只需改 `model` 参数，代码零改动

### 1.3 响应内容提取工具

MiniMax 模型返回的内容格式可能是字符串、数组或对象，需要一个通用提取函数：

```typescript
function extractContent(content: any): string {
  if (typeof content === 'string') return content;

  if (Array.isArray(content)) {
    return content.map(block => {
      if (typeof block === 'string') return block;
      if (block && typeof block === 'object') return block.text || '';
      return '';
    }).join('');
  }

  if (content && typeof content === 'object') {
    return content.text || String(content);
  }

  return String(content);
}
```

### 1.4 tsconfig.json 配置

```json
{
  "compilerOptions": {
    "target": "ES2015",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "sourceMap": true,
    "types": ["node"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

---

## 二、阶段一：LangChain 基础

> 对应源文件：`src/index.ts`、`src/demo.ts`
> 运行：`npm run dev` 或 `npm run demo`

### 2.1 核心概念图

```
┌─────────────────────────────────────────────────────────┐
│                    LangChain 架构                        │
│                                                         │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌───────┐ │
│  │  Model   │──>│  Prompt  │──>│ Output  │──>│ Chain │ │
│  │ (模型)   │   │  (提示)   │   │ Parser  │   │  (链)  │ │
│  └─────────┘   └──────────┘   └─────────┘   └───────┘ │
│       │                                             │    │
│       v                                             v    │
│  ┌─────────┐                                   ┌───────┐ │
│  │  Tool    │<──────────────────────────────────│ Agent │ │
│  │ (工具)   │                                   │(智能体)│ │
│  └─────────┘                                   └───────┘ │
│       │                                             │    │
│       v                                             v    │
│  ┌─────────┐                                   ┌───────┐ │
│  │Memory   │<──────────────────────────────────│ Lang  │ │
│  │(记忆)   │                                   │ Graph │ │
│  └─────────┘                                   └───────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Demo 1：基础对话

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage } from "@langchain/core/messages";

const model = createMiniMaxModel();

// 最简单的调用
const response = await model.invoke([
  new HumanMessage("你好，请用一句话介绍一下你自己。"),
]);

console.log(extractContent(response.content));
```

**学习要点：**
- `ChatAnthropic` 是 LangChain 对 Anthropic/MiniMax API 的封装
- `HumanMessage` 代表用户消息
- `invoke()` 是同步等待的调用方式

### 2.3 Demo 2：系统提示 + 角色设定

```typescript
import { SystemMessage, HumanMessage } from "@langchain/core/messages";

const model = createMiniMaxModel();

const systemPrompt = "你是一个专业的编程助手，精通 TypeScript 和各种前端技术。你的回答应该简洁、准确，并且用中文回复。";

const response = await model.invoke([
  new SystemMessage(systemPrompt),   // 系统提示 —— 设定角色和行为规则
  new HumanMessage("什么是 TypeScript？"), // 用户消息
]);

console.log(extractContent(response.content));
```

**消息类型体系：**

| 类型 | 类名 | 用途 |
|------|------|------|
| 系统消息 | `SystemMessage` | 设定 AI 角色、行为规则、输出格式 |
| 用户消息 | `HumanMessage` | 用户输入的内容 |
| AI 消息 | `AIMessage` | AI 的回复（用于多轮对话） |
| 工具消息 | `ToolMessage` | 工具执行结果 |

### 2.4 Demo 3：多轮对话

```typescript
const model = createMiniMaxModel();

const messages = [
  new HumanMessage("我叫小明，是一名前端开发工程师。"),
  new HumanMessage("你还记得我的名字吗？"),
];

for (const message of messages) {
  console.log("用户:", message.content);
  const response = await model.invoke([message]);
  console.log("MiniMax:", extractContent(response.content));
}
```

> **注意**：这种方式每次都是独立请求，模型不会"记住"上一轮的内容。真正的多轮对话需要将历史消息一起发送（见阶段八 Memory 部分）。

### 2.5 Demo 4：结构化输出

```typescript
const model = createMiniMaxModel();

const prompt = `请分析以下编程语言的特点，并以 JSON 格式返回：
- name: 语言名称
- type: 类型（如：静态类型、动态类型）
- use_cases: 主要应用场景（数组）
- difficulty: 学习难度（简单/中等/困难）

语言：TypeScript

请只返回 JSON，不要有其他内容。`;

const response = await model.invoke([new HumanMessage(prompt)]);
const content = extractContent(response.content);

// 解析 JSON
try {
  const parsed = JSON.parse(content);
  console.log(JSON.stringify(parsed, null, 2));
} catch (e) {
  console.log("JSON 解析失败，显示原始内容:", content);
}
```

### 2.6 Demo 5：流式输出

```typescript
const model = createMiniMaxModel();

const stream = await model.stream([
  new HumanMessage("请用三句话介绍一下 LangChain 框架。"),
]);

// 逐块输出，类似 ChatGPT 的打字效果
for await (const chunk of stream) {
  const content = extractContent(chunk.content);
  if (content) {
    process.stdout.write(content);  // 不换行，实现打字效果
  }
}
```

**三种调用方式对比：**

| 方式 | 方法 | 适用场景 |
|------|------|----------|
| 同步调用 | `model.invoke(messages)` | 简单问答，需要完整结果 |
| 流式调用 | `model.stream(messages)` | 聊天界面，需要实时反馈 |
| 批量调用 | `model.batch([msg1, msg2])` | 并行处理多个请求 |

### 2.7 Demo 6：工具调用模拟

这是理解 Agent 的基础——让模型"学会"调用外部工具：

```typescript
// 步骤 1: 定义工具函数
function getWeather(city: string): string {
  return `${city} 今天天气晴朗，温度 25°C，空气质量良好`;
}

// 步骤 2: 让模型分析用户意图
const analysisPrompt = `分析用户问题，提取需要调用的工具和参数。

可用工具：
- getWeather(city): 获取指定城市的天气信息

用户问题：北京的天气怎么样？

请返回 JSON 格式：
{
  "tool": "工具名称",
  "parameters": { "参数名": "参数值" },
  "reasoning": "选择此工具的原因"
}`;

const analysisResponse = await model.invoke([new HumanMessage(analysisPrompt)]);
const analysis = extractContent(analysisResponse.content);

// 步骤 3: 解析并执行工具
const jsonMatch = analysis.match(/\{[\s\S]*\}/);
if (jsonMatch) {
  const parsed = JSON.parse(jsonMatch[0]);
  if (parsed.tool === "getWeather") {
    const result = getWeather(parsed.parameters.city);
    console.log("工具执行结果:", result);
  }
}

// 步骤 4: 基于工具结果生成最终回答
const finalPrompt = `基于以下工具调用结果，回答用户的问题。
用户问题：北京的天气怎么样？
工具调用结果：${result}
请用自然、友好的方式回答。`;

const finalResponse = await model.invoke([new HumanMessage(finalPrompt)]);
console.log("最终回答:", extractContent(finalResponse.content));
```

**这就是 Agent 的核心原理！** LangChain 的 Agent 就是把上面这个手动过程自动化了。

---

## 三、阶段二：RAG 检索增强生成

> 对应源文件：`src/rag-agent.ts`
> 运行：`npm run rag`

### 3.1 RAG 原理

```
用户提问
   │
   v
┌──────────┐    1. 查询向量化    ┌──────────────┐
│  用户查询  │ ───────────────> │  向量数据库    │
└──────────┘                   │  (知识库)      │
   ^                            └──────┬───────┘
   │                                   │ 2. 检索相似文档
   │                                   v
   │                            ┌──────────────┐
   │                            │  相关文档片段  │
   │                            └──────┬───────┘
   │                                   │ 3. 组装上下文
   v                                   v
┌──────────┐    4. 生成回答    ┌──────────────┐
│  最终回答  │ <─────────────── │  LLM + 上下文  │
└──────────┘                   └──────────────┘
```

### 3.2 文本分割器

```typescript
/**
 * 简化的文本分割器 —— LangChain 的 RecursiveCharacterTextSplitter 的简化版
 * 将长文本按段落分割成小块，每块不超过 chunkSize 字符
 */
class SimpleTextSplitter {
  private chunkSize: number;     // 每块最大字符数
  private chunkOverlap: number;  // 块之间的重叠字符数

  constructor(chunkSize: number = 1000, chunkOverlap: number = 200) {
    this.chunkSize = chunkSize;
    this.chunkOverlap = chunkOverlap;
  }

  splitText(text: string): Document[] {
    const paragraphs = text.split(/\n\n+/);
    const chunks: Document[] = [];
    let currentChunk = "";
    let chunkIndex = 0;

    for (const paragraph of paragraphs) {
      if ((currentChunk + paragraph).length > this.chunkSize) {
        if (currentChunk) {
          chunks.push({
            pageContent: currentChunk.trim(),
            metadata: { chunkIndex: chunkIndex++ },
          });
        }
        currentChunk = paragraph;  // 保留重叠部分
      } else {
        currentChunk += (currentChunk ? "\n\n" : "") + paragraph;
      }
    }

    if (currentChunk) {
      chunks.push({
        pageContent: currentChunk.trim(),
        metadata: { chunkIndex },
      });
    }

    return chunks;
  }
}
```

**关键参数：**
- `chunkSize = 1000`：每块 1000 字符，太大会超出模型上下文窗口，太小会丢失语义
- `chunkOverlap = 200`：块之间重叠 200 字符，确保不会在句子中间断开

### 3.3 向量存储（简化版）

```typescript
/**
 * 简化的向量存储 —— 生产环境应使用 Pinecone、Weaviate、Chroma 等
 * 这里用关键词匹配模拟向量相似度搜索
 */
class SimpleVectorStore {
  private documents: Document[] = [];

  addDocuments(documents: Document[]): void {
    this.documents.push(...documents);
  }

  similaritySearch(query: string, k: number = 4): Document[] {
    const queryLower = query.toLowerCase();
    const queryTerms = queryLower.split(/\s+/);

    const scoredDocs = this.documents.map(doc => {
      const content = doc.pageContent.toLowerCase();
      let score = 0;

      for (const term of queryTerms) {
        if (content.includes(term)) score += 1;
        const words = content.split(/\s+/);
        for (const word of words) {
          if (word.includes(term) || term.includes(word)) score += 0.5;
        }
      }

      return { doc, score };
    });

    return scoredDocs
      .sort((a, b) => b.score - a.score)
      .slice(0, k)
      .filter(item => item.score > 0)
      .map(item => item.doc);
  }
}
```

### 3.4 RAG Agent 完整实现

```typescript
class RAGAgent {
  private model: ChatAnthropic;
  private vectorStore: SimpleVectorStore;
  private textSplitter: SimpleTextSplitter;

  constructor() {
    this.model = createMiniMaxModel("MiniMax-M2.7", 0.3); // 低温度，更确定性
    this.vectorStore = new SimpleVectorStore();
    this.textSplitter = new SimpleTextSplitter();
  }

  // 1. 知识库入库
  async ingestText(text: string, metadata: Record<string, any> = {}): Promise<void> {
    const document: Document = {
      pageContent: text,
      metadata: { source: metadata.source || "unknown", ...metadata },
    };

    const chunks = this.textSplitter.splitDocuments([document]);
    this.vectorStore.addDocuments(chunks);
  }

  // 2. RAG 查询
  async query(query: string, k: number = 3): Promise<string> {
    // Step 1: 检索相关文档
    const relevantDocs = this.vectorStore.similaritySearch(query, k);

    // Step 2: 构建上下文
    const context = relevantDocs
      .map((doc, i) => `[片段 ${i + 1}]:\n${doc.pageContent}`)
      .join("\n\n");

    // Step 3: 构建提示词
    const systemPrompt = `你是一个专业的 AI 助手，擅长基于提供的文档片段回答问题。
请仅基于以下文档片段回答问题，如果文档中没有相关信息，请明确说明。

文档片段：
${context}

回答要求：
- 仅基于提供的文档片段回答
- 如果文档中没有相关信息，明确说明"文档中未提及此内容"
- 回答要准确、简洁
- 引用具体的片段编号支持你的回答`;

    // Step 4: 生成回答
    const response = await this.model.invoke([
      new HumanMessage(systemPrompt + "\n\n" + query),
    ]);

    return extractContent(response.content);
  }
}
```

### 3.5 RAG 实战

```typescript
const ragAgent = new RAGAgent();

// 建立知识库
await ragAgent.ingestText(`
# LangChain 简介
LangChain 是一个用于开发由语言模型驱动的应用程序的框架。
核心特性包括：Models（模型）、Prompts（提示）、Chains（链）、
Agents（智能体）、Memory（记忆）。
`, { source: "LangChain 官方文档" });

// 查询
await ragAgent.query("LangChain 的核心特性有哪些？");
await ragAgent.query("什么是 LangChain 中的 Agents？");
await ragAgent.query("LangSmith 是什么？");
```

### 3.6 生产环境 RAG 升级路径

```typescript
// 实际项目中应使用：
// 1. 真实的 Embedding 模型
import { OpenAIEmbeddings } from "@langchain/openai";
// 或 MiniMax 的 Embedding

// 2. 真实的向量数据库
import { MemoryVectorStore } from "langchain/vectorstores/memory";
// 或 Pinecone、Weaviate、Chroma、FAISS 等

// 3. LangChain 内置的文本分割器
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";

// 4. 文档加载器
import { PDFLoader } from "langchain/document_loaders/fs/pdf";
import { TextLoader } from "langchain/document_loaders/fs/text";
```

---

## 四、阶段三：语义搜索与向量存储

> 对应源文件：`src/semantic-search.ts`
> 运行：`npm run semantic`

### 4.1 语义搜索 vs 关键词搜索

```
关键词搜索：                                    语义搜索：
"AI 和语言模型" ─── 匹配 "AI" "和" "语言" "模型"  ─── 理解"用户想找关于 AI/LLM 的内容"
                                              ─── 匹配 "Agent"、"LLM"、"RAG" 等
```

### 4.2 向量化原理（简化版）

```typescript
/**
 * 文本向量化的核心思路：
 * 1. 将文本拆分为词/字
 * 2. 为每个词分配一个数值（词频或嵌入向量）
 * 3. 将所有词的数值组合成一个固定长度的向量
 * 4. 归一化到单位长度
 *
 * 生产环境使用 Embedding 模型（如 text-embedding-3-small）生成高质量向量
 */
private async generateEmbedding(text: string): Promise<number[]> {
  const words = text.toLowerCase().split(/\s+/);
  const vectorMap = new Map<string, number>();

  // 计算词频
  for (const word of words) {
    const cleanWord = word.replace(/[^\w\u4e00-\u9fa5]/g, '');
    if (cleanWord.length > 1) {
      vectorMap.set(cleanWord, (vectorMap.get(cleanWord) || 0) + 1);
    }
  }

  // 转换为固定长度的向量（512维）
  const vectorSize = 512;
  const vector = new Array(vectorSize).fill(0);
  let index = 0;
  for (const [word, freq] of vectorMap) {
    const hash = this.simpleHash(word);
    vector[hash % vectorSize] += freq;
    if (++index >= vectorSize) break;
  }

  // 归一化
  const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  return magnitude > 0 ? vector.map(v => v / magnitude) : vector;
}
```

### 4.3 余弦相似度

```typescript
/**
 * 余弦相似度：衡量两个向量方向的一致性
 * 值域 [-1, 1]，越接近 1 表示越相似
 *
 * 公式：cos(θ) = (A · B) / (|A| × |B|)
 */
private cosineSimilarity(vec1: number[], vec2: number[]): number {
  let dotProduct = 0;
  let norm1 = 0;
  let norm2 = 0;

  for (let i = 0; i < vec1.length; i++) {
    dotProduct += vec1[i] * vec2[i];
    norm1 += vec1[i] * vec1[i];
    norm2 += vec2[i] * vec2[i];
  }

  return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
}
```

### 4.4 混合搜索（语义 + 关键词）

```typescript
/**
 * 混合搜索 = 语义相似度（70%）+ 关键词匹配（30%）
 * 结合两种搜索的优势：
 * - 语义搜索：理解意图，找到相关但不完全匹配的内容
 * - 关键词搜索：精确匹配，找到包含特定词的内容
 */
async hybridSearch(
  query: string,
  filters?: { category?: string; tags?: string[] },
  topK: number = 5
): Promise<Array<{
  doc: Document;
  semanticScore: number;
  keywordScore: number;
  combinedScore: number;
}>> {
  // 1. 语义搜索
  const semanticResults = await this.semanticSearch(query, this.documents.size);

  // 2. 应用过滤条件
  const results = [];
  for (const result of semanticResults) {
    // 分类过滤
    if (filters?.category && result.doc.metadata.category !== filters.category) continue;
    // 标签过滤
    if (filters?.tags && !filters.tags.some(tag => result.doc.metadata.tags.includes(tag))) continue;

    // 3. 计算关键词匹配分数
    let keywordScore = 0;
    const content = result.doc.content.toLowerCase();
    if (content.includes(query.toLowerCase())) keywordScore += 1.0;

    results.push({
      doc: result.doc,
      semanticScore: result.score,
      keywordScore: Math.min(keywordScore, 1.0),
      combinedScore: 0,  // 稍后计算
    });
  }

  // 4. 计算综合分数
  return results
    .map(r => ({
      ...r,
      combinedScore: r.semanticScore * 0.7 + r.keywordScore * 0.3,
    }))
    .sort((a, b) => b.combinedScore - a.combinedScore)
    .slice(0, topK);
}
```

### 4.5 文档元数据管理

```typescript
interface Document {
  id: string;
  content: string;
  metadata: {
    title: string;
    category: string;  // 分类：编程语言、AI框架、前端框架...
    tags: string[];    // 标签：TypeScript, React, LLM...
    timestamp?: number;
  };
}

// 示例文档
const docs = [
  {
    id: "doc1",
    content: "TypeScript 是 JavaScript 的超集，添加了静态类型检查...",
    metadata: {
      title: "TypeScript 简介",
      category: "编程语言",
      tags: ["TypeScript", "JavaScript", "类型系统"],
    },
  },
  {
    id: "doc3",
    content: "LangChain 是一个开发由语言模型驱动的应用程序的框架...",
    metadata: {
      title: "LangChain 框架",
      category: "AI框架",
      tags: ["LangChain", "LLM", "AI"],
    },
  },
];

// 带过滤条件的搜索
const results = await engine.hybridSearch("开发", { category: "AI技术" }, 3);
```

---

## 五、阶段四：LangGraph 工作流

> 对应源文件：`src/langgraph-workflow.ts`
> 运行：`npm run workflow`

### 5.1 为什么需要 LangGraph？

```
LangChain Chain（线性）:        LangGraph（图/状态机）:
  A → B → C → D                  A → B → C
  固定流程，无法回退               ↑       ↓
                                 F ← D ← E
  无法处理：                       可以循环、条件路由、并行
  - 条件分支                       - 条件分支
  - 循环迭代                       - 循环迭代（如：审核不通过→重新写作）
  - 状态管理                       - 状态管理
  - 人机协作                       - 人机协作
```

### 5.2 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **State（状态）** | 工作流中传递的数据 | 流水线上的工件 |
| **Node（节点）** | 执行特定任务的函数 | 流水线上的工位 |
| **Edge（边）** | 节点之间的连接 | 流水线的传送带 |
| **Conditional Edge（条件边）** | 根据状态决定走哪条路 | 十字路口的导航 |
| **Checkpointer（检查点）** | 保存中间状态 | 游戏存档 |

### 5.3 状态定义

```typescript
/**
 * 工作流状态 —— 所有节点共享的数据结构
 */
type WorkflowState = {
  current: string;      // 当前所在节点名称
  data: Record<string, any>;  // 业务数据（随流程累积）
  history: Array<{     // 执行历史（审计追踪）
    node: string;
    result: any;
    timestamp: number;
  }>;
  metadata: Record<string, any>;  // 元数据
};

/**
 * 节点执行结果 —— 每个节点返回的结果
 */
type NodeResult = {
  nextState: string;           // 下一跳到哪个节点
  data: Record<string, any>;   // 本节点产出的数据
  shouldContinue: boolean;     // 是否继续执行
};
```

### 5.4 工作流引擎

```typescript
class WorkflowGraph {
  private nodes: Map<string, WorkflowNode>;
  private edges: Map<string, string[]>;  // 节点 → 可能的下一节点列表
  private state: WorkflowState;

  constructor(initialState: Record<string, any> = {}) {
    this.nodes = new Map();
    this.edges = new Map();
    this.state = {
      current: "start",
      data: initialState,
      history: [],
      metadata: {},
    };
  }

  addNode(node: WorkflowNode): void {
    this.nodes.set(node.name, node);
  }

  addEdge(from: string, to: string | string[]): void {
    const targets = Array.isArray(to) ? to : [to];
    const existing = this.edges.get(from) || [];
    this.edges.set(from, [...new Set([...existing, ...targets])]);
  }

  /**
   * 核心执行引擎 —— 不断执行当前节点直到到达终止状态
   */
  async execute(maxIterations: number = 10): Promise<WorkflowState> {
    let iteration = 0;

    while (iteration < maxIterations) {
      const currentNodeName = this.state.current;

      // 终止条件
      if (currentNodeName === "end" || currentNodeName === "done") break;

      const currentNode = this.nodes.get(currentNodeName);
      if (!currentNode) break;

      // 执行当前节点
      const result = await currentNode.execute(this.state);

      // 记录历史
      this.state.history.push({
        node: currentNodeName,
        result: result.data,
        timestamp: Date.now(),
      });

      // 合并数据
      Object.assign(this.state.data, result.data);

      // 状态转移
      if (!result.shouldContinue) break;

      // 验证状态转移合法性
      const possibleNext = this.edges.get(currentNodeName) || [];
      if (possibleNext.length > 0 && !possibleNext.includes(result.nextState)) {
        console.log(`无效状态转移: ${currentNodeName} -> ${result.nextState}`);
        break;
      }

      this.state.current = result.nextState;
      iteration++;
    }

    return this.state;
  }
}
```

### 5.5 实战：内容审核工作流

```
                    ┌──────────┐
                    │  start   │
                    └────┬─────┘
                         │
                         v
                ┌────────────────┐
                │ safety_check   │──── 不安全 ────┐
                └───────┬────────┘                 │
                        │ 安全                     │
                        v                          │
                ┌────────────────┐                 │
                │ quality_check  │──── 低分 ───────┤
                └───────┬────────┘                 │
                        │ 高分                     v
                        v                  ┌────────────┐
                ┌────────────────┐          │   reject   │
                │    enhance     │          └──────┬─────┘
                └───────┬────────┘                 │
                        │                         │
                        v                         │
                ┌────────────────┐                 │
                │    approve     │                 │
                └───────┬────────┘                 │
                        │                         │
                        v                         v
                     ┌──────┐
                     │ end  │
                     └──────┘
```

```typescript
// 节点定义
class SafetyCheckNode implements WorkflowNode {
  name = "safety_check";
  private model = createMiniMaxModel("MiniMax-M2.7", 0.1);

  async execute(state: WorkflowState): Promise<NodeResult> {
    const content = state.data.originalContent;
    const prompt = `检查以下内容是否包含不当、有害或敏感信息。
内容：${content}
请仅回答 "安全" 或 "不安全"。`;

    const response = await this.model.invoke([new HumanMessage(prompt)]);
    const isSafe = extractContent(response.content).includes("安全");

    return {
      nextState: isSafe ? "quality_check" : "reject",  // 条件路由！
      data: { safetyCheck: { passed: isSafe } },
      shouldContinue: true,
    };
  }
}

class QualityCheckNode implements WorkflowNode {
  name = "quality_check";
  private model = createMiniMaxModel("MiniMax-M2.7", 0.2);

  async execute(state: WorkflowState): Promise<NodeResult> {
    // ... 评估内容质量，返回分数 ...
    const overallScore = 8; // 从模型响应中解析
    const passed = overallScore >= 6;

    return {
      nextState: passed ? "enhance" : "reject",  // 条件路由！
      data: { qualityCheck: { passed, scores } },
      shouldContinue: true,
    };
  }
}

// 组装工作流
const workflow = new WorkflowGraph();
workflow.addNode(new StartNode());
workflow.addNode(new SafetyCheckNode());
workflow.addNode(new QualityCheckNode());
workflow.addNode(new EnhanceNode());
workflow.addNode(new ApproveNode());
workflow.addNode(new RejectNode());

// 定义边（含条件分支）
workflow.addEdge("start", "safety_check");
workflow.addEdge("safety_check", ["quality_check", "reject"]);  // 分支！
workflow.addEdge("quality_check", ["enhance", "reject"]);       // 分支！
workflow.addEdge("enhance", "approve");
workflow.addEdge("approve", "end");
workflow.addEdge("reject", "end");

// 执行
workflow.reset({ content: "TypeScript 是一种..." });
const result = await workflow.execute();
console.log(result.data.status);  // "approved" 或 "rejected"
```

### 5.6 实战：文章生成工作流（含循环）

```
  start → research → outline → write → review
                                    ↑       │
                                    └───────┘ (需要修改时循环)
                                            │
                                           end
```

```typescript
class ReviewNode implements WorkflowNode {
  name = "review";

  async execute(state: WorkflowState): Promise<NodeResult> {
    // ... 审核文章 ...

    if (review.needsRevision && state.data.revisionCount < 2) {
      // 循环！回到 write 节点重新写作
      return {
        nextState: "write",           // 回到之前的节点
        data: { review, revisionCount: state.data.revisionCount + 1 },
        shouldContinue: true,
      };
    }

    // 最多修订 2 次，然后结束
    return {
      nextState: "end",
      data: { review },
      shouldContinue: true,
    };
  }
}

workflow.addEdge("review", ["write", "end"]);  // 循环边！
```

### 5.7 使用真正的 LangGraph SDK

```typescript
// 上面是简化实现，生产环境使用 LangGraph SDK：
import { StateGraph, Annotation, END } from "@langchain/langgraph";

// 定义状态结构
const GraphState = Annotation.Root({
  content: Annotation<string>,
  safetyCheck: Annotation<{ passed: boolean }>,
  qualityScore: Annotation<number>,
  finalContent: Annotation<string>,
  status: Annotation<string>,
});

// 定义节点函数
async function safetyCheck(state: typeof GraphState.State) {
  const model = createMiniMaxModel();
  const response = await model.invoke([
    new HumanMessage(`检查内容安全性：${state.content}`)
  ]);
  const isSafe = extractContent(response.content).includes("安全");
  return { safetyCheck: { passed: isSafe } };
}

// 条件路由函数
function routeAfterSafety(state: typeof GraphState.State): string {
  return state.safetyCheck.passed ? "quality_check" : "reject";
}

// 构建图
const graph = new StateGraph(GraphState)
  .addNode("safety_check", safetyCheck)
  .addNode("quality_check", qualityCheck)
  .addNode("enhance", enhanceContent)
  .addNode("approve", approveContent)
  .addNode("reject", rejectContent)
  .addEdge("__start__", "safety_check")
  .addConditionalEdges("safety_check", routeAfterSafety)
  .addConditionalEdges("quality_check", routeAfterQuality)
  .addEdge("enhance", "approve")
  .addEdge("approve", END)
  .addEdge("reject", END);

// 编译并执行
const app = graph.compile();
const result = await app.invoke({ content: "TypeScript 是..." });
```

---

## 六、阶段五：多 Agent 协作

> 对应源文件：`src/multi-agent.ts`
> 运行：`npm run multi-agent`

### 6.1 多 Agent 架构

```
                    ┌──────────────┐
                    │  用户任务     │
                    └──────┬───────┘
                           │
                           v
                    ┌──────────────┐
                    │  协调器 Agent  │  ← 任务分析、分配、结果整合
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           v               v               v
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  研究员     │  │  分析师     │  │  策划师     │
    │  Agent     │  │  Agent     │  │  Agent     │
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           v
                    ┌──────────────┐
                    │  审核员 Agent  │  ← 质量把关
                    └──────┬───────┘
                           │
                           v
                    ┌──────────────┐
                    │  最终整合结果  │
                    └──────────────┘
```

### 6.2 Agent 接口定义

```typescript
interface Agent {
  name: string;
  role: string;
  description: string;
  model: ChatAnthropic;
  execute(task: string, context?: string): Promise<string>;
}
```

### 6.3 专业 Agent 实现

```typescript
/**
 * 研究员 Agent —— 收集信息、提供背景资料
 */
class ResearcherAgent implements Agent {
  name = "研究员";
  role = "researcher";
  description = "负责收集和分析信息，提供背景资料和研究数据";
  model = createMiniMaxModel("MiniMax-M2.7", 0.3);  // 低温度，追求准确性

  async execute(task: string, context?: string): Promise<string> {
    const prompt = `作为研究员，请分析以下任务并提供详细的背景信息：
任务：${task}
${context ? `上下文信息：${context}` : ""}
请提供：
1. 相关背景信息
2. 关键数据和事实
3. 现有研究成果
4. 需要进一步研究的问题`;

    const response = await this.model.invoke([
      new SystemMessage("你是一位专业的研究员，擅长收集和分析信息。"),
      new HumanMessage(prompt),
    ]);

    return extractContent(response.content);
  }
}

/**
 * 分析师 Agent —— 数据分析、趋势识别
 */
class AnalystAgent implements Agent {
  name = "分析师";
  role = "analyst";
  description = "负责分析数据，识别模式和趋势，提供洞察";
  model = createMiniMaxModel("MiniMax-M2.7", 0.4);

  async execute(task: string, context?: string): Promise<string> {
    // 基于 context（研究员的结果）进行深度分析
    // ...
  }
}

/**
 * 策划师 Agent —— 制定策略和规划
 */
class StrategistAgent implements Agent {
  name = "策划师";
  role = "strategist";
  description = "负责制定策略和规划，设计解决方案";
  model = createMiniMaxModel("MiniMax-M2.7", 0.5);  // 中等温度，平衡创造性和可行性

  // ...
}

/**
 * 审核员 Agent —— 质量把关
 */
class ReviewerAgent implements Agent {
  name = "审核员";
  role = "reviewer";
  description = "负责审核和验证结果，确保质量";
  model = createMiniMaxModel("MiniMax-M2.7", 0.2);  // 最低温度，追求客观性

  // ...
}
```

### 6.4 协调器 Agent（核心）

```typescript
class CoordinatorAgent implements Agent {
  name = "协调器";
  role = "coordinator";
  model = createMiniMaxModel("MiniMax-M2.7", 0.3);
  private agents: Agent[] = [];

  registerAgent(agent: Agent): void {
    this.agents.push(agent);
  }

  async execute(task: string): Promise<string> {
    // 1. 分析任务
    const taskAnalysis = await this.analyzeTask(task);

    // 2. 按顺序执行工作流（顺序模式）
    const results = await this.executeWorkflow(task);

    // 3. 整合所有 Agent 的结果
    const integration = await this.integrateResults(task, results);

    return integration;
  }

  private async executeWorkflow(task: string): Promise<Map<string, string>> {
    const results = new Map<string, string>();

    // 阶段 1: 研究
    const researcher = this.agents.find(a => a.role === "researcher");
    if (researcher) {
      results.set("research", await researcher.execute(task));
    }

    // 阶段 2: 分析（依赖研究结果）
    const analyst = this.agents.find(a => a.role === "analyst");
    if (analyst && results.has("research")) {
      results.set("analysis", await analyst.execute(task, results.get("research")));
    }

    // 阶段 3: 策划（依赖研究和分析结果）
    const strategist = this.agents.find(a => a.role === "strategist");
    if (strategist && results.has("analysis")) {
      const combinedContext = `研究：${results.get("research")}\n分析：${results.get("analysis")}`;
      results.set("strategy", await strategist.execute(task, combinedContext));
    }

    // 阶段 4: 审核（依赖所有前置结果）
    const reviewer = this.agents.find(a => a.role === "reviewer");
    if (reviewer && results.has("strategy")) {
      const fullContext = `研究：${results.get("research")}\n分析：${results.get("analysis")}\n策略：${results.get("strategy")}`;
      results.set("review", await reviewer.execute(task, fullContext));
    }

    return results;
  }
}
```

### 6.5 使用

```typescript
const coordinator = new CoordinatorAgent();
coordinator.registerAgent(new ResearcherAgent());
coordinator.registerAgent(new AnalystAgent());
coordinator.registerAgent(new StrategistAgent());
coordinator.registerAgent(new ReviewerAgent());

const result = await coordinator.execute(
  "为一个中等规模的电商平台推荐前端技术栈，考虑性能、开发效率和团队规模"
);

console.log(result);  // 整合后的综合方案
```

### 6.6 协作模式对比

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **顺序管道** | A → B → C → D | 有明确前后依赖的任务 |
| **并行扇出** | A 同时发给 B、C、D | 独立的信息收集 |
| **辩论模式** | B 和 C 互相挑战 | 需要多角度验证 |
| **层级委派** | A 分配给 B，B 分配给 C | 复杂的层级任务 |

---

## 七、阶段六：Deep Agents（深度智能体）

> 这是进阶内容，结合 LangGraph + 多 Agent + 工具 + Memory 的完整智能体系统

### 7.1 Deep Agent 架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                      Deep Agent 系统                             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Agent Supervisor                       │   │
│  │  （总控：理解任务 → 规划 → 分配 → 验证）                   │   │
│  └──────────┬──────────────────────────┬────────────────────┘   │
│             │                          │                         │
│  ┌──────────v──────────┐  ┌───────────v──────────┐            │
│  │   Research Agent    │  │   Execution Agent    │            │
│  │  ┌───────────────┐  │  │  ┌───────────────┐  │            │
│  │  │ Web Search    │  │  │  │ Code Executor │  │            │
│  │  │ Doc Loader    │  │  │  │ API Caller    │  │            │
│  │  │ RAG Query     │  │  │  │ File Writer   │  │            │
│  │  └───────────────┘  │  │  └───────────────┘  │            │
│  └──────────┬──────────┘  └───────────┬──────────┘            │
│             │                          │                         │
│  ┌──────────v──────────────────────────v────────────────────┐   │
│  │                   Shared State                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │   │
│  │  │ Memory   │  │  Tools   │  │  Knowledge Base     │   │   │
│  │  │ (对话史)  │  │ (工具集)  │  │  (向量数据库)        │   │   │
│  │  └──────────┘  └──────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   LangGraph Engine                        │   │
│  │  状态机驱动：规划 → 执行 → 反思 → 修正 → 完成              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Deep Agent 核心实现

```typescript
/**
 * Deep Agent = ReAct 循环 + 工具调用 + 自我反思
 *
 * ReAct 模式：
 *   Thought（思考）→ Action（行动）→ Observation（观察）→ 循环
 */
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage, SystemMessage, AIMessage } from "@langchain/core/messages";
import { tool } from "langchain/core/tools";
import { z } from "zod";

// ========== 工具定义 ==========

const searchTool = tool(
  async ({ query }) => {
    // 实际项目中调用搜索 API
    return `搜索 "${query}" 的结果：[模拟结果] TypeScript 是 JavaScript 的超集...`;
  },
  {
    name: "web_search",
    description: "搜索互联网获取最新信息",
    schema: z.object({
      query: z.string().describe("搜索关键词"),
    }),
  }
);

const calculatorTool = tool(
  async ({ expression }) => {
    try {
      const result = Function('"use strict"; return (' + expression + ')')();
      return `计算结果: ${result}`;
    } catch {
      return "计算错误";
    }
  },
  {
    name: "calculator",
    description: "执行数学计算",
    schema: z.object({
      expression: z.string().describe("数学表达式"),
    }),
  }
);

const fileWriteTool = tool(
  async ({ filename, content }) => {
    const fs = await import("fs");
    fs.writeFileSync(filename, content, "utf-8");
    return `文件 ${filename} 已写入`;
  },
  {
    name: "file_write",
    description: "将内容写入文件",
    schema: z.object({
      filename: z.string().describe("文件路径"),
      content: z.string().describe("文件内容"),
    }),
  }
);

// ========== Deep Agent 类 ==========

interface DeepAgentState {
  task: string;
  plan: string[];
  currentStep: number;
  observations: string[];
  reflections: string[];
  finalAnswer: string;
  toolCalls: Array<{ tool: string; args: any; result: string }>;
}

class DeepAgent {
  private model: ChatAnthropic;
  private tools: Map<string, Function>;
  private state: DeepAgentState;
  private maxIterations: number;

  constructor() {
    this.model = createMiniMaxModel("MiniMax-M2.7", 0.3);
    this.tools = new Map();
    this.maxIterations = 10;
    this.state = {
      task: "",
      plan: [],
      currentStep: 0,
      observations: [],
      reflections: [],
      finalAnswer: "",
      toolCalls: [],
    };

    // 注册工具
    this.tools.set("web_search", searchTool.func);
    this.tools.set("calculator", calculatorTool.func);
    this.tools.set("file_write", fileWriteTool.func);
  }

  /**
   * 核心 ReAct 循环
   */
  async run(task: string): Promise<string> {
    this.state.task = task;

    // 阶段 1: 规划（Plan）
    const plan = await this.plan();

    // 阶段 2: 执行（Execute）+ 反思（Reflect）
    for (let i = 0; i < this.maxIterations; i++) {
      if (this.state.currentStep >= plan.length) break;

      const step = plan[this.state.currentStep];
      console.log(`\n📌 步骤 ${this.state.currentStep + 1}/${plan.length}: ${step}`);

      // 执行
      const observation = await this.executeStep(step);
      this.state.observations.push(observation);

      // 反思
      const reflection = await this.reflect(step, observation);
      this.state.reflections.push(reflection);

      // 判断是否需要调整计划
      if (reflection.includes("调整计划") || reflection.includes("重新规划")) {
        console.log("🔄 根据反思调整计划...");
        const newPlan = await this.replan();
        this.state.plan = newPlan;
        this.state.currentStep = 0;
      } else {
        this.state.currentStep++;
      }
    }

    // 阶段 3: 总结（Summarize）
    this.state.finalAnswer = await this.summarize();
    return this.state.finalAnswer;
  }

  /**
   * 规划阶段 —— 将复杂任务分解为可执行的步骤
   */
  private async plan(): Promise<string[]> {
    const toolsDesc = Array.from(this.tools.keys()).join(", ");

    const prompt = `你是一个智能规划助手。请将以下任务分解为具体的执行步骤。

任务：${this.state.task}

可用工具：${toolsDesc}

请返回 JSON 数组格式的步骤列表，例如：
["步骤1描述", "步骤2描述", "步骤3描述"]

注意：
- 每个步骤应该是原子性的（可以独立执行）
- 明确标注需要使用哪个工具
- 步骤之间的顺序应该合理`;

    const response = await this.model.invoke([new HumanMessage(prompt)]);
    const content = extractContent(response.content);

    try {
      const jsonMatch = content.match(/\[[\s\S]*\]/);
      if (jsonMatch) return JSON.parse(jsonMatch[0]);
    } catch {}

    // 默认返回简单步骤
    return [this.state.task];
  }

  /**
   * 执行步骤
   */
  private async executeStep(step: string): Promise<string> {
    // 决定是否需要使用工具
    const toolDecision = await this.model.invoke([
      new HumanMessage(`当前步骤：${step}

请判断需要使用哪个工具。返回 JSON 格式：
{
  "use_tool": true/false,
  "tool_name": "工具名称",
  "tool_args": { "参数": "值" },
  "reasoning": "选择原因"
}

可用工具：${Array.from(this.tools.keys()).join(", ")}
之前的观察：${this.state.observations.join("\n")}`),
    ]);

    const decision = extractContent(toolDecision.content);
    let parsed: any = {};

    try {
      const jsonMatch = decision.match(/\{[\s\S]*\}/);
      if (jsonMatch) parsed = JSON.parse(jsonMatch[0]);
    } catch {}

    if (parsed.use_tool && this.tools.has(parsed.tool_name)) {
      // 调用工具
      const toolFunc = this.tools.get(parsed.tool_name)!;
      const result = await toolFunc(parsed.tool_args);
      console.log(`  🔧 调用工具: ${parsed.tool_name}`);
      console.log(`  📋 结果: ${String(result).substring(0, 100)}...`);

      this.state.toolCalls.push({
        tool: parsed.tool_name,
        args: parsed.tool_args,
        result: String(result),
      });

      return `使用工具 ${parsed.tool_name}，参数 ${JSON.stringify(parsed.tool_args)}，结果：${result}`;
    }

    // 不需要工具，直接用模型回答
    const response = await this.model.invoke([
      new HumanMessage(`请完成以下步骤：${step}\n\n背景信息：${this.state.observations.join("\n")}`),
    ]);

    return extractContent(response.content);
  }

  /**
   * 反思阶段 —— 评估执行结果，决定是否需要调整
   */
  private async reflect(step: string, observation: string): Promise<string> {
    const response = await this.model.invoke([
      new HumanMessage(`请反思以下执行结果：

步骤：${step}
执行结果：${observation}

请评估：
1. 步骤是否完成？
2. 结果是否正确？
3. 是否需要调整后续计划？

返回简短评估（50字以内）。`),
    ]);

    const reflection = extractContent(response.content);
    console.log(`  💭 反思: ${reflection}`);
    return reflection;
  }

  /**
   * 重新规划
   */
  private async replan(): Promise<string[]> {
    const context = `
原始任务：${this.state.task}
已完成的步骤：
${this.state.plan.slice(0, this.state.currentStep + 1).map((s, i) => `${i + 1}. ${s}`).join("\n")}

观察结果：
${this.state.observations.join("\n")}

反思：
${this.state.reflections.join("\n")}`;

    const response = await this.model.invoke([
      new HumanMessage(`基于以上执行情况，重新规划剩余步骤。
${context}
请返回新的步骤列表（JSON 数组格式），只包含未完成的步骤。`),
    ]);

    const content = extractContent(response.content);
    try {
      const jsonMatch = content.match(/\[[\s\S]*\]/);
      if (jsonMatch) return JSON.parse(jsonMatch[0]);
    } catch {}

    return this.state.plan.slice(this.state.currentStep + 1);
  }

  /**
   * 总结
   */
  private async summarize(): Promise<string> {
    const response = await this.model.invoke([
      new HumanMessage(`请基于以下执行过程，总结最终答案：

任务：${this.state.task}
执行计划：${this.state.plan.join(" → ")}
观察结果：${this.state.observations.join("\n")}
反思：${this.state.reflections.join("\n")}

请提供清晰、完整的最终答案。`),
    ]);

    return extractContent(response.content);
  }
}
```

### 7.3 Deep Agent 实战

```typescript
const agent = new DeepAgent();

// 复杂任务：需要多步推理 + 工具调用
const result = await agent.run(
  "研究 TypeScript 5.0 的新特性，写一篇 300 字的技术博客，包含代码示例"
);

console.log(result);

// 执行过程：
// 📌 步骤 1/4: 搜索 TypeScript 5.0 新特性
//   🔧 调用工具: web_search
//   💭 反思: 获得了相关信息，可以继续
//
// 📌 步骤 2/4: 整理关键新特性
//   💭 反思: 已提取 3 个主要特性
//
// 📌 步骤 3/4: 编写博客内容
//   💭 反思: 内容完整，包含代码示例
//
// 📌 步骤 4/4: 将博客写入文件
//   🔧 调用工具: file_write
//   💭 反思: 文件已成功写入
```

### 7.4 用 LangGraph 构建 Deep Agent

```typescript
import { StateGraph, Annotation, END } from "@langchain/langgraph";

const AgentState = Annotation.Root({
  task: Annotation<string>,
  plan: Annotation<string[]>,
  currentStep: Annotation<number>,
  observations: Annotation<string[]>,
  finalAnswer: Annotation<string>,
});

async function planNode(state: typeof AgentState.State) {
  const model = createMiniMaxModel();
  const response = await model.invoke([
    new HumanMessage(`将任务分解为步骤：${state.task}`)
  ]);
  // 解析计划...
  return { plan: steps, currentStep: 0 };
}

async function executeNode(state: typeof AgentState.State) {
  const step = state.plan[state.currentStep];
  // 执行步骤（可能调用工具）...
  return { observations: [...state.observations, result] };
}

async function reflectNode(state: typeof AgentState.State) {
  const model = createMiniMaxModel();
  const response = await model.invoke([
    new HumanMessage(`反思执行结果：${state.observations[state.observations.length - 1]}`)
  ]);
  // 判断是否需要调整...
}

function shouldContinue(state: typeof AgentState.State): string {
  return state.currentStep < state.plan.length ? "execute" : END;
}

function shouldReplan(state: typeof AgentState.State): string {
  const lastReflection = state.reflections?.[state.reflections.length - 1];
  return lastReflection?.includes("调整") ? "plan" : "execute";
}

const graph = new StateGraph(AgentState)
  .addNode("plan", planNode)
  .addNode("execute", executeNode)
  .addNode("reflect", reflectNode)
  .addNode("summarize", summarizeNode)
  .addEdge("__start__", "plan")
  .addEdge("plan", "execute")
  .addEdge("execute", "reflect")
  .addConditionalEdges("reflect", shouldReplan)
  .addConditionalEdges("execute", shouldContinue)
  .addEdge("summarize", END);

const app = graph.compile();
const result = await app.invoke({ task: "研究 TypeScript 5.0..." });
```

---

## 八、阶段七：Memory 持久化与状态管理

> 对应源文件：`src/memory-persistence.ts`
> 运行：`npm run memory`

### 8.1 Memory 的重要性

```
没有 Memory：                       有 Memory：
用户: 我叫小明                     用户: 我叫小明
AI: 你好小明！                     AI: 你好小明！
用户: 我叫什么？                    用户: 我叫什么？
AI: 抱歉我不知道                    AI: 你叫小明！  ← 记住了！
```

### 8.2 会话存储系统

```typescript
interface Message {
  type: "human" | "ai" | "system";
  content: string;
  timestamp: number;
}

interface Conversation {
  id: string;
  userId: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

class MemoryPersistenceStore {
  private storageDir: string;
  private conversations: Map<string, Conversation>;

  constructor(storageDir: string = "./memory_storage") {
    this.storageDir = storageDir;
    this.conversations = new Map();
    this.initializeStorage();  // 从文件加载历史对话
  }

  // CRUD 操作
  createConversation(userId: string, title?: string): Conversation { /* ... */ }
  getConversation(id: string): Conversation | null { /* ... */ }
  addMessage(conversationId: string, type: MessageType, content: string): boolean { /* ... */ }
  getMessages(conversationId: string, limit?: number): Message[] { /* ... */ }
  deleteConversation(id: string): boolean { /* ... */ }

  // 搜索
  searchConversations(query: string, userId?: string): Conversation[] { /* ... */ }

  // AI 总结
  async summarizeConversation(conversationId: string): Promise<string | null> {
    const model = createMiniMaxModel("MiniMax-M2.7", 0.3);
    const messagesText = conversation.messages
      .map(msg => `[${msg.type}]: ${msg.content}`)
      .join("\n");

    const response = await model.invoke([
      new SystemMessage("你是一个对话总结助手。"),
      new HumanMessage(`总结以下对话（200字以内）：\n${messagesText}`),
    ]);

    return extractContent(response.content);
  }

  // 持久化到文件
  private saveConversationToFile(conversation: Conversation): void {
    fs.writeFileSync(
      path.join(this.storageDir, `${conversation.id}.json`),
      JSON.stringify(conversation, null, 2),
      "utf-8"
    );
  }
}
```

### 8.3 带记忆的对话助手

```typescript
class ConversationalAssistant {
  private model: ChatAnthropic;
  private memoryStore: MemoryPersistenceStore;

  async chat(conversationId: string, userMessage: string): Promise<string> {
    // 1. 保存用户消息
    this.memoryStore.addMessage(conversationId, "human", userMessage);

    // 2. 获取最近 N 条消息作为上下文
    const messages = this.memoryStore.getMessages(conversationId, 10);

    // 3. 构建消息列表
    const chatMessages = [
      new SystemMessage("你是一个专业的编程导师。"),
      ...messages.map(msg => {
        switch (msg.type) {
          case "human": return new HumanMessage(msg.content);
          case "ai": return new AIMessage(msg.content);
          default: return new SystemMessage(msg.content);
        }
      }),
    ];

    // 4. 生成回复
    const response = await this.model.invoke(chatMessages);
    const answer = extractContent(response.content);

    // 5. 保存 AI 回复
    this.memoryStore.addMessage(conversationId, "ai", answer);

    return answer;
  }
}
```

### 8.4 Memory 策略对比

| 策略 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **全量记忆** | 发送所有历史消息 | 信息完整 | 超出上下文窗口 |
| **滑动窗口** | 只保留最近 N 条 | 简单高效 | 丢失早期信息 |
| **摘要记忆** | 定期总结历史 | 节省 token | 丢失细节 |
| **向量记忆** | 存储到向量数据库 | 语义检索 | 实现复杂 |
| **混合策略** | 近期全量 + 远期摘要 | 平衡完整和效率 | 实现最复杂 |

---

## 九、完整学习路径图

```
Week 1: LangChain 基础
├── Day 1-2: 环境配置 + MiniMax-M2.7 模型接入
├── Day 3-4: 基础对话、系统提示、流式输出
└── Day 5-7: 结构化输出、工具调用原理

Week 2: LangChain 进阶
├── Day 1-2: RAG 原理与实现（src/rag-agent.ts）
├── Day 3-4: 语义搜索与向量存储（src/semantic-search.ts）
└── Day 5-7: Memory 持久化（src/memory-persistence.ts）

Week 3: LangGraph
├── Day 1-2: 状态机概念、节点与边
├── Day 3-4: 条件路由、循环工作流（src/langgraph-workflow.ts）
└── Day 5-7: LangGraph SDK 实战

Week 4: 多 Agent 与 Deep Agents
├── Day 1-2: 多 Agent 协作模式（src/multi-agent.ts）
├── Day 3-4: ReAct 模式、工具集成
└── Day 5-7: Deep Agent 完整实现
```

### 运行所有 Demo

```bash
cd first-agent

# 阶段一：LangChain 基础
npm run dev          # 完整 Agent 示例
npm run demo         # 多功能演示（含流式输出）

# 阶段二：RAG
npm run rag          # 检索增强生成

# 阶段三：语义搜索
npm run semantic     # 向量存储和语义搜索

# 阶段四：LangGraph
npm run workflow     # 工作流引擎

# 阶段五：多 Agent
npm run multi-agent  # 多 Agent 协作

# 阶段六：Memory
npm run memory       # 持久化记忆
```

---

## 十、API 速查表

### MiniMax 模型配置

```typescript
// 标准配置
const model = new ChatAnthropic({
  model: "MiniMax-M2.7",           // 主力模型
  temperature: 0.7,                 // 创造性
  topP: 1.0,
  apiKey: process.env.ANTHROPIC_API_KEY,
  clientOptions: {
    baseURL: "https://api.minimaxi.com/anthropic",
  },
});

// 确定性任务（分析、审核）
const analyticalModel = new ChatAnthropic({
  model: "MiniMax-M2.7",
  temperature: 0.1,  // 低温度
  // ...
});

// 创造性任务（写作、头脑风暴）
const creativeModel = new ChatAnthropic({
  model: "MiniMax-M2.7",
  temperature: 0.8,  // 高温度
  // ...
});
```

### 消息类型

```typescript
import {
  HumanMessage,     // 用户消息
  AIMessage,        // AI 消息
  SystemMessage,    // 系统消息
  ToolMessage,      // 工具消息
} from "@langchain/core/messages";
```

### 调用方式

```typescript
// 同步
const response = await model.invoke([new HumanMessage("...")]);

// 流式
const stream = await model.stream([new HumanMessage("...")]);
for await (const chunk of stream) { /* ... */ }

// 批量
const responses = await model.batch([
  [new HumanMessage("问题1")],
  [new HumanMessage("问题2")],
]);
```

### LangGraph 核心

```typescript
import { StateGraph, Annotation, END } from "@langchain/langgraph";

// 定义状态
const State = Annotation.Root({
  messages: Annotation<string[]>,
  count: Annotation<number>,
});

// 构建图
const graph = new StateGraph(State)
  .addNode("node1", node1Fn)
  .addNode("node2", node2Fn)
  .addEdge("__start__", "node1")
  .addConditionalEdges("node1", routerFn)
  .addEdge("node2", END);

// 编译运行
const app = graph.compile();
const result = await app.invoke({ messages: [], count: 0 });
```

### 工具定义

```typescript
import { tool } from "langchain/core/tools";
import { z } from "zod";

const myTool = tool(
  async ({ param1, param2 }) => {
    // 处理逻辑
    return "结果";
  },
  {
    name: "my_tool",
    description: "工具描述 —— Agent 根据这个决定是否调用",
    schema: z.object({
      param1: z.string().describe("参数描述"),
      param2: z.number().describe("参数描述"),
    }),
  }
);
```

---

## 附录：温度参数选择指南

| 场景 | temperature | 说明 |
|------|-------------|------|
| 代码生成 | 0.0~0.2 | 需要精确、确定性输出 |
| 内容审核 | 0.1~0.2 | 需要客观、一致的评价 |
| 数据分析 | 0.2~0.4 | 需要准确性，允许一定灵活性 |
| 信息检索 | 0.3~0.5 | 需要准确但不失自然 |
| 对话聊天 | 0.5~0.7 | 平衡准确性和自然度 |
| 内容创作 | 0.7~0.9 | 需要创造性和多样性 |
| 头脑风暴 | 0.8~1.0 | 需要最大创造性 |

---

> **文档版本**: v1.0
> **最后更新**: 2026-04-22
> **基于项目**: first-agent (LangChain + MiniMax-M2.7 TypeScript Demo)
