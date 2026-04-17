/**
 * ========================================
 * Phase 2: LangGraph 进阶
 * Demo 03: Edges - 边的连接与路由
 * ========================================
 *
 * 学习目标:
 * - 理解不同类型的 Edges
 * - 掌握普通边和条件边
 * - 学习复杂的路由逻辑
 * - 实现动态图结构
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";

// ============================================================================
// 1. 普通边 - 直接连接
// ============================================================================

console.log("=== 1. 普通边 (addEdge) ===\n");

const LinearState = Annotation.Root({
  step: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type LinearStateType = typeof LinearState.State;

const step1Node = async (state: LinearStateType): Promise<Partial<LinearStateType>> => {
  console.log("[步骤1] 执行中...");
  return { step: 1, result: "步骤1完成" };
};

const step2Node = async (state: LinearStateType): Promise<Partial<LinearStateType>> => {
  console.log("[步骤2] 执行中...");
  return { step: 2, result: `${state.result} → 步骤2完成` };
};

const step3Node = async (state: LinearStateType): Promise<Partial<LinearStateType>> => {
  console.log("[步骤3] 执行中...");
  return { step: 3, result: `${state.result} → 步骤3完成` };
};

// 线性流程图
const linearGraph = new StateGraph({ stateSchema: LinearState })
  .addNode("step1", step1Node)
  .addNode("step2", step2Node)
  .addNode("step3", step3Node)
  .addEdge(START, "step1")
  .addEdge("step1", "step2")
  .addEdge("step2", "step3")
  .addEdge("step3", END);

const linearApp = linearGraph.compile();

console.log("线性流程执行:");
const linearResult = await linearApp.invoke({});
console.log(`结果: ${linearResult.result}`);
console.log(`步骤: ${linearResult.step}`);

// ============================================================================
// 2. 条件边 - 动态路由
// ============================================================================

console.log("\n=== 2. 条件边 (addConditionalEdges) ===\n");

const RoutingState = Annotation.Root({
  score: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  },
  level: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  message: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type RoutingStateType = typeof RoutingState.State;

const evaluateNode = (state: RoutingStateType): Partial<RoutingStateType> => {
  const score = state.score;
  console.log(`[评估节点] 分数: ${score}`);
  return {};
};

// 路由函数
const routeByScore = (state: RoutingStateType): string => {
  const score = state.score;
  if (score >= 90) return "excellent";
  if (score >= 70) return "good";
  if (score >= 60) return "pass";
  return "fail";
};

// 不同等级的处理节点
const excellentNode = (state: RoutingStateType): Partial<RoutingStateType> => {
  console.log("→ 优秀路径");
  return { level: "优秀", message: "表现优异！" };
};

const goodNode = (state: RoutingStateType): Partial<RoutingStateType> => {
  console.log("→ 良好路径");
  return { level: "良好", message: "做得不错！" };
};

const passNode = (state: RoutingStateType): Partial<RoutingStateType> => {
  console.log("→ 及格路径");
  return { level: "及格", message: "刚好及格，继续努力！" };
};

const failNode = (state: RoutingStateType): Partial<RoutingStateType> => {
  console.log("→ 不及格路径");
  return { level: "不及格", message: "需要加强学习！" };
};

// 条件路由图
const routingGraph = new StateGraph({ stateSchema: RoutingState })
  .addNode("evaluate", evaluateNode)
  .addNode("excellent", excellentNode)
  .addNode("good", goodNode)
  .addNode("pass", passNode)
  .addNode("fail", failNode)
  .addEdge(START, "evaluate")
  .addConditionalEdges("evaluate", routeByScore, {
    excellent: "excellent",
    good: "good",
    pass: "pass",
    fail: "fail",
  })
  .addEdge("excellent", END)
  .addEdge("good", END)
  .addEdge("pass", END)
  .addEdge("fail", END);

const routingApp = routingGraph.compile();

console.log("测试不同分数的路由:");
const testScores = [95, 75, 65, 45];
for (const score of testScores) {
  console.log(`\n分数: ${score}`);
  const result = await routingApp.invoke({ score });
  console.log(`  等级: ${result.level}`);
  console.log(`  消息: ${result.message}`);
}

// ============================================================================
// 3. 循环边 - 重复执行
// ============================================================================

console.log("\n=== 3. 循环边 ===\n");

const LoopState = Annotation.Root({
  count: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  max: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 3,
  }),
  sum: Annotation<number>({
    reducer: (x, y) => (y !== undefined ? x + y : x),
    default: () => 0,
  }),
});

type LoopStateType = typeof LoopState.State;

const incrementNode = (state: LoopStateType): Partial<LoopStateType> => {
  const newCount = state.count + 1;
  console.log(`[递增] count: ${state.count} → ${newCount}`);
  return { count: newCount, sum: state.sum + newCount };
};

// 循环条件
const shouldContinue = (state: LoopStateType): string => {
  return state.count < state.max ? "continue" : "end";
};

const loopGraph = new StateGraph({ stateSchema: LoopState })
  .addNode("increment", incrementNode)
  .addEdge(START, "increment")
  .addConditionalEdges("increment", shouldContinue, {
    continue: "increment",
    end: END,
  });

const loopApp = loopGraph.compile();

console.log("执行循环 (max=3):");
const loopResult = await loopApp.invoke({ max: 3 });
console.log(`最终 count: ${loopResult.count}`);
console.log(`总和 (1+2+3): ${loopResult.sum}`);

// ============================================================================
// 4. 分支汇聚边
// ============================================================================

console.log("\n=== 4. 分支汇聚边 ===\n");

const BranchState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  processA: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  processB: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  final: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type BranchStateType = typeof BranchState.State;

const splitNode = (state: BranchStateType): Partial<BranchStateType> => {
  console.log(`[分裂节点] 输入: ${state.input}`);
  return {};
};

const processANode = (state: BranchStateType): Partial<BranchStateType> => {
  console.log("[处理A] 大写转换");
  return { processA: state.input.toUpperCase() };
};

const processBNode = (state: BranchStateType): Partial<BranchStateType> => {
  console.log("[处理B] 反转转换");
  return { processB: state.input.split("").reverse().join("") };
};

const mergeNode = (state: BranchStateType): Partial<BranchStateType> => {
  console.log("[合并节点] 汇聚结果");
  const result = `A: ${state.processA} | B: ${state.processB}`;
  return { final: result };
};

// 分支汇聚图
const branchGraph = new StateGraph({ stateSchema: BranchState })
  .addNode("split", splitNode)
  .addNode("processA", processANode)
  .addNode("processB", processBNode)
  .addNode("merge", mergeNode)
  .addEdge(START, "split")
  .addEdge("split", "processA")
  .addEdge("split", "processB")
  .addEdge("processA", "merge")
  .addEdge("processB", "merge")
  .addEdge("merge", END);

const branchApp = branchGraph.compile();

console.log("执行分支汇聚:");
const branchResult = await branchApp.invoke({ input: "hello" });
console.log(`最终结果: ${branchResult.final}`);

// ============================================================================
// 5. 复杂路由 - 多层条件
// ============================================================================

console.log("\n=== 5. 复杂多层路由 ===\n");

const ComplexState = Annotation.Root({
  category: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  priority: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  action: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ComplexStateType = typeof ComplexState.State;

const classifyNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log(`[分类] 类别: ${state.category}, 优先级: ${state.priority}`);
  return {};
};

// 第一层路由: 按类别
const routeByCategory = (state: ComplexStateType): string => {
  return state.category || "unknown";
};

// 第二层路由: 按优先级
const routeByPriority = (state: ComplexStateType): string => {
  return state.priority >= 5 ? "high" : "low";
};

// 处理节点
const techHighNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log("  → 技术类-高优先级");
  return { action: "技术类-高优先级处理" };
};

const techLowNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log("  → 技术类-低优先级");
  return { action: "技术类-低优先级处理" };
};

const businessHighNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log("  → 业务类-高优先级");
  return { action: "业务类-高优先级处理" };
};

const businessLowNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log("  → 业务类-低优先级");
  return { action: "业务类-低优先级处理" };
};

const unknownNode = (state: ComplexStateType): Partial<ComplexStateType> => {
  console.log("  → 未知类别");
  return { action: "未知类别处理" };
};

// 复杂路由图
const complexGraph = new StateGraph({ stateSchema: ComplexState })
  .addNode("classify", classifyNode)
  .addNode("tech_high", techHighNode)
  .addNode("tech_low", techLowNode)
  .addNode("business_high", businessHighNode)
  .addNode("business_low", businessLowNode)
  .addNode("unknown", unknownNode)
  .addEdge(START, "classify")
  .addConditionalEdges("classify", routeByCategory, {
    tech: "tech_router",
    business: "business_router",
    unknown: "unknown",
  })
  .addConditionalEdges("tech_router", routeByPriority, {
    high: "tech_high",
    low: "tech_low",
  })
  .addConditionalEdges("business_router", routeByPriority, {
    high: "business_high",
    low: "business_low",
  })
  .addEdge("tech_high", END)
  .addEdge("tech_low", END)
  .addEdge("business_high", END)
  .addEdge("business_low", END)
  .addEdge("unknown", END);

// 注意: 实际使用中需要为中间路由节点添加实现
// 这里简化示例，实际会更复杂

const complexApp = complexGraph.compile();

console.log("测试复杂路由:");
const complexTests = [
  { category: "tech", priority: 8 },
  { category: "tech", priority: 3 },
  { category: "business", priority: 7 },
  { category: "other", priority: 5 },
];

for (const test of complexTests) {
  console.log(`\n输入: ${JSON.stringify(test)}`);
  // const result = await complexApp.invoke(test);
  // console.log(`  动作: ${result.action}`);
}

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. addEdge() - 普通边，直接连接节点");
console.log("2. addConditionalEdges() - 条件边，动态路由");
console.log("3. START/END - 特殊节点，表示开始和结束");
console.log("4. 路由函数 - 返回目标节点名称");
console.log("5. 循环边 - 条件返回当前节点形成循环");
console.log("6. 分支汇聚 - 多个节点指向同一节点");
console.log("\nEdge 类型选择:");
console.log("- 线性流程 → addEdge");
console.log("- 条件分支 → addConditionalEdges");
console.log("- 循环执行 → 条件边返回自身");
console.log("- 并行处理 → 多节点从同一节点出发");
console.log("- 汇聚结果 → 多节点指向同一节点");

export {
  linearApp,
  routingApp,
  loopApp,
  branchApp,
};
