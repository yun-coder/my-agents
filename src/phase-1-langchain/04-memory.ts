/**
 * ========================================
 * Phase 1: LangChain 基础
 * Demo 04: Memory & Conversation History
 * ========================================
 *
 * 学习目标:
 * - 理解 Memory 在对话中的作用
 * - 掌握不同类型的 Memory 实现
 * - 学习历史消息管理
 * - 实现带记忆的对话系统
 */

import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { HumanMessage, AIMessage } from "@langchain/core/messages";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基础 Memory - 数组存储
// ============================================================================

console.log("=== 1. 基础 Memory ===\n");

// 使用简单数组存储历史消息
const memory1: Array<HumanMessage | AIMessage> = [];

const addToMemory1 = (message: HumanMessage | AIMessage) => {
  memory1.push(message);
  console.log(`[Memory 添加] ${message.constructor.name}: ${message.content}`);
};

const chatPrompt1 = ChatPromptTemplate.fromMessages([
  ["system", "你是一个友好的助手，名字叫小智。"],
  new MessagesPlaceholder("history"),
  ["human", "{input}"],
]);

const llm = createClaudeSonnet({ temperature: 0.7 });
const chain1 = chatPrompt1.pipe(llm).pipe(new StringOutputParser());

// 模拟对话
let response = await chain1.invoke({
  input: "你好！我叫小明",
  history: memory1,
});
console.log("助手:", response);
addToMemory1(new HumanMessage("你好！我叫小明"));
addToMemory1(new AIMessage(response));

response = await chain1.invoke({
  input: "我叫什么名字？",
  history: memory1,
});
console.log("助手:", response);
addToMemory1(new HumanMessage("我叫什么名字？"));
addToMemory1(new AIMessage(response));

// ============================================================================
// 2. 带 Token 限制的 Memory
// ============================================================================

console.log("\n=== 2. Token 限制 Memory ===\n");

class TokenLimitedMemory {
  private messages: Array<HumanMessage | AIMessage> = [];
  private maxTokens: number;
  private currentTokens: number = 0;

  constructor(maxTokens: number = 1000) {
    this.maxTokens = maxTokens;
  }

  addMessage(message: HumanMessage | AIMessage) {
    // 简单估算 token 数 (中文约 1 字符 = 1 token)
    const messageTokens = String(message.content).length;
    this.messages.push(message);
    this.currentTokens += messageTokens;

    // 移除最旧的消息直到 token 数在限制内
    while (this.currentTokens > this.maxTokens && this.messages.length > 2) {
      const removed = this.messages.shift();
      this.currentTokens -= String(removed?.content).length;
    }
  }

  getMessages(): Array<HumanMessage | AIMessage> {
    return [...this.messages];
  }

  getMemoryStats() {
    return {
      messageCount: this.messages.length,
      estimatedTokens: this.currentTokens,
    };
  }
}

const memory2 = new TokenLimitedMemory(500);

const chatPrompt2 = ChatPromptTemplate.fromMessages([
  ["system", "你是一个有记忆的助手。"],
  new MessagesPlaceholder("history"),
  ["human", "{input}"],
]);

const chain2 = chatPrompt2.pipe(llm).pipe(new StringOutputParser());

// 模拟长对话
const questions = [
  "什么是 TypeScript？",
  "它和 JavaScript 有什么区别？",
  "TypeScript 有哪些优势？",
  "如何学习 TypeScript？",
  "推荐一些学习资源",
];

for (const q of questions) {
  memory2.addMessage(new HumanMessage(q));

  const resp = await chain2.invoke({
    input: q,
    history: memory2.getMessages(),
  });

  memory2.addMessage(new AIMessage(resp));

  console.log(`\n[Q] ${q}`);
  console.log(`[A] ${resp.substring(0, 100)}...`);
  console.log(`[Memory] ${JSON.stringify(memory2.getMemoryStats())}`);
}

// ============================================================================
// 3. 滑动窗口 Memory
// ============================================================================

console.log("\n=== 3. 滑动窗口 Memory ===\n");

class SlidingWindowMemory {
  private messages: Array<HumanMessage | AIMessage> = [];
  private windowSize: number;

  constructor(windowSize: number = 4) {
    this.windowSize = windowSize;
  }

  addMessage(message: HumanMessage | AIMessage) {
    this.messages.push(message);
    // 保留最近的 windowSize 条消息
    if (this.messages.length > this.windowSize) {
      this.messages = this.messages.slice(-this.windowSize);
    }
  }

  getMessages(): Array<HumanMessage | AIMessage> {
    return [...this.messages];
  }
}

const memory3 = new SlidingWindowMemory(4);

console.log("演示滑动窗口效果:");
for (let i = 1; i <= 6; i++) {
  memory3.addMessage(new HumanMessage(`消息 ${i}`));

  const historySummary = memory3
    .getMessages()
    .map((m, idx) => `[${idx + 1}] ${m.content}`)
    .join(", ");

  console.log(`添加消息 ${i} 后: ${historySummary}`);
}

