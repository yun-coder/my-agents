/**
 * ========================================
 * Phase 2: LangGraph 进阶
 * Demo 04: Conditional Logic - 条件逻辑
 * ========================================
 *
 * 学习目标:
 * - 掌握复杂的条件判断逻辑
 * - 学习状态检查和控制流
 * - 实现智能决策系统
 * - 构建自适应工作流
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 基于阈值的条件判断
// ============================================================================

console.log("=== 1. 基于阈值的条件判断 ===\n");

const ThresholdState = Annotation.Root({
  value: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  status: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  action: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ThresholdStateType = typeof ThresholdState.State;

const evaluateThreshold = (state: ThresholdStateType): Partial<ThresholdStateType> => {
  const value = state.value;
  let status = "normal";
  let action = "monitor";

  if (value > 100) {
    status = "critical";
    action = "alert";
  } else if (value > 75) {
    status = "warning";
    action = "notify";
  } else if (value < 25) {
    status = "low";
    action = "restock";
  }

  console.log(`[评估] 值: ${value}, 状态: ${status}, 动作: ${action}`);
  return { status, action };
};

const thresholdGraph = new StateGraph({ stateSchema: ThresholdState })
  .addNode("evaluate", evaluateThreshold)
  .addEdge(START, "evaluate")
  .addEdge("evaluate", END);

const thresholdApp = thresholdGraph.compile();

console.log("测试阈值判断:");
const thresholds = [120, 80, 50, 20];
for (const t of thresholds) {
  const result = await thresholdApp.invoke({ value: t });
  console.log(`  ${t} → ${result.status} (${result.action})`);
}

// ============================================================================
// 2. 多条件组合判断
// ============================================================================

console.log("\n=== 2. 多条件组合判断 ===\n");

const ComboState = Annotation.Root({
  score: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  attempts: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  timeElapsed: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  decision: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type ComboStateType = typeof ComboState.State;

const evaluateCombo = (state: ComboStateType): Partial<ComboStateType> => {
  const { score, attempts, timeElapsed } = state;
  let decision = "continue";

  // 多条件组合
  if (score >= 90 && attempts < 3) {
    decision = "success";
  } else if (attempts >= 5 || timeElapsed > 60) {
    decision = "timeout";
  } else if (score < 30 && attempts >= 3) {
    decision = "failure";
  }

  console.log(`[组合判断] 分数:${score}, 尝试:${attempts}, 时间:${timeElapsed}s → ${decision}`);
  return { decision };
};

const comboGraph = new StateGraph({ stateSchema: ComboState })
  .addNode("evaluate", evaluateCombo)
  .addEdge(START, "evaluate")
  .addEdge("evaluate", END);

const comboApp = comboGraph.compile();

console.log("测试多条件判断:");
const comboTests = [
  { score: 95, attempts: 2, timeElapsed: 10 },
  { score: 85, attempts: 2, timeElapsed: 70 },
  { score: 25, attempts: 4, timeElapsed: 30 },
  { score: 50, attempts: 2, timeElapsed: 20 },
];

for (const test of comboTests) {
  const result = await comboApp.invoke(test);
  console.log(`  → ${result.decision}`);
}

// ============================================================================
// 3. LLM 驱动的条件判断
// ============================================================================

console.log("\n=== 3. LLM 驱动的条件判断 ===\n");

const LLMConditionState = Annotation.Root({
  query: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  classification: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  confidence: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
});

type LLMConditionStateType = typeof LLMConditionState.State;

const llmClassifyNode = async (state: LLMConditionStateType): Promise<Partial<LLMConditionStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.1 });

  const prompt = `分类以下查询，只返回类别名称 (technical/general/urgent):
查询: ${state.query}

分类:`;

  const response = await llm.invoke(prompt);
  const classification = (response.content as string).toLowerCase().trim();

  // 简单的置信度估算
  const confidence = classification.length > 0 ? 0.9 : 0.5;

  console.log(`[LLM分类] 查询: "${state.query}" → ${classification} (置信度: ${confidence})`);
  return { classification, confidence };
};

const llmGraph = new StateGraph({ stateSchema: LLMConditionState })
  .addNode("classify", llmClassifyNode)
  .addEdge(START, "classify")
  .addEdge("classify", END);

const llmApp = llmGraph.compile();

console.log("测试LLM驱动分类:");
const queries = [
  "如何修复 Python 中的内存泄漏？",
  "今天天气怎么样？",
  "紧急！服务器崩溃了！",
];

for (const query of queries) {
  const result = await llmApp.invoke({ query });
  console.log(`  "${query}" → ${result.classification}`);
}

// ============================================================================
// 4. 自适应工作流
// ============================================================================

console.log("\n=== 4. 自适应工作流 ===\n");

const AdaptiveState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  complexity: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  processed: Annotation<boolean>({
    reducer: (x, y) => y ?? x,
    default: () => false,
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type AdaptiveStateType = typeof AdaptiveState.State;

const analyzeComplexity = (state: AdaptiveStateType): Partial<AdaptiveStateType> => {
  const input = state.input;
  let complexity = "simple";

  // 分析复杂度
  const wordCount = input.split(/\s+/).length;
  const hasNumbers = /\d+/.test(input);
  const hasMultipleParts = input.includes("，") || input.includes("。");

  if (wordCount > 50 || (hasNumbers && hasMultipleParts)) {
    complexity = "complex";
  } else if (wordCount > 20 || hasNumbers || hasMultipleParts) {
    complexity = "medium";
  }

  console.log(`[复杂度分析] "${input.substring(0, 30)}..." → ${complexity}`);
  return { complexity };
};

const processSimple = (state: AdaptiveStateType): Partial<AdaptiveStateType> => {
  console.log("[简单处理] 快速响应");
  return {
    processed: true,
    result: `简单处理结果: ${state.input}`,
  };
};

const processMedium = (state: AdaptiveStateType): Partial<AdaptiveStateType> => {
  console.log("[中等处理] 标准流程");
  return {
    processed: true,
    result: `中等处理结果: ${state.input} (已分析)`,
  };
};

const processComplex = (state: AdaptiveStateType): Partial<AdaptiveStateType> => {
  console.log("[复杂处理] 深度分析");
  return {
    processed: true,
    result: `复杂处理结果: ${state.input} (已深度分析并优化)`,
  };
};

const routeByComplexity = (state: AdaptiveStateType): string => {
  return state.complexity || "simple";
};

const adaptiveGraph = new StateGraph({ stateSchema: AdaptiveState })
  .addNode("analyze", analyzeComplexity)
  .addNode("simple", processSimple)
  .addNode("medium", processMedium)
  .addNode("complex", processComplex)
  .addEdge(START, "analyze")
  .addConditionalEdges("analyze", routeByComplexity, {
    simple: "simple",
    medium: "medium",
    complex: "complex",
  })
  .addEdge("simple", END)
  .addEdge("medium", END)
  .addEdge("complex", END);

const adaptiveApp = adaptiveGraph.compile();

console.log("测试自适应工作流:");
const adaptiveTests = [
  "你好",
  "计算 123 + 456",
  "分析以下数据: 用户增长20%，收入增长15%，但成本增加了30%，请分析利润变化趋势并给出建议",
];

for (const test of adaptiveTests) {
  console.log(`\n输入: "${test.substring(0, 50)}${test.length > 50 ? "..." : ""}"`);
  const result = await adaptiveApp.invoke({ input: test });
  console.log(`复杂度: ${result.complexity}`);
  console.log(`结果: ${result.result}`);
}

// ============================================================================
// 5. 智能重试机制
// ============================================================================

console.log("\n=== 5. 智能重试机制 ===\n");

const RetryState = Annotation.Root({
  input: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  attempts: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  maxAttempts: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 3,
  }),
  lastError: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  success: Annotation<boolean>({
    reducer: (x, y) => y ?? x,
    default: () => false,
  }),
  result: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type RetryStateType = typeof RetryState.State;

const attemptOperation = async (state: RetryStateType): Promise<Partial<RetryStateType>> => {
  const attempt = state.attempts + 1;
  console.log(`[尝试] 第 ${attempt} 次`);

  // 模拟操作: 70% 成功率
  const success = Math.random() > 0.3;

  if (success) {
    console.log("  → 成功！");
    return {
      success: true,
      result: `操作成功 (尝试 ${attempt} 次)`,
    };
  } else {
    console.log("  → 失败");
    return {
      success: false,
      lastError: "操作失败",
      attempts: attempt,
    };
  }
};

const shouldRetry = (state: RetryStateType): string => {
  if (state.success) {
    return "end";
  }
  if (state.attempts >= state.maxAttempts) {
    return "fail";
  }
  return "retry";
};

const retryGraph = new StateGraph({ stateSchema: RetryState })
  .addNode("attempt", attemptOperation)
  .addEdge(START, "attempt")
  .addConditionalEdges("attempt", shouldRetry, {
    retry: "attempt",
    end: END,
    fail: END,
  });

const retryApp = retryGraph.compile();

console.log("测试智能重试:");
const retryResult = await retryApp.invoke({ input: "test operation", maxAttempts: 5 });
console.log(`\n最终结果: ${retryResult.result || "操作失败"}`);
console.log(`尝试次数: ${retryResult.attempts}/${retryResult.maxAttempts}`);

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 阈值判断 - 基于数值范围做决策");
console.log("2. 多条件组合 - 综合多个因素判断");
console.log("3. LLM 驱动 - 使用 AI 智能分类");
console.log("4. 自适应工作流 - 根据输入动态选择处理方式");
console.log("5. 智能重试 - 失败后自动重试");
console.log("\n条件逻辑设计原则:");
console.log("- 明确性: 条件清晰易懂");
console.log("- 可测试: 每个条件都可验证");
console.log("- 幂等性: 相同输入产生相同输出");
console.log("- 降级策略: 提供默认处理路径");
console.log("- 可观测: 记录决策过程");

export {
  thresholdApp,
  comboApp,
  llmApp,
  adaptiveApp,
  retryApp,
};
