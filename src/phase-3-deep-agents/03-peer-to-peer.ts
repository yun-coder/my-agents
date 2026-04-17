/**
 * ========================================
 * Phase 3: Deep Agents 高级
 * Demo 03: Peer-to-Peer - 平等协作模式
 * ========================================
 *
 * 学习目标:
 * - 理解去中心化的智能体协作
 * - 掌握智能体间的直接通信
 * - 学习共识和决策机制
 * - 实现平等协作的工作流
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义协作状态
// ============================================================================

console.log("=== 1. Peer-to-Peer 协作架构 ===\n");

const CollaborationState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  task: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  proposals: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  consensus: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  votes: Annotation<Record<string, number>>({
    reducer: (x, y) => ({ ...x, ...y }),
    default: () => ({}),
  }),
});

type CollaborationStateType = typeof CollaborationState.State;

// ============================================================================
// 2. 定义智能体
// ============================================================================

const agents = [
  {
    name: "Alice",
    role: "创意专家",
    personality: "善于创新和发散思维",
    temperature: 0.9,
  },
  {
    name: "Bob",
    role: "技术专家",
    personality: "注重可行性和技术实现",
    temperature: 0.5,
  },
  {
    name: "Charlie",
    role: "用户 advocate",
    personality: "关注用户体验和需求",
    temperature: 0.6,
  },
  {
    name: "Diana",
    role: "质量专家",
    personality: "追求完美和质量",
    temperature: 0.4,
  },
];

console.log("协作团队成员:");
agents.forEach((agent) => {
  console.log(`  - ${agent.name}: ${agent.role} (${agent.personality})`);
});

// ============================================================================
// 3. 提案生成
// ============================================================================

const generateProposal = async (
  agent: typeof agents[0],
  task: string,
  context: BaseMessage[]
): Promise<string> => {
  const llm = createClaudeSonnet({ temperature: agent.temperature });

  const prompt = `你是 ${agent.name}，${agent.role}。
你的特点是: ${agent.personality}

任务: ${task}

${context.length > 0 ? `\n之前的讨论:\n${context.map((m) => `${m.constructor.name}: ${m.content}`).join("\n")}\n` : ""}

请根据你的专业视角，提出你的建议或方案。`;

  const response = await llm.invoke([new HumanMessage(prompt)]);

  return `${agent.name}: ${response.content}`;
};

const proposalRound = async (state: CollaborationStateType): Promise<Partial<CollaborationStateType>> => {
  console.log("\n--- 提案轮 ---");

  const proposals: string[] = [];
  const newMessages: BaseMessage[] = [];

  for (const agent of agents) {
    console.log(`[${agent.name}] 提出提案...`);
    const proposal = await generateProposal(agent, state.task, state.messages);
    proposals.push(proposal);
    newMessages.push(new AIMessage(proposal));
  }

  console.log(`\n收集到 ${proposals.length} 个提案`);

  return {
    proposals,
    messages: newMessages,
  };
};

// ============================================================================
// 4. 讨论和反馈
// ============================================================================

const discussionRound = async (state: CollaborationStateType): Promise<Partial<CollaborationStateType>> => {
  console.log("\n--- 讨论轮 ---");

  const newMessages: BaseMessage[] = [];

  for (const agent of agents) {
    console.log(`[${agent.name}] 提供反馈...`);

    const llm = createClaudeSonnet({ temperature: agent.temperature });

    const otherProposals = state.proposals.filter((p) => !p.startsWith(agent.name));

    const prompt = `你是 ${agent.name}，${agent.role}。

任务: ${state.task}

其他成员的提案:
${otherProposals.map((p) => `- ${p}`).join("\n")}

你的提案: ${state.proposals.find((p) => p.startsWith(agent.name))}

请对其他提案提供你的反馈意见（支持、反对或建议）。`;

    const response = await llm.invoke([new HumanMessage(prompt)]);
    newMessages.push(new AIMessage(`${agent.name}的反馈: ${response.content}`));
  }

  return {
    messages: newMessages,
  };
};

// ============================================================================
// 5. 投票决策
// ============================================================================

const votingRound = async (state: CollaborationStateType): Promise<Partial<CollaborationStateType>> => {
  console.log("\n--- 投票轮 ---");

  const votes: Record<string, number> = {};
  const newMessages: BaseMessage[] = [];

  for (const agent of agents) {
    console.log(`[${agent.name}] 投票...`);

    const llm = createClaudeSonnet({ temperature: 0.3 });

    const prompt = `你是 ${agent.name}。

任务: ${state.task}

所有提案:
${state.proposals.map((p, i) => `${i + 1}. ${p}`).join("\n")}

请选择你认为最好的提案序号 (1-${state.proposals.length})。

只回答一个数字。`;

    const response = await llm.invoke([new HumanMessage(prompt)]);
    const choice = parseInt((response.content as string).trim());

    if (!isNaN(choice) && choice >= 1 && choice <= state.proposals.length) {
      votes[state.proposals[choice - 1]] = (votes[state.proposals[choice - 1]] || 0) + 1;
      newMessages.push(new AIMessage(`${agent.name} 投票给提案 ${choice}`));
    }
  }

  console.log("\n投票结果:");
  Object.entries(votes).forEach(([proposal, count]) => {
    console.log(`  ${count} 票: ${proposal.substring(0, 50)}...`);
  });

  // 找出最高票的提案
  let maxVotes = 0;
  let consensus = "";
  for (const [proposal, count] of Object.entries(votes)) {
    if (count > maxVotes) {
      maxVotes = count;
      consensus = proposal;
    }
  }

  return {
    votes,
    consensus,
    messages: newMessages,
  };
};

// ============================================================================
// 6. 构建协作图
// ============================================================================

console.log("\n构建平等协作图...\n");

const shouldContinue = (state: CollaborationStateType): string => {
  // 如果没有共识或票数分散，继续讨论
  const maxVotes = Math.max(...Object.values(state.votes), 0);
  const totalAgents = agents.length;

  if (maxVotes >= Math.ceil(totalAgents / 2)) {
    return "end";
  }

  // 如果轮数过多，也结束
  if (state.messages.length > 50) {
    return "end";
  }

  return "continue";
};

const collaborationGraph = new StateGraph({ stateSchema: CollaborationState })
  .addNode("propose", proposalRound)
  .addNode("discuss", discussionRound)
  .addNode("vote", votingRound)
  .addEdge(START, "propose")
  .addEdge("propose", "discuss")
  .addEdge("discuss", "vote")
  .addConditionalEdges("vote", shouldContinue, {
    continue: "propose",
    end: END,
  });

const collaborationApp = collaborationGraph.compile();

// ============================================================================
// 7. 测试协作
// ============================================================================

console.log("=".repeat(60));
console.log("测试: Peer-to-Peer 协作");
console.log("=".repeat(60));

const testTask = "设计一个 AI 聊天机器人的核心功能";

console.log(`\n任务: ${testTask}\n`);

const collaborationResult = await collaborationApp.invoke({
  task: testTask,
});

console.log("\n" + "=".repeat(60));
console.log("协作结果");
console.log("=".repeat(60));
console.log("\n共识决策:");
console.log(collaborationResult.consensus);

console.log("\n最终投票:");
Object.entries(collaborationResult.votes).forEach(([proposal, count]) => {
  console.log(`  ${count} 票: ${proposal.substring(0, 80)}...`);
});

console.log("\n协作历史:");
console.log(`总消息数: ${collaborationResult.messages.length}`);

// ============================================================================
// 8. 其他协作模式
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("其他 Peer-to-Peer 协作模式");
console.log("=".repeat(60));

console.log(`
1. 轮流发言模式
   ┌─────┐    ┌─────┐    ┌─────┐
   │ A   │───▶│ B   │───▶│ C   │
   └─────┘    └─────┘    └─────┘
       │                      │
       └──────────────────────┘

   每个智能体依次发言，循环往复

2. 广播模式
           ┌─────────┐
       ┌───▶│  Topic  │───┐
       │    └─────────┘   │
   ┌───┴───┐         ┌───┴───┐
   │ Agent1│         │ Agent2│
   └───────┘         └───────┘
   ┌───────┐         ┌───────┐
   │ Agent3│         │ Agent4│
   └───────┘         └───────┘

   所有智能体接收同一消息，独立处理

3. 蜂群模式
   ╔═══════════════════════════╗
   ║      共享黑板/消息池       ║
   ╠═══════════════════════════╣
   ║ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ║
   ║ │ A │ │ B │ │ C │ │ D │ ║
   ║ └───┘ └───┘ └───┘ └───┘ ║
   ║                       ║
   ║ 任何智能体可读写任何消息 ║
   ╚═══════════════════════════╝

   智能体通过共享状态协作

4. 契约式模式
   ┌──────┐         ┌──────┐
   │Agent A│◀───────▶│Agent B│
   └──────┘  契约/协议  └──────┘

   基于预先定义的协议进行通信
`);

// ============================================================================
// 总结
// ============================================================================

console.log("=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 去中心化 - 无中心协调者");
console.log("2. 平等协作 - 所有智能体地位平等");
console.log("3. 提案机制 - 每个智能体提出方案");
console.log("4. 讨论反馈 - 智能体间互相交流");
console.log("5. 投票决策 - 通过投票达成共识");
console.log("\nP2P 模式优势:");
console.log("- 去中心化: 无单点故障");
console.log("- 多样性: 不同视角和创新");
console.log("- 鲁棒性: 部分失败不影响整体");
console.log("- 可扩展: 容易添加新成员");
console.log("\n适用场景:");
console.log("- 创意头脑风暴");
console.log("- 方案评审和决策");
console.log("- 分布式问题解决");
console.log("- 共识达成系统");

export { collaborationApp, agents };
