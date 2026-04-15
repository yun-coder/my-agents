/**
 * LangChain 语义搜索和向量存储 Demo
 * 基于 LangChain 官方教程: Semantic Search
 *
 * 学习资源: https://docs.langchain.com/oss/javascript/tutorials/semantic_search
 *
 * 功能特性:
 * - 文档向量化
 * - 语义相似度搜索
 * - 混合搜索（语义+关键词）
 * - 向量存储管理
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
// 加载环境变量
dotenv.config();
/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName = "claude-3-5-sonnet-20241022", temperature = 0.7) {
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
 * 语义搜索引擎
 */
class SemanticSearchEngine {
    constructor() {
        this.documents = new Map();
        this.vectors = new Map();
        this.model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3);
    }
    /**
     * 生成简化的向量表示
     * 在生产环境中应使用真实的嵌入模型
     */
    generateEmbedding(text) {
        return __awaiter(this, void 0, void 0, function* () {
            // 使用 TF-IDF 简化方法生成向量
            const words = text.toLowerCase().split(/\s+/);
            const vectorMap = new Map();
            // 计算词频
            for (const word of words) {
                const cleanWord = word.replace(/[^\w\u4e00-\u9fa5]/g, '');
                if (cleanWord.length > 1) {
                    vectorMap.set(cleanWord, (vectorMap.get(cleanWord) || 0) + 1);
                }
            }
            // 转换为固定长度的向量
            const vectorSize = 512;
            const vector = new Array(vectorSize).fill(0);
            let index = 0;
            for (const [word, freq] of vectorMap) {
                const hash = this.simpleHash(word);
                vector[hash % vectorSize] += freq;
                index++;
                if (index >= vectorSize)
                    break;
            }
            // 归一化
            const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
            return magnitude > 0 ? vector.map(v => v / magnitude) : vector;
        });
    }
    /**
     * 简单的哈希函数
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash);
    }
    /**
     * 添加文档到索引
     */
    addDocument(doc) {
        return __awaiter(this, void 0, void 0, function* () {
            const { id, content, metadata } = doc;
            // 存储文档
            this.documents.set(id, doc);
            // 生成并存储向量
            const embedding = yield this.generateEmbedding(content);
            this.vectors.set(id, {
                values: embedding,
                metadata: doc,
            });
            console.log(`✅ 文档已添加: ${metadata.title} (${id})`);
        });
    }
    /**
     * 批量添加文档
     */
    addDocuments(docs) {
        return __awaiter(this, void 0, void 0, function* () {
            for (const doc of docs) {
                yield this.addDocument(doc);
            }
        });
    }
    /**
     * 计算余弦相似度
     */
    cosineSimilarity(vec1, vec2) {
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
    /**
     * 语义搜索
     */
    semanticSearch(query_1) {
        return __awaiter(this, arguments, void 0, function* (query, topK = 5) {
            console.log(`\n🔍 语义搜索: "${query}"`);
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            // 生成查询向量
            const queryVector = yield this.generateEmbedding(query);
            // 计算所有文档的相似度
            const results = [];
            for (const [id, vector] of this.vectors) {
                const similarity = this.cosineSimilarity(queryVector, vector.values);
                results.push({
                    doc: vector.metadata,
                    score: similarity,
                });
            }
            // 按相似度排序并返回前 topK 个
            const sortedResults = results
                .sort((a, b) => b.score - a.score)
                .slice(0, topK)
                .filter(result => result.score > 0.01); // 过滤低相关性结果
            console.log(`📊 找到 ${sortedResults.length} 个相关结果\n`);
            return sortedResults;
        });
    }
    /**
     * 混合搜索（语义 + 关键词）
     */
    hybridSearch(query_1, filters_1) {
        return __awaiter(this, arguments, void 0, function* (query, filters, topK = 5) {
            console.log(`\n🔍 混合搜索: "${query}"`);
            if (filters) {
                console.log(`📋 过滤条件: ${JSON.stringify(filters)}`);
            }
            console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            // 语义搜索
            const semanticResults = yield this.semanticSearch(query, this.documents.size);
            // 应用过滤条件和关键词匹配
            const results = [];
            const queryLower = query.toLowerCase();
            for (const result of semanticResults) {
                // 应用分类过滤
                if ((filters === null || filters === void 0 ? void 0 : filters.category) && result.doc.metadata.category !== filters.category) {
                    continue;
                }
                // 应用标签过滤
                if ((filters === null || filters === void 0 ? void 0 : filters.tags) && filters.tags.length > 0) {
                    const hasTag = filters.tags.some(tag => result.doc.metadata.tags.includes(tag));
                    if (!hasTag)
                        continue;
                }
                // 计算关键词匹配分数
                let keywordScore = 0;
                const content = result.doc.content.toLowerCase();
                const title = result.doc.metadata.title.toLowerCase();
                // 完全匹配
                if (content.includes(queryLower) || title.includes(queryLower)) {
                    keywordScore += 1.0;
                }
                // 部分匹配
                const queryWords = queryLower.split(/\s+/);
                for (const word of queryWords) {
                    if (content.includes(word) || title.includes(word)) {
                        keywordScore += 0.3;
                    }
                }
                results.push({
                    doc: result.doc,
                    semanticScore: result.score,
                    keywordScore: Math.min(keywordScore, 1.0),
                });
            }
            // 计算综合分数（语义 70% + 关键词 30%）
            const finalResults = results
                .map(result => (Object.assign(Object.assign({}, result), { combinedScore: result.semanticScore * 0.7 + result.keywordScore * 0.3 })))
                .sort((a, b) => b.combinedScore - a.combinedScore)
                .slice(0, topK);
            console.log(`📊 找到 ${finalResults.length} 个相关结果\n`);
            return finalResults;
        });
    }
    /**
     * 获取统计信息
     */
    getStats() {
        const categories = new Set();
        for (const doc of this.documents.values()) {
            categories.add(doc.metadata.category);
        }
        return {
            totalDocuments: this.documents.size,
            categories,
        };
    }
    /**
     * 获取所有分类
     */
    getCategories() {
        const categories = new Set();
        for (const doc of this.documents.values()) {
            categories.add(doc.metadata.category);
        }
        return Array.from(categories).sort();
    }
    /**
     * 获取所有标签
     */
    getAllTags() {
        const tags = new Set();
        for (const doc of this.documents.values()) {
            for (const tag of doc.metadata.tags) {
                tags.add(tag);
            }
        }
        return Array.from(tags).sort();
    }
}
/**
 * 格式化搜索结果
 */
