/**
 * LangChain + MiniMax 简化示例
 *
 * 这个版本使用 MiniMax 模型 (Anthropic API 兼容模式)
 */

import {ChatAnthropic} from "@langchain/anthropic";
import {HumanMessage} from "@langchain/core/messages";
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

    const conversation = [
        new HumanMessage("我喜欢编程，特别是 TypeScript。"),
        new HumanMessage("你能根据我的兴趣推荐一些学习资源吗？"),
    ];

    for (const message of conversation) {
        console.log("用户:", message.content);
        const response = await model.invoke([message]);
        console.log("GPT:", response.content);
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

    console.log("GPT 回复:");
    console.log(response.content);

    try {
        // 尝试解析 JSON
        const parsed = JSON.parse(response.content as string);
        console.log("\n解析后的结构化数据:");
        console.log(JSON.stringify(parsed, null, 2));
    } catch (e) {
        console.log("\n（JSON 解析失败，显示原始内容）");
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

    console.log("GPT 流式回复:");
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
    console.log("🚀 LangChain + MiniMax (Anthropic API) 模型示例\n");
    console.log("使用模型: claude-3-5-sonnet-20241022 (通过 MiniMax Anthropic API)");
    console.log("API 地址: https://api.minimaxi.com/anthropic\n");

    try {
        // 示例 1: 基础对话
        await basicChatExample();

        // 示例 2: 多轮对话
        await multiTurnChatExample();

        // 示例 3: 结构化输出
        await structuredOutputExample();

        // 示例 4: 流式输出
        await streamingChatExample();

        console.log("✅ 所有示例执行完成!");
    } catch (error: any) {
        console.error("\n❌ 执行出错:", error.message);
        console.error("\n请检查:");
        console.error("1. .env 文件中是否设置了 ANTHROPIC_API_KEY");
        console.error("2. API Key 是否正确");
        console.error("3. 网络连接是否正常");
    }
}

// 执行主函数
main();
