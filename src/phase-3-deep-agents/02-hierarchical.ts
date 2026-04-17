/**
 * ========================================
 * Phase 3: Deep Agents 高级
 * Demo 02: Hierarchical Teams - 层级团队
 * ========================================
 *
 * 学习目标:
 * - 理解层级式多智能体架构
 * - 掌握嵌套的团队协作
 * - 学习上下文传递和聚合
 * - 实现复杂的组织结构
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义层级状态
// ============================================================================

console.log("=== 1. 层级团队架构 ===\n");

// 子团队状态
const SubTeamState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  subTeamResult: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type SubTeamStateType = typeof SubTeamState.State;

// 主团队状态
const MainTeamState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  researchResult: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  contentResult: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  finalResult: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
});

type MainTeamStateType = typeof MainTeamState.State;

// ============================================================================
// 2. 研究子团队
// ============================================================================

console.log("构建研究子团队...");

const researcherNode = async (state: SubTeamStateType): Promise<Partial<SubTeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.3 });

  const prompt = `作为研究员，请分析以下内容并提供关键信息:
${state.messages.map((m) => m.content).join("\n")}`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  console.log("[研究子团队] 研究员完成分析");

  return {
    messages: [new AIMessage(`研究员: ${response.content}`)],
  };
};

const analystNode = async (state: SubTeamStateType): Promise<Partial<SubTeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.2 });

  const lastMessage = state.messages[state.messages.length - 1];

  const prompt = `作为分析师，请基于研究员的发现进行深度分析:
${lastMessage.content}`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  console.log("[研究子团队] 分析师完成深度分析");

  return {
    subTeamResult: `研究结论: ${response.content}`,
    messages: [new AIMessage(`分析师: ${response.content}`)],
  };
};

const researchSubTeam = new StateGraph({ stateSchema: SubTeamState })
  .addNode("researcher", researcherNode)
  .addNode("analyst", analystNode)
  .addEdge(START, "researcher")
  .addEdge("researcher", "analyst")
  .addEdge("analyst", END);

const researchSubTeamApp = researchSubTeam.compile();

// ============================================================================
// 3. 内容子团队
// ============================================================================

console.log("构建内容子团队...");

const writerNode = async (state: SubTeamStateType): Promise<Partial<SubTeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });

  const prompt = `作为写作员，请根据以下要求创作内容:
${state.messages.map((m) => m.content).join("\n")}`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  console.log("[内容子团队] 写作员完成创作");

  return {
    messages: [new AIMessage(`草稿: ${response.content}`)],
  };
};

const editorNode = async (state: SubTeamStateType): Promise<Partial<SubTeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.4 });

  const lastMessage = state.messages[state.messages.length - 1];

  const prompt = `作为编辑，请润色和完善以下草稿:
${lastMessage.content}`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  console.log("[内容子团队] 编辑完成润色");

  return {
    subTeamResult: `最终内容: ${response.content}`,
    messages: [new AIMessage(`编辑: ${response.content}`)],
  };
};

const contentSubTeam = new StateGraph({ stateSchema: SubTeamState })
  .addNode("writer", writerNode)
  .addNode("editor", editorNode)
  .addEdge(START, "writer")
  .addEdge("writer", "editor")
  .addEdge("editor", END);

const contentSubTeamApp = contentSubTeam.compile();

// ============================================================================
// 4. 主团队协调器
// ============================================================================

console.log("构建主团队...\n");

const coordinatorNode = (state: MainTeamStateType): Partial<MainTeamStateType> => {
  console.log("\n[主团队-协调器] 评估任务并分配给子团队");
  return {};
};

const invokeResearchTeam = async (state: MainTeamStateType): Promise<Partial<MainTeamStateType>> => {
  console.log("\n[主团队] 调用研究子团队...");

  const subResult = await researchSubTeamApp.invoke({
    messages: state.messages,
  });

  console.log("[主团队] 研究子团队返回结果");

  return {
    researchResult: subResult.subTeamResult,
    messages: [...state.messages, ...subResult.messages],
  };
};

const invokeContentTeam = async (state: MainTeamStateType): Promise<Partial<MainTeamStateType>> => {
  console.log("\n[主团队] 调用内容子团队...");

  const subResult = await contentSubTeamApp.invoke({
    messages: state.messages,
  });

  console.log("[主团队] 内容子团队返回结果");

  return {
    contentResult: subResult.subTeamResult,
    messages: [...state.messages, ...subResult.messages],
  };
};

const integratorNode = async (state: MainTeamStateType): Promise<Partial<MainTeamStateType>> => {
  console.log("\n[主团队-整合器] 汇总所有子团队结果");

  const llm = createClaudeSonnet({ temperature: 0.5 });

  const prompt = `作为整合专家，请将研究和内容团队的工作成果整合成一个完整的输出:

研究成果:
${state.researchResult}

内容成果:
${state.contentResult}

请提供整合后的最终结果。`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  console.log("[主团队-整合器] 完成整合");

  return {
    finalResult: response.content as string,
  };
};

const needsResearch = (state: MainTeamStateType): string => {
  const input = String(state.messages[0]?.content).toLowerCase();
  return input.includes("研究") || input.includes("分析") ? "research" : "content";
};

// ============================================================================
// 5. 构建主团队图
// ============================================================================

const mainTeamGraph = new StateGraph({ stateSchema: MainTeamState })
  .addNode("coordinator", coordinatorNode)
  .addNode("researchTeam", invokeResearchTeam)
  .addNode("contentTeam", invokeContentTeam)
  .addNode("integrator", integratorNode)
  .addEdge(START, "coordinator")
  .addConditionalEdges("coordinator", needsResearch, {
    research: "researchTeam",
    content: "contentTeam",
  })
  .addEdge("researchTeam", "contentTeam")
  .addEdge("contentTeam", "integrator")
  .addEdge("integrator", END);

const mainTeamApp = mainTeamGraph.compile();

// ============================================================================
// 6. 测试层级团队
// ============================================================================

console.log("=".repeat(60));
console.log("测试: 层级团队协作");
console.log("=".repeat(60));

const testInput = "请研究 TypeScript 的特性，并写一份介绍文档";

console.log(`\n用户输入: ${testInput}\n`);

const result = await mainTeamApp.invoke({
  messages: [new HumanMessage(testInput)],
});

console.log("\n" + "=".repeat(60));
console.log("最终结果:");
console.log("=".repeat(60));
console.log(result.finalResult);

// ============================================================================
// 7. 三层架构示例
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("扩展: 三层架构");
console.log("=".repeat(60));

console.log(`
层级团队架构示例:

┌─────────────────────────────────────────┐
│           战略层 (Supervisor)            │
│     - 任务分解和优先级管理                │
│     - 资源分配和协调                      │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼────┐   ┌───▼────┐   ┌───▼────┐
│ 研究团队 │   │ 内容团队 │   │ 技术团队 │
│ ○ 研究员 │   │ ○ 写作员 │   │ ○ 开发者 │
│ ○ 分析师 │   │ ○ 编辑  │   │ ○ 测试员 │
└─────────┘   └─────────┘   └─────────┘
    │             │             │
    └─────────────┴─────────────┘
                  │
            ┌─────▼─────┐
            │  执行层    │
            │ ○ 具体任务 │
            └───────────┘

优势:
- 清晰的责任划分
- 专业的子团队
- 高效的资源利用
- 可扩展的结构
`);

// ============================================================================
// 总结
// ============================================================================

console.log("=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 层级架构 - 多层级的智能体组织");
console.log("2. 子团队 - 独立的智能体小组");
console.log("3. 上下文传递 - 跨层级的信息流动");
console.log("4. 结果聚合 - 整合多个子团队的输出");
console.log("5. 嵌套执行 - 主团队调用子团队");
console.log("\n层级团队优势:");
console.log("- 专业化: 每个子团队专注特定领域");
console.log("- 可组合: 灵活组合不同子团队");
console.log("- 可扩展: 容易添加新的层级");
console.log("- 高效性: 并行处理独立任务");
console.log("\n适用场景:");
console.log("- 大型项目开发");
console.log("- 复杂任务分解");
console.log("- 跨领域协作");
console.log("- 企业级应用架构");

export { mainTeamApp, researchSubTeamApp, contentSubTeamApp };
