/**
 * LangChain Memory 持久化 Demo
 * 基于 LangChain 官方教程: Memory
 *
 * 学习资源: https://docs.langchain.com/oss/javascript/concepts/memory
 *
 * 功能特性:
 * - 对话历史管理
 * - 跨会话记忆持久化
 * - 本地文件存储
 * - 记忆检索和总结
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
import { HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";
import * as fs from "fs";
import * as path from "path";
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
 * 内存持久化存储
 */
class MemoryPersistenceStore {
    constructor(storageDir = "./memory_storage") {
        this.storageDir = storageDir;
        this.conversations = new Map();
        this.initializeStorage();
    }
    /**
     * 初始化存储目录
     */
    initializeStorage() {
        if (!fs.existsSync(this.storageDir)) {
            fs.mkdirSync(this.storageDir, { recursive: true });
            console.log(`✅ 创建存储目录: ${this.storageDir}`);
        }
        // 加载已保存的对话
        this.loadAllConversations();
    }
    /**
     * 保存对话到文件
     */
    saveConversationToFile(conversation) {
        const filePath = path.join(this.storageDir, `${conversation.id}.json`);
        fs.writeFileSync(filePath, JSON.stringify(conversation, null, 2), "utf-8");
    }
    /**
     * 从文件加载对话
     */
    loadConversationFromFile(id) {
        const filePath = path.join(this.storageDir, `${id}.json`);
        if (fs.existsSync(filePath)) {
            try {
                const data = fs.readFileSync(filePath, "utf-8");
                return JSON.parse(data);
            }
            catch (error) {
                console.error(`加载对话 ${id} 失败:`, error);
                return null;
            }
        }
        return null;
    }
    /**
     * 加载所有对话
     */
    loadAllConversations() {
        try {
            const files = fs.readdirSync(this.storageDir);
            let loadedCount = 0;
            for (const file of files) {
                if (file.endsWith('.json')) {
                    const conversationId = file.replace('.json', '');
                    const conversation = this.loadConversationFromFile(conversationId);
                    if (conversation) {
                        this.conversations.set(conversationId, conversation);
                        loadedCount++;
                    }
                }
            }
            if (loadedCount > 0) {
                console.log(`✅ 加载了 ${loadedCount} 个历史对话`);
            }
        }
        catch (error) {
            console.error("加载对话失败:", error);
        }
    }
    /**
     * 创建新对话
     */
    createConversation(userId, title, metadata) {
        const id = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        const now = Date.now();
        const conversation = {
            id,
            userId,
            title: title || "新对话",
            messages: [],
            createdAt: now,
            updatedAt: now,
            metadata,
        };
        this.conversations.set(id, conversation);
        this.saveConversationToFile(conversation);
        console.log(`✅ 创建新对话: ${conversation.title} (${id})`);
        return conversation;
    }
    /**
     * 获取对话
     */
    getConversation(id) {
        return this.conversations.get(id) || null;
    }
    /**
     * 添加消息到对话
     */
    addMessage(conversationId, type, content) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) {
            console.error(`对话 ${conversationId} 不存在`);
            return false;
        }
        const message = {
            type,
            content,
            timestamp: Date.now(),
        };
        conversation.messages.push(message);
        conversation.updatedAt = Date.now();
        this.saveConversationToFile(conversation);
        return true;
    }
    /**
     * 获取对话的消息历史
     */
    getMessages(conversationId, limit) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) {
            return [];
        }
        const messages = conversation.messages;
        return limit ? messages.slice(-limit) : messages;
    }
    /**
     * 获取用户的所有对话
     */
    getUserConversations(userId) {
        return Array.from(this.conversations.values())
            .filter(conv => conv.userId === userId)
            .sort((a, b) => b.updatedAt - a.updatedAt);
    }
    /**
     * 更新对话标题
     */
    updateConversationTitle(id, title) {
        const conversation = this.conversations.get(id);
        if (!conversation) {
            return false;
        }
        conversation.title = title;
        conversation.updatedAt = Date.now();
        this.saveConversationToFile(conversation);
        return true;
    }
    /**
     * 删除对话
     */
    deleteConversation(id) {
        const conversation = this.conversations.get(id);
        if (!conversation) {
            return false;
        }
        this.conversations.delete(id);
        const filePath = path.join(this.storageDir, `${id}.json`);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
        console.log(`✅ 删除对话: ${id}`);
        return true;
    }
    /**
     * 搜索对话
     */
    searchConversations(query, userId) {
        const queryLower = query.toLowerCase();
        return Array.from(this.conversations.values())
            .filter(conv => {
            if (userId && conv.userId !== userId) {
                return false;
            }
            // 搜索标题
            if (conv.title.toLowerCase().includes(queryLower)) {
                return true;
            }
            // 搜索消息内容
            return conv.messages.some(msg => msg.content.toLowerCase().includes(queryLower));
        })
            .sort((a, b) => b.updatedAt - a.updatedAt);
    }
    /**
     * 生成对话总结
     */
    summarizeConversation(conversationId) {
        return __awaiter(this, void 0, void 0, function* () {
            const conversation = this.conversations.get(conversationId);
            if (!conversation || conversation.messages.length === 0) {
                return null;
            }
            const model = createMiniMaxModel("claude-3-5-haiku-20241022", 0.3);
            const messagesText = conversation.messages
                .map(msg => `[${msg.type}]: ${msg.content}`)
                .join('\n');
            const prompt = `请总结以下对话的主要内容，包括：
1. 对话主题
2. 关键讨论点
3. 达成的结论
4. 待办事项（如有）

请用简洁清晰的语言总结，不超过 200 字。

对话内容：
${messagesText}`;
            try {
                const response = yield model.invoke([
                    new SystemMessage("你是一个专业的对话总结助手，擅长提取对话的核心内容和关键信息。"),
                    new HumanMessage(prompt),
                ]);
                return typeof response.content === 'string'
                    ? response.content
                    : String(response.content);
            }
            catch (error) {
                console.error("生成对话总结失败:", error);
                return null;
            }
        });
    }
    /**
     * 获取存储统计信息
     */
    getStats() {
        let totalMessages = 0;
        let storageSize = 0;
        for (const conversation of this.conversations.values()) {
            totalMessages += conversation.messages.length;
            storageSize += JSON.stringify(conversation).length;
        }
        return {
            totalConversations: this.conversations.size,
            totalMessages,
            storageSize,
        };
    }
}
/**
 * 智能对话助手
 */
