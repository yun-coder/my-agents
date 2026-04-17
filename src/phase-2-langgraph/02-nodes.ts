/**
 * ========================================
 * Phase 2: LangGraph 进阶
 * Demo 02: Nodes - 节点深入
 * ========================================
 *
 * 学习目标:
 * - 理解不同类型的 Nodes
 * - 掌握异步 Node 处理
 * - 学习 Node 间数据传递
 * - 实现复杂 Node 逻辑
 */

import { StateGraph, END } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基础 Node 类型
// ============================================================================

console.log("=== 1. 基础 Node 类型 ===\n");

const BasicState = Annotation.Root({
  value: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  label: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type BasicStateType = typeof BasicState.State;

// 同步 Node
const syncNode = (state: BasicStateType): Partial<BasicStateType> => {
  console.log(`[同步节点] 输入值: ${state.value}`);
  return { value: state.value * 2 };
};

// 异步 Node
const asyncNode = async (state: BasicStateType): Promise<Partial<BasicStateType>> => {
  console.log(`[异步节点] 输入值: ${state.value}`);
  await new Promise((resolve) => setTimeout(resolve, 100)); // 模拟异步操作
  return { value: state.value + 10 };
};

// 链式执行
const basicGraph = new StateGraph({ stateSchema: BasicState })
  .addNode("sync", syncNode)
  .addNode("async", asyncNode)
  .addEdge("__start__", "sync")
  .addEdge("sync", "async")
  .addEdge("async", END);

const basicApp = basicGraph.compile();

console.log("执行同步+异步节点链:");
const basicResult = await basicApp.invoke({ value: 5 });
console.log(`结果: ${basicResult.value} (5 × 2 + 10 = 20)`);

// ============================================================================
// 2. 条件更新 Node
// ============================================================================

console.log("\n=== 2. 条件更新 Node ===\n");

const ConditionalState = Annotation.Root({
  input: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  category: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ConditionalStateType = typeof ConditionalState.State;

const conditionalNode = (state: ConditionalStateType): Partial<ConditionalStateType> => {
  const input = state.input;
  let category = "normal";
  let result = "";

  if (input < 0) {
    category = "negative";
    result = `负数: ${Math.abs(input)}`;
  } else if (input === 0) {
    category = "zero";
    result = "零";
  } else if (input % 2 === 0) {
    category = "even";
    result = `偶数: ${input}`;
  } else {
    category = "odd";
    result = `奇数: ${input}`;
  }

  console.log(`[条件节点] 输入: ${input}, 分类: ${category}`);
  return { category, result };
};

const conditionalGraph = new StateGraph({ stateSchema: ConditionalState })
  .addNode("process", conditionalNode)
  .addEdge("__start__", "process")
  .addEdge("process", END);

const conditionalApp = conditionalGraph.compile();

console.log("测试不同输入:");
for (const num of [-5, 0, 4, 7]) {
  const result = await conditionalApp.invoke({ input: num });
  console.log(`  ${num} → ${result.result} (${result.category})`);
}

// ============================================================================
// 3. LLM 调用 Node
// ============================================================================

console.log("\n=== 3. LLM 调用 Node ===\n");

const LLMState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  summary: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  sentiment: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type LLMStateType = typeof LLMState.State;

// 摘要节点
const summaryNode = async (state: LLMStateType): Promise<Partial<LLMStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.3 });
  const lastMessage = state.messages[state.messages.length - 1];

  console.log(`[摘要节点] 处理: ${(lastMessage as HumanMessage).content}`);

  const prompt = `请用一句话总结以下内容: ${(lastMessage as HumanMessage).content}`;
  const response = await llm.invoke([new HumanMessage(prompt)]);

  return {
    summary: (response as AIMessage).content as string,
    messages: [response as AIMessage],
  };
};

// 情感分析节点
const sentimentNode = async (state: LLMStateType): Promise<Partial<LLMStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.1 });
  const lastMessage = state.messages[state.messages.length - 1];

  console.log(`[情感节点] 分析: ${(lastMessage as HumanMessage).content}`);

  const prompt = `分析以下文本的情感，只回答: 正面/负面/中性\n\n文本: ${(lastMessage as HumanMessage).content}`;
  const response = await llm.invoke([new HumanMessage(prompt)]);

  return {
    sentiment: (response as AIMessage).content as string,
    messages: [response as AIMessage],
  };
};

const llmGraph = new StateGraph({ stateSchema: LLMState })
  .addNode("summarize", summaryNode)
  .addNode("sentiment", sentimentNode)
  .addEdge("__start__", "summarize")
  .addEdge("summarize", "sentiment")
  .addEdge("sentiment", END);

const llmApp = llmGraph.compile();

console.log("\n执行 LLM 处理流程:");
const llmResult = await llmApp.invoke({
  messages: [new HumanMessage("这个新产品太棒了，我很喜欢！")],
});
console.log(`摘要: ${llmResult.summary}`);
console.log(`情感: ${llmResult.sentiment}`);