function formatSearchResults(results) {
    if (results.length === 0) {
        return "未找到相关结果";
    }
    let output = "";
    for (let i = 0; i < results.length; i++) {
        const result = results[i];
        output += `\n[结果 ${i + 1}] ${result.doc.metadata.title}\n`;
        output += `分类: ${result.doc.metadata.category}\n`;
        output += `标签: ${result.doc.metadata.tags.join(', ')}\n`;
        if (result.semanticScore !== undefined) {
            output += `语义相似度: ${(result.semanticScore * 100).toFixed(1)}%`;
        }
        if (result.keywordScore !== undefined) {
            output += ` | 关键词匹配: ${(result.keywordScore * 100).toFixed(1)}%`;
        }
        if (result.combinedScore !== undefined) {
            output += ` | 综合分数: ${(result.combinedScore * 100).toFixed(1)}%`;
        }
        output += `\n摘要: ${result.doc.content.substring(0, 150)}...\n`;
        output += "─".repeat(50) + "\n";
    }
    return output;
}
/**
 * 创建示例文档库
 */
function createSampleDocuments() {
    return [
        {
            id: "doc1",
            content: "TypeScript 是 JavaScript 的超集，添加了静态类型检查。它可以帮助开发者在编译时发现错误，提高代码质量和可维护性。",
            metadata: {
                title: "TypeScript 简介",
                category: "编程语言",
                tags: ["TypeScript", "JavaScript", "类型系统"],
            },
        },
        {
            id: "doc2",
            content: "React 是一个用于构建用户界面的 JavaScript 库。它采用组件化开发模式，使得代码更加模块化和可重用。",
            metadata: {
                title: "React 框架概述",
                category: "前端框架",
                tags: ["React", "JavaScript", "UI", "组件化"],
            },
        },
        {
            id: "doc3",
            content: "LangChain 是一个开发由语言模型驱动的应用程序的框架。它提供了工具、组件和接口，简化了 LLM 应用的开发。",
            metadata: {
                title: "LangChain 框架",
                category: "AI框架",
                tags: ["LangChain", "LLM", "AI", "语言模型"],
            },
        },
        {
            id: "doc4",
            content: "向量数据库是一种专门用于存储和检索向量数据的数据库。它在语义搜索、推荐系统等场景中发挥重要作用。",
            metadata: {
                title: "向量数据库介绍",
                category: "数据库",
                tags: ["向量数据库", "搜索", "AI", "语义搜索"],
            },
        },
        {
            id: "doc5",
            content: "RAG (Retrieval Augmented Generation) 是一种结合检索和生成的技术。它先从知识库中检索相关信息，然后基于这些信息生成回答。",
            metadata: {
                title: "RAG 技术详解",
                category: "AI技术",
                tags: ["RAG", "检索增强生成", "AI", "LLM"],
            },
        },
        {
            id: "doc6",
            content: "Node.js 是一个基于 Chrome V8 引擎的 JavaScript 运行时环境，使得 JavaScript 可以在服务器端运行。",
            metadata: {
                title: "Node.js 运行时",
                category: "运行时环境",
                tags: ["Node.js", "JavaScript", "后端"],
            },
        },
        {
            id: "doc7",
            content: "GraphQL 是一种用于 API 的查询语言，提供了更高效、强大和灵活的数据查询方式，相比 REST API 有很多优势。",
            metadata: {
                title: "GraphQL API 设计",
                category: "API设计",
                tags: ["GraphQL", "API", "查询语言"],
            },
        },
        {
            id: "doc8",
            content: "语义搜索是一种基于内容语义理解而非关键词匹配的搜索技术。它能更好地理解用户意图，提供更准确的搜索结果。",
            metadata: {
                title: "语义搜索技术",
                category: "搜索技术",
                tags: ["语义搜索", "搜索", "AI", "NLP"],
            },
        },
        {
            id: "doc9",
            content: "Agent（智能体）是一种能够感知环境、做出决策并执行行动的自主系统。在 AI 领域，Agent 通常使用 LLM 作为核心决策引擎。",
            metadata: {
                title: "AI Agent 概念",
                category: "AI概念",
                tags: ["Agent", "AI", "智能体", "LLM"],
            },
        },
        {
            id: "doc10",
            content: "Prompt Engineering 是设计和优化提示词以获得更好的 LLM 输出的技术。好的 prompt 可以显著提升 AI 模型的性能。",
            metadata: {
                title: "提示词工程",
                category: "AI技术",
                tags: ["Prompt", "LLM", "AI", "提示工程"],
            },
        },
    ];
}
/**
 * 语义搜索演示
 */
function semanticSearchDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("🚀 LangChain 语义搜索和向量存储演示");
        console.log("基于 LangChain 官方教程\n");
        try {
            // 创建搜索引擎
            const engine = new SemanticSearchEngine();
            // 添加示例文档
            console.log("📚 正在创建文档索引...\n");
            const sampleDocs = createSampleDocuments();
            yield engine.addDocuments(sampleDocs);
            // 显示统计信息
            const stats = engine.getStats();
            console.log(`\n📊 索引统计:`);
            console.log(`   文档总数: ${stats.totalDocuments}`);
            console.log(`   分类数量: ${stats.categories.size}`);
            console.log(`   所有分类: ${Array.from(stats.categories).join(', ')}`);
            console.log(`   所有标签: ${engine.getAllTags().join(', ')}\n`);
            // 示例 1: 基础语义搜索
            console.log("🔍 示例 1: 基础语义搜索");
            console.log("=".repeat(50));
            const semanticResults = yield engine.semanticSearch("AI 和语言模型");
            console.log(formatSearchResults(semanticResults));
            // 示例 2: 混合搜索
            console.log("🔍 示例 2: 混合搜索（语义 + 关键词）");
            console.log("=".repeat(50));
            const hybridResults = yield engine.hybridSearch("TypeScript 编程");
            console.log(formatSearchResults(hybridResults));
            // 示例 3: 带过滤条件的搜索
            console.log("🔍 示例 3: 带分类过滤的搜索");
            console.log("=".repeat(50));
            const filteredResults = yield engine.hybridSearch("开发", { category: "AI技术" }, 3);
            console.log(formatSearchResults(filteredResults));
            // 示例 4: 标签过滤搜索
            console.log("🔍 示例 4: 带标签过滤的搜索");
            console.log("=".repeat(50));
            const tagFilteredResults = yield engine.hybridSearch("开发工具", { tags: ["LLM", "AI"] }, 5);
            console.log(formatSearchResults(tagFilteredResults));
            // 示例 5: 使用 GPT 生成智能推荐
            console.log("🤖 示例 5: 基于 GPT 的智能推荐");
            console.log("=".repeat(50));
            const model = createMiniMaxModel();
            const searchQuery = "前端开发技术";
            const relevantDocs = yield engine.semanticSearch(searchQuery, 3);
            const recommendationsPrompt = `基于以下搜索结果，为对"${searchQuery}"感兴趣的用户推荐相关的学习路径：

搜索结果：
${relevantDocs.map((r, i) => `${i + 1}. ${r.doc.metadata.title}: ${r.doc.content.substring(0, 100)}`).join('\n')}

请提供一个结构化的学习建议，包括：
1. 核心概念
2. 推荐的学习顺序
3. 相关技术栈
4. 实践建议`;
            const response = yield model.invoke([
                new HumanMessage("你是一个技术学习顾问，擅长提供学习路径建议。\n\n" + recommendationsPrompt),
            ]);
            console.log("📋 智能学习建议:");
            console.log(typeof response.content === 'string' ? response.content : String(response.content));
            console.log("\n");
            console.log("✅ 语义搜索演示完成！");
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
 * 主函数
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        yield semanticSearchDemo();
    });
}
// 执行主函数
main();
//# sourceMappingURL=semantic-search.js.map