/**
 * ========================================
 * Phase 3: Deep Agents 高级
 * Demo 01: Supervisor Pattern - 中心协调模式
 * ========================================
 *
 * 学习目标:
 * - 理解 Supervisor 模式架构
 * - 掌握多智能体协调
 * - 学习智能体间的通信
 * - 实现中心化的任务分配
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义团队状态
// ============================================================================

console.log("=== 1. Supervisor 模式架构 ===\n");

const TeamState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  next: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  teamMembers: Annotation<string[]>({
    reducer: (x, y) => y ?? x,
    default: () => ["researcher", "writer", "critic"],
  }),
});

type TeamStateType = typeof TeamState.State;

// ============================================================================
// 2. 定义 Supervisor 节点
// ============================================================================

const supervisorPrompt = `你是一个团队主管，负责协调团队成员完成任务。

团队成员:
- researcher: 研究员，负责收集信息和数据分析
- writer: 写作员，负责内容创作和整理
- critic: 评论员，负责质量审查和改进建议

工作流程:
1. 分析用户需求
2. 选择合适的团队成员处理任务
3. 根据成员输出决定下一步
4. 当任务完成时，标记为 END

输出格式: 只输出成员名称 (researcher/writer/critic) 或 END`;

const supervisorNode = async (state: TeamStateType): Promise<Partial<TeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.1 });

  const messages: BaseMessage[] = [
    new SystemMessage(supervisorPrompt),
    ...state.messages,
  ];

  console.log("\n[Supervisor] 决策中...");
  const response = await llm.invoke(messages);
  const next = (response.content as string).trim().toLowerCase();

  console.log(`[Supervisor] 选择: ${next}`);

  return { next };
};

// ============================================================================
// 3. 定义团队成员节点
// ============================================================================

const researcherPrompt = `你是一个专业的研究员。
你的任务是:
- 收集和分析信息
- 提供准确的数据和事实
- 回答研究相关问题

请用简洁专业的语言回答。`;

const researcherNode = async (state: TeamStateType): Promise<Partial<TeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.3 });

  const messages: BaseMessage[] = [
    new SystemMessage(researcherPrompt),
    ...state.messages,
  ];

  console.log("\n[Researcher] 研究中...");
  const response = await llm.invoke(messages);

  const result = `[研究员报告]: ${response.content}`;
  console.log(`[Researcher] 完成: ${result.substring(0, 50)}...`);

  return {
    messages: [new AIMessage(result)],
  };
};

const writerPrompt = `你是一个专业的写作员。
你的任务是:
- 创作清晰的内容
- 整理和组织信息
- 确保内容易读易懂

请用流畅的语言撰写内容。`;

const writerNode = async (state: TeamStateType): Promise<Partial<TeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });

  const messages: BaseMessage[] = [
    new SystemMessage(writerPrompt),
    ...state.messages,
  ];

  console.log("\n[Writer] 写作中...");
  const response = await llm.invoke(messages);

  const result = `[写作成果]: ${response.content}`;
  console.log(`[Writer] 完成: ${result.substring(0, 50)}...`);

  return {
    messages: [new AIMessage(result)],
  };
};

const criticPrompt = `你是一个专业的评论员。
你的任务是:
- 审查内容质量
- 提出改进建议
- 指出潜在问题

请提供建设性的反馈意见。`;

const criticNode = async (state: TeamStateType): Promise<Partial<TeamStateType>> => {
  const llm = createClaudeSonnet({ temperature: 0.2 });

  const messages: BaseMessage[] = [
    new SystemMessage(criticPrompt),
    ...state.messages,
  ];

  console.log("\n[Critic] 审查中...");
  const response = await llm.invoke(messages);

  const result = `[审查意见]: ${response.content}`;
  console.log(`[Critic] 完成: ${result.substring(0, 50)}...`);

  return {
    messages: [new AIMessage(result)],
  };
};

// ============================================================================
// 4. 路由函数
// ============================================================================

const routeToMember = (state: TeamStateType): string | typeof END => {
  const next = state.next;
  if (next === "end" || !next) {
    return END;
  }
  return next;
};

// ============================================================================
// 5. 构建团队图
// ============================================================================

console.log("构建团队协作图...\n");

const teamGraph = new StateGraph({ stateSchema: TeamState })
  .addNode("supervisor", supervisorNode)
  .addNode("researcher", researcherNode)
  .addNode("writer", writerNode)
  .addNode("critic", criticNode)
  .addEdge(START, "supervisor")
  .addConditionalEdges("supervisor", routeToMember, {
    researcher: "researcher",
    writer: "writer",
    critic: "critic",
    [END]: END,
  })
  .addEdge("researcher", "supervisor")
  .addEdge("writer", "supervisor")
  .addEdge("critic", "supervisor");

const teamApp = teamGraph.compile();

// ============================================================================
// 6. 测试团队协作
// ============================================================================

console.log("=".repeat(60));
console.log("测试 1: 简单研究任务");
console.log("=".repeat(60));

const test1 = await teamApp.invoke({
  messages: [new HumanMessage("请研究一下 TypeScript 的主要特性")],
  next: "",
});

console.log("\n最终消息数:", test1.messages.length);
console.log("\n最后一条消息:");
console.log((test1.messages[test1.messages.length - 1] as AIMessage).content);

console.log("\n" + "=".repeat(60));
console.log("测试 2: 内容创作任务");
console.log("=".repeat(60));

const test2 = await teamApp.invoke({
  messages: [new HumanMessage("写一篇关于 AI 未来发展的短文，需要研究、写作和审查")],
  next: "",
});

console.log("\n协作历史:");
test2.messages.forEach((msg, i) => {
  const role = msg instanceof HumanMessage ? "用户" : "AI";
  const content = String(msg.content).substring(0, 80);
  console.log(`[${i + 1}] ${role}: ${content}...`);
});

// ============================================================================
// 7. 流式输出团队协作过程
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("测试 3: 流式观察协作过程");
console.log("=".repeat(60));

const streamTest = await teamApp.invoke(
  {
    messages: [new HumanMessage("分析一下 LangGraph 的优势")],
    next: "",
  },
  { streamMode: "values" } as any
);

console.log("\n完整协作流程:");
for await (const event of await teamApp.stream(
  {
    messages: [new HumanMessage("分析一下 LangGraph 的优势")],
    next: "",
  }
)) {
  for (const [nodeName, nodeState] of Object.entries(event)) {
    if (nodeName !== "__start__" && nodeName !== "__end__") {
      console.log(`\n→ ${nodeName}`);
    }
  }
}

// ============================================================================
// 总结
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. Supervisor 模式 - 中心协调者分配任务");
console.log("2. 成员节点 - 各司其职的专业智能体");
console.log("3. 路由机制 - Supervisor 动态选择下一个执行者");
console.log("4. 反馈循环 - 成员完成后返回 Supervisor");
console.log("5. 协作流程 - START → Supervisor → Member → Supervisor → ... → END");
console.log("\nSupervisor 模式优势:");
console.log("- 集中控制: 统一的任务分配和决策");
console.log("- 灵活性: 动态选择执行路径");
console.log("- 可扩展: 容易添加新成员");
console.log("- 可观测: 清晰的执行流程");
console.log("\n适用场景:");
console.log("- 需要多步骤处理的复杂任务");
console.log("- 需要不同专业能力的场景");
console.log("- 需要质量审查的工作流");
console.log("- 需要灵活调整执行顺序");

export { teamApp, TeamState, TeamStateType };