class ConversationalAssistant {
    constructor(memoryStore, systemPrompt) {
        this.model = createMiniMaxModel();
        this.memoryStore = memoryStore;
        this.systemPrompt = systemPrompt || "你是一个友好、专业的 AI 助手，擅长回答各种问题并提供帮助。";
    }
    /**
     * 开始新对话
     */
    startConversation(userId, title) {
        const conversation = this.memoryStore.createConversation(userId, title);
        return conversation.id;
    }
    /**
     * 继续对话
     */
    chat(conversationId, userMessage) {
        return __awaiter(this, void 0, void 0, function* () {
            // 添加用户消息
            this.memoryStore.addMessage(conversationId, "human", userMessage);
            // 获取对话历史
            const messages = this.memoryStore.getMessages(conversationId, 10); // 最近 10 条消息
            // 构建消息列表
            const chatMessages = [
                new SystemMessage(this.systemPrompt),
            ];
            for (const msg of messages) {
                switch (msg.type) {
                    case "human":
                        chatMessages.push(new HumanMessage(msg.content));
                        break;
                    case "ai":
                        chatMessages.push(new AIMessage(msg.content));
                        break;
                    case "system":
                        chatMessages.push(new SystemMessage(msg.content));
                        break;
                }
            }
            // 生成回复
            const response = yield this.model.invoke(chatMessages);
            const assistantMessage = typeof response.content === 'string'
                ? response.content
                : String(response.content);
            // 保存助手回复
            this.memoryStore.addMessage(conversationId, "ai", assistantMessage);
            return assistantMessage;
        });
    }
    /**
     * 获取对话历史
     */
    getConversationHistory(conversationId) {
        return this.memoryStore.getMessages(conversationId);
    }
}
/**
 * 格式化消息显示
 */
function formatMessage(message) {
    const timestamp = new Date(message.timestamp).toLocaleTimeString();
    const role = message.type === "human" ? "用户" : message.type === "ai" ? "助手" : "系统";
    return `[${timestamp}] ${role}: ${message.content}`;
}
/**
 * 格式化对话列表
 */
function formatConversations(conversations) {
    if (conversations.length === 0) {
        return "暂无对话";
    }
    let output = "";
    for (let i = 0; i < conversations.length; i++) {
        const conv = conversations[i];
        output += `\n[对话 ${i + 1}] ${conv.title}\n`;
        output += `ID: ${conv.id}\n`;
        output += `消息数: ${conv.messages.length}\n`;
        output += `创建时间: ${new Date(conv.createdAt).toLocaleString()}\n`;
        output += `更新时间: ${new Date(conv.updatedAt).toLocaleString()}\n`;
        output += "─".repeat(40) + "\n";
    }
    return output;
}
/**
 * Memory 持久化演示
 */
