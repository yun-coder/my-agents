/**
 * LangChain RAG (Retrieval Augmented Generation) Agent Demo
 * 基于 LangChain 官方教程的检索增强生成示例
 *
 * 学习资源: https://docs.langchain.com/oss/javascript/tutorials/rag
 *
 * 功能特性:
 * - 文档加载和预处理
 * - 文本分割和向量化
 * - 向量存储和语义搜索
 * - RAG 检索增强生成
 * - 使用 MiniMax 模型进行问答
 */
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";
// 注释掉 LangChain 社区包导入，使用简化实现
// import { PDFLoader } from "langchain/document_loaders/fs/pdf";
// import { TextSplitter } from "langchain/text_splitter";
// import { OpenAIEmbeddings } from "langchain/embeddings/openai";
// import { MemoryVectorStore } from "langchain/vectorstores/memory";
import * as fs from "fs";
import * as path from "path";
// 加载环境变量
dotenv.config();
/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName = "MiniMax-M2.7", temperature = 0.7) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    const baseURL = process.env.ANTHROPIC_BASE_URL || "https://api.minimaxi.com/anthropic";
    if (!apiKey) {
        throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");
    }
    return new ChatAnthropic({
        model: modelName,
        temperature,
        apiKey: apiKey,
        clientOptions: {
            baseURL: baseURL,
        },
    });
}
/**
 * 简化的文本分割器
 * 将长文本分割成更小的块
 */
class SimpleTextSplitter {
    constructor(chunkSize = 1000, chunkOverlap = 200) {
        this.chunkSize = chunkSize;
        this.chunkOverlap = chunkOverlap;
    }
    /**
     * 分割文本
     */
    splitText(text) {
        const paragraphs = text.split(/\n\n+/);
        const chunks = [];
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
                currentChunk = paragraph;
            }
            else {
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
    /**
     * 分割文档
     */
    splitDocuments(documents) {
        const allChunks = [];
        for (const doc of documents) {
            const chunks = this.splitText(doc.pageContent);
            for (const chunk of chunks) {
                allChunks.push(Object.assign(Object.assign({}, chunk), { metadata: Object.assign(Object.assign({}, doc.metadata), chunk.metadata) }));
            }
        }
        return allChunks;
    }
}
/**
 * 简化的向量存储（基于关键词匹配）
 * 在生产环境中应使用真实的向量数据库如 Pinecone、Weaviate 等
 */
class SimpleVectorStore {
    constructor() {
        this.documents = [];
    }
    /**
     * 添加文档
     */
    addDocuments(documents) {
        this.documents.push(...documents);
        console.log(`✅ 已添加 ${documents.length} 个文档到向量存储`);
    }
    /**
     * 简化的相似度搜索（基于关键词匹配）
     * 生产环境应使用真实的向量相似度计算
     */
    similaritySearch(query, k = 4) {
        const queryLower = query.toLowerCase();
        const queryTerms = queryLower.split(/\s+/);
        // 计算每个文档的相似度分数
        const scoredDocs = this.documents.map(doc => {
            const content = doc.pageContent.toLowerCase();
            let score = 0;
            // 简单的关键词匹配计分
            for (const term of queryTerms) {
                if (content.includes(term)) {
                    score += 1;
                }
                // 检查部分匹配
                const words = content.split(/\s+/);
                for (const word of words) {
                    if (word.includes(term) || term.includes(word)) {
                        score += 0.5;
                    }
                }
            }
            return { doc, score };
        });
        // 按分数排序并返回前 k 个
        return scoredDocs
            .sort((a, b) => b.score - a.score)
            .slice(0, k)
            .filter(item => item.score > 0)
            .map(item => item.doc);
    }
    /**
     * 获取存储的文档数量
     */
    getDocumentCount() {
        return this.documents.length;
    }
}
/**
 * RAG Agent 类
 */
class RAGAgent {
    constructor() {
        this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3); // 使用较低的温度以获得更确定的答案
        this.vectorStore = new SimpleVectorStore();
        this.textSplitter = new SimpleTextSplitter();
    }
    /**
     * 从文本创建知识库
     */
    ingestText(text_1) {
        return __awaiter(this, arguments, void 0, function* (text, metadata = {}) {
            console.log("📚 正在处理文档...");
            // 创建文档对象
            const document = {
                pageContent: text,
                metadata: Object.assign({ source: metadata.source || "unknown" }, metadata),
            };
            // 分割文档
            const chunks = this.textSplitter.splitDocuments([document]);
            console.log(`✂️ 文档已分割为 ${chunks.length} 个块`);
            // 添加到向量存储
            this.vectorStore.addDocuments(chunks);
        });
    }
    /**
     * 从文件创建知识库
     */
    ingestFile(filePath) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log(`📄 正在读取文件: ${filePath}`);
            if (!fs.existsSync(filePath)) {
                throw new Error(`文件不存在: ${filePath}`);
            }
            const text = fs.readFileSync(filePath, "utf-8");
            yield this.ingestText(text, {
                source: path.basename(filePath),
                path: filePath,
            });
        });
    }
    /**
     * 执行 RAG 查询
     */
    query(query_1) {
        return __awaiter(this, arguments, void 0, function* (query, k = 3) {
            console.log(`\n🔍 查询: ${query}`);
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            // 1. 检索相关文档
            const relevantDocs = this.vectorStore.similaritySearch(query, k);
            if (relevantDocs.length === 0) {
                console.log("⚠️ 未找到相关文档");
                return "抱歉，我在知识库中没有找到相关信息。";
            }
            console.log(`📖 找到 ${relevantDocs.length} 个相关文档片段`);
            // 2. 构建上下文
            const context = relevantDocs
                .map((doc, i) => `[片段 ${i + 1}]:\n${doc.pageContent}`)
                .join("\n\n");
            // 3. 构建提示词
            const systemPrompt = `你是一个专业的 AI 助手，擅长基于提供的文档片段回答问题。
请仅基于以下文档片段回答问题，如果文档中没有相关信息，请明确说明。

文档片段：
${context}

回答要求：
- 仅基于提供的文档片段回答
- 如果文档中没有相关信息，明确说明"文档中未提及此内容"
- 回答要准确、简洁
- 引用具体的片段编号支持你的回答`;
            // 4. 生成回答
            const response = yield this.model.invoke([
                new HumanMessage(systemPrompt + "\n\n" + query),
            ]);
            const answer = typeof response.content === 'string'
                ? response.content
                : String(response.content);
            console.log(`\n💡 回答: ${answer}`);
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
            return answer;
        });
    }
    /**
     * 获取知识库信息
     */
    getKnowledgeBaseInfo() {
        return {
            documentCount: this.vectorStore.getDocumentCount(),
        };
    }
}
/**
 * RAG Agent 演示
 */
function ragAgentDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("🚀 LangChain RAG Agent 演示");
        console.log("基于 LangChain 官方教程: 检索增强生成\n");
        try {
            // 创建 RAG Agent
            const ragAgent = new RAGAgent();
            // 示例知识库内容
            const sampleKnowledge = `
# LangChain 简介

LangChain 是一个用于开发由语言模型驱动的应用程序的框架。它提供了一套工具、组件和接口，简化了创建 LLM（大型语言模型）应用的过程。

## 核心特性

### 1. Models（模型）
LangChain 提供了对各种模型的统一接口：
- LLMs（大型语言模型）
- Chat Models（聊天模型）
- Embeddings（嵌入模型）

### 2. Prompts（提示）
管理和优化模型提示的工具：
- Prompt Templates（提示模板）
- Output Parsers（输出解析器）
- Example Selectors（示例选择器）

### 3. Chains（链）
将多个组件组合在一起形成更复杂的应用：
- LLMChain（基础链）
- Sequential Chains（顺序链）
- Router Chains（路由链）

### 4. Agents（智能体）
使用 LLM 决定采取什么行动的代理：
- Tools（工具）
- Agent Executors（代理执行器）
- Toolkits（工具包）

### 5. Memory（记忆）
为对话历史添加状态：
- Conversation Buffer（对话缓冲）
- Conversation Summary（对话摘要）
- Vector Store Memory（向量存储记忆）

## 主要应用场景

1. **问答系统**：基于文档的问答
2. **聊天机器人**：具备记忆的对话系统
3. **内容生成**：自动化内容创作
4. **代码分析**：理解和生成代码
5. **数据提取**：从文本中提取结构化信息

## 生态系统

LangChain 拥有丰富的生态系统：
- LangSmith：调试和监控平台
- LangServe：部署和托管服务
- LangGraph：状态机框架用于构建复杂 Agent

## 快速开始

安装 LangChain：
\`\`\`bash
npm install langchain
\`\`\`

基础使用：
\`\`\`typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  modelName: "gpt-3.5-turbo",
  temperature: 0.7,
});

const response = await model.invoke([
  new HumanMessage("你好！")
]);
\`\`\`
`;
            // 将知识库内容添加到向量存储
            console.log("📚 正在创建知识库...\n");
            yield ragAgent.ingestText(sampleKnowledge, {
                source: "LangChain 官方文档",
                type: "教程",
            });
            // 显示知识库信息
            const info = ragAgent.getKnowledgeBaseInfo();
            console.log(`✅ 知识库创建完成，共 ${info.documentCount} 个文档块\n`);
            // 执行示例查询
            const queries = [
                "LangChain 的核心特性有哪些？",
                "什么是 LangChain 中的 Agents？",
                "如何快速开始使用 LangChain？",
                "LangChain 支持哪些类型的模型？",
                "LangSmith 是什么？",
            ];
            for (const query of queries) {
                yield new Promise(resolve => setTimeout(resolve, 500)); // 添加延迟避免 API 限制
                yield ragAgent.query(query);
            }
            console.log("✅ RAG Agent 演示完成！");
        }
        catch (error) {
            console.error("\n❌ 执行出错:", error.message);
            console.error("\n请检查:");
            console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
            console.error("2. API Key 是否正确");
            console.error("3. 网络连接是否正常");
        }
    });
}
/**
 * 自定义文档 RAG 演示
 */
function customDocRagDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("\n📄 自定义文档 RAG 演示");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
        const ragAgent = new RAGAgent();
        // 自定义知识内容
        const customDoc = `
# TypeScript 高级特性指南

## 泛型 (Generics)

泛型是 TypeScript 中强大的特性，允许你创建可重用的组件，同时保持类型安全。

\`\`\`typescript
function identity<T>(arg: T): T {
  return arg;
}

const output = identity<string>("hello");
\`\`\`

## 装饰器 (Decorators)

装饰器是一种特殊类型的声明，可以附加到类、方法、属性或参数上。

\`\`\`typescript
@Component({
  selector: 'app-example',
  templateUrl: './example.component.html'
})
class ExampleComponent {
  constructor() {}
}
\`\`\`

## 联合类型和交叉类型

### 联合类型 (Union Types)
\`\`\`typescript
type Status = 'pending' | 'approved' | 'rejected';

function handleStatus(status: Status) {
  // ...
}
\`\`\`

### 交叉类型 (Intersection Types)
\`\`\`typescript
type Person = { name: string };
type Employee = { employeeId: number };
type PersonEmployee = Person & Employee;

const person: PersonEmployee = {
  name: 'Alice',
  employeeId: 12345
};
\`\`\`

## 条件类型

条件类型允许你根据类型关系选择类型：
\`\`\`typescript
type NonNullable<T> = T extends null | undefined ? never : T;
\`\`\`

## 映射类型

映射类型允许你基于旧类型创建新类型：
\`\`\`typescript
type Readonly<T> = {
  readonly [P in keyof T]: T[P];
};
\`\`\`

## 实用工具类型

TypeScript 提供了许多实用工具类型：
- Partial<T>：将 T 的所有属性设为可选
- Required<T>：将 T 的所有属性设为必需
- Readonly<T>：将 T 的所有属性设为只读
- Record<K, T>：构建一个类型为 T 的属性 K 的类型
- Pick<T, K>：从 T 中选择一组属性 K
- Omit<T, K>：从 T 中排除一组属性 K
`;
        yield ragAgent.ingestText(customDoc, {
            source: "TypeScript 高级特性指南",
            type: "技术文档",
        });
        const customQueries = [
            "解释 TypeScript 中的泛型是什么",
            "什么是装饰器？",
            "TypeScript 的实用工具类型有哪些？",
        ];
        for (const query of customQueries) {
            yield new Promise(resolve => setTimeout(resolve, 500));
            yield ragAgent.query(query);
        }
    });
}
/**
 * 主函数
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        // 运行主要 RAG 演示
        yield ragAgentDemo();
        // 运行自定义文档演示
        yield customDocRagDemo();
    });
}
// 执行主函数
main();
//# sourceMappingURL=rag-agent.js.map