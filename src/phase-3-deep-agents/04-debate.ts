/**
 * ========================================
 * Phase 3: Deep Agents 高级
 * Demo 04: Debate Pattern - 辩论对抗模式
 * ========================================
 *
 * 学习目标:
 * - 理解对抗式智能体系统
 * - 掌握辩论和论证机制
 * - 学习观点合成和折中
 * - 实现质量优化的对抗系统
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { Annotation } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage, SystemMessage } from "@langchain/core/messages";
import { createClaudeSonnet } from "../shared/llm";

// ============================================================================
// 1. 定义辩论状态
// ============================================================================

console.log("=== 1. 辩论对抗架构 ===\n");

const DebateState = Annotation.Root({
  topic: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  rounds: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 0,
  }),
  maxRounds: Annotation<number>({
    reducer: (x, y) => y ?? x,
    default: () => 3,
  }),
  proArguments: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  conArguments: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  rebuttals: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  synthesis: Annotation<string>({
    reducer: (x, y) => y ?? x,
    default: () => "",
  }),
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
});

type DebateStateType = typeof DebateState.State;

// ============================================================================
// 2. 正方观点生成
// ============================================================================

const proAgentPrompt = `你是一个正方辩手。
你的任务是支持并论证给定的观点。

论证策略:
1. 提供有力的论据
2. 引用事实和数据
3. 使用逻辑推理
4. 预测并反驳反对意见

请用有说服力的语言提出你的论点。`;

const generateProArgument = async (state: DebateStateType): Promise<Partial<DebateState>> => {
  const llm = createClaudeSonnet({ temperature: 0.8 });

  console.log(`\n[正方] 第 ${state.rounds + 1} 轮 - 生成支持论点`);

  const prompt = `话题: ${state.topic}

${state.proArguments.length > 0 ? `\n之前的正方论点:\n${state.proArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}\n` : ""}
${state.conArguments.length > 0 ? `\n反方论点:\n${state.conArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}\n` : ""}

请提出支持该话题的新论点。`;

  const response = await llm.invoke([
    new SystemMessage(proAgentPrompt),
    new HumanMessage(prompt),
  ]);

  const argument = response.content as string;

  console.log(`[正方] 论点: ${argument.substring(0, 100)}...`);

  return {
    proArguments: [argument],
    messages: [new AIMessage(`正方论点 ${state.proArguments.length + 1}: ${argument}`)],
  };
};

// ============================================================================
// 3. 反方观点生成
// ============================================================================

const conAgentPrompt = `你是一个反方辩手。
你的任务是反对并质疑给定的观点。

论证策略:
1. 指出观点的问题和风险
2. 提供反面案例
3. 揭示逻辑漏洞
4. 质疑正方论据的有效性

请用批判性的思维提出反对意见。`;

const generateConArgument = async (state: DebateStateType): Promise<Partial<DebateState>> => {
  const llm = createClaudeSonnet({ temperature: 0.8 });

  console.log(`\n[反方] 第 ${state.rounds + 1} 轮 - 生成反对论点`);

  const prompt = `话题: ${state.topic}

${state.proArguments.length > 0 ? `\n正方论点:\n${state.proArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}\n` : ""}
${state.conArguments.length > 0 ? `\n之前的反方论点:\n${state.conArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}\n` : ""}

请提出反对该话题的新论点。`;

  const response = await llm.invoke([
    new SystemMessage(conAgentPrompt),
    new HumanMessage(prompt),
  ]);

  const argument = response.content as string;

  console.log(`[反方] 论点: ${argument.substring(0, 100)}...`);

  return {
    conArguments: [argument],
    messages: [new AIMessage(`反方论点 ${state.conArguments.length + 1}: ${argument}`)],
  };
};

// ============================================================================
// 4. 反驳和辩论
// ============================================================================

const generateRebuttal = async (state: DebateStateType): Promise<Partial<DebateState>> => {
  const llm = createClaudeSonnet({ temperature: 0.7 });

  console.log(`\n[辩论] 第 ${state.rounds + 1} 轮 - 反驳阶段`);

  const lastProArgument = state.proArguments[state.proArguments.length - 1];
  const lastConArgument = state.conArguments[state.conArguments.length - 1];

  const prompt = `话题: ${state.topic}

正方最新论点:
${lastProArgument}

反方最新论点:
${lastConArgument}

请双方进行互相反驳:
1. 正方对反方的反驳
2. 反方对正方的反驳

输出格式:
【正方反驳】...
【反方反驳】...`;

  const response = await llm.invoke([new HumanMessage(prompt)]);
  const rebuttalText = response.content as string;

  console.log(`[辩论] 反驳内容: ${rebuttalText.substring(0, 150)}...`);

  return {
    rebuttals: [rebuttalText],
    messages: [new AIMessage(`反驳 ${state.rebuttals.length + 1}:\n${rebuttalText}`)],
    rounds: state.rounds + 1,
  };
};

// ============================================================================
// 5. 观点合成
// ============================================================================

const synthesize = async (state: DebateStateType): Promise<Partial<DebateState>> => {
  const llm = createClaudeSonnet({ temperature: 0.5 });

  console.log("\n[合成器] 整合辩论结果");

  const prompt = `话题: ${state.topic}

经过 ${state.rounds} 轮辩论，以下是双方的主要论点:

正方论点:
${state.proArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}

反方论点:
${state.conArguments.map((a, i) => `${i + 1}. ${a}`).join("\n")}

请作为中立裁判:
1. 分析双方论点的优缺点
2. 辨别哪些论据最有说服力
3. 提供一个平衡的综合结论
4. 指出需要进一步探讨的问题

输出格式:
【正方优势】...
【反方优势】...
【综合结论】...
【建议】...`;

  const response = await llm.invoke([new HumanMessage(prompt)]);
  const synthesis = response.content as string;

  console.log("[合成器] 完成");

  return {
    synthesis,
    messages: [new AIMessage(`辩论总结:\n${synthesis}`)],
  };
};

// ============================================================================
// 6. 构建辩论图
// ============================================================================

console.log("构建辩论流程图...\n");

const shouldContinue = (state: DebateStateType): string => {
  return state.rounds < state.maxRounds ? "continue" : "synthesize";
};

const debateGraph = new StateGraph({ stateSchema: DebateState })
  .addNode("proArgument", generateProArgument)
  .addNode("conArgument", generateConArgument)
  .addNode("rebuttal", generateRebuttal)
  .addNode("synthesize", synthesize)
  .addEdge(START, "proArgument")
  .addEdge("proArgument", "conArgument")
  .addEdge("conArgument", "rebuttal")
  .addConditionalEdges("rebuttal", shouldContinue, {
    continue: "proArgument",
    synthesize: "synthesize",
  })
  .addEdge("synthesize", END);

const debateApp = debateGraph.compile();

// ============================================================================
// 7. 测试辩论系统
// ============================================================================

console.log("=".repeat(60));
console.log("测试: 辩论对抗系统");
console.log("=".repeat(60));

const debateTopic = "人工智能将取代人类大部分工作";

console.log(`\n辩论话题: ${debateTopic}\n`);

const debateResult = await debateApp.invoke({
  topic: debateTopic,
  maxRounds: 3,
});

console.log("\n" + "=".repeat(60));
console.log("辩论总结");
console.log("=".repeat(60));
console.log(debateResult.synthesis);

console.log("\n" + "=".repeat(60));
console.log("辩论统计");
console.log("=".repeat(60));
console.log(`辩论轮数: ${debateResult.rounds}`);
console.log(`正方论点数: ${debateResult.proArguments.length}`);
console.log(`反方论点数: ${debateResult.conArguments.length}`);
console.log(`反驳轮数: ${debateResult.rebuttals.length}`);

// ============================================================================
// 8. 其他对抗模式
// ============================================================================

console.log("\n" + "=".repeat(60));
console.log("其他对抗模式");
console.log("=".repeat(60));

console.log(`
1. 甲方-乙方模式
   ┌──────────┐         ┌──────────┐
   │ 甲方     │◀───────▶│ 乙方     │
   │ (提议)   │  协商   │ (评估)   │
   └──────────┘         └──────────┘

   模拟商业谈判、合同协商等场景

2. 审查者-改进者模式
   ┌──────────┐         ┌──────────┐
   │ 改进者   │───方案─▶│ 审查者   │
   │          │◀──反馈──│          │
   └──────────┘         └──────────┘

   持续改进和优化

3. 红队-蓝队模式
   ┌──────────┐         ┌──────────┐
   │ 红队     │   攻击   │ 蓝队     │
   │ (攻击者) │◀───────▶│ (防御者) │
   └──────────┘   防御   └──────────┘

   安全测试、对抗演练

4. 生成器-判别器模式
   ┌──────────┐         ┌──────────┐
   │ 生成器   │───内容─▶│ 判别器   │
   │ Generator│◀──评分──│Discriminator│
   └──────────┘  反馈    └──────────┘

   类似 GAN，通过对抗提升质量

5. 辩论者-调停者模式
   ┌────────┐
   │调停者  │
   └───┬────┘
       │
   ┌───┴──────────┐
   │              │
┌──▼───┐       ┌──▼───┐
│正方  │       │反方  │
└──────┘       └──────┘

   引入调停者促进建设性对话
`);

// ============================================================================
// 总结
// ============================================================================

console.log("=".repeat(60));
console.log("=== 本节要点总结 ===");
console.log("=".repeat(60));
console.log("1. 对抗式设计 - 正反方对抗");
console.log("2. 论点生成 - 各自支持立场");
console.log("3. 反驳机制 - 互相质疑和辩驳");
console.log("4. 观点合成 - 平衡的综合结论");
console.log("5. 质量优化 - 通过对抗提升");
console.log("\n对抗模式优势:");
console.log("- 全面性: 考虑多个视角");
console.log("- 鲁棒性: 发现潜在问题");
console.log("- 创新性: 激发新观点");
console.log("- 质量提升: 通过批判改进");
console.log("\n适用场景:");
console.log("- 决策分析");
console.log("- 方案评审");
console.log("- 内容优化");
console.log("- 风险评估");
console.log("- 学术辩论");

export { debateApp, DebateState, DebateStateType };