// ============================================================================
// 4. 摘要 Memory
// ============================================================================

console.log("\n=== 4. 摘要 Memory ===\n");

class SummaryMemory {
  private summary: string = "";
  private recentMessages: Array<HumanMessage | AIMessage> = [];
  private maxRecentMessages: number = 2;

  async update(messages: Array<HumanMessage | AIMessage>) {
    // 定期总结旧消息
    if (this.recentMessages.length >= this.maxRecentMessages) {
      await this.summarize();
    }

    // 添加新消息
    this.recentMessages.push(...messages);
  }

  private async summarize() {
    const summaryPrompt = ChatPromptTemplate.fromMessages([
      [
        "system",
        "你是一个对话总结专家。请将以下对话总结成一段简短的文字，保留关键信息。",
      ],
      ["human", "对话历史:\n{history}\n\n请总结:"],
    ]);

    const historyText = this.recentMessages
      .map((m) => `${m.constructor.name}: ${m.content}`)
      .join("\n");

    const summaryChain = summaryPrompt.pipe(llm).pipe(new StringOutputParser());

    const newSummary = await summaryChain.invoke({
      history: historyText,
    });

    this.summary = this.summary ? `${this.summary}\n${newSummary}` : newSummary;
    this.recentMessages = [];
  }

  getContext(): string {
    if (!this.summary && this.recentMessages.length === 0) {
      return "";
    }

    const parts: string[] = [];
    if (this.summary) {
      parts.push(`[对话摘要]\n${this.summary}`);
    }
    if (this.recentMessages.length > 0) {
      parts.push(
        `[近期对话]\n${this.recentMessages.map((m) => `${m.constructor.name}: ${m.content}`).join("\n")}`
      );
    }
    return parts.join("\n\n");
  }
}

const memory4 = new SummaryMemory();

await memory4.update([
  new HumanMessage("我喜欢编程，特别是 Python"),
  new AIMessage("Python 是一门很棒的编程语言！"),
]);

await memory4.update([
  new HumanMessage("最近在学 TypeScript"),
  new AIMessage("TypeScript 也很好，它能让你写出更安全的代码"),
]);

console.log("摘要 Memory 内容:");
console.log(memory4.getContext());

// ============================================================================
// 5. 完整的对话管理器
// ============================================================================

console.log("\n=== 5. 对话管理器 ===\n");

class ConversationManager {
  private memory: TokenLimitedMemory;
  private chain: any;
  private conversationId: string;

  constructor(conversationId: string = "default") {
    this.conversationId = conversationId;
    this.memory = new TokenLimitedMemory(1000);

    const prompt = ChatPromptTemplate.fromMessages([
      ["system", "你是一个专业的 AI 助手。"],
      new MessagesPlaceholder("history"),
      ["human", "{input}"],
    ]);

    this.chain = prompt.pipe(llm).pipe(new StringOutputParser());
  }

  async chat(userInput: string): Promise<string> {
    // 添加用户消息
    this.memory.addMessage(new HumanMessage(userInput));

    // 获取响应
    const response = await this.chain.invoke({
      input: userInput,
      history: this.memory.getMessages(),
    });

    // 添加助手响应
    this.memory.addMessage(new AIMessage(response));

    return response;
  }

  getConversationHistory(): Array<HumanMessage | AIMessage> {
    return this.memory.getMessages();
  }

  clear() {
    this.memory = new TokenLimitedMemory(1000);
  }

  getStats() {
    return this.memory.getMemoryStats();
  }
}

// 使用对话管理器
const conversation = new ConversationManager("demo-001");

const demoInputs = [
  "你好",
  "我想了解 TypeScript",
  "它有什么优势？",
  "谢谢你的介绍",
];

for (const input of demoInputs) {
  console.log(`\n用户: ${input}`);
  const response = await conversation.chat(input);
  console.log(`助手: ${response.substring(0, 100)}...`);
  console.log(`统计: ${JSON.stringify(conversation.getStats())}`);
}

// ============================================================================
// 总结
// ============================================================================

console.log("\n=== 本节要点总结 ===");
console.log("1. 基础 Memory - 使用数组存储消息历史");
console.log("2. Token 限制 - 控制上下文窗口大小");
console.log("3. 滑动窗口 - 保留最近 N 条消息");
console.log("4. 摘要 Memory - 压缩历史信息");
console.log("5. 对话管理器 - 完整的对话状态管理");
console.log("\n选择 Memory 类型的建议:");
console.log("- 短对话: 基础 Memory 或滑动窗口");
console.log("- 长对话: Token 限制或摘要 Memory");
console.log("- 生产环境: 对话管理器 + 持久化");

export {
  TokenLimitedMemory,
  SlidingWindowMemory,
  SummaryMemory,
  ConversationManager,
};