// ============================================================================
// 4. 错误处理 Node
// ============================================================================

console.log("\n=== 4. 错误处理 Node ===\n");

const ErrorHandlingState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  output: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  errors: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
});

type ErrorHandlingStateType = typeof ErrorHandlingState.State;

const processNode = async (state: ErrorHandlingStateType): Promise<Partial<ErrorHandlingStateType>> => {
  const input = state.input;
  console.log(`[处理节点] 输入: ${input}`);

  try {
    // 模拟可能出错的操作
    if (input.includes("error")) {
      throw new Error("检测到错误标记");
    }

    const result = input.toUpperCase();
    return { output: result };
  } catch (error) {
    const errorMsg = `处理失败: ${error}`;
    console.log(`[处理节点] ${errorMsg}`);
    return {
      errors: [errorMsg],
    };
  }
};

const errorHandlingGraph = new StateGraph({ stateSchema: ErrorHandlingState })
  .addNode("process", processNode)
  .addEdge("__start__", "process")
  .addEdge("process", END);

const errorApp = errorHandlingGraph.compile();

console.log("测试错误处理:");
const errorTests = ["hello world", "this has error in it", "success"];
for (const test of errorTests) {
  const result = await errorApp.invoke({ input: test });
  console.log(`  输入: "${test}"`);
  console.log(`  输出: ${result.output || "无"}`);
  console.log(`  错误: ${result.errors.length > 0 ? result.errors.join(", ") : "无"}`);
  console.log();
}

// ============================================================================
// 5. 并行 Node 执行
// ============================================================================

console.log("=== 5. 并行 Node 执行 ===\n");

const ParallelState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  length: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  words: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  uppercase: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  reversed: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ParallelStateType = typeof ParallelState.State;

// 并行执行的节点
const lengthNode = async (state: ParallelStateType): Promise<Partial<ParallelStateType>> => {
  console.log("[长度节点] 计算中...");
  await new Promise((resolve) => setTimeout(resolve, 50));
  return { length: state.input.length };
};

const wordCountNode = async (state: ParallelStateType): Promise<Partial<ParallelStateType>> => {
  console.log("[字数节点] 计算中...");
  await new Promise((resolve) => setTimeout(resolve, 50));
  return { words: state.input.split(/\s+/).length };
};

const uppercaseNode = async (state: ParallelStateType): Promise<Partial<ParallelStateType>> => {
  console.log("[大写节点] 转换中...");
  await new Promise((resolve) => setTimeout(resolve, 50));
  return { uppercase: state.input.toUpperCase() };
};

const reverseNode = async (state: ParallelStateType): Promise<Partial<ParallelStateType>> => {
  console.log("[反转节点] 反转中...");
  await new Promise((resolve) => setTimeout(resolve, 50));
  return { reversed: state.input.split("").reverse().join("") };
};

// 收集结果节点
const collectNode = (state: ParallelStateType): Partial<ParallelStateType> => {
  console.log("[收集节点] 汇总所有结果");
  return {};
};

const parallelGraph = new StateGraph({ stateSchema: ParallelState })
  .addNode("length", lengthNode)
  .addNode("words", wordCountNode)
  .addNode("uppercase", uppercaseNode)
  .addNode("reverse", reverseNode)
  .addNode("collect", collectNode)
  .addEdge("__start__", "length")
  .addEdge("__start__", "words")
  .addEdge("__start__", "uppercase")
  .addEdge("__start__", "reverse")
  .addEdge("length", "collect")
  .addEdge("words", "collect")
  .addEdge("uppercase", "collect")
  .addEdge("reverse", "collect")
  .addEdge("collect", END);

const parallelApp = parallelGraph.compile();

console.log("执行并行节点:");
const parallelResult = await parallelApp.invoke({ input: "Hello LangGraph" });
console.log("\n并行执行结果:");
console.log(`  长度: ${parallelResult.length}`);
console.log(`  字数: ${parallelResult.words}`);
console.log(`  大写: ${parallelResult.uppercase}`);
console.log(`  反转: ${parallelResult.reversed}`);

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 同步 Node - 直接返回状态更新");
console.log("2. 异步 Node - 使用 async/await");
console.log("3. 条件 Node - 根据输入执行不同逻辑");
console.log("4. LLM Node - 调用语言模型");
console.log("5. 错误处理 Node - try/catch 并记录错误");
console.log("6. 并行 Node - 多个节点同时执行");
console.log("\nNode 最佳实践:");
console.log("- 单一职责: 每个 Node 只做一件事");
console.log("- 幂等性: 相同输入产生相同输出");
console.log("- 错误处理: 优雅处理异常情况");
console.log("- 类型安全: 使用 TypeScript 类型");
console.log("- 可测试: Node 逻辑易于单元测试");

export {
  BasicState,
  ConditionalState,
  LLMState,
  ErrorHandlingState,
  ParallelState,
};
