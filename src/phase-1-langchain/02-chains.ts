/**
 * ========================================
 * Phase 1: LangChain 基础
 * Demo 02: Chains - 链式调用组合
 * ========================================
 *
 * 学习目标:
 * - 理解 LCEL (LangChain Expression Language)
 * - 掌握 Sequential Chain 顺序执行
 * - 学习条件分支和路由
 * - 使用 RunnablePassthrough 和 RunnableLambda
 */

import { ChatPromptTemplate } from "@langchain/core/prompts";
import {
  RunnablePassthrough,
  RunnableSequence,
  RunnableLambda,
} from "@langchain/core/runnables";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基础 Chain: Prompt | LLM | Parser
// ============================================================================

console.log("=== 1. 基础 Chain ===\n");

const llm = createClaudeSonnet({ temperature: 0.7 });

// 创建最简单的 chain
const simpleChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个有帮助的助手。"],
  ["human", "{input}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

const result1 = await simpleChain.invoke({ input: "什么是 LangChain？" });
console.log("简单 Chain 结果:", result1);

// ============================================================================
// 2. RunnablePassthrough - 传递数据
// ============================================================================

console.log("\n=== 2. RunnablePassthrough ===\n");

// RunnablePassthrough 让数据流通过，同时可以添加新字段
const passThroughChain = RunnableSequence.from([
  {
    // 保留原始输入
    input: RunnablePassthrough(),
    // 添加新字段
    upper: (x: { input: string }) => x.input.toUpperCase(),
    lower: (x: { input: string }) => x.input.toLowerCase(),
    length: (x: { input: string }) => x.input.length,
  },
]);

const passResult = await passThroughChain.invoke({ input: "Hello World" });
console.log("Passthrough 结果:", passResult);

// ============================================================================
// 3. RunnableLambda - 自定义处理函数
// ============================================================================

console.log("\n=== 3. RunnableLambda ===\n");

// 创建自定义处理函数
const preprocess = RunnableLambda.from(async (input: { text: string }) => {
  console.log("预处理: 去除首尾空格");
  return { text: input.text.trim() };
});

const postprocess = RunnableLambda.from(async (output: string) => {
  console.log("后处理: 添加总结标记");
  return `【总结】${output}`;
});

const lambdaChain = preprocess
  .pipe(
    ChatPromptTemplate.fromMessages([
      ["system", "你是一个简洁的总结助手。"],
      ["human", "请用一句话总结: {text}"],
    ])
  )
  .pipe(llm)
  .pipe(new StringOutputParser())
  .pipe(postprocess);

const lambdaResult = await lambdaChain.invoke({
  text: "  人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。  ",
});
console.log("\nLambda Chain 结果:", lambdaResult);

// ============================================================================
// 4. Sequential Chain - 多步骤处理
// ============================================================================

console.log("\n=== 4. Sequential Chain ===\n");

// 步骤 1: 提取关键信息
const extractChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个信息提取专家。请提取文本中的关键信息。"],
  ["human", "从以下文本中提取关键信息:\n\n{text}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

// 步骤 2: 翻译成英文
const translateChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个专业翻译。"],
  ["human", "将以下内容翻译成英文:\n\n{summary}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

// 组合两个 chain
const sequentialChain = RunnableSequence.from([
  {
    text: (input: { text: string }) => input.text,
    summary: extractChain,
  },
  {
    translated: translateChain,
    originalSummary: (prev: { summary: string }) => prev.summary,
  },
]);

const seqResult = await sequentialChain.invoke({
  text: "北京是中国的首都，有着三千多年的历史。",
});
console.log("Sequential Chain 结果:");
console.log("原文总结:", seqResult.originalSummary);
console.log("英文翻译:", seqResult.translated);

// ============================================================================
// 5. 并行处理
// ============================================================================

console.log("\n=== 5. 并行处理 ===\n");

// 同时执行多个任务
const parallelChain = RunnableSequence.from([
  {
    input: (input: { text: string }) => input.text,
  },
  {
    // 这三个任务会并行执行
    sentiment: ChatPromptTemplate.fromMessages([
      ["system", "分析情感，只回答: 正面/负面/中性"],
      ["human", "{input}"],
    ])
      .pipe(llm)
      .pipe(new StringOutputParser()),
    keywords: ChatPromptTemplate.fromMessages([
      ["system", "提取3-5个关键词，用逗号分隔"],
      ["human", "{input}"],
    ])
      .pipe(llm)
      .pipe(new StringOutputParser()),
    category: ChatPromptTemplate.fromMessages([
      ["system", "分类: 科技/娱乐/体育/政治/其他"],
      ["human", "{input}"],
    ])
      .pipe(llm)
      .pipe(new StringOutputParser()),
  },
]);

const parallelResult = await parallelChain.invoke({
  text: "新款 iPhone 发布了，性能提升显著，但价格也不便宜。",
});
console.log("并行处理结果:");
console.log("情感:", parallelResult.sentiment);
console.log("关键词:", parallelResult.keywords);
console.log("分类:", parallelResult.category);

// ============================================================================
// 6. 条件路由
// ============================================================================

console.log("\n=== 6. 条件路由 ===\n");

// 定义不同类型的处理函数
const mathChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个数学专家。"],
  ["human", "解决这个数学问题: {input}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

const historyChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个历史专家。"],
  ["human", "回答这个历史问题: {input}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

const generalChain = ChatPromptTemplate.fromMessages([
  ["system", "你是一个有帮助的助手。"],
  ["human", "{input}"],
])
  .pipe(llm)
  .pipe(new StringOutputParser());

// 路由函数
const routeFunction = async (input: { input: string }): Promise<string> => {
  const text = input.input.toLowerCase();
  if (text.includes("计算") || text.includes("数学") || /\d+[\+\-\*\/]\d+/.test(text)) {
    return "math";
  } else if (text.includes("历史") || text.includes("朝代") || text.includes("战争")) {
    return "history";
  } else {
    return "general";
  }
};

// 创建路由 chain
const routerChain = RunnableSequence.from([
  RunnablePassthrough.assign({
    route: routeFunction,
  }),
  async (input: { input: string; route: string }) => {
    switch (input.route) {
      case "math":
        return mathChain.invoke(input);
      case "history":
        return historyChain.invoke(input);
      default:
        return generalChain.invoke(input);
    }
  },
]);

const routeResult1 = await routerChain.invoke({ input: "计算 123 * 456" });
console.log("路由结果 1 (数学):", routeResult1);

const routeResult2 = await routerChain.invoke({ input: "三国演义是什么时候写的？" });
console.log("\n路由结果 2 (历史):", routeResult2);

// ============================================================================
// 总结
// ============================================================================

console.log("\n=== 本节要点总结 ===");
console.log("1. pipe() - 使用 LCEL 连接组件");
console.log("2. RunnablePassthrough - 传递数据不变");
console.log("3. RunnableLambda - 自定义处理逻辑");
console.log("4. RunnableSequence.from() - 创建复杂序列");
console.log("5. 并行执行 - 对象中多个字段并行处理");
console.log("6. 条件路由 - 根据输入动态选择处理流程");

export {
  simpleChain,
  passThroughChain,
  lambdaChain,
  sequentialChain,
  parallelChain,
  routerChain,
};
