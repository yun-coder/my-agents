/**
 * LangChain + MiniMax 模型 TypeScript 示例
 *
 * 使用 MiniMax Anthropic API 兼容模式
 * 文档: https://platform.minimaxi.com/docs/guides/quickstart-preparation
 */

import {ChatAnthropic} from "@langchain/anthropic";
import {HumanMessage, SystemMessage} from "@langchain/core/messages";
import * as dotenv from "dotenv";

// 加载环境变量
dotenv.config();

// ============ MiniMax 模型配置 ============

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
 * 获取天气工具函数
 */
function getWeather(city: string): string {
    return `${city} 今天天气晴朗，温度 25°C，空气质量良好`;
}

/**
 * 计算器工具函数
 */
function calculator(expression: string): string {
    try {
        // 使用安全的计算方式
        const result = Function('"use strict"; return (' + expression + ')')();
        return `计算结果: ${result}`;
    } catch (error) {
        return "计算错误，请检查表达式格式";
    }
}

/**
 * 获取当前时间工具函数
 */
function getCurrentTime(): string {
    const now = new Date();
    return `当前时间: ${now.toLocaleString('zh-CN', {timeZone: 'Asia/Shanghai'})}`;
}

// ============ 主函数 ============

async function main() {
    console.log("🚀 LangChain + MiniMax (Anthropic API) 模型示例\n");

    // 检查 API Key
    if (!process.env.ANTHROPIC_API_KEY) {
        console.error("❌ 请设置 ANTHROPIC_API_KEY 环境变量");
        console.log("在 .env 文件中添加:");
        console.log("ANTHROPIC_API_KEY=your_minimax_api_key_here");
        console.log("ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic");
        process.exit(1);
    }

    // 创建 MiniMax 模型
    const model = createMiniMaxModel("claude-3-5-sonnet-20241022");

    // ============ 示例 1: 基础对话 ============
    console.log("📌 示例 1: 基础对话");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    const basicResponse = await model.invoke([
        new HumanMessage("你好，请用一句话介绍一下你自己。"),
    ]);

    console.log("用户: 你好，请用一句话介绍一下你自己。");
    console.log("MiniMax 回复:", typeof basicResponse.content === 'string' ? basicResponse.content : String(basicResponse.content));
    console.log("");

    // ============ 示例 2: 带系统提示的对话 ============
    console.log("📌 示例 2: 带系统提示的对话");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    const systemPrompt = "你是一个专业的编程助手，精通 TypeScript 和各种前端技术。你的回答应该简洁、准确，并且用中文回复。";

    const systemResponse = await model.invoke([
        new SystemMessage(systemPrompt),
        new HumanMessage("什么是 TypeScript？它和 JavaScript 有什么区别？"),
    ]);

    console.log("系统提示: 你是一个专业的编程助手...");
    console.log("用户: 什么是 TypeScript？");
    console.log("MiniMax 回复:", typeof systemResponse.content === 'string' ? systemResponse.content : String(systemResponse.content));
    console.log("");

    // ============ 示例 3: 工具使用模拟 ============
    console.log("📌 示例 3: 工具使用（模拟）");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    // 模拟工具调用 - 在实际应用中，这应该由模型自动决策
    const toolUsePrompt = `用户想要查询天气。请使用以下工具：
- getWeather: 获取指定城市的天气信息

用户问题：北京的天气怎么样？

请直接调用工具并返回结果。`;

    const toolResponse = await model.invoke([
        new HumanMessage(toolUsePrompt),
    ]);

    // 这里我们直接调用工具函数来演示
    const weatherResult = getWeather("北京");
    console.log("工具调用结果:", weatherResult);
    console.log("模型响应:", typeof toolResponse.content === 'string' ? toolResponse.content.substring(0, 100) + "..." : String(toolResponse.content).substring(0, 100) + "...");
    console.log("");

    // ============ 示例 4: 数学计算 ============
    console.log("📌 示例 4: 数学计算");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    const mathPrompt = "帮我计算 25 * 8 + 100";

    const mathResponse = await model.invoke([
        new HumanMessage(mathPrompt),
    ]);

    console.log("用户:", mathPrompt);
    console.log("MiniMax 回复:", typeof mathResponse.content === 'string' ? mathResponse.content : String(mathResponse.content));
    console.log("实际结果:", calculator("25 * 8 + 100"));
    console.log("");

    // ============ 示例 5: 获取时间 ============
    console.log("📌 示例 5: 获取当前时间");
    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    const timeResponse = await model.invoke([
        new HumanMessage("现在几点了？"),
    ]);

    console.log("用户: 现在几点了？");
    console.log("MiniMax 回复:", typeof timeResponse.content === 'string' ? timeResponse.content : String(timeResponse.content));
    console.log("实际时间:", getCurrentTime());
    console.log("");

    console.log("✅ 所有示例执行完成!");
}

// 执行主函数
main().catch((error) => {
    console.error("\n❌ 执行出错:", error.message);
    console.error(error);
});

// ============ 导出 ============

export {createMiniMaxModel, getWeather, calculator, getCurrentTime};
