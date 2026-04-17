/**
 * ========================================
 * Phase 2: LangGraph 进阶
 * Demo 01: StateGraph - 状态图基础
 * ========================================
 *
 * 学习目标:
 * - 理解 StateGraph 的核心概念
 * - 掌握 State 定义和管理
 * - 学习 Node 和 Edge 的使用
 * - 构建第一个状态图
 */

import { StateGraph, END } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义 State
// ============================================================================

console.log("=== 1. 定义 State ===\n");

// 使用 Annotation 定义状态 (推荐方式)
const AgentState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  output: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type AppState = typeof AgentState.State;

console.log("State 定义完成:");
console.log("- messages: 消息历史 (累加)");
console.log("- input: 用户输入 (覆盖)");
console.log("- output: 输出结果 (覆盖)");

// ============================================================================
// 2. 定义 Nodes
// ============================================================================

console.log("\n=== 2. 定义 Nodes ===\n");

// 节点 1: 处理输入
const inputNode = async (state: AppState): Promise<Partial<AppState>> => {
  console.log(`[输入节点] 处理: ${state.input}`);
  return {
    messages: [new HumanMessage(state.input || "")],
  };
};

// 节点 2: LLM 处理
const llmNode = async (state: AppState): Promise<Partial<AppState>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });
  const messages = state.messages;

  console.log(`[LLM节点] 处理 ${messages.length} 条消息`);

  const response = await llm.invoke(messages);
  return {
    messages: [response as AIMessage],
    output: response.content as string,
  };
};

// 节点 3: 格式化输出
const outputNode = async (state: AppState): Promise<Partial<AppState>> => {
  console.log(`[输出节点] 格式化结果`);
  const formatted = `回答: ${state.output}`;
  return {
    output: formatted,
  };
};

console.log("节点定义完成:");
console.log("- inputNode: 处理用户输入");
console.log("- llmNode: 调用 LLM");
console.log("- outputNode: 格式化输出");

// ============================================================================
// 3. 构建 Graph
// ============================================================================

console.log("\n=== 3. 构建 Graph ===\n");

const graph = new StateGraph({ stateSchema: AgentState })
  .addNode("input", inputNode)
  .addNode("llm", llmNode)
  .addNode("output", outputNode)
  .addEdge("__start__", "input")
  .addEdge("input", "llm")
  .addEdge("llm", "output")
  .addEdge("output", END);

const app = graph.compile();

console.log("Graph 构建完成:");
console.log("  __start__ → input → llm → output → END");

// ============================================================================
// 4. 执行 Graph
// ============================================================================

console.log("\n=== 4. 执行 Graph ===\n");

// 第一次运行
console.log("─".repeat(50));
const result1 = await app.invoke({
  input: "什么是 TypeScript？",
});

console.log("\n最终状态:");
console.log("- messages:", result1.messages.length, "条");
console.log("- output:", result1.output?.substring(0, 100), "...");

// 第二次运行 - 状态累积
console.log("\n─".repeat(50));
const result2 = await app.invoke({
  input: "它和 JavaScript 有什么区别？",
  ...result1, // 传递之前的状态
});

console.log("\n最终状态:");
console.log("- messages:", result2.messages.length, "条 (历史消息累积)");
console.log("- output:", result2.output?.substring(0, 100), "...");

// ============================================================================
// 5. 流式输出
// ============================================================================

console.log("\n=== 5. 流式输出 ===\n");

console.log("─".repeat(50));
console.log("流式执行 (逐步输出每个节点):");

for await (const event of await app.stream(
  { input: "用一句话介绍 LangGraph" },
  { subgraphs: false }
)) {
  for (const [nodeName, nodeOutput] of Object.entries(event)) {
    console.log(`\n[${nodeName}]`);
    if (nodeName === "llm" && nodeOutput.messages) {
      const lastMsg = nodeOutput.messages[nodeOutput.messages.length - 1];
      console.log("  响应:", (lastMsg as AIMessage).content?.toString().substring(0, 80), "...");
    }
  }
}

// ============================================================================
// 6. 多分支 Graph
// ============================================================================

console.log("\n=== 6. 多分支 Graph ===\n");

// 定义不同类型的处理状态
const ProcessingState = Annotation.Root({
  text: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  category: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ProcessingStateType = typeof ProcessingState.State;

// 分类节点
const classifyNode = async (state: ProcessingStateType): Promise<Partial<ProcessingStateType>> => {
  const text = state.text.toLowerCase();
  let category = "general";

  if (text.includes("计算") || /\d+/.test(text)) {
    category = "math";
  } else if (text.includes("天气") || text.includes("温度")) {
    category = "weather";
  } else if (text.includes("新闻") || text.includes("资讯")) {
    category = "news";
  }

  console.log(`[分类] 文本分类为: ${category}`);
  return { category };
};

// 不同类型的结果生成节点
const mathHandler = async (state: ProcessingStateType): Promise<Partial<ProcessingStateType>> => {
  console.log(`[数学处理] ${state.text}`);
  return { result: `数学结果: 已识别为数学相关问题` };
};

const weatherHandler = async (state: ProcessingStateType): Promise<Partial<ProcessingStateType>> => {
  console.log(`[天气处理] ${state.text}`);
  return { result: "天气结果: 今天晴朗，温度 20-25°C" };
};

const newsHandler = async (state: ProcessingStateType): Promise<Partial<ProcessingStateType>> => {
  console.log(`[新闻处理] ${state.text}`);
  return { result: "新闻结果: 今日要闻..." };
};

const generalHandler = async (state: ProcessingStateType): Promise<Partial<ProcessingStateType>> => {
  console.log(`[通用处理] ${state.text}`);
  return { result: "通用回答: 我收到了你的消息" };
};

// 条件路由函数
const routeByCategory = (state: ProcessingStateType): string => {
  return state.category || "general";
};

// 构建多分支图
const multiBranchGraph = new StateGraph({ stateSchema: ProcessingState })
  .addNode("classify", classifyNode)
  .addNode("math", mathHandler)
  .addNode("weather", weatherHandler)
  .addNode("news", newsHandler)
  .addNode("general", generalHandler)
  .addEdge("__start__", "classify")
  .addConditionalEdges("classify", routeByCategory, {
    math: "math",
    weather: "weather",
    news: "news",
    general: "general",
  })
  .addEdge("math", END)
  .addEdge("weather", END)
  .addEdge("news", END)
  .addEdge("general", END);

const multiApp = multiBranchGraph.compile();

console.log("多分支 Graph 构建完成");
console.log("测试不同输入:");

const testInputs = [
  "计算 123 + 456",
  "今天天气怎么样",
  "有什么新闻",
  "你好",
];

for (const input of testInputs) {
  console.log(`\n输入: ${input}`);
  const result = await multiApp.invoke({ text: input });
  console.log(`输出: ${result.result}`);
}

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. Annotation.Root() - 定义状态结构");
console.log("2. StateGraph - 创建状态图");
console.log("3. addNode() - 添加处理节点");
console.log("4. addEdge() - 添加连接边");
console.log("5. addConditionalEdges() - 添加条件边");
console.log("6. compile() - 编译为可执行应用");
console.log("7. invoke() - 执行图");
console.log("8. stream() - 流式执行");
console.log("\nStateGraph 的优势:");
console.log("- 状态管理: 自动管理复杂状态");
console.log("- 可视化: 清晰的流程结构");
console.log("- 可扩展: 容易添加新节点和逻辑");
console.log("- 持久化: 支持检查点和恢复");

export { AgentState, AppState, graph, app, multiBranchGraph, multiApp };
