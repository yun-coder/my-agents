/**
 * LangChain + MiniMax 简化示例
 *
 * 使用 Anthropic API 兼容模式调用 MiniMax 模型
 */

import { ChatAnthropic } from "@langchain/anthropic";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import * as dotenv from "dotenv";

// 加载环境变量
dotenv.config();

/**
 * 创建 MiniMax 模型实例 (使用 Anthropic API 兼容模式)
 */
function createMiniMaxModel(modelName: string = "MiniMax-M2.7") {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  const baseURL = process.env.ANTHROPIC_BASE_URL;

  if (!apiKey) {
    throw new Error("请设置 ANTHROPIC_API_KEY 环境变量");
  }

  return new ChatAnthropic({
    model: modelName,
    temperature: 0.7,
    topP: 1.0,
    apiKey: apiKey,
    clientOptions: {
      baseURL: baseURL,
    },
  });
}

/**
 * 基础对话示例
 */
async function basicChatExample() {
  console.log("📌 基础对话示例");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const model = createMiniMaxModel();

  const response = await model.invoke([
    new HumanMessage("你好，请用一句话介绍一下你自己。"),
  ]);

  console.log("用户: 你好，请用一句话介绍一下你自己。");
  console.log("MiniMax 回复:", response.content);
  console.log("\n");
}

/**
 * 带系统提示的对话示例
 */
async function systemPromptExample() {
  console.log("📌 带系统提示的对话示例");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const model = createMiniMaxModel();

  const systemPrompt = "你是一个专业的编程助手，精通 TypeScript 和各种前端技术。你的回答应该简洁、准确，并且用中文回复。";

  const response = await model.invoke([
    new SystemMessage(systemPrompt),
    new HumanMessage("什么是 TypeScript？它和 JavaScript 有什么区别？"),
  ]);

  console.log("系统提示: 你是一个专业的编程助手...");
  console.log("用户: 什么是 TypeScript？");
  console.log("MiniMax 回复:", response.content);
  console.log("\n");
}

/**
 * 多轮对话示例
 */
async function multiTurnChatExample() {
  console.log("📌 多轮对话示例");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const model = createMiniMaxModel();

  const messages = [
    new HumanMessage("我叫小明，是一名前端开发工程师。"),
    new HumanMessage("你还记得我的名字吗？"),
  ];

  for (const message of messages) {
    console.log("用户:", message.content);
    const response = await model.invoke([message]);
    console.log("MiniMax:", response.content);
    console.log();
  }
}

/**
 * 结构化输出示例
 */
async function structuredOutputExample() {
  console.log("📌 结构化输出示例");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const model = createMiniMaxModel();

  const prompt = `请分析以下编程语言的特点，并以 JSON 格式返回：
- name: 语言名称
- type: 类型（如：静态类型、动态类型）
- use_cases: 主要应用场景（数组）
- difficulty: 学习难度（简单/中等/困难）

语言：TypeScript

请只返回 JSON，不要有其他内容。`;

  const response = await model.invoke([new HumanMessage(prompt)]);

  console.log("用户: 分析 TypeScript 的特点...");
  console.log("MiniMax 回复:");
  console.log(response.content);

  try {
    const content = typeof response.content === 'string' ? response.content : String(response.content);
    const parsed = JSON.parse(content);
    console.log("\n解析后的结构化数据:");
    console.log(JSON.stringify(parsed, null, 2));
  } catch (e) {
    console.log("\n（JSON 解析可能失败，这是正常的）");
  }

  console.log("\n");
}

/**
 * 流式输出示例
 */
async function streamingChatExample() {
  console.log("📌 流式输出示例");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

  const model = createMiniMaxModel();

  const stream = await model.stream([
    new HumanMessage("请用三句话介绍一下 LangChain 框架。"),
  ]);

  console.log("MiniMax 流式回复:");
  console.log();
  for await (const chunk of stream) {
    const content = typeof chunk.content === 'string' ? chunk.content : String(chunk.content);
    process.stdout.write(content);
  }

  console.log("\n\n");
}

/**
 * 主函数
 */
async function main() {
  console.log("🚀 LangChain + MiniMax (Anthropic API 兼容模式) 模型示例\n");
  console.log("API: https://api.minimaxi.com/anthropic");
  console.log("注意: MiniMax 使用 GLM 系列模型后端\n");

  try {
    // 示例 1: 基础对话
    await basicChatExample();

    // 示例 2: 带系统提示的对话
    await systemPromptExample();

    // 示例 3: 多轮对话
    await multiTurnChatExample();

    // 示例 4: 结构化输出
    await structuredOutputExample();

    // 示例 5: 流式输出
    await streamingChatExample();

    console.log("✅ 所有示例执行完成!");
  } catch (error: any) {
    console.error("\n❌ 执行出错:", error.message);
    console.error("\n请检查:");
    console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
    console.error("2. API Key 是否正确");
    console.error("3. 网络连接是否正常");
    console.error("4. 账户余额是否充足");
  }
}

// 执行主函数
main();
