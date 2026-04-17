/**
 * ========================================
 * Phase 1: LangChain 基础
 * Demo 01: Prompts & Prompt Templates
 * ========================================
 *
 * 学习目标:
 * - 理解 PromptTemplate 的作用
 * - 掌握 System/Human/AI 消息格式
 * - 学习变量插值和部分变量
 * - 使用 MessagesPlaceholder
 */

import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基础 Prompt Template
// ============================================================================

console.log("=== 1. 基础 Prompt Template ===\n");

const basicPrompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个有帮助的助手，专门解答 {topic} 相关的问题。"],
  ["human", "{input}"],
]);

// 格式化 prompt
const formattedPrompt = await basicPrompt.formatMessages({
  topic: "编程",
  input: "什么是 TypeScript？",
});

console.log("格式化后的 Prompt:");
console.log(JSON.stringify(formattedPrompt, null, 2));

// ============================================================================
// 2. 使用 LCEL 调用 LLM
// ============================================================================

console.log("\n=== 2. 使用 LCEL 调用 LLM ===\n");

const llm = createClaudeSonnet({ temperature: 0.7 });
const chain = basicPrompt.pipe(llm);

const response = await chain.invoke({
  topic: "编程",
  input: "什么是 TypeScript？",
});

console.log("LLM 响应:", response.content);

// ============================================================================
// 3. 多轮对话模板
// ============================================================================

console.log("\n=== 3. 多轮对话模板 ===\n");

const chatPrompt = ChatPromptTemplate.fromMessages([
  ["system", "你是一个友好的助手，名字叫 Claude。"],
  new MessagesPlaceholder("history"), // 历史消息占位符
  ["human", "{input}"],
]);

// 格式化带历史记录的 prompt
const chatFormatted = await chatPrompt.formatMessages({
  history: [
    new HumanMessage("你好！"),
    new SystemMessage("你好！有什么我可以帮助你的吗？"),
    new HumanMessage("我叫小明"),
  ],
  input: "我叫什么名字？",
});

console.log("带历史记录的 Prompt:");
chatFormatted.forEach((msg, i) => {
  console.log(`[${i}] ${msg.constructor.name}:`, msg.content);
});

// ============================================================================
// 4. 部分变量
// ============================================================================

console.log("\n=== 4. 部分变量 ===\n");

// 创建一个只包含系统消息的部分 prompt
const partialPrompt = await ChatPromptTemplate.fromMessages([
  ["system", "你是一个 {role}，专门处理 {domain} 相关的问题。"],
  ["human", "{input}"],
]).partial({
  role: "高级工程师",
  domain: "Web 开发",
});

// 现在只需要提供 input
const finalPrompt = await partialPrompt.formatMessages({
  input: "React 和 Vue 有什么区别？",
});

console.log("使用部分变量后的 Prompt:");
console.log(JSON.stringify(finalPrompt, null, 2));

// ============================================================================
// 5. 自定义 Prompt 模板
// ============================================================================

console.log("\n=== 5. 自定义 Prompt 模板 ===\n");

// 创建代码审查模板
const codeReviewPrompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    `你是一个专业的代码审查员。请按照以下标准审查代码：
    1. 代码质量和可读性
    2. 潜在的 bug 和问题
    3. 性能优化建议
    4. 最佳实践建议`,
  ],
  ["human", "请审查以下 {language} 代码：\n\n```{language}\n{code}\n```"],
]);

const codeReviewChain = codeReviewPrompt.pipe(llm);

const code = `
function calculateSum(numbers) {
  let sum = 0;
  for (let i = 0; i < numbers.length; i++) {
    sum += numbers[i];
  }
  return sum;
}
`;

const review = await codeReviewChain.invoke({
  language: "JavaScript",
  code: code.trim(),
});

console.log("代码审查结果:");
console.log(review.content);

// ============================================================================
// 6. Few-shot 示例
// ============================================================================

console.log("\n=== 6. Few-shot 示例 ===\n");

const fewShotPrompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    `你是一个情感分析专家。以下是一些示例：

    示例 1:
    输入: "这个产品太棒了！"
    输出: 正面

    示例 2:
    输入: "服务很差，不会再来了。"
    输出: 负面

    示例 3:
    输入: "还可以，没什么特别的。"
    输出: 中性`,
  ],
  ["human", "输入: \"{input}\"\n输出: "],
]);

const sentimentChain = fewShotPrompt.pipe(llm);

const sentiment = await sentimentChain.invoke({
  input: "这个功能很有用，推荐大家使用！",
});

console.log("情感分析结果:", sentiment.content);

// ============================================================================
// 总结
// ============================================================================

console.log("\n=== 本节要点总结 ===");
console.log("1. ChatPromptTemplate.fromMessages() - 创建提示模板");
console.log("2. .formatMessages() - 格式化消息");
console.log("3. .pipe() - 使用 LCEL 连接 LLM");
console.log("4. MessagesPlaceholder - 历史消息占位符");
console.log("5. .partial() - 预设部分变量");
console.log("6. Few-shot 示例 - 提供示例提高准确性");

export {
  basicPrompt,
  chatPrompt,
  codeReviewPrompt,
  fewShotPrompt,
};
