/**
 * ========================================
 * Phase 1: LangChain 基础
 * Demo 05: Basic Agent
 * ========================================
 *
 * 学习目标:
 * - 理解 Agent 的核心概念
 * - 实现基础 ReAct Agent
 * - 掌握 Agent 的思考-行动循环
 * - 学习 Agent 的调试和优化
 */

import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { HumanMessage, AIMessage, ToolMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义 Tools
// ============================================================================

console.log("=== 1. 定义 Agent Tools ===\n");

// 搜索工具
const search = tool(async ({ query }) => {
  // 模拟搜索结果
  const mockResults: Record<string, string> = {
    "TypeScript": "TypeScript 是一种由微软开发的自由和开源的编程语言。它是 JavaScript 的一个超集，而且本质上向这个语言添加了可选的静态类型和基于类的面向对象编程。",
    "React": "React 是一个用于构建用户界面的 JavaScript 库，由 Facebook 维护。",
    "LangChain": "LangChain 是一个用于开发由语言模型驱动的应用程序的框架。",
  };

  return mockResults[query] || `未找到关于 "${query}" 的搜索结果。`;
}, {
  name: "search",
  description: "搜索信息，用于查找知识、定义、概念等",
  schema: z.object({
    query: z.string().describe("搜索关键词"),
  }),
});

// 计算工具
const calculator = tool(async ({ expression }) => {
  try {
    // 安全的数学表达式计算 (仅支持基本运算)
    const sanitized = expression.replace(/[^0-9+\-*/().\s]/g, "");
    const result = Function(`"use strict"; return (${sanitized})`)();
    return `${expression} = ${result}`;
  } catch (error) {
    return `计算错误: ${error}`;
  }
}, {
  name: "calculator",
  description: "计算数学表达式，支持加减乘除和括号",
  schema: z.object({
    expression: z.string().describe("要计算的数学表达式"),
  }),
});

// 天气工具
const getWeather = tool(async ({ city }) => {
  const weatherData: Record<string, string> = {
    "北京": "北京今天: 晴，温度 15-25°C",
    "上海": "上海今天: 多云，温度 18-26°C",
    "广州": "广州今天: 阵雨，温度 22-30°C",
    "深圳": "深圳今天: 阴，温度 21-29°C",
  };
  return weatherData[city] || `抱歉，没有 ${city} 的天气信息。`;
}, {
  name: "get_weather",
  description: "查询指定城市的天气情况",
  schema: z.object({
    city: z.string().describe("城市名称"),
  }),
});

const tools = [search, calculator, getWeather];

console.log("可用工具:");
tools.forEach((t) => console.log(`  - ${t.name}: ${t.description}`));

// ============================================================================
// 2. ReAct Agent Prompt
// ============================================================================

console.log("\n=== 2. ReAct Agent Prompt ===\n");

const reactPrompt = ChatPromptTemplate.fromMessages([
  [
    "system",
    `你是一个使用 ReAct (推理 + 行动) 方法的 AI 助手。

可用工具:
${tools.map((t) => `- ${t.name}: ${t.description}`).join("\n")}

工作流程:
1. 思考 (Thought): 分析用户的问题
2. 行动 (Action): 选择并执行工具
3. 观察 (Observation): 查看工具返回结果
4. 重复: 直到获得足够信息，给出最终答案

输出格式:
Thought: <你的思考>
Action: <工具名称>
Action Input: <参数 JSON>

或 (获得足够信息时):
Thought: <你的思考>
Final Answer: <最终答案>

示例:
Question: 北京今天天气怎么样？
Thought: 用户问的是北京的天气，我应该使用 get_weather 工具
Action: get_weather
Action Input: {{"city": "北京"}}
Observation: 北京今天: 晴，温度 15-25°C
Thought: 我已经获得了北京的天气信息，可以给用户最终答案了
Final Answer: 北京今天是晴天，温度在 15 到 25 摄氏度之间。`,
  ],
  ["placeholder", "{chat_history}"],
  ["human", "{input}"],
  ["placeholder", "{agent_scratchpad}"],
]);

// ============================================================================
// 3. Agent 执行循环
// ============================================================================

console.log("=== 3. Agent 执行 ===\n");

interface AgentStep {
  thought: string;
  action?: string;
  actionInput?: string;
  observation?: string;
  finalAnswer?: string;
}

class ReActAgent {
  private llm: any;
  private tools: Map<string, any>;
  private maxIterations: number;
  private history: Array<HumanMessage | AIMessage | ToolMessage> = [];

  constructor(tools: any[], maxIterations: number = 5) {
    this.llm = createClaudeSonnet({ temperature: 0.1 });
    this.maxIterations = maxIterations;
    this.tools = new Map();

    for (const tool of tools) {
      this.tools.set(tool.name, tool);
    }
  }

  async run(input: string): Promise<string> {
    console.log(`\n🤖 Agent 开始执行: ${input}\n`);
    console.log("─".repeat(60));

    let currentInput = input;
    const steps: AgentStep[] = [];

    for (let iteration = 0; iteration < this.maxIterations; iteration++) {
      console.log(`\n[迭代 ${iteration + 1}/${this.maxIterations}]`);

      // 构建 prompt
      const agentScratchpad = this.formatScratchpad(steps);
      const promptValue = await reactPrompt.formatMessages({
        input: currentInput,
        chat_history: this.history,
        agent_scratchpad: agentScratchpad,
      });

      // 调用 LLM
      const response = await this.llm.invoke(promptValue);
      const responseText = response.content as string;

      console.log(`\nLLM 响应:\n${responseText}`);

      // 解析响应
      const step = this.parseResponse(responseText);
      steps.push(step);

      // 检查是否有最终答案
      if (step.finalAnswer) {
        console.log("\n" + "─".repeat(60));
        console.log(`✅ 最终答案: ${step.finalAnswer}`);
        console.log("─".repeat(60));

        // 保存到历史
        this.history.push(new HumanMessage(input));
        this.history.push(new AIMessage(step.finalAnswer));

        return step.finalAnswer;
      }

      // 执行工具
      if (step.action && step.actionInput) {
        console.log(`\n🔧 执行工具: ${step.action}`);
        console.log(`   参数: ${step.actionInput}`);

        const tool = this.tools.get(step.action);
        if (!tool) {
          step.observation = `错误: 未找到工具 ${step.action}`;
        } else {
          try {
            const toolInput = JSON.parse(step.actionInput);
            step.observation = await tool.invoke(toolInput);
          } catch (error) {
            step.observation = `工具执行错误: ${error}`;
          }
        }

        console.log(`   结果: ${step.observation}`);

        // 添加工具消息到历史
        this.history.push(new ToolMessage(step.observation, this.history.length.toString()));
      }
    }

    return "错误: 达到最大迭代次数仍未得到答案";
  }

  private parseResponse(response: string): AgentStep {
    const step: AgentStep = { thought: "" };

    // 提取 Thought
    const thoughtMatch = response.match(/Thought:\s*(.+?)(?=\n(?:Action|Final Answer)|$)/s);
    if (thoughtMatch) {
      step.thought = thoughtMatch[1].trim();
    }

    // 提取 Final Answer
    const finalMatch = response.match(/Final Answer:\s*(.+)$/s);
    if (finalMatch) {
      step.finalAnswer = finalMatch[1].trim();
      return step;
    }

    // 提取 Action
    const actionMatch = response.match(/Action:\s*(\w+)/);
    if (actionMatch) {
      step.action = actionMatch[1];
    }

    // 提取 Action Input
    const inputMatch = response.match(/Action Input:\s*(\{.+\})/s);
    if (inputMatch) {
      step.actionInput = inputMatch[1];
    }

    return step;
  }

  private formatScratchpad(steps: AgentStep[]): string {
    return steps
      .map((step) => {
        let output = `Thought: ${step.thought}\n`;
        if (step.action) {
          output += `Action: ${step.action}\n`;
          output += `Action Input: ${step.actionInput}\n`;
        }
        if (step.observation) {
          output += `Observation: ${step.observation}\n`;
        }
        return output;
      })
      .join("\n");
  }

  getHistory() {
    return this.history;
  }

  clearHistory() {
    this.history = [];
  }
}

// ============================================================================
// 4. 测试 Agent
// ============================================================================

const agent = new ReActAgent(tools);

// 测试 1: 简单问题
console.log("\n" + "=".repeat(60));
console.log("测试 1: 简单计算");
console.log("=".repeat(60));
await agent.run("100 乘以 25 等于多少？");

// 测试 2: 复杂问题
console.log("\n" + "=".repeat(60));
console.log("测试 2: 信息查询");
console.log("=".repeat(60));
await agent.run("什么是 TypeScript？");

// 测试 3: 多步骤问题
console.log("\n" + "=".repeat(60));
console.log("测试 3: 多步骤问题");
console.log("=".repeat(60));
await agent.run("北京和上海今天天气怎么样？");

// ============================================================================
// 5. 带对话历史的 Agent
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("测试 4: 多轮对话");
console.log("=".repeat(60));

await agent.run("我的名字是小明");
console.log("\n--- 对话历史 ---");
console.log(`历史消息数: ${agent.getHistory().length}`);

await agent.run("我叫什么名字？");

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. Agent 是使用 LLM 决定行动的系统");
console.log("2. ReAct 模式: Thought → Action → Observation 循环");
console.log("3. Tools 扩展了 LLM 的能力边界");
console.log("4. Agent 可以处理复杂的多步骤任务");
console.log("5. 对话历史使 Agent 具有上下文记忆");
console.log("\nAgent 的优势:");
console.log("- 自主决策: 根据情况选择合适的行为");
console.log("- 工具使用: 调用外部 API 和函数");
console.log("- 推理能力: 一步步解决复杂问题");
console.log("- 可扩展: 容易添加新的工具和能力");

export { ReActAgent, tools };
