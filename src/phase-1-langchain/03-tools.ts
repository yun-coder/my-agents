/**
 * ========================================
 * Phase 1: LangChain 基础
 * Demo 03: Tools & Function Calling
 * ========================================
 *
 * 学习目标:
 * - 理解 Tool 的概念和作用
 * - 创建自定义 Tool
 * - 使用 StructuredTool 处理复杂参数
 * - 实现带 Tools 的 Agent
 */

import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { createClaudeSonnet } from "../shared/llm";
import { BaseMessage, HumanMessage, AIMessage, ToolMessage } from "@langchain/core/messages";

// ============================================================================
// 1. 简单 Tool - 无参数
// ============================================================================

console.log("=== 1. 简单 Tool ===\n");

const getCurrentTime = tool(async () => {
  const now = new Date();
  return `当前时间: ${now.toLocaleString("zh-CN")}`;
}, {
  name: "get_current_time",
  description: "获取当前日期和时间",
});

const timeResult = await getCurrentTime.invoke({});
console.log("Tool 调用结果:", timeResult);

// ============================================================================
// 2. 带参数的 Tool - 使用 Zod 验证
// ============================================================================

console.log("\n=== 2. 带参数的 Tool ===\n");

const calculator = tool(async ({ a, b, operation }) => {
  const numA = Number(a);
  const numB = Number(b);

  switch (operation) {
    case "add":
      return `${numA} + ${numB} = ${numA + numB}`;
    case "subtract":
      return `${numA} - ${numB} = ${numA - numB}`;
    case "multiply":
      return `${numA} × ${numB} = ${numA * numB}`;
    case "divide":
      if (numB === 0) return "错误: 除数不能为零";
      return `${numA} ÷ ${numB} = ${numA / numB}`;
    default:
      return `未知操作: ${operation}`;
  }
}, {
  name: "calculator",
  description: "执行基本数学运算",
  schema: z.object({
    a: z.number().describe("第一个数字"),
    b: z.number().describe("第二个数字"),
    operation: z.enum(["add", "subtract", "multiply", "divide"]).describe("运算类型"),
  }),
});

const calcResult = await calculator.invoke({
  a: 10,
  b: 5,
  operation: "multiply",
});
console.log("计算器 Tool 结果:", calcResult);

// ============================================================================
// 3. 复杂 Tool - 天气查询
// ============================================================================

console.log("\n=== 3. 复杂 Tool - 天气查询 ===\n");

// 模拟天气数据库
const weatherDatabase: Record<string, { temp: number; condition: string; humidity: number }> = {
  "北京": { temp: 25, condition: "晴", humidity: 45 },
  "上海": { temp: 28, condition: "多云", humidity: 65 },
  "广州": { temp: 32, condition: "阵雨", humidity: 80 },
  "深圳": { temp: 30, condition: "阴", humidity: 70 },
  "杭州": { temp: 26, condition: "晴", humidity: 55 },
};

const getWeather = tool(async ({ city }) => {
  const data = weatherDatabase[city];
  if (!data) {
    return `抱歉，没有找到 ${city} 的天气信息。`;
  }
  return `${city} 当前天气: 温度 ${data.temp}°C，${data.condition}，湿度 ${data.humidity}%`;
}, {
  name: "get_weather",
  description: "获取指定城市的当前天气信息",
  schema: z.object({
    city: z.string().describe("城市名称，如: 北京、上海、广州"),
  }),
});

const weatherResult = await getWeather.invoke({ city: "北京" });
console.log("天气查询结果:", weatherResult);

// ============================================================================
// 4. 文件操作 Tool
// ============================================================================

console.log("\n=== 4. 文件操作 Tool ===\n");

const readFile = tool(async ({ filename, content }) => {
  // 模拟文件写入
  return `成功写入文件: ${filename}\n内容: ${content}\n文件大小: ${content.length} 字节`;
}, {
  name: "write_file",
  description: "将内容写入文件",
  schema: z.object({
    filename: z.string().describe("文件名"),
    content: z.string().describe("文件内容"),
  }),
});

const fileResult = await readFile.invoke({
  filename: "example.txt",
  content: "Hello, LangChain!",
});
console.log("文件操作结果:", fileResult);

// ============================================================================
// 5. 多 Tool 组合
// ============================================================================

console.log("\n=== 5. 多 Tool 组合 ===\n");

// 创建工具列表
const availableTools = [getCurrentTime, calculator, getWeather, readFile];

console.log("可用工具列表:");
availableTools.forEach((t) => {
  console.log(`- ${t.name}: ${t.description}`);
});

// ============================================================================
// 6. 手动实现 Tool 调用流程
// ============================================================================

console.log("\n=== 6. 手动 Tool 调用流程 ===\n");

const llm = createClaudeSonnet({ temperature: 0.3 });

// 创建带 tool 说明的 prompt
const toolPrompt = ChatPromptTemplate.fromMessages([
  ["system", `你是一个有帮助的助手。你可以使用以下工具:

${availableTools.map((t) => `- ${t.name}: ${t.description}`).join("\n")}

当你需要使用工具时，请按以下格式响应:
Tool: <工具名称>
Input: <JSON 格式的参数>

示例:
Tool: get_weather
Input: {"city": "北京"}`],
  ["human", "{input}"],
  ["placeholder", "{chat_history}"],
]);

const toolChain = toolPrompt.pipe(llm);

const userQuestion = "北京现在天气怎么样？";
console.log(`用户问题: ${userQuestion}\n`);

// 第一次 LLM 调用
const firstResponse = await toolChain.invoke({
  input: userQuestion,
  chat_history: [],
});

console.log("LLM 响应:");
console.log(firstResponse.content);

// 解析工具调用 (简化版，实际需要更复杂的解析)
const responseText = firstResponse.content as string;
if (responseText.includes("Tool:")) {
  const toolName = responseText.match(/Tool:\s*(\w+)/)?.[1];
  const inputMatch = responseText.match(/Input:\s*(\{.*\})/);
  const toolInput = inputMatch ? JSON.parse(inputMatch[1]) : {};

  console.log(`\n解析到工具调用: ${toolName}`);
  console.log(`工具参数:`, toolInput);

  // 执行工具
  let toolResult = "";
  if (toolName === "get_weather") {
    toolResult = await getWeather.invoke(toolInput);
  }

  console.log(`\n工具执行结果: ${toolResult}`);

  // 第二次 LLM 调用 - 包含工具结果
  const secondResponse = await toolChain.invoke({
    input: userQuestion,
    chat_history: [
      new HumanMessage(userQuestion),
      firstResponse,
      new ToolMessage(toolResult, firstResponse.tool_calls?.[0]?.id || ""),
    ],
  });

  console.log("\n最终响应:");
  console.log(secondResponse.content);
}

// ============================================================================
// 总结
// ============================================================================

console.log("\n=== 本节要点总结 ===");
console.log("1. tool() 函数 - 创建自定义工具");
console.log("2. Zod schema - 定义工具参数和验证");
console.log("3. 工具描述 - LLM 根据描述选择合适的工具");
console.log("4. Tool 调用流程: LLM 解析 → 执行 Tool → 返回结果 → LLM 生成答案");
console.log("5. 多工具协作 - 提供工具列表让 LLM 选择");

export {
  getCurrentTime,
  calculator,
  getWeather,
  readFile,
  availableTools,
};