function memoryPersistenceDemo() {
    return __awaiter(this, void 0, void 0, function* () {
        console.log("🚀 LangChain Memory 持久化演示");
        console.log("基于 LangChain 官方教程: Memory\n");
        try {
            // 创建内存存储
            const memoryStore = new MemoryPersistenceStore();
            // 显示存储统计
            const stats = memoryStore.getStats();
            console.log(`📊 存储统计:`);
            console.log(`   对话总数: ${stats.totalConversations}`);
            console.log(`   消息总数: ${stats.totalMessages}`);
            console.log(`   存储大小: ${(stats.storageSize / 1024).toFixed(2)} KB\n`);
            // 创建对话助手
            const assistant = new ConversationalAssistant(memoryStore, "你是一个专业的编程导师，擅长解释技术概念，提供编程建议，并帮助解决编程问题。");
            // 演示 1: 创建新对话并进行多轮交流
            console.log("📌 演示 1: 新对话与多轮交流");
            console.log("=".repeat(60));
            const conversationId = assistant.startConversation("user123", "TypeScript 学习");
            console.log(`✅ 创建对话: ${conversationId}\n`);
            const questions = [
                "什么是 TypeScript？它和 JavaScript 有什么区别？",
                "TypeScript 的泛型是什么？能举个例子吗？",
                "在实际项目中使用 TypeScript 有什么好处？",
            ];
            for (const question of questions) {
                console.log(`👤 用户: ${question}`);
                const answer = yield assistant.chat(conversationId, question);
                console.log(`🤖 助手: ${answer.substring(0, 200)}...\n`);
                yield new Promise(resolve => setTimeout(resolve, 1000)); // 避免API限流
            }
            // 演示 2: 获取对话历史
            console.log("\n📌 演示 2: 对话历史");
            console.log("=".repeat(60));
            const history = assistant.getConversationHistory(conversationId);
            console.log("📜 对话历史:");
            for (const msg of history) {
                console.log(formatMessage(msg));
            }
            // 演示 3: 跨会话记忆
            console.log("\n📌 演示 3: 跨会话记忆（恢复对话）");
            console.log("=".repeat(60));
            // 模拟新会话恢复对话
            const restoredConversation = memoryStore.getConversation(conversationId);
            if (restoredConversation) {
                console.log(`✅ 恢复对话: ${restoredConversation.title}`);
                console.log(`   历史消息数: ${restoredConversation.messages.length}\n`);
                // 继续对话
                const followUpQuestion = "根据我们刚才的讨论，我应该如何开始学习 TypeScript？";
                console.log(`👤 用户: ${followUpQuestion}`);
                const followUpAnswer = yield assistant.chat(conversationId, followUpQuestion);
                console.log(`🤖 助手: ${followUpAnswer.substring(0, 200)}...\n`);
            }
            // 演示 4: 对话总结
            console.log("📌 演示 4: 对话总结");
            console.log("=".repeat(60));
            const summary = yield memoryStore.summarizeConversation(conversationId);
            if (summary) {
                console.log("📋 对话总结:");
                console.log(summary);
            }
            // 演示 5: 用户所有对话
            console.log("\n📌 演示 5: 用户的所有对话");
            console.log("=".repeat(60));
            const userConversations = memoryStore.getUserConversations("user123");
            console.log(formatConversations(userConversations));
            // 演示 6: 搜索对话
            console.log("📌 演示 6: 搜索对话");
            console.log("=".repeat(60));
            const searchResults = memoryStore.searchConversations("TypeScript", "user123");
            console.log(`🔍 搜索 "TypeScript" 结果:\n`);
            console.log(formatConversations(searchResults));
            // 演示 7: 创建多个用户对话
            console.log("\n📌 演示 7: 多用户场景");
            console.log("=".repeat(60));
            const assistant2 = new ConversationalAssistant(memoryStore, "你是一个旅行规划助手，擅长提供旅行建议和规划行程。");
            const travelConversationId = assistant2.startConversation("user456", "日本旅行规划");
            yield assistant2.chat(travelConversationId, "我计划去日本旅行，有什么建议吗？");
            const allConversations = Array.from(memoryStore.getUserConversations("user123"))
                .concat(memoryStore.getUserConversations("user456"));
            console.log("👥 所有用户对话:");
            console.log(formatConversations(allConversations));
            // 最终统计
            const finalStats = memoryStore.getStats();
            console.log(`\n📊 最终存储统计:`);
            console.log(`   对话总数: ${finalStats.totalConversations}`);
            console.log(`   消息总数: ${finalStats.totalMessages}`);
            console.log(`   存储大小: ${(finalStats.storageSize / 1024).toFixed(2)} KB`);
            console.log("\n✅ Memory 持久化演示完成！");
        }
        catch (error) {
            console.error("\n❌ 执行出错:", error.message);
            console.error("\n请检查:");
            console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
            console.error("2. API Key 是否正确");
            console.error("3. 网络连接是否正常");
            console.error("4. 磁盘空间是否充足");
        }
    });
}
/**
 * 主函数
 */
function main() {
    return __awaiter(this, void 0, void 0, function* () {
        yield memoryPersistenceDemo();
    });
}
// 执行主函数
main();
//# sourceMappingURL=memory-persistence.js.map